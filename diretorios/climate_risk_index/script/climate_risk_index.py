"""
CLIMATE_RISK_INDEX.PY - Multi-Year Climate Risk Index (2002-2023)

Risk = Hazard x Exposure x Vulnerability

Inputs:
  output/hazard_index_2002_2023.csv
  output/exposure_index_2002_2023.csv
  output/vulnerability_index_2002_2023.csv

Additional component inputs for dashboard/detail columns:
  data/data_handling/hazard_raw_2002_2023.csv
  data/data_handling/hazard_normalized_2002_2023.csv
  data/data_handling/exposure_per_capita_normalized_2002_2023.csv
  data/data_handling/vulnerability_normalized_2002_2023.csv

Outputs:
  output/climate_risk_index_2002_2023.csv
  output/dashboard_dataset_2002_2023.csv
  output/map_climate_risk_sc_2023.png
"""

from pathlib import Path
import unicodedata

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# =========================
# CONFIG
# =========================

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "output"
DATA_HANDLING_DIR = BASE_DIR / "data" / "data_handling"
SHAPEFILE_PATH = BASE_DIR / "data" / "raw_data" / "shapes" / "SC_Municipios_2025.shp"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = list(range(2002, 2024))
MAP_YEAR = 2023

print("=" * 80)
print("CLIMATE_RISK_INDEX.PY - MULTI-YEAR PIPELINE (2002-2023)")
print("=" * 80)


# =========================
# TEXT NORMALIZATION
# =========================

def normalize_text(text):
    """Normalize municipality names consistently across project files."""
    if pd.isna(text):
        return text

    text = str(text).strip()
    for char in ["-", "_", "'", "\u2019", "\u00B4", "`"]:
        text = text.replace(char, " ")

    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("ASCII")
    text = text.upper().strip()
    text = " ".join(text.split())
    return text


def harmonize_names(name):
    if pd.isna(name):
        return name

    mapping = {
        "GRAO-PARA": "GRAO PARA",
        "HERVAL DO OESTE": "HERVAL D OESTE",
        "LAGEADO GRANDE": "LAJEADO GRANDE",
        "LAURO MULLER (ARCRI)": "LAURO MULLER",
        "LAURO MULLER (ARTUB)": "LAURO MULLER",
        "PICARRAS": "BALNEARIO PICARRAS",
        "PRESIDENTE CASTELO BRANCO": "PRESIDENTE CASTELLO BRANCO",
        "SAO LOURENCO D OESTE": "SAO LOURENCO DO OESTE",
        "SAO MIGUEL D OESTE": "SAO MIGUEL DO OESTE",
    }
    return mapping.get(name, name)


def clean_municipio_column(df):
    df = df.copy()
    df["municipio"] = df["municipio"].apply(normalize_text).apply(harmonize_names)
    return df


def minmax_by_year(df, value_col, norm_col):
    df[norm_col] = np.nan
    for year in YEARS:
        mask = df["ano"] == year
        values = df.loc[mask, value_col]
        min_val = values.min()
        max_val = values.max()

        if pd.isna(min_val) or pd.isna(max_val) or max_val == min_val:
            df.loc[mask, norm_col] = 0.0
        else:
            df.loc[mask, norm_col] = (values - min_val) / (max_val - min_val)
    return df


def load_index(path, required_cols):
    df = pd.read_csv(path)
    df = clean_municipio_column(df)
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype(int)
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in {path.name}: {missing_cols}")
    return df[required_cols].drop_duplicates(["municipio", "ano"])


# =========================
# LOAD DATA
# =========================

print("\n[1/5] Loading sub-index files...")

df_hazard = load_index(
    OUTPUT_DIR / "hazard_index_2002_2023.csv",
    ["municipio", "ano", "hazard_mean", "hazard_max", "hazard_index"],
)
df_exposure = load_index(
    OUTPUT_DIR / "exposure_index_2002_2023.csv",
    ["municipio", "ano", "exposure_index"],
)
df_vulnerability = load_index(
    OUTPUT_DIR / "vulnerability_index_2002_2023.csv",
    ["municipio", "ano", "vulnerability_index"],
)

print(f"  Hazard records: {len(df_hazard)}")
print(f"  Exposure records: {len(df_exposure)}")
print(f"  Vulnerability records: {len(df_vulnerability)}")

print("\n[2/5] Loading detail component files...")

df_hazard_raw = pd.read_csv(DATA_HANDLING_DIR / "hazard_raw_2002_2023.csv")
df_hazard_raw = clean_municipio_column(df_hazard_raw)
df_hazard_raw["ano"] = pd.to_numeric(df_hazard_raw["ano"], errors="coerce").astype(int)

df_hazard_norm = pd.read_csv(DATA_HANDLING_DIR / "hazard_normalized_2002_2023.csv")
df_hazard_norm = clean_municipio_column(df_hazard_norm)
df_hazard_norm["ano"] = pd.to_numeric(df_hazard_norm["ano"], errors="coerce").astype(int)

df_exposure_detail = pd.read_csv(DATA_HANDLING_DIR / "exposure_per_capita_normalized_2002_2023.csv")
df_exposure_detail = clean_municipio_column(df_exposure_detail)
df_exposure_detail["ano"] = pd.to_numeric(df_exposure_detail["ano"], errors="coerce").astype(int)

df_vulnerability_detail = pd.read_csv(DATA_HANDLING_DIR / "vulnerability_normalized_2002_2023.csv")
df_vulnerability_detail = clean_municipio_column(df_vulnerability_detail)
df_vulnerability_detail["ano"] = pd.to_numeric(df_vulnerability_detail["ano"], errors="coerce").astype(int)


