"""
HAZARD.PY - Multi-Year Climate Hazard Index Processing (2002-2023)

Purpose:
  Process TerraClimate NetCDF files to extract climate hazard indicators
  for each SC municipality across 22 years (2002-2023)

Processing Pipeline:
  1. Load NetCDF files (def, ppt, tmax, tmin, ws) for each year
  2. Clip to SC boundaries to reduce memory
  3. Calculate 4 metrics per municipality per year:
     - def_mean: spatial mean of water deficit
     - ppt_std: temporal std of precipitation (12 months) → spatial mean
     - ws_std: temporal std of wind speed (12 months) → spatial mean
     - dtr_mean: spatial mean of diurnal temperature range (tmax - tmin)
  4. Normalize per year (min-max [0,1] independently)
  5. Calculate hazard_index = 0.5×(mean of 4 metrics) + 0.5×(max of 4 metrics)

Output Files:
  1. hazard_raw_2002_2023.csv: Raw metrics per municipality per year
  2. hazard_normalized_2002_2023.csv: Normalized metrics [0,1] per year
  3. hazard_index_2002_2023.csv: Final hazard index values

Expected Output: 295 municipalities × 22 years = 6,490 records per file
"""

from pathlib import Path
import xarray as xr
import geopandas as gpd
import rioxarray
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# ================================
# CONFIG
# ================================

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "raw_data" / "terraclimate"
SHAPE_PATH = BASE_DIR / "data" / "raw_data" / "shapes"
OUTPUT_PATH = BASE_DIR / "data" / "data_handling"
FINAL_OUTPUT_PATH = BASE_DIR / "output"

# Create output directory
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
FINAL_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

# SC Bounding box for clipping (reduces file size, saves memory)
SC_LAT_MIN, SC_LAT_MAX = -29.5, -25.8
SC_LON_MIN, SC_LON_MAX = -53.9, -48.3

# Years to process (2024-2025 excluded, as per requirement)
YEARS = list(range(2002, 2024))  # 2002-2023

print("=" * 80)
print("HAZARD.PY - MULTI-YEAR CLIMATE HAZARD INDEX PROCESSING (2002-2023)")
print("=" * 80)

# ================================
# FUNCTION: Load and clip NC file
# ================================

def load_and_clip_netcdf(file_name, year):
    """
    Load NetCDF file and clip to SC boundaries
    
    Args:
        file_name: Name of file to load (e.g., 'TerraClimate_def_2002.nc')
        year: Year for data (2002-2023)
    
    Returns:
        xarray.Dataset clipped to SC region
    """
    path = DATA_PATH / file_name
    
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    
    try:
        ds = xr.open_dataset(path, engine="netcdf4")
    except Exception as e:
        print(f"Error loading {file_name}: {e}")
        return None
    
    # Clip to SC boundaries
    try:
        ds = ds.sel(
            lat=slice(SC_LAT_MAX, SC_LAT_MIN),  # Note: reversed for ascending order
            lon=slice(SC_LON_MIN, SC_LON_MAX)
        )
        ds = ds.rio.write_crs("EPSG:4326")
    except Exception as e:
        print(f"Error clipping {file_name}: {e}")
        return None
    
    return ds

# ================================
# FUNCTION: Extract metrics for municipality
# ================================

def extract_municipality_metrics(def_clip, ppt_clip, ws_clip, dtr_clip, geom, gdf_crs):
    """
    Extract 4 hazard metrics for a single municipality from clipped NetCDF data
    
    Args:
        def_clip, ppt_clip, ws_clip, dtr_clip: Clipped xarray DataArrays
        geom: Municipality geometry for spatial clipping
        gdf_crs: CRS of the geometry
    
    Returns:
        tuple: (def_mean, ppt_std, ws_std, dtr_mean) or (None, None, None, None) on error
    """
    try:
        # ===== DEFICIT =====
        # Spatial mean of deficit across all grid cells in municipality
        def_clipped = def_clip.rio.clip([geom], gdf_crs, drop=True)
        def_mean = float(def_clipped["def"].mean().values)
        
        # ===== PRECIPITATION =====
        # Temporal std (across 12 monthly values) → then spatial mean
        ppt_clipped = ppt_clip.rio.clip([geom], gdf_crs, drop=True)
        
        if "time" in ppt_clipped["ppt"].dims and ppt_clipped["ppt"].count().values > 1:
            # Temporal std (if time dimension exists)
            ppt_temporal_std = ppt_clipped["ppt"].std(dim="time")
            # Spatial mean of the std
            ppt_std = float(ppt_temporal_std.mean().values)
        else:
            ppt_std = np.nan
        
        # ===== WIND SPEED =====
        # Temporal std (across 12 monthly values) → then spatial mean
        ws_clipped = ws_clip.rio.clip([geom], gdf_crs, drop=True)
        
        if "time" in ws_clipped["ws"].dims and ws_clipped["ws"].count().values > 1:
            # Temporal std
            ws_temporal_std = ws_clipped["ws"].std(dim="time")
            # Spatial mean of the std
            ws_std = float(ws_temporal_std.mean().values)
        else:
            ws_std = np.nan
        
        # ===== DTR (Diurnal Temperature Range) =====
        # Spatial mean of (tmax - tmin)
        dtr_clipped = dtr_clip.rio.clip([geom], gdf_crs, drop=True)
        dtr_mean = float(dtr_clipped.mean().values)
        
        return def_mean, ppt_std, ws_std, dtr_mean
    
    except Exception as e:
        return None, None, None, None

