import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
import unicodedata
import warnings
warnings.filterwarnings('ignore')

# =========================
# FUNÇÃO PARA PADRONIZAR MUNICÍPIOS
# =========================

def normalize_text(text):
    """Normalize municipality names: remove accents, standardize case and spaces"""
    if pd.isna(text):
        return text
    text = str(text).strip()
    # Replace hyphens, underscores, and apostrophe variants with spaces
    # Handle all apostrophe/quote variants using character codes
    for char in ['-', '_', "'", '\u2019', '\u00B4', '`']:  # straight and curly quotes, accents
        text = text.replace(char, ' ')
    # Remove accents and convert to ASCII
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    # Uppercase and remove extra spaces
    text = text.upper().strip()
    # Replace multiple spaces with single space
    text = ' '.join(text.split())
    return text

# =========================
# CAMINHOS
# =========================

BASE_DIR = Path(r"C:\Users\rebecca-lara\Documents\Projetos\diretorios\climate_risk_index")

# Raw data paths
estabelecimentos_2021_2002_path = BASE_DIR / "data/raw_data/RAIS/Estabelecimentos - 2021 a 2002.csv"
estabelecimentos_2024_2022_path = BASE_DIR / "data/raw_data/RAIS/Estabelecimentos - 2024, 2023, 2022.csv"
vinculos_2021_2002_path = BASE_DIR / "data/raw_data/RAIS/Vinculos - 2021 a 2002.csv"
vinculos_2024_2022_path = BASE_DIR / "data/raw_data/RAIS/Vinculos - 2024, 2023, 2022.csv"
populacao_2000_2010_path = BASE_DIR / "data/raw_data/RAIS/População - 2000 e 2010.xlsx"
populacao_2022_path = BASE_DIR / "data/raw_data/RAIS/População 2022.xlsx"
mesoregiao_shapefile = BASE_DIR / "data/raw_data/shapes/42MEE250GC_SIR.shp"
municipios_shapefile = BASE_DIR / "data/raw_data/shapes/SC_Municipios_2025.shp"

# Output directory
data_handling_dir = BASE_DIR / "data/data_handling"
data_handling_dir.mkdir(parents=True, exist_ok=True)
output_dir = BASE_DIR / "output"
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("EXPOSURE.PY - MULTI-YEAR TIME SERIES PROCESSING (2002-2023)")
print("=" * 80)

# =========================
# 1. LOAD & PROCESS ESTABELECIMENTOS (COMPANIES)
# =========================

print("\n[1/5] Loading Estabelecimentos (Companies)...")

# Load 2021-2002
df_est_2021_2002 = pd.read_csv(estabelecimentos_2021_2002_path, skiprows=1, encoding='latin-1', sep=';')
print(f"  → 2021-2002: {df_est_2021_2002.shape[0]} rows")

# Load 2024-2022
df_est_2024_2022 = pd.read_csv(estabelecimentos_2024_2022_path, skiprows=1, encoding='latin-1', sep=';')
print(f"  → 2024-2022: {df_est_2024_2022.shape[0]} rows")

# Clean Estabelecimentos
def clean_estabelecimentos(df, year_cols):
    """Clean estabelecimentos data: remove prefix, melt years"""
    df = df.copy()
    
    # First column is municipio
    municipio_col = df.columns[0]
    df = df.rename(columns={municipio_col: "municipio"})
    
    # Remove "Sc-" or "SC-" prefix (case-insensitive)
    df["municipio"] = df["municipio"].str.replace(r"^Sc-", "", regex=True, case=False)
    df["municipio"] = df["municipio"].apply(normalize_text)
    
    # Filter out metadata rows - EXACT MATCH ONLY
    metadata_exact = {'TOTAL', 'IND RAIS NEGATIVA', 'SELECOES VIGENTES', 'ANO', 'VARIAVEL', 'IBGE GR SETOR'}
    df = df[~df["municipio"].isin(metadata_exact)]
    df = df[df["municipio"].notna()]
    df = df[df["municipio"].str.len() >= 3]  # Changed from > 3 to >= 3 to include ITA (3 chars)
    
    # Select only municipio and year columns
    df = df[["municipio"] + year_cols]
    
    # Melt: convert year columns to rows
    df = df.melt(id_vars=["municipio"], var_name="ano", value_name="estabelecimentos")
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    df = df.dropna(subset=["ano"])
    df["ano"] = df["ano"].astype(int)
    
    # Convert values to numeric, removing non-numeric rows
    df["estabelecimentos"] = pd.to_numeric(df["estabelecimentos"], errors="coerce")
    df = df.dropna(subset=["estabelecimentos"])
    
    return df

