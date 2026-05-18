"""
ECONOMIC_IMPACT.PY - Environmental Fiscal Impact Model (2002-2023)

Goal:
  Estimate how changes in the normalized climate risk index are associated with
  municipal environmental expenses in Santa Catarina.

Model:
  log(real_environmental_expense_it) =
      beta0 * risk_mean_3yr_it
    + beta1 * log(real_transfer_revenue_it)
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
ENV_EXPENSE_PATH = RAW_SICONFI_DIR / "Interface com RSiconfi - Despesas Gestão Ambiental.xlsx"
TRANSFER_REVENUE_PATH = RAW_SICONFI_DIR / "municipio_receita_transferencia.csv"
IPCA_PATH = RAW_IPEADATA_DIR / "IPCA.xls"
VA_INDUSTRIAL_PATH = next(RAW_IPEADATA_DIR.glob("VA Industrial*.xls"))
VA_AGRO_PATH = RAW_IPEADATA_DIR / "VA Agro.xls"
VULNERABILITY_RAW_PATH = DATA_HANDLING_DIR / "vulnerability_raw_2002_2023.csv"

EXPENSE_SCOPE = "environmental"
EXPENSE_LABEL = "Environmental expenses"
GDP_SCOPE = "gdp_industrial_control"
GDP_LABEL = "Real GDP with industrial value-added control"
GDP_YEARS = list(range(2002, 2022))

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


def safe_log(series):
    """Return log for positive values only, leaving zero/negative/missing as NaN."""
    series = pd.to_numeric(series, errors="coerce")
    output = pd.Series(np.nan, index=series.index, dtype="float64")
    positive = series > 0
    output.loc[positive] = np.log(series.loc[positive])
    return output


def interpolate_inside_by_municipio(df, value_col, output_col):
    df = df.sort_values(["municipio", "ano"]).copy()
    df[output_col] = (
        df.groupby("municipio")[value_col]
        .transform(lambda s: s.interpolate(method="linear", limit_area="inside"))
    )
    return df


def load_va_panel(path, value_col, years):
    """Load a wide IPEADATA municipal value-added workbook into long format."""
    wide = pd.read_excel(path, sheet_name="Séries")
    year_cols = [
        col for col in wide.columns
        if str(col).isdigit() and int(col) in years
    ]
    long = wide.melt(
        id_vars=["Município"],
        value_vars=year_cols,
        var_name="ano",
        value_name=value_col
    )
    long["municipio"] = clean_municipio_series(long["Município"])
    long["ano"] = pd.to_numeric(long["ano"], errors="coerce").astype(int)
    long[value_col] = to_numeric(long[value_col])
    return long[["municipio", "ano", value_col]].drop_duplicates(["municipio", "ano"])


def fit_panel_spec(model_data, spec):
    """Fit one panel specification and return the linearmodels result object."""
    model_panel = model_data.set_index(["municipio", "ano"])
    y = model_panel["log_real_expense"]
    x_cols = [
        "risk_mean_3yr",
        "log_real_transfer_revenue",
    ]
    X = model_panel[x_cols].copy()

    if not spec["entity_effects"] and not spec["time_effects"]:
        X.insert(0, "constant", 1.0)

    model = PanelOLS(
        y,
        X,
        entity_effects=spec["entity_effects"],
        time_effects=spec["time_effects"],
        drop_absorbed=True
    )
    return model.fit(cov_type="clustered", cluster_entity=True)


def result_rows_from_spec(results, model_data, spec):
    params = results.params
    std_errors = results.std_errors
    pvalues = results.pvalues
    conf_int = results.conf_int()

    rows = []
    for variable in params.index:
        beta = params[variable]
        rows.append({
            "model_id": spec["model_id"],
            "model_label": spec["model_label"],
            "expense_scope": EXPENSE_SCOPE,
            "expense_label": EXPENSE_LABEL,
            "variable": variable,
            "coefficient": beta,
            "std_error_cluster_municipio": std_errors[variable],
            "p_value": pvalues[variable],
            "conf_low": conf_int.loc[variable].iloc[0],
            "conf_high": conf_int.loc[variable].iloc[1],
            "pct_effect_0_1": pct_effect(beta) if variable == "risk_mean_3yr" else np.nan,
            "pct_effect_0_1_percent": (
                pct_effect(beta) * 100 if variable == "risk_mean_3yr" else np.nan
            ),
            "nobs": int(results.nobs),
            "n_municipalities": int(model_data["municipio"].nunique()),
            "year_min": int(model_data["ano"].min()),
            "year_max": int(model_data["ano"].max()),
            "entity_effects": spec["entity_effects"],
            "time_effects": spec["time_effects"],
            "dependent_variable": "log(real_environmental_expense)",
            "delta_risk": DELTA_RISK,
            "controls": "log_real_transfer_revenue",
            "interpretation_note": (
                "Monetary impacts are in each municipality's environmental-expense scale "
                "and are not directly comparable across municipalities."
            )
        })
    return rows


def fit_gdp_panel_spec(model_data, spec):
    """Fit one GDP panel specification and return the linearmodels result object."""
    model_panel = model_data.set_index(["municipio", "ano"])
    y = model_panel["gdp_growth_log"]
    x_cols = [
        "risk_norm_without_GDP_lag1",
        "va_industrial_growth_log",
    ]
    X = model_panel[x_cols].copy()

    if not spec["entity_effects"] and not spec["time_effects"]:
        X.insert(0, "constant", 1.0)

    model = PanelOLS(
        y,
        X,
        entity_effects=spec["entity_effects"],
        time_effects=spec["time_effects"],
        drop_absorbed=True
    )
    return model.fit(cov_type="clustered", cluster_entity=True)


def fit_custom_panel_spec(model_data, spec, y_col, x_cols):
    """Fit a custom panel model used for GDP robustness checks."""
    model_panel = model_data.set_index(["municipio", "ano"])
    y = model_panel[y_col]
    X = model_panel[x_cols].copy()

    if not spec["entity_effects"] and not spec["time_effects"]:
        X.insert(0, "constant", 1.0)

    model = PanelOLS(
        y,
        X,
        entity_effects=spec["entity_effects"],
        time_effects=spec["time_effects"],
        drop_absorbed=True
    )
    return model.fit(cov_type="clustered", cluster_entity=True)


def gdp_result_rows_from_spec(results, model_data, spec):
    params = results.params
    std_errors = results.std_errors
    pvalues = results.pvalues
    conf_int = results.conf_int()

    rows = []
    for variable in params.index:
        beta = params[variable]
        rows.append({
            "model_id": spec["model_id"],
            "model_label": spec["model_label"],
            "model_scope": GDP_SCOPE,
            "model_description": GDP_LABEL,
            "variable": variable,
            "coefficient": beta,
            "std_error_cluster_municipio": std_errors[variable],
            "p_value": pvalues[variable],
            "conf_low": conf_int.loc[variable].iloc[0],
            "conf_high": conf_int.loc[variable].iloc[1],
            "pct_effect_0_1": (
                pct_effect(beta) if variable == "risk_norm_without_GDP_lag1" else np.nan
            ),
            "pct_effect_0_1_percent": (
                pct_effect(beta) * 100
                if variable == "risk_norm_without_GDP_lag1" else np.nan
            ),
            "nobs": int(results.nobs),
            "n_municipalities": int(model_data["municipio"].nunique()),
            "year_min": int(model_data["ano"].min()),
            "year_max": int(model_data["ano"].max()),
            "entity_effects": spec["entity_effects"],
            "time_effects": spec["time_effects"],
            "dependent_variable": "gdp_growth_log",
            "delta_risk": DELTA_RISK,
            "risk_variable": "risk_norm_without_GDP_lag1",
            "controls": "va_industrial_growth_log",
            "interpretation_note": (
                "The dependent variable is log(real_gdp_t) - log(real_gdp_t-1). "
                "The risk index excludes pib_pc_inv and enters lagged by one year. "
                "Industrial value added is already expressed in 2010 prices and "
                "enters as log growth."
            )
        })
    return rows


def robustness_result_rows(results, model_data, spec, test_id, test_label, y_col, x_cols, risk_col):
    params = results.params
    std_errors = results.std_errors
    pvalues = results.pvalues
    conf_int = results.conf_int()

    rows = []
    for variable in params.index:
        beta = params[variable]
        rows.append({
            "test_id": test_id,
            "test_label": test_label,
            "model_id": spec["model_id"],
            "model_label": spec["model_label"],
            "variable": variable,
            "coefficient": beta,
            "std_error_cluster_municipio": std_errors[variable],
            "p_value": pvalues[variable],
            "conf_low": conf_int.loc[variable].iloc[0],
            "conf_high": conf_int.loc[variable].iloc[1],
            "pct_effect_0_1": pct_effect(beta) if variable == risk_col else np.nan,
            "pct_effect_0_1_percent": (
                pct_effect(beta) * 100 if variable == risk_col else np.nan
            ),
            "nobs": int(results.nobs),
            "n_municipalities": int(model_data["municipio"].nunique()),
            "year_min": int(model_data["ano"].min()),
            "year_max": int(model_data["ano"].max()),
            "entity_effects": spec["entity_effects"],
            "time_effects": spec["time_effects"],
            "dependent_variable": y_col,
            "risk_variable": risk_col,
            "controls": ", ".join([col for col in x_cols if col != risk_col]),
            "delta_risk": DELTA_RISK,
        })
    return rows


# =========================
# LOAD RISK PANEL
# =========================

print("\n[1/8] Loading climate risk panel...")

risk = pd.read_csv(RISK_PATH)
risk["municipio"] = clean_municipio_series(risk["municipio"])
risk["ano"] = pd.to_numeric(risk["ano"], errors="coerce").astype(int)
risk = risk[risk["ano"].isin(YEARS)].copy()

risk_cols = [
    "municipio", "ano", "risk_norm", "climate_risk_index",
    "hazard_index", "exposure_index", "vulnerability_index",
    "energia_pc_norm", "agro_pc_norm"
]
risk = risk[risk_cols].drop_duplicates(["municipio", "ano"])

print(f"  Risk records: {len(risk)}")
print(f"  Municipalities: {risk['municipio'].nunique()}")
print(f"  Years: {risk['ano'].min()}-{risk['ano'].max()}")


# =========================
# LOAD ENVIRONMENTAL EXPENSES
# =========================

print("\n[2/8] Loading SICONFI environmental expenses...")

expense = pd.read_excel(ENV_EXPENSE_PATH, header=1)
expense["municipio"] = clean_municipio_series(expense["NO_ENTE"])
expense["ano"] = pd.to_numeric(expense["AN_EXERCICIO"], errors="coerce").astype(int)
expense["expense_nominal"] = to_numeric(expense["VALUE"])
expense = expense[expense["ano"].isin(YEARS)].copy()
expense = expense.groupby(["municipio", "ano"], as_index=False).agg({
    "ID_ENTE": "first",
    "expense_nominal": "sum"
})

print(f"  Filtered expense records: {len(expense)}")
print(f"  Municipalities: {expense['municipio'].nunique()}")
print(f"  Years: {expense['ano'].min()}-{expense['ano'].max()}")


# =========================
# LOAD REVENUE CONTROLS
# =========================

print("\n[3/8] Loading revenue controls...")

transfer_revenue = pd.read_csv(TRANSFER_REVENUE_PATH, sep=";", encoding="utf-8")
transfer_revenue["municipio"] = clean_municipio_series(transfer_revenue["nome_municipio"])
transfer_revenue["ano"] = pd.to_numeric(transfer_revenue["exercicio"], errors="coerce").astype(int)
transfer_revenue["transfer_revenue_nominal"] = to_numeric(transfer_revenue["valor"])
transfer_revenue = transfer_revenue[transfer_revenue["ano"].isin(YEARS)].copy()
transfer_revenue = transfer_revenue.groupby(["municipio", "ano"], as_index=False).agg({
    "transfer_revenue_nominal": "sum"
})

print(f"  Transfer revenue records: {len(transfer_revenue)}")
print(f"  Transfer revenue municipalities: {transfer_revenue['municipio'].nunique()}")


# =========================
# LOAD DEFLATOR
# =========================

print("\n[4/8] Loading IPCA deflator...")

ipca = pd.read_excel(IPCA_PATH)
ipca = ipca.rename(columns={"Data": "ano", "Indice": "ipca_index"})
ipca["ano"] = pd.to_numeric(ipca["ano"], errors="coerce").astype(int)
ipca["ipca_index"] = pd.to_numeric(ipca["ipca_index"], errors="coerce")
ipca = ipca[ipca["ano"].isin(YEARS)][["ano", "ipca_index"]].copy()

print(f"  IPCA records: {len(ipca)}")


# =========================
# BUILD PANEL
# =========================

print("\n[5/8] Building model panel and interpolating internal gaps...")

panel = (
    risk
    .merge(expense, on=["municipio", "ano"], how="left")
    .merge(transfer_revenue, on=["municipio", "ano"], how="left")
    .merge(ipca, on="ano", how="left")
)
panel["expense_scope"] = EXPENSE_SCOPE
panel["expense_label"] = EXPENSE_LABEL

panel["real_expense_original"] = (panel["expense_nominal"] / panel["ipca_index"]) * 100
panel["real_transfer_revenue_original"] = (
    panel["transfer_revenue_nominal"] / panel["ipca_index"]
) * 100
panel = interpolate_inside_by_municipio(panel, "real_expense_original", "real_expense")
panel = interpolate_inside_by_municipio(
    panel,
    "real_transfer_revenue_original",
    "real_transfer_revenue"
)

panel["expense_interpolated"] = panel["real_expense_original"].isna() & panel["real_expense"].notna()
panel["expense_missing_after_interpolation"] = panel["real_expense"].isna()
panel["transfer_revenue_interpolated"] = (
    panel["real_transfer_revenue_original"].isna() &
    panel["real_transfer_revenue"].notna()
)

print(f"  Missing expenses before interpolation: {int(panel['real_expense_original'].isna().sum())}")
print(f"  Interpolated expense municipality-years: {int(panel['expense_interpolated'].sum())}")
print(f"  Missing expenses after interpolation: {int(panel['expense_missing_after_interpolation'].sum())}")
print(f"  Missing transfer revenue after interpolation: {int(panel['real_transfer_revenue'].isna().sum())}")

raw_output = DATA_HANDLING_DIR / "economic_impact_raw_2002_2023.csv"
panel.to_csv(raw_output, index=False, encoding="utf-8")


# =========================
# LAGS AND MODEL DATA
# =========================

print("\n[6/8] Creating risk lags and model dataset...")

panel = panel.sort_values(["municipio", "ano"]).copy()
panel["risk_norm_lag1"] = panel.groupby("municipio")["risk_norm"].shift(1)
panel["risk_norm_lag2"] = panel.groupby("municipio")["risk_norm"].shift(2)
panel["risk_mean_3yr"] = panel[["risk_norm", "risk_norm_lag1", "risk_norm_lag2"]].mean(
    axis=1,
    skipna=False
)
panel["log_real_expense"] = safe_log(panel["real_expense"])
panel["log_real_transfer_revenue"] = safe_log(panel["real_transfer_revenue"])

model_cols = [
    "municipio", "ano", "log_real_expense",
    "risk_mean_3yr", "log_real_transfer_revenue"
]
model_data = panel.dropna(subset=model_cols).copy()

model_output = DATA_HANDLING_DIR / "economic_impact_model_data_2002_2023.csv"
model_data.to_csv(model_output, index=False, encoding="utf-8")

print(f"  Model observations: {len(model_data)}")
print(f"  Model municipalities: {model_data['municipio'].nunique()}")
print(f"  Model years: {model_data['ano'].min()}-{model_data['ano'].max()}")


# =========================
# PANEL MODEL COMPARISON
# =========================

print("\n[7/8] Estimating panel model comparison...")

model_specs = [
    {
        "model_id": "municipality_year_fe",
        "model_label": "Municipality FE + year FE",
        "entity_effects": True,
        "time_effects": True,
    },
    {
        "model_id": "municipality_fe_only",
        "model_label": "Municipality FE only",
        "entity_effects": True,
        "time_effects": False,
    },
    {
        "model_id": "year_fe_only",
        "model_label": "Year FE only",
        "entity_effects": False,
        "time_effects": True,
    },
    {
        "model_id": "no_fe",
        "model_label": "No fixed effects",
        "entity_effects": False,
        "time_effects": False,
    },
]

fitted_results = {}
results_rows = []
for spec in model_specs:
    print(f"\n--- {spec['model_label']} ---")
    fitted = fit_panel_spec(model_data, spec)
    fitted_results[spec["model_id"]] = fitted
    print(fitted.summary)
    results_rows.extend(result_rows_from_spec(fitted, model_data, spec))

results_df = pd.DataFrame(results_rows)

results_output = OUTPUT_DIR / "economic_impact_results_2002_2023.csv"
results_df.to_csv(results_output, index=False, encoding="utf-8")


# =========================
# MUNICIPAL IMPACT ESTIMATES
# =========================

print("\n[8/8] Creating municipality-year monetary impact estimates...")

preferred_results = fitted_results["municipality_year_fe"]
beta_risk = preferred_results.params["risk_mean_3yr"]

impact = panel.copy()
impact["pct_effect_0_1_risk_mean_3yr"] = pct_effect(beta_risk)
impact["impact_real_brl_0_1_risk_mean_3yr"] = (
    impact["real_expense"] * impact["pct_effect_0_1_risk_mean_3yr"]
)
impact["impact_comparability_note"] = (
    "Values in reais reflect each municipality's environmental-expense scale and "
    "should not be used as direct cross-municipality rankings."
)

impact_cols = [
    "expense_scope", "expense_label", "municipio", "ano",
    "risk_norm", "risk_norm_lag1", "risk_norm_lag2", "risk_mean_3yr",
    "real_expense", "real_expense_original",
    "real_transfer_revenue", "real_transfer_revenue_original",
    "expense_interpolated", "expense_missing_after_interpolation",
    "transfer_revenue_interpolated",
    "pct_effect_0_1_risk_mean_3yr",
    "impact_real_brl_0_1_risk_mean_3yr",
    "impact_comparability_note"
]

impact_output = OUTPUT_DIR / "economic_impact_municipal_2002_2023.csv"
impact[impact_cols].to_csv(impact_output, index=False, encoding="utf-8")


# =========================
# GDP GROWTH MODEL WITH INDUSTRIAL GROWTH CONTROL
# =========================

print("\n[GDP 1/4] Building risk index without GDP component...")

risk_without_gdp = risk.copy()
risk_without_gdp["vulnerability_index_without_GDP"] = risk_without_gdp[
    ["energia_pc_norm", "agro_pc_norm"]
].mean(axis=1)
risk_without_gdp["climate_risk_index_without_GDP"] = (
    risk_without_gdp["hazard_index"] *
    risk_without_gdp["exposure_index"] *
    risk_without_gdp["vulnerability_index_without_GDP"]
)

def normalize_by_year(series):
    min_value = series.min()
    max_value = series.max()
    if pd.isna(min_value) or pd.isna(max_value) or max_value == min_value:
        return pd.Series(0.0, index=series.index)
    return (series - min_value) / (max_value - min_value)

risk_without_gdp["risk_norm_without_GDP"] = (
    risk_without_gdp
    .groupby("ano")["climate_risk_index_without_GDP"]
    .transform(normalize_by_year)
)
risk_without_gdp = risk_without_gdp[
    [
        "municipio", "ano", "risk_norm_without_GDP",
        "hazard_index", "climate_risk_index_without_GDP",
        "vulnerability_index_without_GDP"
    ]
].copy()

print(f"  Risk-without-GDP records: {len(risk_without_gdp)}")
print(f"  Municipalities: {risk_without_gdp['municipio'].nunique()}")

print("\n[GDP 2/4] Loading real GDP and industrial value added...")

gdp = pd.read_csv(VULNERABILITY_RAW_PATH)
gdp["municipio"] = clean_municipio_series(gdp["municipio"])
gdp["ano"] = pd.to_numeric(gdp["ano"], errors="coerce").astype(int)
gdp["real_gdp"] = to_numeric(gdp["pib_real_mil_reais"])
gdp = gdp[gdp["ano"].isin(GDP_YEARS)][["municipio", "ano", "real_gdp"]].copy()

va_industrial = load_va_panel(VA_INDUSTRIAL_PATH, "va_industrial_2010", GDP_YEARS)
va_agro = load_va_panel(VA_AGRO_PATH, "va_agro_2010", GDP_YEARS)

print(f"  GDP records: {len(gdp)}")
print(f"  GDP municipalities: {gdp['municipio'].nunique()}")
print(f"  VA industrial records: {len(va_industrial)}")
print(f"  VA industrial municipalities: {va_industrial['municipio'].nunique()}")
print(f"  VA agro records: {len(va_agro)}")
print(f"  VA agro municipalities: {va_agro['municipio'].nunique()}")

print("\n[GDP 3/4] Creating GDP model dataset...")

gdp_panel = (
    risk_without_gdp[risk_without_gdp["ano"].isin(GDP_YEARS)]
    .merge(gdp, on=["municipio", "ano"], how="left")
    .merge(va_industrial, on=["municipio", "ano"], how="left")
    .merge(va_agro, on=["municipio", "ano"], how="left")
)
gdp_panel = gdp_panel.sort_values(["municipio", "ano"]).copy()
gdp_panel["risk_norm_without_GDP_lag1"] = (
    gdp_panel.groupby("municipio")["risk_norm_without_GDP"].shift(1)
)
gdp_panel["hazard_index_lag1"] = (
    gdp_panel.groupby("municipio")["hazard_index"].shift(1)
)
gdp_panel["hazard_index_lag2"] = (
    gdp_panel.groupby("municipio")["hazard_index"].shift(2)
)
gdp_panel["risk_norm_without_GDP_lag2"] = (
    gdp_panel.groupby("municipio")["risk_norm_without_GDP"].shift(2)
)
gdp_panel["risk_mean_3yr_without_GDP"] = gdp_panel[
    ["risk_norm_without_GDP", "risk_norm_without_GDP_lag1", "risk_norm_without_GDP_lag2"]
].mean(axis=1, skipna=False)
gdp_panel["log_real_gdp"] = safe_log(gdp_panel["real_gdp"])
gdp_panel["log_va_industrial_2010"] = safe_log(gdp_panel["va_industrial_2010"])
gdp_panel["log_va_agro_2010"] = safe_log(gdp_panel["va_agro_2010"])
gdp_panel["gdp_growth_log"] = (
    gdp_panel.groupby("municipio")["log_real_gdp"].diff()
)
gdp_panel["va_industrial_growth_log"] = (
    gdp_panel.groupby("municipio")["log_va_industrial_2010"].diff()
)
gdp_panel["va_agro_growth_log"] = (
    gdp_panel.groupby("municipio")["log_va_agro_2010"].diff()
)

gdp_model_cols = [
    "municipio", "ano", "gdp_growth_log",
    "risk_norm_without_GDP_lag1", "va_industrial_growth_log"
]
gdp_model_data = gdp_panel.dropna(subset=gdp_model_cols).copy()

gdp_raw_output = DATA_HANDLING_DIR / "gdp_growth_impact_raw_2002_2021.csv"
gdp_model_output = DATA_HANDLING_DIR / "gdp_growth_impact_model_data_2002_2021.csv"
gdp_panel.to_csv(gdp_raw_output, index=False, encoding="utf-8")
gdp_model_data.to_csv(gdp_model_output, index=False, encoding="utf-8")

print(f"  GDP model observations: {len(gdp_model_data)}")
print(f"  GDP model municipalities: {gdp_model_data['municipio'].nunique()}")
print(f"  GDP model years: {gdp_model_data['ano'].min()}-{gdp_model_data['ano'].max()}")
print(f"  Missing GDP values: {int(gdp_panel['real_gdp'].isna().sum())}")
print(f"  Missing VA industrial values: {int(gdp_panel['va_industrial_2010'].isna().sum())}")
print(f"  Missing VA agro values: {int(gdp_panel['va_agro_2010'].isna().sum())}")

print("\n[GDP 4/4] Estimating GDP panel model comparison...")

gdp_fitted_results = {}
gdp_results_rows = []
for spec in model_specs:
    print(f"\n--- GDP: {spec['model_label']} ---")
    fitted = fit_gdp_panel_spec(gdp_model_data, spec)
    gdp_fitted_results[spec["model_id"]] = fitted
    print(fitted.summary)
    gdp_results_rows.extend(gdp_result_rows_from_spec(fitted, gdp_model_data, spec))

gdp_results_df = pd.DataFrame(gdp_results_rows)
gdp_results_output = OUTPUT_DIR / "gdp_growth_impact_results_2002_2021.csv"
gdp_results_df.to_csv(gdp_results_output, index=False, encoding="utf-8")

gdp_preferred_results = gdp_fitted_results["municipality_year_fe"]
gdp_beta_risk = gdp_preferred_results.params["risk_norm_without_GDP_lag1"]
gdp_impact = gdp_panel.copy()
gdp_impact["growth_effect_0_1_risk_lag1_log_points"] = gdp_beta_risk * DELTA_RISK
gdp_impact["growth_effect_0_1_risk_lag1_percent_points"] = (
    gdp_impact["growth_effect_0_1_risk_lag1_log_points"] * 100
)
gdp_impact["impact_note"] = (
    "GDP growth model uses lagged risk_norm_without_GDP and controls for "
    "industrial value-added growth at 2010 prices."
)

gdp_impact_cols = [
    "municipio", "ano",
    "risk_norm_without_GDP", "risk_norm_without_GDP_lag1",
    "hazard_index", "hazard_index_lag1", "hazard_index_lag2",
    "risk_norm_without_GDP_lag2", "risk_mean_3yr_without_GDP",
    "climate_risk_index_without_GDP", "vulnerability_index_without_GDP",
    "real_gdp", "va_industrial_2010", "va_agro_2010",
    "log_real_gdp", "log_va_industrial_2010", "log_va_agro_2010",
    "gdp_growth_log", "va_industrial_growth_log", "va_agro_growth_log",
    "growth_effect_0_1_risk_lag1_log_points",
    "growth_effect_0_1_risk_lag1_percent_points", "impact_note"
]
gdp_impact_output = OUTPUT_DIR / "gdp_growth_impact_municipal_2002_2021.csv"
gdp_impact[gdp_impact_cols].to_csv(gdp_impact_output, index=False, encoding="utf-8")


# =========================
# GDP ROBUSTNESS TESTS
# =========================

print("\n[GDP robustness] Testing current-year hazard model with industrial VA growth control...")

preferred_spec = model_specs[0]
gdp_robustness_rows = []

gdp_robustness_rows.extend(
    robustness_result_rows(
        gdp_preferred_results,
        gdp_model_data,
        preferred_spec,
        "baseline_risk_without_gdp_lag1",
        "Baseline: GDP growth on lagged risk without GDP",
        "gdp_growth_log",
        ["risk_norm_without_GDP_lag1", "va_industrial_growth_log"],
        "risk_norm_without_GDP_lag1",
    )
)

x_cols = ["hazard_index", "va_industrial_growth_log"]
hazard_model_cols = ["municipio", "ano", "gdp_growth_log"] + x_cols
hazard_model_data = gdp_panel.dropna(subset=hazard_model_cols).copy()
hazard_results = fit_custom_panel_spec(
    hazard_model_data,
    preferred_spec,
    "gdp_growth_log",
    x_cols,
)
gdp_robustness_rows.extend(
    robustness_result_rows(
        hazard_results,
        hazard_model_data,
        preferred_spec,
        "hazard_current",
        "Second model: GDP growth on current hazard subindex",
        "gdp_growth_log",
        x_cols,
        "hazard_index",
    )
)

agro_risk_model_cols = [
    "municipio", "ano", "va_agro_growth_log", "risk_norm_without_GDP_lag1"
]
agro_risk_model_data = gdp_panel.dropna(subset=agro_risk_model_cols).copy()
agro_risk_results = fit_custom_panel_spec(
    agro_risk_model_data,
    preferred_spec,
    "va_agro_growth_log",
    ["risk_norm_without_GDP_lag1"],
)
gdp_robustness_rows.extend(
    robustness_result_rows(
        agro_risk_results,
        agro_risk_model_data,
        preferred_spec,
        "agro_growth_risk_lag1",
        "Mechanism check: Agro growth on lagged risk without GDP",
        "va_agro_growth_log",
        ["risk_norm_without_GDP_lag1"],
        "risk_norm_without_GDP_lag1",
    )
)

industrial_agro_model_cols = [
    "municipio", "ano", "va_industrial_growth_log", "va_agro_growth_log"
]
industrial_agro_model_data = gdp_panel.dropna(subset=industrial_agro_model_cols).copy()
industrial_agro_results = fit_custom_panel_spec(
    industrial_agro_model_data,
    preferred_spec,
    "va_industrial_growth_log",
    ["va_agro_growth_log"],
)
gdp_robustness_rows.extend(
    robustness_result_rows(
        industrial_agro_results,
        industrial_agro_model_data,
        preferred_spec,
        "industrial_growth_agro_growth",
        "Exploratory: Industrial growth on agro growth",
        "va_industrial_growth_log",
        ["va_agro_growth_log"],
        "va_agro_growth_log",
    )
)

gdp_robustness_df = pd.DataFrame(gdp_robustness_rows)
gdp_robustness_output = OUTPUT_DIR / "gdp_growth_robustness_tests_2002_2021.csv"
gdp_robustness_df.to_csv(gdp_robustness_output, index=False, encoding="utf-8")


# =========================
# DASHBOARD MUNICIPAL-YEAR IMPACTS
# =========================

print("\n[Dashboard] Creating municipality-year economic impact estimates...")

beta_hazard_gdp = hazard_results.params["hazard_index"]
beta_agro_risk = agro_risk_results.params["risk_norm_without_GDP_lag1"]
beta_industrial_agro = industrial_agro_results.params["va_agro_growth_log"]

dashboard_impact = gdp_panel.sort_values(["municipio", "ano"]).copy()
dashboard_impact["previous_ano"] = dashboard_impact.groupby("municipio")["ano"].shift(1)
dashboard_impact["risk_norm_without_GDP_previous"] = (
    dashboard_impact.groupby("municipio")["risk_norm_without_GDP"].shift(1)
)
dashboard_impact["hazard_index_previous"] = (
    dashboard_impact.groupby("municipio")["hazard_index"].shift(1)
)
dashboard_impact["risk_change"] = (
    dashboard_impact["risk_norm_without_GDP"] -
    dashboard_impact["risk_norm_without_GDP_previous"]
)
dashboard_impact["hazard_change"] = (
    dashboard_impact["hazard_index"] -
    dashboard_impact["hazard_index_previous"]
)

dashboard_impact["real_gdp_previous"] = (
    dashboard_impact.groupby("municipio")["real_gdp"].shift(1)
)
dashboard_impact["va_agro_2010_previous"] = (
    dashboard_impact.groupby("municipio")["va_agro_2010"].shift(1)
)
dashboard_impact["va_industrial_2010_previous"] = (
    dashboard_impact.groupby("municipio")["va_industrial_2010"].shift(1)
)
dashboard_impact["observed_gdp_change_mil_reais"] = (
    dashboard_impact["real_gdp"] - dashboard_impact["real_gdp_previous"]
)
dashboard_impact["observed_agro_change_mil_reais"] = (
    dashboard_impact["va_agro_2010"] - dashboard_impact["va_agro_2010_previous"]
)
dashboard_impact["observed_industrial_change_mil_reais"] = (
    dashboard_impact["va_industrial_2010"] -
    dashboard_impact["va_industrial_2010_previous"]
)

dashboard_impact["gdp_risk_log_effect"] = gdp_beta_risk * dashboard_impact["risk_change"]
dashboard_impact["gdp_risk_pct_effect"] = np.exp(
    dashboard_impact["gdp_risk_log_effect"]
) - 1
dashboard_impact["gdp_risk_percent_points"] = (
    dashboard_impact["gdp_risk_pct_effect"] * 100
)
dashboard_impact["estimated_gdp_risk_impact_mil_reais"] = (
    dashboard_impact["real_gdp"] * dashboard_impact["gdp_risk_pct_effect"]
)

dashboard_impact["gdp_hazard_log_effect"] = (
    beta_hazard_gdp * dashboard_impact["hazard_change"]
)
dashboard_impact["gdp_hazard_pct_effect"] = np.exp(
    dashboard_impact["gdp_hazard_log_effect"]
) - 1
dashboard_impact["gdp_hazard_percent_points"] = (
    dashboard_impact["gdp_hazard_pct_effect"] * 100
)
dashboard_impact["estimated_gdp_hazard_impact_mil_reais"] = (
    dashboard_impact["real_gdp"] * dashboard_impact["gdp_hazard_pct_effect"]
)

dashboard_impact["agro_risk_log_effect"] = beta_agro_risk * dashboard_impact["risk_change"]
dashboard_impact["agro_risk_pct_effect"] = np.exp(
    dashboard_impact["agro_risk_log_effect"]
) - 1
dashboard_impact["agro_risk_percent_points"] = (
    dashboard_impact["agro_risk_pct_effect"] * 100
)
dashboard_impact["estimated_agro_risk_impact_mil_reais"] = (
    dashboard_impact["va_agro_2010"] * dashboard_impact["agro_risk_pct_effect"]
)

dashboard_impact["industrial_indirect_log_effect"] = (
    beta_industrial_agro * dashboard_impact["agro_risk_log_effect"]
)
dashboard_impact["industrial_indirect_pct_effect"] = np.exp(
    dashboard_impact["industrial_indirect_log_effect"]
) - 1
dashboard_impact["industrial_indirect_percent_points"] = (
    dashboard_impact["industrial_indirect_pct_effect"] * 100
)
dashboard_impact["estimated_industrial_indirect_impact_mil_reais"] = (
    dashboard_impact["va_industrial_2010"] *
    dashboard_impact["industrial_indirect_pct_effect"]
)

money_col_brl_map = {
    "real_gdp": "real_gdp_brl",
    "real_gdp_previous": "real_gdp_previous_brl",
    "observed_gdp_change_mil_reais": "observed_gdp_change_brl",
    "va_agro_2010": "va_agro_2010_brl",
    "va_agro_2010_previous": "va_agro_2010_previous_brl",
    "observed_agro_change_mil_reais": "observed_agro_change_brl",
    "va_industrial_2010": "va_industrial_2010_brl",
    "va_industrial_2010_previous": "va_industrial_2010_previous_brl",
    "observed_industrial_change_mil_reais": "observed_industrial_change_brl",
    "estimated_gdp_risk_impact_mil_reais": "estimated_gdp_risk_impact_brl",
    "estimated_gdp_hazard_impact_mil_reais": "estimated_gdp_hazard_impact_brl",
    "estimated_agro_risk_impact_mil_reais": "estimated_agro_risk_impact_brl",
    "estimated_industrial_indirect_impact_mil_reais": (
        "estimated_industrial_indirect_impact_brl"
    ),
}
for source_col, brl_col in money_col_brl_map.items():
    dashboard_impact[brl_col] = dashboard_impact[source_col] * 1000

dashboard_impact["dashboard_note"] = (
    "Model-associated values use the selected year's change from the previous year. "
    "They are associations from fixed-effects panel models, not causal proof. "
    "Money columns are converted from thousand reais to reais."
)

dashboard_impact_cols = [
    "municipio", "ano", "previous_ano",
    "risk_norm_without_GDP", "risk_norm_without_GDP_previous", "risk_change",
    "hazard_index", "hazard_index_previous", "hazard_change",
    "real_gdp", "real_gdp_brl", "real_gdp_previous", "real_gdp_previous_brl",
    "observed_gdp_change_mil_reais", "observed_gdp_change_brl",
    "gdp_risk_percent_points", "estimated_gdp_risk_impact_mil_reais",
    "estimated_gdp_risk_impact_brl",
    "gdp_hazard_percent_points", "estimated_gdp_hazard_impact_mil_reais",
    "estimated_gdp_hazard_impact_brl",
    "va_agro_2010", "va_agro_2010_brl",
    "va_agro_2010_previous", "va_agro_2010_previous_brl",
    "observed_agro_change_mil_reais", "observed_agro_change_brl",
    "agro_risk_percent_points", "estimated_agro_risk_impact_mil_reais",
    "estimated_agro_risk_impact_brl",
    "va_industrial_2010", "va_industrial_2010_brl",
    "va_industrial_2010_previous", "va_industrial_2010_previous_brl",
    "observed_industrial_change_mil_reais", "observed_industrial_change_brl",
    "industrial_indirect_percent_points",
    "estimated_industrial_indirect_impact_mil_reais",
    "estimated_industrial_indirect_impact_brl",
    "gdp_beta_risk", "gdp_beta_hazard", "agro_beta_risk",
    "industrial_beta_agro", "dashboard_note"
]

dashboard_impact["gdp_beta_risk"] = gdp_beta_risk
dashboard_impact["gdp_beta_hazard"] = beta_hazard_gdp
dashboard_impact["agro_beta_risk"] = beta_agro_risk
dashboard_impact["industrial_beta_agro"] = beta_industrial_agro

dashboard_impact_output = OUTPUT_DIR / "economic_impact_dashboard_municipal_year_2002_2021.csv"
dashboard_impact[dashboard_impact_cols].to_csv(
    dashboard_impact_output,
    index=False,
    encoding="utf-8"
)

print("\nSaved outputs:")
print(f"  {raw_output}")
print(f"  {model_output}")
print(f"  {results_output}")
print(f"  {impact_output}")
print(f"  {gdp_raw_output}")
print(f"  {gdp_model_output}")
print(f"  {gdp_results_output}")
print(f"  {gdp_impact_output}")
print(f"  {gdp_robustness_output}")
print(f"  {dashboard_impact_output}")

print("\nKey coefficients:")
print(
    results_df[
        ["model_label", "variable", "coefficient", "pct_effect_0_1_percent", "p_value"]
    ].to_string(index=False)
)

print("\nGDP model key coefficients:")
print(
    gdp_results_df[
        ["model_label", "variable", "coefficient", "pct_effect_0_1_percent", "p_value"]
    ].to_string(index=False)
)

print("\nGDP robustness comparison, preferred FE specification only:")
print(
    gdp_robustness_df[
        gdp_robustness_df["variable"] == gdp_robustness_df["risk_variable"]
    ][
        [
            "test_label", "dependent_variable", "risk_variable",
            "coefficient", "pct_effect_0_1_percent", "p_value",
            "nobs", "year_min", "year_max"
        ]
    ].to_string(index=False)
)

print("\nDone.")