# ================================
# MAIN: Processing loop
# ================================

all_results = []

print(f"\nProcessing {len(YEARS)} years: {YEARS[0]}-{YEARS[-1]}")
print(f"Reading municipality boundaries from shapefile...")

# Load municipality shapefile once (reuse for all years)
gdf = gpd.read_file(SHAPE_PATH / "SC_Municipios_2025.shp", engine="pyogrio")
gdf = gdf.to_crs("EPSG:4326")
num_municipalities = len(gdf)

print(f"✓ Loaded {num_municipalities} municipalities from shapefile")
print("\n" + "=" * 80)

# ================================
# YEAR LOOP
# ================================

for year_idx, year in enumerate(YEARS, 1):
    print(f"\n[{year_idx}/{len(YEARS)}] Processing year {year}...")
    
    # ===== LOAD FILES =====
    file_def = f"TerraClimate_def_{year}.nc"
    file_ppt = f"TerraClimate_ppt_{year}.nc"
    file_ws = f"TerraClimate_ws_{year}.nc"
    file_tmax = f"TerraClimate_tmax_{year}.nc"
    file_tmin = f"TerraClimate_tmin_{year}.nc"
    
    try:
        print(f"  Loading NetCDF files...")
        ds_def = load_and_clip_netcdf(file_def, year)
        ds_ppt = load_and_clip_netcdf(file_ppt, year)
        ds_ws = load_and_clip_netcdf(file_ws, year)
        ds_tmax = load_and_clip_netcdf(file_tmax, year)
        ds_tmin = load_and_clip_netcdf(file_tmin, year)
        
        if any(ds is None for ds in [ds_def, ds_ppt, ds_ws, ds_tmax, ds_tmin]):
            print(f"  ✗ Error: Missing or corrupted NetCDF file for {year}")
            continue
        
        # ===== CREATE DTR =====
        # DTR = Diurnal Temperature Range = tmax - tmin
        dtr = ds_tmax["tmax"] - ds_tmin["tmin"]
        dtr.name = "dtr"
        dtr = dtr.rio.write_crs("EPSG:4326")
        
        print(f"  ✓ Loaded 5 variables + computed DTR for {year}")
        
    except Exception as e:
        print(f"  ✗ Error loading files for {year}: {e}")
        continue
    
    # ===== MUNICIPALITY LOOP =====
    year_records = 0
    
    for mun_idx, (idx, row) in enumerate(gdf.iterrows()):
        mun_name = row["NM_MUN"]
        geom = row.geometry
        
        try:
            # Extract 4 metrics
            def_mean, ppt_std, ws_std, dtr_mean = extract_municipality_metrics(
                ds_def, ds_ppt, ds_ws, dtr, geom, gdf.crs
            )
            
            # Handle NaN values
            if any(pd.isna(x) for x in [def_mean, ppt_std, ws_std, dtr_mean]):
                # Try with 0 instead of NaN for missing time dimension
                if pd.isna(ppt_std):
                    ppt_std = 0
                if pd.isna(ws_std):
                    ws_std = 0
                if pd.isna(dtr_mean):
                    dtr_mean = 0
            
            all_results.append({
                "municipio": mun_name,
                "ano": year,
                "def_mean": def_mean,
                "ppt_std": ppt_std,
                "ws_std": ws_std,
                "dtr_mean": dtr_mean
            })
            
            year_records += 1
        
        except Exception as e:
            print(f"  ✗ Error processing {mun_name} ({year}): {e}")
            all_results.append({
                "municipio": mun_name,
                "ano": year,
                "def_mean": np.nan,
                "ppt_std": np.nan,
                "ws_std": np.nan,
                "dtr_mean": np.nan
            })
    
    print(f"  ✓ Processed {year_records}/{num_municipalities} municipalities")
    
    # Close datasets to free memory
    ds_def.close()
    ds_ppt.close()
    ds_ws.close()
    ds_tmax.close()
    ds_tmin.close()

print("\n" + "=" * 80)

# ================================
# CREATE DATAFRAME & SAVE RAW
# ================================

print("\nCreating raw data dataframe...")
df_raw = pd.DataFrame(all_results)

# Verify completeness
expected_records = len(YEARS) * num_municipalities
actual_records = len(df_raw)

print(f"\nRAW DATA STATISTICS:")
print(f"  Expected records: {expected_records} ({num_municipalities} municipalities × {len(YEARS)} years)")
print(f"  Actual records: {actual_records}")
print(f"  Missing municipalities per year:")