# Get year columns for each file
year_cols_2021_2002 = [str(year) for year in range(2021, 2001, -1)]  # 2021 to 2002
year_cols_2024_2022 = ["2024", "2023", "2022"]

df_est_2021_2002 = clean_estabelecimentos(df_est_2021_2002, year_cols_2021_2002)
df_est_2024_2022 = clean_estabelecimentos(df_est_2024_2022, year_cols_2024_2022)

# Combine both
df_estabelecimentos = pd.concat([df_est_2021_2002, df_est_2024_2022], ignore_index=True)
df_estabelecimentos = df_estabelecimentos.sort_values(["municipio", "ano"]).reset_index(drop=True)

print(f"\n✓ Estabelecimentos combined: {len(df_estabelecimentos)} rows")
print(f"  Years: {sorted(df_estabelecimentos['ano'].unique())}")
print(f"  Municipalities: {df_estabelecimentos['municipio'].nunique()}")

# =========================
# 2. LOAD & PROCESS VÍNCULOS (EMPLOYEES)
# =========================

print("\n[2/5] Loading Vínculos (Employees)...")

# Load 2021-2002
df_vinc_2021_2002 = pd.read_csv(vinculos_2021_2002_path, skiprows=1, encoding='latin-1', sep=';')
print(f"  → 2021-2002: {df_vinc_2021_2002.shape[0]} rows")

# Load 2024-2022
df_vinc_2024_2022 = pd.read_csv(vinculos_2024_2022_path, skiprows=1, encoding='latin-1', sep=';')
print(f"  → 2024-2022: {df_vinc_2024_2022.shape[0]} rows")

# Clean Vínculos
def clean_vinculos(df, year_cols):
    """Clean vínculos data: remove prefix, melt years"""
    df = df.copy()
    
    # First column is municipio
    municipio_col = df.columns[0]
    df = df.rename(columns={municipio_col: "municipio"})
    
    # Remove "SC-" prefix and normalize
    df["municipio"] = df["municipio"].str.replace(r"^SC-", "", regex=True, case=False)
    df["municipio"] = df["municipio"].apply(normalize_text)
    
    # Filter out metadata rows - EXACT MATCH ONLY
    metadata_exact = {'TOTAL', 'IND RAIS NEGATIVA', 'SELECOES VIGENTES', 'ANO', 'VARIAVEL', 'IBGE GR SETOR'}
    df = df[~df["municipio"].isin(metadata_exact)]
    df = df[df["municipio"].notna()]
    df = df[df["municipio"].str.len() >= 3]
    
    # Select only municipio and year columns
    df = df[["municipio"] + year_cols]
    
    # Melt: convert year columns to rows
    df = df.melt(id_vars=["municipio"], var_name="ano", value_name="empregos")
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    df = df.dropna(subset=["ano"])
    df["ano"] = df["ano"].astype(int)
    
    # Convert values to numeric, removing non-numeric rows
    df["empregos"] = pd.to_numeric(df["empregos"], errors="coerce")
    df = df.dropna(subset=["empregos"])
    
    return df

# Get year columns for each file
year_cols_vinc_2021_2002 = [str(year) for year in range(2021, 2001, -1)]  # 2021 to 2002
year_cols_vinc_2024_2022 = ["2024", "2023", "2022"]

df_vinc_2021_2002 = clean_vinculos(df_vinc_2021_2002, year_cols_vinc_2021_2002)
df_vinc_2024_2022 = clean_vinculos(df_vinc_2024_2022, year_cols_vinc_2024_2022)

# Combine both
df_vinculos = pd.concat([df_vinc_2021_2002, df_vinc_2024_2022], ignore_index=True)
df_vinculos = df_vinculos.sort_values(["municipio", "ano"]).reset_index(drop=True)

print(f"\n✓ Vínculos combined: {len(df_vinculos)} rows")
print(f"  Years: {sorted(df_vinculos['ano'].unique())}")
print(f"  Municipalities: {df_vinculos['municipio'].nunique()}")

# =========================
# 3. LOAD & PROCESS POPULATION (WITH INTERPOLATION)
# =========================

print("\n[3/5] Loading and Interpolating Population...")

# Load 2000 & 2010
df_pop_2000_2010 = pd.read_excel(populacao_2000_2010_path, skiprows=6)
print(f"  → 2000-2010: {df_pop_2000_2010.shape[0]} rows")

