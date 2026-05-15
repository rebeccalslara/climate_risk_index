"""
ECONOMIC_IMPACT.PY - Environmental Fiscal Impact Model (2002-2023)

Goal:
  Estimate how changes in the normalized climate risk index are associated with
  municipal environmental expenses in Santa Catarina.

Model:
  log(real_environmental_expense_it) =
      beta0 * risk_norm_it
    + beta1 * risk_norm_i,t-1
    + beta2 * risk_norm_i,t-2
    + municipality fixed effects
    + year fixed effects
    + error_it

Important interpretation:
  Monetary impacts are expressed in each municipality's own environmental-expense
  scale. Values in reais are not directly comparable across municipalities because
  municipalities have different budget sizes and reporting structures.

Outputs:
  data/data_handling/economic_impact_raw_2002_2023.csv
  data/data_handling/economic_impact_model_data_2002_2023.csv
  output/economic_impact_results_2002_2023.csv
  output/economic_impact_municipal_2002_2023.csv
"""

from pathlib import Path
import unicodedata

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS


# =========================
# CONFIG
# =========================

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_HANDLING_DIR = BASE_DIR / "data" / "data_handling"
OUTPUT_DIR = BASE_DIR / "output"
RAW_SICONFI_DIR = BASE_DIR / "data" / "raw_data" / "SICONFI"
RAW_IPEADATA_DIR = BASE_DIR / "data" / "raw_data" / "IPEADATA"

DATA_HANDLING_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = list(range(2002, 2024))
DELTA_RISK = 0.1

RISK_PATH = OUTPUT_DIR / "climate_risk_index_2002_2023.csv"
FISCAL_PATH = RAW_SICONFI_DIR / "municipio_despesa_ambiental.csv"
IPCA_PATH = RAW_IPEADATA_DIR / "IPCA.xls"

EXPENSE_SCOPE = "environmental"
EXPENSE_LABEL = "Environmental expenses"

print("=" * 80)
print("ECONOMIC_IMPACT.PY - ENVIRONMENTAL FISCAL IMPACT MODEL (2002-2023)")
print("=" * 80)


# =========================
# HELPERS
# =========================

def normalize_text(text):
    """Normalize municipality and account labels consistently across project files."""
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


def clean_municipio_series(series):
    return series.apply(normalize_text).apply(harmonize_names)