# =========================
# MERGE
# =========================

print("\n[3/5] Merging annual climate risk dataset...")

df = (
    df_hazard
    .merge(df_exposure, on=["municipio", "ano"], how="inner")
    .merge(df_vulnerability, on=["municipio", "ano"], how="inner")
    .merge(
        df_hazard_raw[[
            "municipio", "ano", "def_mean", "ppt_std", "ws_std", "dtr_mean"
        ]],
        on=["municipio", "ano"],
        how="left",
    )
    .merge(
        df_hazard_norm[[
            "municipio", "ano",
            "def_mean_norm", "ppt_std_norm", "ws_std_norm", "dtr_mean_norm"
        ]],
        on=["municipio", "ano"],
        how="left",
    )
    .merge(
        df_exposure_detail[[
            "municipio", "ano", "empregos_pc", "empresas_pc",
            "empregos_pc_norm", "empresas_pc_norm"
        ]],
        on=["municipio", "ano"],
        how="left",
    )
    .merge(
        df_vulnerability_detail[[
            "municipio", "ano", "energia_pc", "pib_real_pc", "agro_real_pc",
            "energia_pc_norm", "pib_pc_inv", "agro_pc_norm"
        ]],
        on=["municipio", "ano"],
        how="left",
    )
)

expected_records = 295 * len(YEARS)
print(f"  Records after merge: {len(df)}")
print(f"  Expected records: {expected_records}")
print(f"  Municipalities: {df['municipio'].nunique()}")
print(f"  Years: {df['ano'].min()}-{df['ano'].max()}")

if len(df) != expected_records:
    counts = df.groupby("ano").size()
    print("\n  WARNING: unexpected record count by year:")
    print(counts.to_string())


# =========================
# CLIMATE RISK
# =========================

print("\n[4/5] Calculating climate risk index...")

df["climate_risk_index"] = (
    df["hazard_index"] *
    df["exposure_index"] *
    df["vulnerability_index"]
)

df = minmax_by_year(df, "climate_risk_index", "risk_norm")
df["rank_risk"] = df.groupby("ano")["risk_norm"].rank(ascending=False, method="min")

col_order = [
    "municipio", "ano",
    "hazard_index", "exposure_index", "vulnerability_index",
    "climate_risk_index", "risk_norm", "rank_risk",
    "hazard_mean", "hazard_max",
    "def_mean", "ppt_std", "ws_std", "dtr_mean",
    "def_mean_norm", "ppt_std_norm", "ws_std_norm", "dtr_mean_norm",
    "empregos_pc", "empresas_pc", "empregos_pc_norm", "empresas_pc_norm",
    "energia_pc", "pib_real_pc", "agro_real_pc",
    "energia_pc_norm", "pib_pc_inv", "agro_pc_norm",
]

df = df[col_order].sort_values(["municipio", "ano"]).reset_index(drop=True)


# =========================
# SAVE OUTPUTS
# =========================

print("\n[5/5] Saving outputs...")

climate_risk_file = OUTPUT_DIR / "climate_risk_index_2002_2023.csv"
df.to_csv(climate_risk_file, index=False)
print(f"  Saved: {climate_risk_file}")

dashboard_file = OUTPUT_DIR / "dashboard_dataset_2002_2023.csv"
df.to_csv(dashboard_file, index=False)
print(f"  Saved: {dashboard_file}")


# =========================
# MAP FOR LATEST YEAR
# =========================

print(f"\nGenerating map for {MAP_YEAR}...")

gdf_map = gpd.read_file(SHAPEFILE_PATH, engine="pyogrio")
gdf_map["municipio"] = gdf_map["NM_MUN"].apply(normalize_text).apply(harmonize_names)

df_map_year = df[df["ano"] == MAP_YEAR]
map_matches = gdf_map.merge(df_map_year, on="municipio", how="inner").shape[0]
print(f"  Shapefile municipalities: {len(gdf_map)}")
print(f"  Matches with {MAP_YEAR} data: {map_matches}")

gdf_final = gdf_map.merge(df_map_year, on="municipio", how="left")

fig, ax = plt.subplots(figsize=(10, 10))
gdf_final.plot(
    column="risk_norm",
    cmap="Reds",
    linewidth=0.2,
    edgecolor="black",
    legend=True,
    ax=ax,
)

ax.set_title(f"Climate Risk Index - Santa Catarina ({MAP_YEAR})")
ax.axis("off")

map_path = OUTPUT_DIR / f"map_climate_risk_sc_{MAP_YEAR}.png"
plt.savefig(map_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"  Saved: {map_path}")


# =========================
# SUMMARY
# =========================

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print("\nMissing values:")
print(df.isna().sum().loc[lambda values: values > 0].to_string())

print("\nClimate Risk Index Statistics by Year:")
print(df.groupby("ano")["risk_norm"].describe())

latest_ranking = df[df["ano"] == MAP_YEAR].sort_values("rank_risk")

print(f"\nTOP 10 HIGHEST RISK - {MAP_YEAR}")
print(latest_ranking[[
    "municipio", "ano", "risk_norm", "rank_risk",
    "climate_risk_index", "hazard_index", "exposure_index", "vulnerability_index",
]].head(10).to_string(index=False))

print(f"\nTOP 10 LOWEST RISK - {MAP_YEAR}")
print(latest_ranking[[
    "municipio", "ano", "risk_norm", "rank_risk",
    "climate_risk_index", "hazard_index", "exposure_index", "vulnerability_index",
]].tail(10).sort_values("rank_risk", ascending=False).to_string(index=False))

print("\nDone.")