# Load 2022
df_pop_2022 = pd.read_excel(populacao_2022_path, skiprows=3)
print(f"  → 2022: {df_pop_2022.shape[0]} rows")

# Clean 2000-2010
df_pop_2000_2010.columns = ["municipio", "2000", "2010"]
df_pop_2000_2010["municipio"] = df_pop_2000_2010["municipio"].str.replace(r"\s*\(SC\)", "", regex=True)
df_pop_2000_2010["municipio"] = df_pop_2000_2010["municipio"].apply(normalize_text)

# Filter out metadata rows - keep only rows where municipio length >= 3 and doesn't contain numbers only
df_pop_2000_2010 = df_pop_2000_2010[df_pop_2000_2010["municipio"].notna()]
df_pop_2000_2010 = df_pop_2000_2010[df_pop_2000_2010["municipio"].str.len() >= 3]
df_pop_2000_2010 = df_pop_2000_2010[~df_pop_2000_2010["municipio"].str.isnumeric()]
df_pop_2000_2010 = df_pop_2000_2010.dropna(subset=["municipio", "2000", "2010"])

# Clean 2022
# Remove state total and NaN  
df_pop_2022 = df_pop_2022[df_pop_2022["municipio"].notna()]
df_pop_2022 = df_pop_2022[~df_pop_2022["municipio"].astype(str).str.contains("Santa Catarina", case=False, na=False)]
df_pop_2022.columns = ["municipio", "2022"]
df_pop_2022["municipio"] = df_pop_2022["municipio"].str.replace(r"\s*\(SC\)", "", regex=True)
df_pop_2022["municipio"] = df_pop_2022["municipio"].apply(normalize_text)

# Filter out metadata rows
df_pop_2022 = df_pop_2022[df_pop_2022["municipio"].notna()]
df_pop_2022 = df_pop_2022[df_pop_2022["municipio"].str.len() >= 3]
df_pop_2022 = df_pop_2022[~df_pop_2022["municipio"].str.isnumeric()]
df_pop_2022 = df_pop_2022.dropna(subset=["municipio", "2022"])

# Merge 2000-2010 with 2022
df_pop = df_pop_2000_2010.merge(df_pop_2022, on="municipio", how="outer")

# Deduplicate: in case normalize_text still produced variants, combine them
# This shouldn't be needed after the normalize_text fix, but adding as safety
df_pop_before_dedup = len(df_pop)
if df_pop_before_dedup > 295:
    print(f"\n  Deduplicating municipality names...")
    # Group by normalized version (in case trailing spaces or other issues)
    df_pop["municipio"] = df_pop["municipio"].str.strip()
    df_pop = df_pop.groupby("municipio", as_index=False).agg({
        "2000": lambda x: x.mean() if x.notna().any() else np.nan,
        "2010": lambda x: x.mean() if x.notna().any() else np.nan,
        "2022": lambda x: x.mean() if x.notna().any() else np.nan,
    })
    print(f"    Deduplicated: {df_pop_before_dedup} → {len(df_pop)} municipalities")

print(f"\n  Municipalities with data: {len(df_pop)}")
print(f"  Missing municipalities: {295 - len(df_pop)}")

# Melt to long format for interpolation
df_pop = df_pop.melt(id_vars=["municipio"], var_name="ano", value_name="populacao")
df_pop["ano"] = pd.to_numeric(df_pop["ano"], errors="coerce")
df_pop = df_pop.sort_values(["municipio", "ano"]).reset_index(drop=True)

# Identify missing municipalities
municipios_with_data = set(df_pop["municipio"].unique())
municipios_estabelecimentos = set(df_estabelecimentos["municipio"].unique())
municipios_vinculos = set(df_vinculos["municipio"].unique())
all_municipios_needed = municipios_estabelecimentos.union(municipios_vinculos)

missing_municipios = all_municipios_needed - municipios_with_data
print(f"\n  Missing municipalities in population data: {missing_municipios}")

# Pivot and interpolate
df_pop_pivot = df_pop.pivot_table(index="municipio", columns="ano", values="populacao", aggfunc="first")