def to_numeric(series):
    """Convert numeric values, accepting both decimal comma and decimal point."""
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    cleaned = series.astype(str).str.strip()
    has_decimal_comma = cleaned.str.contains(",", regex=False)
    cleaned = cleaned.where(
        ~has_decimal_comma,
        cleaned.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def pct_effect(beta, delta=DELTA_RISK):
    """Convert log-linear coefficient into percent effect for a risk-index change."""
    return np.exp(beta * delta) - 1


# =========================
# LOAD RISK PANEL
# =========================

print("\n[1/7] Loading climate risk panel...")

risk = pd.read_csv(RISK_PATH)
risk["municipio"] = clean_municipio_series(risk["municipio"])
risk["ano"] = pd.to_numeric(risk["ano"], errors="coerce").astype(int)
risk = risk[risk["ano"].isin(YEARS)].copy()

risk_cols = [
    "municipio", "ano", "risk_norm", "climate_risk_index",
    "hazard_index", "exposure_index", "vulnerability_index"
]
risk = risk[risk_cols].drop_duplicates(["municipio", "ano"])

print(f"  Risk records: {len(risk)}")
print(f"  Municipalities: {risk['municipio'].nunique()}")
print(f"  Years: {risk['ano'].min()}-{risk['ano'].max()}")


# =========================
# LOAD ENVIRONMENTAL FISCAL DATA
# =========================

print("\n[2/7] Loading SICONFI environmental expenses...")

fiscal = pd.read_csv(FISCAL_PATH, sep=";", encoding="utf-8")
fiscal["tipo_norm"] = fiscal["tipo_despesa"].apply(normalize_text)
fiscal = fiscal[fiscal["tipo_norm"] == "DESPESAS EMPENHADAS"].copy()

fiscal["municipio"] = clean_municipio_series(fiscal["nome_municipio"])
fiscal["ano"] = pd.to_numeric(fiscal["exercicio"], errors="coerce").astype(int)
fiscal["expense_nominal"] = to_numeric(fiscal["valor"])
fiscal = fiscal[fiscal["ano"].isin(YEARS)].copy()

fiscal = fiscal.groupby(["municipio", "ano"], as_index=False).agg({
    "codigo_ibge7": "first",
    "expense_nominal": "sum"
})

fiscal_names = set(fiscal["municipio"].unique())
risk_names = set(risk["municipio"].unique())

print(f"  Filtered fiscal records: {len(fiscal)}")
print(f"  Municipalities: {fiscal['municipio'].nunique()}")
print(f"  Years: {fiscal['ano'].min()}-{fiscal['ano'].max()}")
print(f"  Risk names not in fiscal: {len(risk_names - fiscal_names)}")
print(f"  Fiscal names not in risk: {len(fiscal_names - risk_names)}")


# =========================
# LOAD DEFLATOR
# =========================

print("\n[3/7] Loading IPCA deflator...")

ipca = pd.read_excel(IPCA_PATH)
ipca = ipca.rename(columns={"Data": "ano", "Indice": "ipca_index"})
ipca["ano"] = pd.to_numeric(ipca["ano"], errors="coerce").astype(int)
ipca["ipca_index"] = pd.to_numeric(ipca["ipca_index"], errors="coerce")
ipca = ipca[ipca["ano"].isin(YEARS)][["ano", "ipca_index"]].copy()

print(f"  IPCA records: {len(ipca)}")


# =========================
# BUILD PANEL
# =========================

print("\n[4/7] Building model panel and interpolating internal fiscal gaps...")

panel = (
    risk
    .merge(fiscal, on=["municipio", "ano"], how="left")
    .merge(ipca, on="ano", how="left")
)
panel["expense_scope"] = EXPENSE_SCOPE
panel["expense_label"] = EXPENSE_LABEL
panel["real_expense_original"] = (panel["expense_nominal"] / panel["ipca_index"]) * 100

panel = panel.sort_values(["municipio", "ano"]).copy()
panel["real_expense"] = (
    panel.groupby("municipio")["real_expense_original"]
    .transform(lambda s: s.interpolate(method="linear", limit_area="inside"))
)
panel["expense_interpolated"] = panel["real_expense_original"].isna() & panel["real_expense"].notna()
panel["expense_missing_after_interpolation"] = panel["real_expense"].isna()

missing_before = int(panel["real_expense_original"].isna().sum())
interpolated = int(panel["expense_interpolated"].sum())
missing_after = int(panel["expense_missing_after_interpolation"].sum())

print(f"  Missing before interpolation: {missing_before}")
print(f"  Interpolated municipality-years: {interpolated}")
print(f"  Missing after interpolation: {missing_after}")

raw_output = DATA_HANDLING_DIR / "economic_impact_raw_2002_2023.csv"
panel.to_csv(raw_output, index=False, encoding="utf-8")


# =========================
# LAGS AND MODEL DATA
# =========================

print("\n[5/7] Creating risk lags and model dataset...")

panel["risk_norm_lag1"] = panel.groupby("municipio")["risk_norm"].shift(1)
panel["risk_norm_lag2"] = panel.groupby("municipio")["risk_norm"].shift(2)
panel["log_real_expense"] = np.where(panel["real_expense"] > 0, np.log(panel["real_expense"]), np.nan)

model_cols = [
    "municipio", "ano", "log_real_expense",
    "risk_norm", "risk_norm_lag1", "risk_norm_lag2"
]
model_data = panel.dropna(subset=model_cols).copy()

model_output = DATA_HANDLING_DIR / "economic_impact_model_data_2002_2023.csv"
model_data.to_csv(model_output, index=False, encoding="utf-8")

print(f"  Model observations: {len(model_data)}")
print(f"  Model municipalities: {model_data['municipio'].nunique()}")
print(f"  Model years: {model_data['ano'].min()}-{model_data['ano'].max()}")


# =========================
# PANEL FIXED EFFECTS MODEL
# =========================

print("\n[6/7] Estimating panel fixed effects model...")

model_panel = model_data.set_index(["municipio", "ano"])
y = model_panel["log_real_expense"]
X = model_panel[["risk_norm", "risk_norm_lag1", "risk_norm_lag2"]]

model = PanelOLS(
    y,
    X,
    entity_effects=True,
    time_effects=True,
    drop_absorbed=True
)
results = model.fit(cov_type="clustered", cluster_entity=True)

print(results.summary)

params = results.params
std_errors = results.std_errors
pvalues = results.pvalues
conf_int = results.conf_int()

results_rows = []
for variable in params.index:
    beta = params[variable]
    results_rows.append({
        "expense_scope": EXPENSE_SCOPE,
        "expense_label": EXPENSE_LABEL,
        "variable": variable,
        "coefficient": beta,
        "std_error_cluster_municipio": std_errors[variable],
        "p_value": pvalues[variable],
        "conf_low": conf_int.loc[variable].iloc[0],
        "conf_high": conf_int.loc[variable].iloc[1],
        "pct_effect_0_1": pct_effect(beta),
        "pct_effect_0_1_percent": pct_effect(beta) * 100
    })

cumulative_beta = params[["risk_norm", "risk_norm_lag1", "risk_norm_lag2"]].sum()
results_rows.append({
    "expense_scope": EXPENSE_SCOPE,
    "expense_label": EXPENSE_LABEL,
    "variable": "risk_norm_cumulative_lag0_lag2",
    "coefficient": cumulative_beta,
    "std_error_cluster_municipio": np.nan,
    "p_value": np.nan,
    "conf_low": np.nan,
    "conf_high": np.nan,
    "pct_effect_0_1": pct_effect(cumulative_beta),
    "pct_effect_0_1_percent": pct_effect(cumulative_beta) * 100
})

results_df = pd.DataFrame(results_rows)
results_df["nobs"] = int(results.nobs)
results_df["n_municipalities"] = int(model_data["municipio"].nunique())
results_df["year_min"] = int(model_data["ano"].min())
results_df["year_max"] = int(model_data["ano"].max())
results_df["entity_effects"] = True
results_df["time_effects"] = True
results_df["dependent_variable"] = "log(real_environmental_expense)"
results_df["delta_risk"] = DELTA_RISK
results_df["interpretation_note"] = (
    "Monetary impacts are in each municipality's environmental-expense scale "
    "and are not directly comparable across municipalities."
)

results_output = OUTPUT_DIR / "economic_impact_results_2002_2023.csv"
results_df.to_csv(results_output, index=False, encoding="utf-8")


# =========================
# MUNICIPAL IMPACT ESTIMATES
# =========================

print("\n[7/7] Creating municipality-year monetary impact estimates...")

beta_0 = params["risk_norm"]
beta_1 = params["risk_norm_lag1"]
beta_2 = params["risk_norm_lag2"]

impact = panel.copy()
impact["pct_effect_0_1_same_year"] = pct_effect(beta_0)
impact["pct_effect_0_1_lag1"] = pct_effect(beta_1)
impact["pct_effect_0_1_lag2"] = pct_effect(beta_2)
impact["pct_effect_0_1_cumulative_lag0_lag2"] = pct_effect(cumulative_beta)

impact["impact_real_brl_0_1_same_year"] = impact["real_expense"] * impact["pct_effect_0_1_same_year"]
impact["impact_real_brl_0_1_lag1"] = impact["real_expense"] * impact["pct_effect_0_1_lag1"]
impact["impact_real_brl_0_1_lag2"] = impact["real_expense"] * impact["pct_effect_0_1_lag2"]
impact["impact_real_brl_0_1_cumulative_lag0_lag2"] = (
    impact["real_expense"] * impact["pct_effect_0_1_cumulative_lag0_lag2"]
)
impact["impact_comparability_note"] = (
    "Values in reais reflect each municipality's environmental-expense scale and "
    "should not be used as direct cross-municipality rankings."
)

impact_cols = [
    "expense_scope", "expense_label", "municipio", "ano",
    "risk_norm", "risk_norm_lag1", "risk_norm_lag2",
    "real_expense", "real_expense_original",
    "expense_interpolated", "expense_missing_after_interpolation",
    "pct_effect_0_1_same_year",
    "pct_effect_0_1_lag1",
    "pct_effect_0_1_lag2",
    "pct_effect_0_1_cumulative_lag0_lag2",
    "impact_real_brl_0_1_same_year",
    "impact_real_brl_0_1_lag1",
    "impact_real_brl_0_1_lag2",
    "impact_real_brl_0_1_cumulative_lag0_lag2",
    "impact_comparability_note"
]

impact_output = OUTPUT_DIR / "economic_impact_municipal_2002_2023.csv"
impact[impact_cols].to_csv(impact_output, index=False, encoding="utf-8")

print("\nSaved outputs:")
print(f"  {raw_output}")
print(f"  {model_output}")
print(f"  {results_output}")
print(f"  {impact_output}")

print("\nKey coefficients:")
print(results_df[["variable", "coefficient", "pct_effect_0_1_percent", "p_value"]].to_string(index=False))
print("\nDone.")
