# Climate Risk Index - Industrial Sector (Santa Catarina, Brazil)

## Overview

This project develops a municipal Climate Risk Index for the industrial sector in Santa Catarina, Brazil. The index adapts the IPCC AR5 risk framework to measure relative climate risk across the state's 295 municipalities.

The current version expands the project from a single-year index into a 2002-2023 time series. This allows the dashboard to compare municipalities in a selected year and prepares the project for future analysis of how changes in climate risk relate to fiscal and economic outcomes.

The model follows:

```text
Risk = Hazard x Exposure x Vulnerability
```

The final risk score is normalized within each year, so municipalities are compared against the state distribution for that year.

## Methodology

### Hazard

The hazard index captures climate variability and climate stress using TerraClimate-based indicators:

- Mean water deficit: `def_mean`
- Precipitation variability: `ppt_std`
- Wind speed variability: `ws_std`
- Diurnal temperature range: `dtr_mean`

Each variable is normalized by year, producing:

- `def_mean_norm`
- `ppt_std_norm`
- `ws_std_norm`
- `dtr_mean_norm`

The hazard index is calculated from the normalized hazard components.

### Exposure

The exposure index measures the size and concentration of municipal industrial activity exposed to climate shocks:

- Industrial employment per capita: `empregos_pc`
- Industrial firms per capita: `empresas_pc`

Both variables are normalized by year:

- `empregos_pc_norm`
- `empresas_pc_norm`

The exposure index is the mean of the normalized exposure variables.

### Vulnerability

The vulnerability index captures structural sensitivity and adaptive capacity:

- Industrial energy consumption per capita: `energia_pc`
- Real GDP per capita, inverted after normalization: `pib_pc_inv`
- Real agricultural production value per capita: `agro_pc`

Energy consumption is calculated using CELESC industrial consumption only. GDP is deflated with the GDP implicit deflator from IPEADATA. Agricultural production is deflated with IGP-DI from IPEADATA.

The vulnerability components used in the final index are:

- `energia_pc_norm`
- `pib_pc_inv`
- `agro_pc_norm`

The vulnerability index is the mean of these three normalized variables.

## Time Series

The pipeline covers the years 2002-2023.

All sub-indexes are calculated by municipality and year. The final dataset contains:

```text
295 municipalities x 22 years = 6,490 records
```

This structure supports year-by-year analysis in the Streamlit dashboard and future panel-data modeling.

## Deflators

Inflation and price adjustments are stored in:

```text
diretorios/climate_risk_index/data/raw_data/IPEADATA/
```

Current deflator files:

- `deflator do PIB.xls`: GDP implicit deflator used to calculate real GDP.
- `IGP-DI indice.xls`: IGP-DI index used to calculate real agricultural production values.
- `IPCA.xls`: IPCA index used for the planned fiscal expenditure module.

The deflation rule is:

```text
real value = (nominal value / deflator index) x 100
```

## Missing Data And Harmonization Rules

Municipality names are normalized consistently across scripts by removing accents, uppercasing text, replacing hyphens and apostrophes with spaces, and collapsing duplicate spaces. This is important for special cases such as:

- `HERVAL D'OESTE` / `HERVAL D OESTE`
- `GRAO PARA`

Specific missing-data treatment:

- Energy data: municipalities present in CELESC but not in the Santa Catarina population universe are discarded. Municipalities in the population universe but missing from CELESC receive the mesoregion average energy consumption.
- GDP data: `PESCARIA BRAVA` and `BALNEARIO RINCAO` receive mesoregion averages for years before their own municipal data are available.
- Agricultural production: only `PESCARIA BRAVA` and `BALNEARIO RINCAO` receive mesoregion averages for early missing years. Other missing agricultural values are treated as zero activity when the municipality has no reported agricultural production.
- The final map merge is checked against the 295-municipality shapefile.

## Data Sources

Main data sources include:

- TerraClimate climate variables
- RAIS industrial structure
- CELESC municipal energy consumption
- IBGE/SIDRA economic and agricultural indicators
- IPEADATA deflator indexes
- Population interpolation dataset for 2002-2023
- Santa Catarina municipal shapefiles

Raw data are stored locally under `diretorios/climate_risk_index/data/raw_data/`. Large raw files are ignored by Git.

## Project Structure