# Handle missing municipalities with mesoregion average BEFORE interpolation
if missing_municipios:
    print(f"\n  Handling missing municipalities: {missing_municipios}")
    
    # Load mesoregion assignment
    gdf_municipios = gpd.read_file(municipios_shapefile, engine="pyogrio")
    gdf_meso = gpd.read_file(mesoregiao_shapefile, engine="pyogrio")
    
    # Normalize municipality names in shapefile
    gdf_municipios["NM_MUN_norm"] = gdf_municipios["NM_MUN"].apply(normalize_text)
    
    # Spatial join for mesoregion assignment
    gdf_centroids = gdf_municipios[["NM_MUN_norm", "geometry"]].copy()
    gdf_centroids["centroid"] = gdf_centroids["geometry"].centroid
    gdf_centroids = gdf_centroids.set_geometry("centroid")
    gdf_joined = gpd.sjoin(gdf_centroids, gdf_meso, how="left", predicate="within")
    
    # Create mesoregion mapping
    meso_map = dict(zip(gdf_joined["NM_MUN_norm"], gdf_joined["NM_MESO"]))
    
    # Fill missing municipalities with mesoregion average
    for missing_mun in missing_municipios:
        if missing_mun in meso_map:
            meso_name = meso_map[missing_mun]
            # Find all municipalities in same mesoregion that HAVE data
            meso_muns = [m for m, meso in meso_map.items() if meso == meso_name and m in df_pop_pivot.index]
            
            if meso_muns:
                # Calculate mesoregion average for years we have (2000, 2010, 2022)
                meso_avg = df_pop_pivot.loc[meso_muns].mean()
                df_pop_pivot.loc[missing_mun] = meso_avg
                print(f"    ✓ {missing_mun}: filled with {meso_name} mesoregion average")

# Handle municipalities with partial temporal coverage (in 2022 but missing from 2000-2010)
# These are: BALNEÁRIO RINÇÃO, PESCARIA BRAVA
print("\n  Handling municipalities with partial temporal coverage...")
municipalities_2022_only = set(df_pop.loc[df_pop["ano"] == 2022, "municipio"].unique()) - set(df_pop.loc[df_pop["ano"].isin([2000, 2010]), "municipio"].unique())

if municipalities_2022_only:
    print(f"    Found {len(municipalities_2022_only)} municipalities: {municipalities_2022_only}")
    
    # Load mesoregion mapping (if not already loaded)
    if 'meso_map' not in locals():
        gdf_municipios = gpd.read_file(municipios_shapefile, engine="pyogrio")
        gdf_meso = gpd.read_file(mesoregiao_shapefile, engine="pyogrio")
        gdf_municipios["NM_MUN_norm"] = gdf_municipios["NM_MUN"].apply(normalize_text)
        gdf_centroids = gdf_municipios[["NM_MUN_norm", "geometry"]].copy()
        gdf_centroids["centroid"] = gdf_centroids["geometry"].centroid
        gdf_centroids = gdf_centroids.set_geometry("centroid")
        gdf_joined = gpd.sjoin(gdf_centroids, gdf_meso, how="left", predicate="within")
        meso_map = dict(zip(gdf_joined["NM_MUN_norm"], gdf_joined["NM_MESO"]))
    
    for partial_mun in municipalities_2022_only:
        if partial_mun in meso_map:
            meso_name = meso_map[partial_mun]
            # Find municipalities in same mesoregion WITH 2000-2010 data
            meso_muns_with_data = [m for m, meso in meso_map.items() if meso == meso_name and m in df_pop.loc[df_pop["ano"].isin([2000, 2010]), "municipio"].values]
            
            if meso_muns_with_data:
                # Get mesoregion average for 2000 and 2010
                for year in [2000, 2010]:
                    year_avg = df_pop.loc[(df_pop["ano"] == year) & (df_pop["municipio"].isin(meso_muns_with_data)), "populacao"].mean()
                    if not pd.isna(year_avg):
                        new_row = pd.DataFrame({"municipio": [partial_mun], "ano": [year], "populacao": [year_avg]})
                        df_pop = pd.concat([df_pop, new_row], ignore_index=True)
                
                # Keep 2022 as is (already in df_pop)
                print(f"    ✓ {partial_mun}: filled 2000-2010 with {meso_name} mesoregion average, keeping 2022 actual data")

# Now interpolate ALL years from 2002-2023
all_years = list(range(2002, 2024))
df_pop_pivot_full = df_pop_pivot.copy()

# Reindex to include all years 2000-2023
all_years_full = list(range(2000, 2024))
df_pop_pivot = df_pop_pivot.reindex(columns=all_years_full)

# Interpolate linearly between all years
df_pop_pivot = df_pop_pivot.interpolate(method="linear", axis=1, limit_direction="both")

# Keep only years 2002-2023
df_pop_pivot = df_pop_pivot[[year for year in all_years if year in df_pop_pivot.columns]]