for year in YEARS:
    year_count = len(df_raw[df_raw["ano"] == year])
    if year_count < num_municipalities:
        print(f"    {year}: {year_count}/{num_municipalities} (missing {num_municipalities - year_count})")

# Save raw data
output_raw = OUTPUT_PATH / "hazard_raw_2002_2023.csv"
df_raw.to_csv(output_raw, index=False)
print(f"\n✓ Saved: {output_raw}")

# ================================
# NORMALIZATION (MIN-MAX per year)
# ================================

print("\nNormalizing per year (min-max scaling [0,1])...")

df_norm = df_raw.copy()
norm_cols = ["def_mean", "ppt_std", "ws_std", "dtr_mean"]

for col in norm_cols:
    norm_col_name = f"{col}_norm"
    df_norm[norm_col_name] = 0.0
    
    for year in YEARS:
        # Get data for this year
        year_mask = df_norm["ano"] == year
        year_data = df_norm.loc[year_mask, col]
        
        # Min-max scaling
        min_val = year_data.min()
        max_val = year_data.max()
        
        if max_val - min_val == 0:
            df_norm.loc[year_mask, norm_col_name] = 0
        else:
            df_norm.loc[year_mask, norm_col_name] = (year_data - min_val) / (max_val - min_val)

print("✓ Normalization complete")

# Select normalized columns
norm_output_cols = ["municipio", "ano"] + [f"{col}_norm" for col in norm_cols]
df_norm_output = df_norm[norm_output_cols]

output_norm = OUTPUT_PATH / "hazard_normalized_2002_2023.csv"
df_norm_output.to_csv(output_norm, index=False)
print(f"✓ Saved: {output_norm}")

# ================================
# HAZARD INDEX CALCULATION
# ================================

print("\nCalculating hazard index...")

df_index = df_norm[["municipio", "ano"] + norm_cols].copy()

# Rename to normalized versions
for col in norm_cols:
    df_index[f"{col}_norm"] = df_norm[f"{col}_norm"]

norm_metric_cols = [f"{col}_norm" for col in norm_cols]

# Fill any remaining NaN with 0
df_index[norm_metric_cols] = df_index[norm_metric_cols].fillna(0)

# Calculate mean and max
df_index["hazard_mean"] = df_index[norm_metric_cols].mean(axis=1)
df_index["hazard_max"] = df_index[norm_metric_cols].max(axis=1)

# Calculate final index: 0.5 * mean + 0.5 * max
alpha = 0.5
df_index["hazard_index"] = (
    alpha * df_index["hazard_mean"] +
    (1 - alpha) * df_index["hazard_max"]
)

# Select final columns
df_index_output = df_index[["municipio", "ano", "hazard_mean", "hazard_max", "hazard_index"]]

output_index = FINAL_OUTPUT_PATH / "hazard_index_2002_2023.csv"
df_index_output.to_csv(output_index, index=False)
print(f"✓ Saved: {output_index}")

# ================================
# SUMMARY STATISTICS
# ================================

print("\n" + "=" * 80)
print("FINAL SUMMARY")
print("=" * 80)

print(f"\nDataset Completeness:")
print(f"  Total records: {len(df_index_output)}")
print(f"  Expected: {expected_records}")
print(f"  Status: {'✓ COMPLETE' if len(df_index_output) == expected_records else '✗ INCOMPLETE'}")

print(f"\nHazard Index Statistics by Year:")
print(f"\n{'Year':<6} {'Count':<8} {'Mean':<10} {'Std':<10} {'Min':<10} {'Max':<10}")
print("-" * 54)

for year in YEARS:
    year_data = df_index_output[df_index_output["ano"] == year]["hazard_index"]
    count = len(year_data)
    mean = year_data.mean()
    std = year_data.std()
    min_val = year_data.min()
    max_val = year_data.max()
    print(f"{year:<6} {count:<8} {mean:<10.4f} {std:<10.4f} {min_val:<10.4f} {max_val:<10.4f}")

# Overall statistics
print(f"\n{'TOTAL':<6} {len(df_index_output):<8} {df_index_output['hazard_index'].mean():<10.4f} {df_index_output['hazard_index'].std():<10.4f} {df_index_output['hazard_index'].min():<10.4f} {df_index_output['hazard_index'].max():<10.4f}")

print(f"\nTrend Analysis:")
mean_2002 = df_index_output[df_index_output["ano"] == 2002]["hazard_index"].mean()
mean_2023 = df_index_output[df_index_output["ano"] == 2023]["hazard_index"].mean()
change_pct = ((mean_2023 - mean_2002) / mean_2002) * 100
print(f"  2002 average hazard_index: {mean_2002:.4f}")
print(f"  2023 average hazard_index: {mean_2023:.4f}")
print(f"  Change: {change_pct:+.1f}%")

print(f"\nSample Records (First 10):")
print(df_index_output.head(10).to_string())

print(f"\nSample Records (Last 10):")
print(df_index_output.tail(10).to_string())

print("\n" + "=" * 80)
print("✓ HAZARD.PY PROCESSING COMPLETE")
print("=" * 80)
