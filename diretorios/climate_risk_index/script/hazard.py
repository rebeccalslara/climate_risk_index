from pathlib import Path
import shutil
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
DOWNLOADS_PATH = Path.home() / "Downloads"

DATA_PATH.mkdir(parents=True, exist_ok=True)

# ================================
# MOVER ARQUIVOS
# ================================

def move_nc_files():
    for file in DOWNLOADS_PATH.iterdir():
        if file.suffix == ".nc" and "TerraClimate" in file.name:
            dest = DATA_PATH / file.name
            if not dest.exists():
                print(f"Movendo {file.name}...")
                shutil.move(str(file), str(dest))

# ================================
# CARREGAR E RECORTAR SC
# ================================

def load_sc_dataset(file_name):
    path = DATA_PATH / file_name

    if not path.exists():
        raise FileNotFoundError(path)

    ds = xr.open_dataset(path, engine="netcdf4")

    ds = ds.sel(
        lat=slice(-25.8, -29.5),
        lon=slice(-53.9, -48.3)
    )

    ds = ds.rio.write_crs("EPSG:4326")

    return ds

# ================================
# EXECUÇÃO
# ================================

if __name__ == "__main__":

    move_nc_files()

    # =========================
    # CARREGAR DATASETS
    # =========================

    ds_def  = load_sc_dataset("TerraClimate_def_2025.nc")
    ds_ppt  = load_sc_dataset("TerraClimate_ppt_2025.nc")
    ds_ws   = load_sc_dataset("TerraClimate_ws_2025.nc")
    ds_tmax = load_sc_dataset("TerraClimate_tmax_2025.nc")
    ds_tmin = load_sc_dataset("TerraClimate_tmin_2025.nc")

    # =========================
    # CRIAR DTR
    # =========================

    dtr = ds_tmax["tmax"] - ds_tmin["tmin"]
    dtr.name = "dtr"
    dtr = dtr.rio.write_crs("EPSG:4326")

    # =========================
    # SHAPEFILE
    # =========================

    gdf = gpd.read_file(SHAPE_PATH / "SC_Municipios_2025.shp")
    gdf = gdf.to_crs("EPSG:4326")

    # =========================
    # LOOP MUNICÍPIOS
    # =========================

    results = []

    for idx, row in gdf.iterrows():
        geom = [row.geometry]

        try:
            # ======================
            # CLIP
            # ======================
            def_clip = ds_def.rio.clip(geom, gdf.crs, drop=True)
            ppt_clip = ds_ppt.rio.clip(geom, gdf.crs, drop=True)
            ws_clip  = ds_ws.rio.clip(geom, gdf.crs, drop=True)
            dtr_clip = dtr.rio.clip(geom, gdf.crs, drop=True)

            # ======================
            # CÁLCULOS
            # ======================
            def_mean = def_clip["def"].mean().values.item()

            # PPT STD
            if "time" in ppt_clip["ppt"].dims and ppt_clip["ppt"].count().values > 1:
                ppt_std = ppt_clip["ppt"].std(dim="time").mean().values.item()
            else:
                ppt_std = np.nan

            # WS STD
            if "time" in ws_clip["ws"].dims and ws_clip["ws"].count().values > 1:
                ws_std = ws_clip["ws"].std(dim="time").mean().values.item()
            else:
                ws_std = np.nan

            dtr_mean = dtr_clip.mean().values.item()

        except Exception as e:
            print(f"Erro no município {row['NM_MUN']}: {e}")
            def_mean = None
            ppt_std = None
            ws_std = None
            dtr_mean = None

        results.append({
            "municipio": row["NM_MUN"],
            "def_mean": def_mean,
            "ppt_std": ppt_std,
            "ws_std": ws_std,
            "dtr_mean": dtr_mean
        })

    # =========================
    # DATAFRAME FINAL
    # =========================

    df = pd.DataFrame(results)

    output = BASE_DIR / "hazard_sc_2025.csv"
    df.to_csv(output, index=False)

    print("\nArquivo final salvo em:", output)
    print(df.head())
    print("\nTotal de municípios:", len(df))

# =========================
# NORMALIZAÇÃO (MIN-MAX)
#=========================

df_norm = df.copy()

cols = ["def_mean", "ppt_std", "ws_std", "dtr_mean"]

for col in cols:
    min_val = df[col].min()
    max_val = df[col].max()

    if max_val - min_val == 0:
        df_norm[col] = 0
    else:
        df_norm[col] = (df[col] - min_val) / (max_val - min_val)

print("\nDados normalizados:")   
print(df_norm.head())
    
output_norm = BASE_DIR / "hazard_sc_2025_normalized.csv"

df_norm.to_csv(output_norm, index=False)

print("\nArquivo normalizado salvo em:", output_norm)

# =========================
# HAZARD INDEX (MÉDIA + MÁXIMO)
# =========================

# colunas dos subíndices
hazard_cols = ["def_mean", "ppt_std", "ws_std", "dtr_mean"]

# garantir que não há valores faltantes
df_norm[hazard_cols] = df_norm[hazard_cols].fillna(0)

# média dos subíndices
df_norm["hazard_mean"] = df_norm[hazard_cols].mean(axis=1)

# máximo dos subíndices
df_norm["hazard_max"] = df_norm[hazard_cols].max(axis=1)

# peso da média (ajustável)
alpha = 0.5

# índice final
df_norm["hazard_index"] = (
    alpha * df_norm["hazard_mean"] +
    (1 - alpha) * df_norm["hazard_max"]
)

# =========================
# CHECAGEM
# =========================

print("\nPrévia do Hazard Index:")
print(df_norm[["municipio", "hazard_mean", "hazard_max", "hazard_index"]].head())

print("\nResumo estatístico do hazard_index:")
print(df_norm["hazard_index"].describe())

# =========================
# SALVAR RESULTADO FINAL
# =========================

output_final = BASE_DIR / "hazard_index_2025.csv"

df_norm.to_csv(output_final, index=False)

print("\nArquivo com hazard index salvo em:", output_final)