```text
diretorios/climate_risk_index/
|
|-- app/
|   |-- app2.py                         # Main Streamlit dashboard
|
|-- data/
|   |-- raw_data/                       # Original input files
|   |   |-- CELESC/
|   |   |-- IPEADATA/                   # Deflators: GDP, IGP-DI, IPCA
|   |   |-- RAIS/
|   |   |-- SICONFI/
|   |   |-- shapes/
|   |   |-- terraclimate/
|   |-- data_handling/                  # Intermediate handled datasets
|
|-- output/                             # Final app-ready outputs
|   |-- climate_risk_index_2002_2023.csv
|   |-- dashboard_dataset_2002_2023.csv
|   |-- exposure_index_2002_2023.csv
|   |-- hazard_index_2002_2023.csv
|   |-- vulnerability_index_2002_2023.csv
|   |-- map_climate_risk_sc_2023.png
|
|-- script/
|   |-- exposure.py                     # Builds exposure time series
|   |-- hazard.py                       # Builds hazard time series
|   |-- vulnerability.py                # Builds vulnerability time series
|   |-- climate_risk_index.py           # Combines sub-indexes into final risk index
|
|-- .gitignore
```

## Pipeline

Run the scripts in this order:

```bash
python diretorios/climate_risk_index/script/exposure.py
python diretorios/climate_risk_index/script/hazard.py
python diretorios/climate_risk_index/script/vulnerability.py
python diretorios/climate_risk_index/script/climate_risk_index.py
python diretorios/climate_risk_index/script/economic_impact.py
```

The sub-index scripts save raw and normalized intermediate files in `data/data_handling/`. Final index files used by the dashboard are saved in `output/`.

## Dashboard

The Streamlit dashboard is implemented in:

```text
diretorios/climate_risk_index/app/app2.py
```

Run locally with:

```bash
streamlit run diretorios/climate_risk_index/app/app2.py
```

Dashboard features include:

- Year selector for the 2002-2023 time series
- Municipal risk ranking
- Interactive map of climate risk
- Detailed municipality view
- Municipality comparison
- Statistical insights, including risk distribution, mismatch analysis, and correlation matrices

## Current Outputs

The main dashboard dataset is:

```text
diretorios/climate_risk_index/output/dashboard_dataset_2002_2023.csv
```

It includes the final risk score, sub-indexes, normalized component variables, rankings, and variables used by the dashboard.

## Economic Impact Module

The `economic_impact.py` script estimates the association between climate risk and municipal environmental expenditure.

Fiscal expense input:

```text
diretorios/climate_risk_index/data/raw_data/SICONFI/Interface com RSiconfi - Despesas Gestão Ambiental.xlsx
```

Fiscal expense fields:

- municipality: `NO_ENTE`
- year: `AN_EXERCICIO`
- nominal environmental expense: `VALUE`
- no filter is applied; bimonthly rows are summed by municipality and year
- current coverage: 2015-2023

Revenue control:

```text
diretorios/climate_risk_index/data/raw_data/SICONFI/municipio_receita_transferencia.csv
```

Transfer revenue uses the Cota ICMS transfer file. This is used as the fiscal capacity control because climate and environmental expenses are often financed through transferred resources.

Nominal expense and revenue values are deflated with:

```text
diretorios/climate_risk_index/data/raw_data/IPEADATA/IPCA.xls
```

using:

```text
real value = (nominal value / IPCA index) x 100
```

The current model is:

```text
log(real_environmental_expense_it) =
    beta0 * risk_mean_3yr_it
  + beta1 * log(real_transfer_revenue_it)
  + municipality fixed effects
  + year fixed effects
  + error_it
```

`risk_mean_3yr` is the average of current risk, one-year lagged risk, and two-year lagged risk. This captures delayed climate pressure while avoiding multicollinearity among highly correlated separate lag terms.

Missing fiscal and revenue values are temporally interpolated only when they are internal gaps in an existing municipal time series. Pre-creation years for `BALNEARIO RINCAO` and `PESCARIA BRAVA` remain missing.

Economic impact outputs:

```text
diretorios/climate_risk_index/data/data_handling/economic_impact_raw_2002_2023.csv
diretorios/climate_risk_index/data/data_handling/economic_impact_model_data_2002_2023.csv
diretorios/climate_risk_index/output/economic_impact_results_2002_2023.csv
diretorios/climate_risk_index/output/economic_impact_municipal_2002_2023.csv
```

The monetary impact estimates translate a `0.1` increase in `risk_norm` into each municipality's own environmental-expense scale. Values in reais should not be interpreted as direct cross-municipality rankings, because municipalities have different budget sizes and reporting structures.

## Author

Rebecca Lorandi Silveira Lara  
Industrial Economics Researcher - Observatorio FIESC

## Notes

This project is intended for research and policy analysis. The index is relative and should be interpreted as a comparative measure of municipal climate risk within Santa Catarina, not as an absolute probability of climate loss.