# Melt back to long format
df_pop_long = df_pop_pivot.reset_index().melt(id_vars=["municipio"], var_name="ano", value_name="populacao")
df_pop_long["ano"] = pd.to_numeric(df_pop_long["ano"], errors="coerce").astype(int)
df_pop_long = df_pop_long.sort_values(["municipio", "ano"]).reset_index(drop=True)

print(f"\n✓ Population interpolated: {len(df_pop_long)} rows")
print(f"  Municipalities: {df_pop_long['municipio'].nunique()}")

# =========================
# 4. SAVE POPULATION (SEPARATE FILE)
# =========================

print("\n[4/5] Saving Population Time Series...")

population_file = data_handling_dir / "population_interpolated_2002_2023.csv"
df_pop_long.to_csv(population_file, index=False)
print(f"✓ Saved: {population_file}")

# =========================
# 5. MERGE ALL & CALCULATE INDICES
# =========================

print("\n[5/5] Merging Data and Calculating Exposure Index...")

# Merge estabelecimentos + vinculos + population
df_combined = df_estabelecimentos.merge(df_vinculos, on=["municipio", "ano"], how="inner")
df_combined = df_combined.merge(df_pop_long, on=["municipio", "ano"], how="inner")

print(f"\nCombined data shape: {df_combined.shape}")
print(f"Year range: {df_combined['ano'].min()}-{df_combined['ano'].max()}")
print(f"Municipalities per year:")
print(df_combined.groupby("ano").size())

# Calculate per capita
df_combined["empregos_pc"] = df_combined["empregos"] / df_combined["populacao"]
df_combined["empresas_pc"] = df_combined["estabelecimentos"] / df_combined["populacao"]

# Normalize (min-max) separately by year to avoid distortion
print("\nNormalizing per capita indices...")

df_combined["empregos_pc_norm"] = np.nan
df_combined["empresas_pc_norm"] = np.nan

for year in sorted(df_combined["ano"].unique()):
    year_mask = df_combined["ano"] == year
    
    # Normalize empregos_pc
    min_emp = df_combined.loc[year_mask, "empregos_pc"].min()
    max_emp = df_combined.loc[year_mask, "empregos_pc"].max()
    norm_values = ((df_combined.loc[year_mask, "empregos_pc"] - min_emp) / (max_emp - min_emp)).values
    df_combined.loc[year_mask, "empregos_pc_norm"] = norm_values
    
    # Normalize empresas_pc
    min_emp_est = df_combined.loc[year_mask, "empresas_pc"].min()
    max_emp_est = df_combined.loc[year_mask, "empresas_pc"].max()
    norm_values_est = ((df_combined.loc[year_mask, "empresas_pc"] - min_emp_est) / (max_emp_est - min_emp_est)).values
    df_combined.loc[year_mask, "empresas_pc_norm"] = norm_values_est

# Calculate exposure index
df_combined["exposure_index"] = df_combined[["empregos_pc_norm", "empresas_pc_norm"]].mean(axis=1)

# Reorder columns
df_combined = df_combined[[
    "municipio", "ano", "empregos", "estabelecimentos", "populacao",
    "empregos_pc", "empresas_pc", "empregos_pc_norm", "empresas_pc_norm", "exposure_index"
]]

df_combined = df_combined.sort_values(["municipio", "ano"]).reset_index(drop=True)

# =========================
# 6. SAVE OUTPUTS
# =========================

print("\nSaving outputs...")

# Raw combined
raw_file = data_handling_dir / "exposure_raw_combined_2002_2023.csv"
df_combined[[
    "municipio", "ano", "empregos", "estabelecimentos", "populacao"
]].to_csv(raw_file, index=False)
print(f"✓ {raw_file}")

# Per capita normalized
normalized_file = data_handling_dir / "exposure_per_capita_normalized_2002_2023.csv"
df_combined[[
    "municipio", "ano", "empregos_pc", "empresas_pc",
    "empregos_pc_norm", "empresas_pc_norm"
]].to_csv(normalized_file, index=False)
print(f"✓ {normalized_file}")

# Final exposure index
index_file = output_dir / "exposure_index_2002_2023.csv"
df_combined[[
    "municipio", "ano", "exposure_index"
]].to_csv(index_file, index=False)
print(f"✓ {index_file}")

# =========================
# 7. SUMMARY & VALIDATION
# =========================

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\nFinal dataset shape: {df_combined.shape}")
print(f"Years covered: {sorted(df_combined['ano'].unique())}")
print(f"Municipalities: {df_combined['municipio'].nunique()}")
print(f"\nExposure Index Statistics:")
print(df_combined.groupby("ano")["exposure_index"].describe())

print("\n✓ All files saved to:", data_handling_dir)
