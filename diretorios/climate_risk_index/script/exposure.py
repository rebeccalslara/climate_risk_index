import pandas as pd
from pathlib import Path
import unicodedata

# =========================
# FUNÇÃO PARA PADRONIZAR MUNICÍPIOS
# =========================

def normalize_text(text):
    if pd.isna(text):
        return text
    text = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('ASCII')
    return text.upper().strip()

# =========================
# CAMINHOS
# =========================

BASE_DIR = Path(r"C:\Users\rebecca-lara\Documents\Projetos\diretorios\climate_risk_index")

empregos_path = BASE_DIR / "data/raw_data/RAIS/Empregos.xlsx"
empresas_path = BASE_DIR / "data/raw_data/RAIS/Empresas.xlsx"
pop_path = BASE_DIR / "data/raw_data/RAIS/População.xlsx"

processed_dir = BASE_DIR / "data/processed_data"
processed_dir.mkdir(parents=True, exist_ok=True)

outputs_dir = BASE_DIR / "outputs"
outputs_dir.mkdir(parents=True, exist_ok=True)

# =========================
# CARREGAR DADOS
# =========================

df_empregos = pd.read_excel(empregos_path, sheet_name="Empregos_Industria")
df_empresas = pd.read_excel(empresas_path, sheet_name="Empresas_Industria")

# população (pula cabeçalho + total SC)
df_pop = pd.read_excel(pop_path, skiprows=4)
df_pop.columns = ["municipio", "populacao"]

# =========================
# RENOMEAR COLUNAS
# =========================

df_empregos = df_empregos.rename(columns={
    df_empregos.columns[0]: "municipio",
    df_empregos.columns[5]: "empregos"
})

df_empresas = df_empresas.rename(columns={
    df_empresas.columns[0]: "municipio",
    df_empresas.columns[5]: "empresas"
})

df_pop = df_pop.rename(columns={
    df_pop.columns[0]: "municipio",
    df_pop.columns[1]: "populacao"
})

# =========================
# LIMPEZA POPULAÇÃO
# =========================

df_pop = df_pop.dropna(subset=["municipio", "populacao"])

# REMOVE "(SC)"
df_pop["municipio"] = df_pop["municipio"].str.replace(r"\s*\(SC\)", "", regex=True)

# PADRONIZA
df_pop["municipio"] = df_pop["municipio"].apply(normalize_text)

# =========================
# PADRONIZAR MUNICÍPIOS
# =========================

df_empregos["municipio"] = df_empregos["municipio"].apply(normalize_text)
df_empresas["municipio"] = df_empresas["municipio"].apply(normalize_text)
df_pop["municipio"] = df_pop["municipio"].apply(normalize_text)

# =========================
# AGREGAÇÃO POR MUNICÍPIO
# =========================

empregos_mun = (
    df_empregos
    .groupby("municipio", as_index=False)["empregos"]
    .sum()
)

empresas_mun = (
    df_empresas
    .groupby("municipio", as_index=False)["empresas"]
    .sum()
)

# =========================
# MERGE DAS BASES
# =========================

df = empregos_mun.merge(empresas_mun, on="municipio", how="inner")

print("\nExemplo municípios base:")
print(df["municipio"].head(10))

print("\nExemplo municípios população:")
print(df_pop["municipio"].head(10))

# =========================
# CORREÇÕES MANUAIS DE MUNICÍPIOS
# =========================

correcoes = {
    "GRAO PARA": "GRAO-PARA",
}

df["municipio"] = df["municipio"].replace(correcoes)
df_pop["municipio"] = df_pop["municipio"].replace(correcoes)

# merge com população
df = df.merge(df_pop, on="municipio", how="left")

missing = df[df["populacao"].isna()]["municipio"]
print("\nMunicípios sem população:")
print(missing)

# =========================
# CHECAGENS
# =========================

print("\nPrévia da base consolidada:")
print(df.head())

print("\nTotal de municípios:", len(df))

missing_pop = df["populacao"].isna().sum()
print(f"\nMunicípios sem população: {missing_pop}")

# =========================
# SALVAR BASE CONSOLIDADA
# =========================

base_file = processed_dir / "exposure_sc_2025.csv"
df.to_csv(base_file, index=False)

print("\nArquivo base salvo em:", base_file)

# =========================
# CÁLCULO PER CAPITA
# =========================

df["empregos_pc"] = df["empregos"] / df["populacao"]
df["empresas_pc"] = df["empresas"] / df["populacao"]

print("\nPrévia per capita:")
print(df[["municipio", "empregos_pc", "empresas_pc"]].head())

# =========================
# NORMALIZAÇÃO (MIN-MAX)
# =========================

cols_pc = ["empregos_pc", "empresas_pc"]

df_norm = df.copy()

for col in cols_pc:
    min_val = df_norm[col].min()
    max_val = df_norm[col].max()
    
    print(f"{col}: min={min_val}, max={max_val}")
    
    df_norm[col] = (df_norm[col] - min_val) / (max_val - min_val)

# =========================
# CHECAGEM
# =========================

print("\nDados normalizados (per capita):")
print(df_norm[["municipio"] + cols_pc].head())

# =========================
# SALVAR NORMALIZADOS
# =========================

normalized_file = processed_dir / "exposure_per_capita_normalized_sc_2025.csv"
df_norm.to_csv(normalized_file, index=False)

print("\nArquivo normalizado salvo em:", normalized_file)

# =========================
# EXPOSURE INDEX PER CAPITA
# =========================

df_norm["exposure_index_pc"] = df_norm[cols_pc].mean(axis=1)

# =========================
# CHECAGEM FINAL
# =========================

print("\nPrévia do Exposure Index (per capita):")
print(df_norm[["municipio", "exposure_index_pc"]].head())

print("\nResumo estatístico do exposure_index_pc:")
print(df_norm["exposure_index_pc"].describe())

# =========================
# SALVAR ÍNDICE FINAL
# =========================

final_file = outputs_dir / "exposure_index_per_capita_sc_2025.csv"
df_norm.to_csv(final_file, index=False)

print("\nArquivo final salvo em:", final_file)