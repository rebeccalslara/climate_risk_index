# ============================================
# CLIMATE RISK INDEX - FINAL PIPELINE (VERSÃO LIMPA)
# Risk = Hazard × Exposure × Vulnerability
# ============================================

import pandas as pd
from pathlib import Path
import unicodedata
import geopandas as gpd
import matplotlib.pyplot as plt

# =========================
# NORMALIZAÇÃO TEXTO
# =========================

def normalize_text(text):
    if pd.isna(text):
        return text
    text = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('ASCII')
    return text.upper().strip()

def harmonize_names(name):
    mapping = {
        "GRAO PARA": "GRAO PARA",
        "GRAO-PARA": "GRAO PARA",
        "GRÃO PARA": "GRAO PARA",
        "GRÃO-PARÁ": "GRAO PARA",
        "HERVAL D OESTE": "HERVAL D'OESTE",
    }
    return mapping.get(name, name)

# =========================
# CAMINHOS
# =========================

BASE_DIR = Path(r"C:\Users\rebecca-lara\Documents\Projetos\diretorios\climate_risk_index")

outputs_dir = BASE_DIR / "outputs"
outputs_dir.mkdir(parents=True, exist_ok=True)

processed_dir = BASE_DIR / "data/processed_data"

# ✔ SHAPEFILE CORRETO
shapefile_path = BASE_DIR / "data/raw_data/shapes/SC_Municipios_2025.shp"

# =========================
# CARREGAR DADOS
# =========================

df_vul = pd.read_csv(outputs_dir / "vulnerability_index_sc_2025.csv")
df_hazard = pd.read_csv(outputs_dir / "hazard_index_2025.csv")
df_exposure = pd.read_csv(outputs_dir / "exposure_index_per_capita_sc_2025.csv")

# ✔ SUBÍNDICES
df_hazard_sub = pd.read_csv(processed_dir / "hazard_sc_2025_normalized.csv")
df_exposure_sub = pd.read_csv(processed_dir / "exposure_per_capita_normalized_sc_2025.csv")

# =========================
# PADRONIZAR NOMES
# =========================

for df_temp in [df_vul, df_hazard, df_exposure, df_hazard_sub, df_exposure_sub]:
    df_temp["municipio"] = df_temp["municipio"].apply(normalize_text)
    df_temp["municipio"] = df_temp["municipio"].apply(harmonize_names)

# =========================
# MERGE COMPLETO
# =========================

df = df_vul.merge(
    df_hazard[["municipio", "hazard_index"]],
    on="municipio",
    how="inner"
).merge(
    df_exposure[["municipio", "exposure_index_pc"]],
    on="municipio",
    how="inner"
).merge(
    df_hazard_sub[["municipio", "def_mean", "ppt_std", "ws_std", "dtr_mean"]],
    on="municipio",
    how="left"
).merge(
    df_exposure_sub[["municipio", "empregos_pc", "empresas_pc"]],
    on="municipio",
    how="left"
)

print("\nTotal municípios após merge:", len(df))

# =========================
# CLIMATE RISK
# =========================

df["climate_risk_index"] = (
    df["hazard_index"] *
    df["exposure_index_pc"] *
    df["vulnerability_index"]
)

# =========================
# NORMALIZAÇÃO FINAL
# =========================

min_risk = df["climate_risk_index"].min()
max_risk = df["climate_risk_index"].max()

df["risk_norm"] = (
    (df["climate_risk_index"] - min_risk) / (max_risk - min_risk)
)

# =========================
# RANKING
# =========================

df["rank_risk"] = df["risk_norm"].rank(ascending=False, method="min")

# =========================
# ORGANIZAR COLUNAS (FORMATO FINAL)
# =========================

col_order = [
    "municipio",
    "energia_norm", "pib_pc_inv", "agro_pc_norm", "vulnerability_index",
    "def_mean", "ppt_std", "ws_std", "dtr_mean", "hazard_index",
    "empregos_pc", "empresas_pc", "exposure_index_pc",
    "climate_risk_index", "risk_norm", "rank_risk"
]

df = df[col_order]

# =========================
# OUTPUT 1 → BASE COMPLETA
# =========================

df.to_csv(outputs_dir / "climate_risk_index_sc_2025_new.csv", index=False)

# =========================
# OUTPUT 2 → RANKING LIMPO
# =========================

ranking = df.sort_values("risk_norm", ascending=False)[
    ["municipio", "risk_norm"]
]

ranking.to_csv(outputs_dir / "climate_risk_ranking_sc_2025_new.csv", index=False)

print("\n🔝 TOP 10 MAIS EM RISCO:")
print(ranking.head(10))

print("\n🔻 TOP 10 MENOR RISCO:")
print(ranking.tail(10))

# =========================
# RESUMO
# =========================

print("\n📊 RESUMO CLIMATE RISK INDEX")
print(df["climate_risk_index"].describe())

print("\n📊 QUANTIS")
print(df["risk_norm"].quantile([0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]))

# =========================
# MAPA
# =========================

print("\nGerando mapa...")

gdf_map = gpd.read_file(shapefile_path)

print("\nColunas do shapefile:")
print(gdf_map.columns)

# AJUSTAR SE NECESSÁRIO
col_mun = "NM_MUN"

gdf_map["municipio"] = gdf_map[col_mun].apply(normalize_text)
gdf_map["municipio"] = gdf_map["municipio"].apply(harmonize_names)

# diagnóstico
print("\nMatch mapa:")
print("Total shapefile:", len(gdf_map))
print("Match com dados:", gdf_map.merge(df, on="municipio", how="inner").shape[0])

# merge
gdf_final = gdf_map.merge(df, on="municipio", how="left")

# plot
fig, ax = plt.subplots(figsize=(10, 10))

gdf_final.plot(
    column="risk_norm",
    cmap="Reds",
    linewidth=0.2,
    edgecolor="black",
    legend=True,
    ax=ax
)

ax.set_title("Climate Risk Index - Santa Catarina (2025)")
ax.axis("off")

map_path = outputs_dir / "map_climate_risk_sc_2025.png"
plt.savefig(map_path, dpi=300, bbox_inches="tight")

print("\nMapa salvo em:", map_path)

# =========================
# STREAMLIT DATASET
# =========================

df_streamlit = df[
    [
        "municipio",
        "hazard_index",
        "exposure_index_pc",
        "vulnerability_index",
        "def_mean",
        "ppt_std",
        "ws_std",
        "dtr_mean",
        "empregos_pc",
        "empresas_pc",
        "climate_risk_index",
        "risk_norm",
        "rank_risk"
    ]
]

df_streamlit.to_csv(outputs_dir / "dashboard_dataset_sc_2025.csv", index=False)

print("\nBase completa para dashboard salva.")
