# ============================================
# STREAMLIT DASHBOARD - CLIMATE RISK INDEX SC
# ============================================

from turtle import color

import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import unicodedata
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import numpy as np

# =========================
# CONFIG
# =========================

st.set_page_config(
    page_title="Indice de Risco Climatico Industrial de Santa Catarina",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
<style>
[data-testid="stImage"] img {
    height: 120px;
    object-fit: cover;
}
</style>
""", unsafe_allow_html=True)

st.image(
    "https://upload.wikimedia.org/wikipedia/commons/b/b2/20181204_Warming_stripes_%28global%2C_WMO%2C_1850-2018%29_-_Climate_Lab_Book_%28Ed_Hawkins%29.svg",
    use_container_width=True
)

# =========================
# CCS
# =========================

st.markdown("""
<style>

/* FUNDO */
[data-testid="stAppViewContainer"] {
    background-color: #0e1117;
}

/* SIDEBAR - FIXED */
[data-testid="stSidebar"] {
    background-color: #101010;
    position: fixed;
    overflow-y: auto;
    width: 210px !important;
}

[data-testid="stSidebar"] * {
    color: white !important;
}

/* ABOUT BUTTON STYLING */
[data-testid="stSidebar"] button {
    background-color: transparent !important;
    border: 1px solid white !important;
    color: white !important;
    padding: 0.5rem 1rem !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    margin: 0 !important;
}

/* REMOVE SPACING FROM SIDEBAR ELEMENTS */
[data-testid="stSidebar"] .stButton {
    margin: 0 !important;
    padding: 0 !important;
}

[data-testid="stSidebar"] hr {
    margin: 0.5rem 0 !important;
    padding: 0 !important;
}

/* SELECTBOX */
[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: #101010 !important;
    color: white !important;
}

ul[role="listbox"] {
    background-color: #101010 !important;
}

li[role="option"] {
    background-color: #101010 !important;
    color: white !important;
}

li[role="option"]:hover {
    background-color: #374151 !important;
}

li[aria-selected="true"] {
    background-color: #ea580c !important;
}

/* TEXTO */
[data-testid="stMarkdownContainer"] p {
    color: #e5e7eb;
}
            
/* HEADERS DO STREAMLIT */
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {
    color: white;
}

/* HEADERS CRIADOS POR st.title / st.header */
h1, h2, h3 {
    color: white;
}

/* REMOVE TOPO */
header {
    background: transparent !important;
}

/* Reduce subheader spacing */
[data-testid="stMarkdownContainer"] h3 {
    margin: 0 !important;
    padding: 0 !important;
}

.stPlotlyChart {
    background-color: transparent !important;
}
       
/* REMOVE PADDING DO CONTAINER PRINCIPAL */
.block-container {
    padding-top: 0rem;
    padding-left: 0rem;
    padding-right: 0rem;
}
.block-container {
    padding-top: 0rem;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
}
/* KPI CARDS */
.kpi-container {
    display: flex;
    gap: 8px;
    margin-bottom: 10px;
}

.kpi-card {
    background-color: #111827;
    padding: 14px 18px;
    border-radius: 10px;
    flex: 1;
    min-height: 70px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    }

.kpi-title {
    font-size: 11px;
    color: #9ca3af;
    margin-bottom: 4px;
    }

.kpi-value {
    font-size: 22px;
    color: white;
    font-weight: 600;
    line-height: 1.2;
    }

/* MUNICIPALITY HEADER WITH SQUARE KPI CARDS */
.mun-header-section {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
    margin-bottom: 20px;
    width: fit-content;
}

.mun-header {
    font-size: 30px;
    font-weight: 600;
    color: #4292c6;
    padding-top: 10px;
}

.kpi-square-container {
    display: flex;
    gap: 15px;
}

.kpi-square {
    background-color: #111827;
    border-radius: 10px;
    width: 120px;
    height: 120px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    border-left: 4px solid;
}

.kpi-square-title {
    font-size: 12px;
    color: #9ca3af;
    margin-bottom: 8px;
}

.kpi-square-value {
    font-size: 20px;
    color: white;
    font-weight: 600;
    line-height: 1.3;
}
                   
</style>
""", unsafe_allow_html=True)

def titulo_h2(texto):
    st.markdown(
        f'<h2 style="color:#4292c6;">{texto}</h2>',
        unsafe_allow_html=True
    )

def titulo_h3(texto):
    st.markdown(
        f'<h3 style="color:#a50f15; font-size:22px; font-weight:600; margin-top:15px;">{texto}</h3>',
        unsafe_allow_html=True
    )

# =========================
# FUNÃ‡Ã•ES
# =========================

def normalize_text(text):
    if pd.isna(text):
        return text
    
    text = str(text)

    text = text.replace("-", " ")

    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    
    return text.upper().strip()

# TABELA ESTILIZADA (CORRIGIDA)
def styled_table(df_input, font_size="14px"):

    df_input = df_input.sort_values("Valor", ascending=False).reset_index(drop=True)

    norm = mcolors.Normalize(
        vmin=df_input["Valor"].min(),
        vmax=df_input["Valor"].max()
    )

    cmap = cm.get_cmap("OrRd")  # mais vermelho/laranja

    # Build HTML table manually with rounded corners (no header)
    html_table = f'<table style="width: 100%; font-size: {font_size}; border-collapse: separate; border-spacing: 0; border-radius: 10px; overflow: hidden;">'
    
    # Rows (no header)
    for idx, row in df_input.iterrows():
        valor = row["Valor"]
        color = cmap(norm(valor))
        darkened = (color[0] * 0.85, color[1] * 0.65, color[2] * 0.5, 1)
        hex_color = mcolors.to_hex(darkened)
        
        html_table += '<tr>'
        for col in df_input.columns:
            cell_value = row[col]
            # Format numeric values to 2 decimal places
            if isinstance(cell_value, (int, float)) and col == "Valor":
                cell_value = f"{cell_value:.2f}"
            html_table += f'<td style="padding: 8px; background-color: {hex_color}; color: white; font-size: {font_size}; border: none;">{cell_value}</td>'
        html_table += '</tr>'
    
    html_table += '</table>'
    
    return html_table

# =========================
# PATHS (COMPATÃVEL COM STREAMLIT CLOUD)
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent

data_path = BASE_DIR / "output" / "dashboard_dataset_2002_2023.csv"
shapefile_path = BASE_DIR / "data" / "raw_data" / "shapes" / "SC_Municipios_2025.shp"
mesoregiao_path = BASE_DIR / "data" / "raw_data" / "shapes" / "42MEE250GC_SIR.shp"

# =========================
# LOAD DATA
# =========================

@st.cache_data
def load_data():
    df = pd.read_csv(data_path)
    gdf = gpd.read_file(shapefile_path, engine="pyogrio")
    gdf["geometry"] = gdf["geometry"].simplify(0.01)
    gdf_meso = gpd.read_file(mesoregiao_path, engine="pyogrio")
    return df, gdf, gdf_meso

df_all, gdf_map, gdf_meso = load_data()

# =========================
# DETECTAR COLUNA MUNICÃPIO
# =========================

possible_cols = ["NM_MUN", "NOME_MUN", "NM_MUNICIP", "municipio", "name"]

col_municipio = None
for col in gdf_map.columns:
    if col.upper() in [c.upper() for c in possible_cols]:
        col_municipio = col
        break

if col_municipio is None:
    st.error(f"Colunas disponÃ­veis: {list(gdf_map.columns)}")
    st.stop()

gdf_map["municipio"] = gdf_map[col_municipio].apply(normalize_text)
df_all["municipio"] = df_all["municipio"].apply(normalize_text)

available_years = sorted(df_all["ano"].dropna().astype(int).unique())
ano_selecionado = st.sidebar.selectbox(
    "Selecione o ano:",
    available_years,
    index=len(available_years) - 1
)

df = df_all[df_all["ano"] == ano_selecionado].copy()
ranking = df[["municipio", "risk_norm"]].copy()

gdf_final = gdf_map.merge(df, on="municipio", how="left")
df["municipio_nome"] = df["municipio"].str.title()

# =========================
# BUILD MESOREGIÃƒO INDICES
# =========================

# Spatial join using centroid: assign municipality to mesoregion
gdf_centroids = gdf_map[["municipio", "geometry"]].copy()
gdf_centroids["centroid"] = gdf_centroids["geometry"].centroid
gdf_centroids = gdf_centroids.set_geometry("centroid")

# Perform spatial join
gdf_meso_join = gpd.sjoin(gdf_centroids, gdf_meso, how="left", predicate="within")

# Get mesoregion name column
meso_col = None
for col in gdf_meso.columns:
    if col.upper() in ["NM_MESO", "NOME_MESO", "MESOREGIAO", "name"]:
        meso_col = col
        break

if meso_col:
    gdf_meso_join["mesoregiao"] = gdf_meso_join[meso_col].apply(lambda x: normalize_text(x) if pd.notna(x) else x)
    
    # Merge mesoregion back to df
    df = df.merge(gdf_meso_join[["municipio", "mesoregiao"]], on="municipio", how="left")
    
    # Calculate mesoregion averages
    mesoregiao_indices = df.groupby("mesoregiao").agg({
        "hazard_index": "mean",
        "exposure_index": "mean",
        "vulnerability_index": "mean",
        "risk_norm": "mean"
    }).reset_index()
    
    mesoregiao_indices.columns = ["mesoregiao", "hazard_avg", "exposure_avg", "vulnerability_avg", "risk_avg"]
else:
    mesoregiao_indices = pd.DataFrame()

# =========================
# SIDEBAR - FIXED NAVIGATION
# =========================

# ABOUT BUTTON
if st.sidebar.button("About", use_container_width=True):
    st.session_state["show_about"] = not st.session_state.get("show_about", False)

# Display About Box when button is clicked
if st.session_state.get("show_about", False):
    st.markdown("""
    <div style="
        background-color:#111827;
        padding:25px;
        border-radius:10px;
        border-left:4px solid #4292c6;
        margin-bottom:20px;
    ">
    <h2 style="color:#4292c6; margin-top:0;">Sobre o Modelo</h2>
    
    <h3 style="color:#a50f15;">Metodologia</h3>
    <p style="color:#e5e7eb; line-height:1.6;">
    Este projeto apresenta uma <b>adaptaÃ§Ã£o do Ã­ndice de risco climÃ¡tico do IPCC (AR5)</b> para o contexto industrial dos municÃ­pios de Santa Catarina. O modelo segue o framework conceitual amplamente utilizado na literatura de risco climÃ¡tico, no qual o risco Ã© definido como a interaÃ§Ã£o entre trÃªs dimensÃµes fundamentais:
    </p>
    
    <div style="text-align:center; margin:20px 0;">
        <span style="font-size:20px; font-weight:500; color:white;">
            Risk = Hazard Ã— Exposure Ã— Vulnerability
        </span>
    </div>
    
    <p style="color:#e5e7eb; line-height:1.6;">
    Essa formulaÃ§Ã£o, adotada por organismos internacionais como o IPCC e o UNDRR, entende o risco como um fenÃ´meno sistÃªmico, resultante da combinaÃ§Ã£o entre condiÃ§Ãµes climÃ¡ticas adversas, a exposiÃ§Ã£o de ativos econÃ´micos e a vulnerabilidade estrutural dos sistemas analisados. A formulaÃ§Ã£o multiplicativa implica que a ausÃªncia ou baixa intensidade de qualquer componente reduz significativamente o risco total, evitando compensaÃ§Ãµes indevidas entre fatores.
    </p>
    
    <p style="color:#e5e7eb; line-height:1.6;">
    Neste trabalho, o modelo foi adaptado para capturar especificamente o <b>risco climÃ¡tico sobre a estrutura produtiva industrial municipal</b>, incorporando variÃ¡veis que refletem a dinÃ¢mica regional.
    </p>
    
    <blockquote style="color:#9ca3af; border-left:3px solid #4292c6; padding-left:15px; margin:15px 0;">
    O Ã­ndice resultante representa o <b>nÃ­vel relativo de risco climÃ¡tico associado Ã  atividade industrial municipal</b>. Valores variam entre 0 e 1, sendo que os mais elevados indicam maior suscetibilidade a impactos econÃ´micos decorrentes de choques climÃ¡ticos.
    </blockquote>
    
    <h3 style="color:#a50f15;">ConstruÃ§Ã£o dos Ã­ndices</h3>
    
    <h4 style="color:#a50f15;">Hazard (Perigo climÃ¡tico)</h4>
    <p style="color:#e5e7eb; line-height:1.6;">
    O Ã­ndice de hazard foi construÃ­do a partir de variÃ¡veis climÃ¡ticas que capturam tanto a variabilidade quanto a ocorrÃªncia de extremos, incluindo dÃ©ficit hÃ­drico mÃ©dio (<code>def_mean</code>), variabilidade da precipitaÃ§Ã£o (<code>ppt_std</code>), variabilidade da velocidade do vento (<code>ws_std</code>) e amplitude tÃ©rmica diÃ¡ria (<code>dtr_mean</code>).
    </p>
    
    <p style="color:#e5e7eb; line-height:1.6;">
    A agregaÃ§Ã£o combina a mÃ©dia dessas variÃ¡veis, representando as condiÃ§Ãµes climÃ¡ticas estruturais, com o valor mÃ¡ximo, de modo a incorporar eventos extremos. Essa abordagem estÃ¡ alinhada com a literatura climÃ¡tica, que destaca o papel desproporcional de eventos extremos na geraÃ§Ã£o de danos econÃ´micos, especialmente em sistemas industriais sensÃ­veis a choques abruptos.
    </p>
    
    <h4 style="color:#a50f15;">Exposure (ExposiÃ§Ã£o)</h4>
    <p style="color:#e5e7eb; line-height:1.6;">
    O Ã­ndice de exposiÃ§Ã£o mensura o grau em que a atividade econÃ´mica municipal estÃ¡ sujeita a riscos climÃ¡ticos, utilizando indicadores per capita de empregos industriais (<code>empregos_pc</code>) e nÃºmero de empresas (<code>empresas_pc</code>).
    </p>
    
    <p style="color:#e5e7eb; line-height:1.6;">
    A utilizaÃ§Ã£o de mÃ©tricas per capita e sua agregaÃ§Ã£o por mÃ©dia simples permitem capturar a <b>intensidade relativa da atividade industrial exposta</b>, garantindo comparabilidade entre municÃ­pios com diferentes escalas populacionais.
    </p>
    
    <h4 style="color:#a50f15;">Vulnerability (Vulnerabilidade)</h4>
    <p style="color:#e5e7eb; line-height:1.6;">
    A vulnerabilidade reflete a sensibilidade climÃ¡tica e energÃ©tica e a capacidade adaptativa da renda, sendo composta por trÃªs dimensÃµes principais: intensidade energÃ©tica industrial per capita (<code>energia_pc_norm</code>), valor da produÃ§Ã£o agrÃ­cola per capita (<code>agro_pc_norm</code>) e renda per capita (<code>pib_pc_inv</code>).
    </p>
    
    <p style="color:#e5e7eb; line-height:1.6;">
    Esse conjunto de variÃ¡veis captura a sensibilidade dos municÃ­pios a choques energÃ©ticos e climaticos do setor agrÃ­cola, bem como sua capacidade adaptativa, aproximada pela renda disponÃ­vel para resposta e reconstruÃ§Ã£o. A agregaÃ§Ã£o foi realizada por meio de mÃ©dia simples, assumindo contribuiÃ§Ã£o equilibrada entre os fatores estruturais.
    </p>
    
    <hr style="border:0.5px solid #374151; margin:20px 0;">
    
    <div style="display:flex; gap:20px;">
        <div style="flex:1;">
            <h4 style="color:#a50f15;">Nota sobre os dados</h4>
            <p style="color:#9ca3af; font-size:13px; line-height:1.6;">
            Os dados utilizados sÃ£o provenientes de bases oficiais e amplamente reconhecidas, incluindo TerraClimate (variÃ¡veis climÃ¡ticas), SIDRA/IBGE (indicadores econÃ´micos), RAIS (estrutura produtiva) e CELESC (dados energÃ©ticos).
            </p>
            <p style="color:#9ca3af; font-size:13px; line-height:1.6;">
            Todas as variÃ¡veis foram previamente tratadas, normalizadas e harmonizadas ao nÃ­vel municipal, assegurando consistÃªncia e comparabilidade entre as unidades de anÃ¡lise.
            </p>
        </div>
        <div style="flex:1;">
            <h4 style="color:#a50f15;">ConsideraÃ§Ãµes finais</h4>
            <p style="color:#9ca3af; font-size:13px; line-height:1.6;">
            O Ã­ndice proposto constitui uma ferramenta analÃ­tica para a identificaÃ§Ã£o de <b>hotspots de risco climÃ¡tico industrial em Santa Catarina</b>, podendo subsidiar a formulaÃ§Ã£o de polÃ­ticas pÃºblicas, estratÃ©gias de adaptaÃ§Ã£o e anÃ¡lises econÃ´micas regionais sob a perspectiva das mudanÃ§as climÃ¡ticas.
            </p>
            <p style="color:#9ca3af; font-size:13px; line-height:1.6;">
            Trata-se de uma medida relativa, adaptada ao contexto regional, que mantÃ©m aderÃªncia ao arcabouÃ§o conceitual do IPCC.
            </p>
        </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

# SIDEBAR CONTROLS
municipios = sorted(df["municipio_nome"].unique())

municipio_selecionado = st.sidebar.selectbox(
    "Selecione um municÃ­pio:",
    ["Todos"] + municipios
)

modo_analise = st.sidebar.radio(
    "Modo de anÃ¡lise:",
    ["Individual", "ComparaÃ§Ã£o"]
)

# Segundo municÃ­pio (apenas se comparaÃ§Ã£o)
if modo_analise == "ComparaÃ§Ã£o":
    municipio_2 = st.sidebar.selectbox(
        "Selecione o segundo municÃ­pio:",
        municipios
    )
else:
    municipio_2 = None

# =========================
# TÃTULO
# =========================

st.title("Ãndice de Risco ClimÃ¡tico Industrial de Santa Catarina")

# =========================
# FUNÃ‡ÃƒO PARA ANÃLISE
# =========================

def gerar_texto_insight(df, df_mun):

    # =========================
    # VARIÃVEIS BASE
    # =========================
    risk = df_mun["risk_norm"].values[0]
    hazard = df_mun["hazard_index"].values[0]
    exposure = df_mun["exposure_index"].values[0]
    vulnerability = df_mun["vulnerability_index"].values[0]

    # =========================
    # CLASSIFICAÃ‡ÃƒO RELATIVA (QUANTIL)
    # =========================
    p33 = df["risk_norm"].quantile(0.33)
    p66 = df["risk_norm"].quantile(0.66)

    if risk > p66:
        nivel = "alto"
    elif risk > p33:
        nivel = "moderado"
    else:
        nivel = "baixo"

    # posiÃ§Ã£o no estado
    posicao = (df["risk_norm"] < risk).mean()

    if posicao > 0.66:
        pos_text = "entre os municÃ­pios de maior risco no estado"
    elif posicao > 0.33:
        pos_text = "em posiÃ§Ã£o intermediÃ¡ria no estado"
    else:
        pos_text = "entre os municÃ­pios de menor risco no estado"

    # =========================
    # DRIVERS
    # =========================
    drivers = {
        "Hazard": hazard,
        "Exposure": exposure,
        "Vulnerability": vulnerability
    }

    main_driver = max(drivers, key=drivers.get)
    min_driver = min(drivers, key=drivers.get)

    # =========================
    # VARIÃVEL DOMINANTE
    # =========================
    if main_driver == "Hazard":
        vars_dict = {
            "dÃ©ficit hÃ­drico": df_mun["def_mean"].values[0],
            "variabilidade da precipitaÃ§Ã£o": df_mun["ppt_std"].values[0],
            "variabilidade do vento": df_mun["ws_std"].values[0],
            "amplitude tÃ©rmica": df_mun["dtr_mean"].values[0]
        }

    elif main_driver == "Exposure":
        vars_dict = {
            "empregos industriais per capita": df_mun["empregos_pc"].values[0],
            "empresas industriais per capita": df_mun["empresas_pc"].values[0]
        }

    else:
        vars_dict = {
            "intensidade energÃ©tica": df_mun["energia_pc_norm"].values[0],
            "sensibilidade da produÃ§Ã£o agrÃ­cola": df_mun["agro_pc_norm"].values[0],
            "resiliÃªncia da renda": df_mun["pib_pc_inv"].values[0]
        }

    main_variable = max(vars_dict, key=vars_dict.get)

    # =========================
    # LÃ“GICA DE POLÃTICA (AJUSTE EXPOSURE)
    # =========================
    if main_driver == "Exposure":

        # segundo driver
        drivers_sorted = sorted(drivers.items(), key=lambda x: x[1], reverse=True)
        second_driver = drivers_sorted[1][0]

        # variÃ¡vel dominante do segundo driver
        if second_driver == "Hazard":
            second_vars = {
                "dÃ©ficit hÃ­drico": df_mun["def_mean"].values[0],
                "variabilidade da precipitaÃ§Ã£o": df_mun["ppt_std"].values[0],
                "variabilidade do vento": df_mun["ws_std"].values[0],
                "amplitude tÃ©rmica": df_mun["dtr_mean"].values[0]
            }
        else:
            second_vars = {
                "intensidade energÃ©tica": df_mun["energia_pc_norm"].values[0],
                "sensibilidade da produÃ§Ã£o agrÃ­cola": df_mun["agro_pc_norm"].values[0],
                "resiliÃªncia da renda": df_mun["pib_pc_inv"].values[0]
            }

        second_variable = max(second_vars, key=second_vars.get)

        politica_texto = f"""
Do ponto de vista econÃ´mico, o risco reflete principalmente o volume de atividade exposta. 
Nesse contexto, polÃ­ticas devem atuar sobre **{second_driver.lower()}**, 
especialmente em **{second_variable}**, reduzindo a sensibilidade a choques climÃ¡ticos.
"""

    else:

        politica_texto = f"""
Do ponto de vista econÃ´mico, isso sugere que intervenÃ§Ãµes direcionadas a **{main_driver.lower()}**, 
especialmente sobre **{main_variable}**, tendem a gerar maior efetividade na mitigaÃ§Ã£o do risco climÃ¡tico industrial.
"""

    # =========================
    # ANULAÃ‡ÃƒO
    # =========================
    if drivers[min_driver] < 0.1:
        anulacao_texto = f"""
Observa-se que a dimensÃ£o **{min_driver}** apresenta valor muito reduzido, 
atuando como fator limitante do risco agregado. Na formulaÃ§Ã£o multiplicativa 
do Ã­ndice, essa baixa intensidade contribui para **atenuar o risco total**, 
mesmo na presenÃ§a de valores mais elevados nas demais dimensÃµes.
"""
    else:
        anulacao_texto = ""

    # =========================
    # TEXTO FINAL
    # =========================
    texto = f"""
O municÃ­pio apresenta um nÃ­vel **{nivel} de risco climÃ¡tico industrial** 
(Ã­ndice = {risk:.2f}), situando-se {pos_text}.

A decomposiÃ§Ã£o do Ã­ndice indica que o principal fator de risco Ã© **{main_driver}**, 
com destaque para **{main_variable}** como principal componente explicativo dentro dessa dimensÃ£o.

{politica_texto}

{anulacao_texto}
"""

    return texto

# =========================
# TABS - NEW STRUCTURE
# =========================

tab0, tab1, tab2 = st.tabs(["Analysis","Economic Impact", "Statistical Insights"])

# =========================================================
# TAB 0 - ANALYSIS (Ranking + Map + Analysis)
# =========================================================

with tab0:

    # =========================
    # SECTION 1: RANKING + MAP
    # =========================

    col1, col2 = st.columns([1, 1.2])

    # ========================
    # COL1: RANKING CHARTS
    # ========================
    with col1:

        # ORDENAÃ‡ÃƒO
        top10 = ranking.sort_values("risk_norm", ascending=False).head(10)
        bottom10 = ranking.sort_values("risk_norm", ascending=True).head(10)

        # MAIOR RISCO
        st.markdown("**MunicÃ­pios de Maior Risco**")

        fig_top = px.bar(
            top10.sort_values("risk_norm", ascending=True),  
            x="risk_norm",
            y="municipio",
            orientation="h",
            color="risk_norm",
            color_continuous_scale="OrRd", 
            labels={"risk_norm": "Ãndice de Risco ClimÃ¡tico"}
        )

        fig_top.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_showscale=False,
            height=300,
            font=dict(color="white"),
            xaxis=dict(
                title_font=dict(color="white"),
                tickfont=dict(color="white")
            ),
            yaxis=dict(
                tickfont=dict(color="white"),
                title_font=dict(color="white")
            )
        )

        st.plotly_chart(fig_top, use_container_width=True)
        st.markdown("---")
        # MENOR RISCO
        st.markdown("**MunicÃ­pios de Menor Risco**")

        fig_bot = px.bar(
            bottom10.sort_values("risk_norm", ascending=True),
            x="risk_norm",
            y="municipio",
            orientation="h",
            color="risk_norm",
            color_continuous_scale="Blues", 
            labels={"risk_norm": "Ãndice de Risco ClimÃ¡tico"}
        )

        fig_bot.update_layout(
            yaxis=dict(
                autorange="reversed",
                tickfont=dict(color="white"),
                title_font=dict(color="white")
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            height=300,
            coloraxis_showscale=False,
            font=dict(color="white"),
            xaxis=dict(
                title_font=dict(color="white"),
                tickfont=dict(color="white")
            )
        )

        st.plotly_chart(fig_bot, use_container_width=True)

    # ========================
    # COL2: MAP + TEXT
    # ========================
    with col2:
        st.markdown("**DistribuiÃ§Ã£o GeogrÃ¡fica**")
        container = st.container(border=False)
        with container:
            fig = px.choropleth(
                gdf_final,
                geojson=gdf_final.geometry,
                locations=gdf_final.index,
                color="risk_norm",
                color_continuous_scale="Reds",
                hover_name="municipio",
                labels={"risk_norm": "Ãndice de Risco ClimÃ¡tico"},
            
            )

            fig.update_geos(
                fitbounds="locations",
                visible=False,
                bgcolor='rgba(0,0,0,0)' 
            )

            fig.update_traces(
                hovertemplate="<b>%{hovertext}</b><br>Ãndice de Risco ClimÃ¡tico: %{z:.3f}<extra></extra>"
            )

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=0, b=60),
                height=400,
                coloraxis_colorbar=dict(
                    orientation="h",
                    x=0.5,
                    y=-0.15,
                    len=1,
                    title=dict(text="Ãndice de Risco ClimÃ¡tico", font=dict(color="white", size=12)),
                    tickfont=dict(color="white", size=11)
                )
            )

            st.plotly_chart(fig, use_container_width=True, config={'responsive': True})

        # TEXTO EXPLICATIVO
        st.markdown("""
        <div style="
            background-color:#111827;
            padding:15px;
            border-radius:8px;
            border-left:3px solid #fb923c;
            margin-top:10px;
            color:#e5e7eb;
            font-size:15px;
            line-height:1.5;
        ">
        <b>InterpretaÃ§Ã£o dos Dados</b><br><br>
        MunicÃ­pios de maior risco combinam nÃ­veis elevados de hazard climÃ¡tico, alta exposiÃ§Ã£o da atividade industrial e maior vulnerabilidade.
        
        JÃ¡ municÃ­pios de menor risco apresentam menor suscetibilidade a impactos climÃ¡ticos, seja por menor exposiÃ§Ã£o, melhores condiÃ§Ãµes estruturais ou menor intensidade de eventos climÃ¡ticos. 
        Como o Ã­ndice de risco Ã© construÃ­do de forma multiplicativa, valores prÃ³ximos de zero em qualquer uma das dimensÃµes reduzem significativamente o risco total.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # =========================
    # SECTION 2: DETAILED ANALYSIS
    # =========================

    st.subheader("AnÃ¡lise Detalhada por MunicÃ­pio")

    # CASO 1 â€” TODOS
    if municipio_selecionado == "Todos" and modo_analise == "Individual":
        st.markdown(
            '<p style="color:#9ca3af; font-size:13px; font-style:italic;">Selecione um municÃ­pio na barra lateral para visualizar a anÃ¡lise detalhada.</p>',
            unsafe_allow_html=True
        )

    # CASO 3 â€” COMPARAÃ‡ÃƒO
    elif modo_analise == "ComparaÃ§Ã£o":

        if municipio_selecionado == municipio_2:
            st.warning("Selecione dois municÃ­pios diferentes para comparaÃ§Ã£o.")
        
        else:
            df_mun1 = df[df["municipio_nome"] == municipio_selecionado]
            df_mun2 = df[df["municipio_nome"] == municipio_2]

            colA, colB = st.columns(2)

            # FUNÃ‡ÃƒO REUTILIZÃVEL
            def render_municipio(df_mun, nome, show_tables=True, show_charts=True):

                risk = df_mun["risk_norm"].values[0]
                hazard = df_mun["hazard_index"].values[0]
                exposure = df_mun["exposure_index"].values[0]
                vulnerability = df_mun["vulnerability_index"].values[0]

                # ðŸ”¹ garantir normalizaÃ§Ã£o para o ranking
                ranking_temp = ranking.copy()
                ranking_temp["municipio"] = ranking_temp["municipio"].apply(normalize_text)
                ranking_sorted_temp = ranking_temp.sort_values("risk_norm", ascending=False).reset_index(drop=True)
                ranking_sorted_temp["rank"] = ranking_sorted_temp.index + 1
                
                mun_norm = normalize_text(nome)
                pos_row_temp = ranking_sorted_temp.loc[
                    ranking_sorted_temp["municipio"] == mun_norm,
                    "rank"
                ]
                
                posicao_temp = int(pos_row_temp.values[0]) if not pos_row_temp.empty else "-"
                total_municipios_temp = len(ranking_sorted_temp)
                ranking_display_temp = f"{posicao_temp}Âº / {total_municipios_temp}<br><span style='font-size:11px;'>(Maior risco = 1Â°)</span>" if posicao_temp != "-" else "-"

                st.markdown(f"""
                <div class="mun-header-section">
                    <div class="mun-header">{nome}</div>
                    <div class="kpi-square-container">
                        <div class="kpi-square" style="border-left-color: #fb923c;">
                            <div class="kpi-square-title">Risco</div>
                            <div class="kpi-square-value">{round(risk, 3)}</div>
                        </div>
                        <div class="kpi-square" style="border-left-color: #38bdf8;">
                            <div class="kpi-square-title">Ranking</div>
                            <div class="kpi-square-value" style="font-size:17px;">{ranking_display_temp}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                c1, c2, c3 = st.columns(3)
                c1.metric("Hazard", round(hazard,3))
                c2.metric("Exposure", round(exposure,3))
                c3.metric("Vulnerability", round(vulnerability,3))

                if show_tables:
                    st.markdown(
                    '<p style="color:white; font-size:18px; font-weight: 500; ">DecomposiÃ§Ã£o dos SubÃ­ndices</p>',
                    unsafe_allow_html=True
                    )

                    sub1, sub2, sub3 = st.columns(3)

                    with sub1:
                        st.markdown("**Hazard**")

                        hazard_df = pd.DataFrame({
                            "VariÃ¡veis": [
                                "DÃ©ficit HÃ­drico",
                                "Variabilidade da PrecipitaÃ§Ã£o",
                                "Variabilidade do Vento",
                                "Amplitude TÃ©rmica"
                                ],
                            "Valor": [
                                df_mun["def_mean"].values[0],
                                df_mun["ppt_std"].values[0],
                                df_mun["ws_std"].values[0],
                                df_mun["dtr_mean"].values[0]
                                ]
                        })

                        st.markdown(styled_table(hazard_df), unsafe_allow_html=True)
                    
                    with sub2:
                        st.markdown("**Exposure**")

                        exposure_df = pd.DataFrame({
                            "VariÃ¡veis": [
                                "Empregos Industriais per capita",
                                "Empresas Industriais per capita"
                                ],
                            "Valor": [
                                df_mun["empregos_pc"].values[0],
                                df_mun["empresas_pc"].values[0]
                                ]
                        })

                        st.markdown(styled_table(exposure_df), unsafe_allow_html=True)

                    with sub3:
                        st.markdown("**Vulnerability**")

                        vuln_df = pd.DataFrame({
                            "VariÃ¡veis": [
                                "Intensidade EnergÃ©tica",
                                "Sensibilidade da ProduÃ§Ã£o AgrÃ­cola",
                                "ResiliÃªncia da Renda"
                            ],
                            "Valor": [
                                df_mun["energia_pc_norm"].values[0],
                                df_mun["agro_pc_norm"].values[0],
                                df_mun["pib_pc_inv"].values[0]
                            ]
                        })

                        st.markdown(styled_table(vuln_df), unsafe_allow_html=True)

                if show_charts:
                    fig = go.Figure()

                    fig.add_trace(go.Scatterpolar(
                        r=[hazard, exposure, vulnerability],
                        theta=["Hazard","Exposure","Vulnerability"],
                        fill='toself',
                        fillcolor='rgba(251,146,60,0.4)',
                        line=dict(color='#fb923c'),
                        name="MunicÃ­pio",
                        hovertemplate='<b>%{theta}</b><br>%{r:.2f}<extra></extra>'
                    ))

                    # Add mesoregion comparison
                    if "mesoregiao" in df_mun.columns and not df_mun["mesoregiao"].isna().all():
                        meso = df_mun["mesoregiao"].values[0]
                        if meso in mesoregiao_indices["mesoregiao"].values:
                            meso_data = mesoregiao_indices[mesoregiao_indices["mesoregiao"] == meso].iloc[0]
                            fig.add_trace(go.Scatterpolar(
                                r=[meso_data["hazard_avg"], meso_data["exposure_avg"], meso_data["vulnerability_avg"]],
                                theta=["Hazard","Exposure","Vulnerability"],
                                fill='toself',
                                fillcolor='rgba(56,189,248,0.2)',
                                line=dict(color='#38bdf8'),
                                name=f"MÃ©dia da MesoregiÃ£o: {meso.title()}",
                                hovertemplate='<b>%{theta}</b><br>%{r:.2f}<extra></extra>'
                            ))

                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color="white"),
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[0,1],
                                tickfont=dict(color="#9ca3af")
                            )
                        ),
                        showlegend=True,
                        legend=dict(
                            x=0.75,
                            y=1.0,
                            bgcolor='rgba(0,0,0,0)',
                            bordercolor='#4b5563',
                            borderwidth=1,
                            font=dict(color="white")
                        )
                    )

                    st.plotly_chart(fig, use_container_width=True)
                    textoin = gerar_texto_insight(df, df_mun)

                    st.markdown(f"""
                    <div style="
                        background-color:#111827;
                        padding:15px;
                        border-radius:8px;
                        border-left:3px solid #fb923c;
                        margin-top:15px;
                        color:#e5e7eb;
                        font-size:13px;
                        line-height:1.4;
                    ">
                        {textoin}
                    
                    """, unsafe_allow_html=True)

                return hazard, exposure, vulnerability

            # Renderiza lado a lado
            with colA:
                hazard1, exposure1, vulnerability1 = render_municipio(df_mun1, municipio_selecionado, show_tables=False, show_charts=False)

            with colB:
                hazard2, exposure2, vulnerability2 = render_municipio(df_mun2, municipio_2, show_tables=False, show_charts=False)

            # Exibe tÃ­tulo e tabelas lado a lado
            st.markdown(
                '<p style="color:white; font-size:18px; font-weight: 500; ">DecomposiÃ§Ã£o dos SubÃ­ndices</p>',
                unsafe_allow_html=True
            )

            sub1, sub2, sub3, sub4, sub5, sub6 = st.columns(6)

            # Tabelas para municipio 1
            with sub1:
                st.markdown("**Hazard**")
                hazard_df = pd.DataFrame({
                    "VariÃ¡veis": [
                        "DÃ©ficit HÃ­drico",
                        "Variabilidade da PrecipitaÃ§Ã£o",
                        "Variabilidade do Vento",
                        "Amplitude TÃ©rmica"
                    ],
                    "Valor": [
                        df_mun1["def_mean"].values[0],
                        df_mun1["ppt_std"].values[0],
                        df_mun1["ws_std"].values[0],
                        df_mun1["dtr_mean"].values[0]
                    ]
                })
                st.markdown(styled_table(hazard_df, font_size="12px"), unsafe_allow_html=True)

            with sub2:
                st.markdown("**Exposure**")
                exposure_df = pd.DataFrame({
                    "VariÃ¡veis": [
                        "Empregos Industriais per capita",
                        "Empresas Industriais per capita"
                    ],
                    "Valor": [
                        df_mun1["empregos_pc"].values[0],
                        df_mun1["empresas_pc"].values[0]
                    ]
                })
                st.markdown(styled_table(exposure_df, font_size="12px"), unsafe_allow_html=True)

            with sub3:
                st.markdown("**Vulnerability**")
                vuln_df = pd.DataFrame({
                    "VariÃ¡veis": [
                        "Intensidade EnergÃ©tica",
                        "Sensibilidade da ProduÃ§Ã£o AgrÃ­cola",
                        "ResiliÃªncia da Renda"
                    ],
                    "Valor": [
                        df_mun1["energia_pc_norm"].values[0],
                        df_mun1["agro_pc_norm"].values[0],
                        df_mun1["pib_pc_inv"].values[0]
                    ]
                })
                st.markdown(styled_table(vuln_df, font_size="12px"), unsafe_allow_html=True)

            # Tabelas para municipio 2
            with sub4:
                st.markdown("**Hazard**")
                hazard_df = pd.DataFrame({
                    "VariÃ¡veis": [
                        "DÃ©ficit HÃ­drico",
                        "Variabilidade da PrecipitaÃ§Ã£o",
                        "Variabilidade do Vento",
                        "Amplitude TÃ©rmica"
                    ],
                    "Valor": [
                        df_mun2["def_mean"].values[0],
                        df_mun2["ppt_std"].values[0],
                        df_mun2["ws_std"].values[0],
                        df_mun2["dtr_mean"].values[0]
                    ]
                })
                st.markdown(styled_table(hazard_df, font_size="12px"), unsafe_allow_html=True)

            with sub5:
                st.markdown("**Exposure**")
                exposure_df = pd.DataFrame({
                    "VariÃ¡veis": [
                        "Empregos Industriais per capita",
                        "Empresas Industriais per capita"
                    ],
                    "Valor": [
                        df_mun2["empregos_pc"].values[0],
                        df_mun2["empresas_pc"].values[0]
                    ]
                })
                st.markdown(styled_table(exposure_df, font_size="12px"), unsafe_allow_html=True)

            with sub6:
                st.markdown("**Vulnerability**")
                vuln_df = pd.DataFrame({
                    "VariÃ¡veis": [
                        "Intensidade EnergÃ©tica",
                        "Sensibilidade da ProduÃ§Ã£o AgrÃ­cola",
                        "ResiliÃªncia da Renda"
                    ],
                    "Valor": [
                        df_mun2["energia_pc_norm"].values[0],
                        df_mun2["agro_pc_norm"].values[0],
                        df_mun2["pib_pc_inv"].values[0]
                    ]
                })
                st.markdown(styled_table(vuln_df, font_size="12px"), unsafe_allow_html=True)

            # Exibe grÃ¡ficos lado a lado
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                fig1 = go.Figure()
                fig1.add_trace(go.Scatterpolar(
                    r=[hazard1, exposure1, vulnerability1],
                    theta=["Hazard","Exposure","Vulnerability"],
                    fill='toself',
                    fillcolor='rgba(251,146,60,0.4)',
                    line=dict(color='#fb923c'),
                    name="MunicÃ­pio",
                    hovertemplate='<b>%{theta}</b><br>%{r:.2f}<extra></extra>'
                ))
                
                # Add mesoregion comparison for municipality 1
                if "mesoregiao" in df_mun1.columns and not df_mun1["mesoregiao"].isna().all():
                    meso1 = df_mun1["mesoregiao"].values[0]
                    if meso1 in mesoregiao_indices["mesoregiao"].values:
                        meso_data1 = mesoregiao_indices[mesoregiao_indices["mesoregiao"] == meso1].iloc[0]
                        fig1.add_trace(go.Scatterpolar(
                            r=[meso_data1["hazard_avg"], meso_data1["exposure_avg"], meso_data1["vulnerability_avg"]],
                            theta=["Hazard","Exposure","Vulnerability"],
                            fill='toself',
                            fillcolor='rgba(56,189,248,0.2)',
                            line=dict(color='#38bdf8'),
                            name=f"MÃ©dia da MesoregiÃ£o",
                            hovertemplate='<b>%{theta}</b><br>%{r:.2f}<extra></extra>'
                        ))
                
                fig1.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="white"),
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0,1],
                            tickfont=dict(color="#9ca3af")
                        )
                    ),
                    showlegend=True,
                    legend=dict(
                        x=0.75,
                        y=1.0,
                        bgcolor='rgba(0,0,0,0)',
                        bordercolor='#4b5563',
                        borderwidth=1,
                        font=dict(color="white")
                    )
                )
                st.plotly_chart(fig1, use_container_width=True)
                texto1 = gerar_texto_insight(df, df_mun1)
                st.markdown(f"""
                <div style="
                    background-color:#111827;
                    padding:15px;
                    border-radius:8px;
                    border-left:3px solid #fb923c;
                    margin-top:15px;
                    color:#e5e7eb;
                    font-size:13px;
                    line-height:1.4;
                ">
                    {texto1}
                
                """, unsafe_allow_html=True)

            with chart_col2:
                fig2 = go.Figure()
                fig2.add_trace(go.Scatterpolar(
                    r=[hazard2, exposure2, vulnerability2],
                    theta=["Hazard","Exposure","Vulnerability"],
                    fill='toself',
                    fillcolor='rgba(251,146,60,0.4)',
                    line=dict(color='#fb923c'),
                    name="MunicÃ­pio",
                    hovertemplate='<b>%{theta}</b><br>%{r:.2f}<extra></extra>'
                ))
                
                # Add mesoregion comparison for municipality 2
                if "mesoregiao" in df_mun2.columns and not df_mun2["mesoregiao"].isna().all():
                    meso2 = df_mun2["mesoregiao"].values[0]
                    if meso2 in mesoregiao_indices["mesoregiao"].values:
                        meso_data2 = mesoregiao_indices[mesoregiao_indices["mesoregiao"] == meso2].iloc[0]
                        fig2.add_trace(go.Scatterpolar(
                            r=[meso_data2["hazard_avg"], meso_data2["exposure_avg"], meso_data2["vulnerability_avg"]],
                            theta=["Hazard","Exposure","Vulnerability"],
                            fill='toself',
                            fillcolor='rgba(56,189,248,0.2)',
                            line=dict(color='#38bdf8'),
                            name=f"MÃ©dia da MesoregiÃ£o",
                            hovertemplate='<b>%{theta}</b><br>%{r:.2f}<extra></extra>'
                        ))
                
                fig2.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="white"),
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0,1],
                            tickfont=dict(color="#9ca3af")
                        )
                    ),
                    showlegend=True,
                    legend=dict(
                        x=0.75,
                        y=1.0,
                        bgcolor='rgba(0,0,0,0)',
                        bordercolor='#4b5563',
                        borderwidth=1,
                        font=dict(color="white")
                    )
                )
                st.plotly_chart(fig2, use_container_width=True)
                texto2 = gerar_texto_insight(df, df_mun2)
                st.markdown(f"""
                <div style="
                    background-color:#111827;
                    padding:15px;
                    border-radius:8px;
                    border-left:3px solid #fb923c;
                    margin-top:15px;
                    color:#e5e7eb;
                    font-size:13px;
                    line-height:1.4;
                ">
                    {texto2}
                
                """, unsafe_allow_html=True)

    # CASO 2 â€” INDIVIDUAL
     
    else:

        df_mun = df[df["municipio_nome"] == municipio_selecionado]

        if not df_mun.empty:

            # ðŸ”¹ garantir normalizaÃ§Ã£o
            ranking["municipio"] = ranking["municipio"].apply(normalize_text)

            ranking_sorted = ranking.sort_values("risk_norm", ascending=False).reset_index(drop=True)
            ranking_sorted["rank"] = ranking_sorted.index + 1

            mun_norm = normalize_text(municipio_selecionado)

            pos_row = ranking_sorted.loc[
                ranking_sorted["municipio"] == mun_norm,
                "rank"
            ]

            posicao = int(pos_row.values[0]) if not pos_row.empty else "-"
            total_municipios = len(ranking_sorted)

            municipio = municipio_selecionado
            risk = round(df_mun["risk_norm"].values[0], 3)
            
            ranking_display = f"{posicao}Âº / {total_municipios}<br><span style='font-size:11px;'>(Maior risco = 1Â°)</span>" if posicao != "-" else "-"

            st.markdown(f"""
            
            <div class="mun-header-section">
                <div class="mun-header">{municipio}</div>
                <div class="kpi-square-container">
                    <div class="kpi-square" style="border-left-color: #fb923c;">
                        <div class="kpi-square-title">Risco</div>
                        <div class="kpi-square-value">{risk}</div>
                    </div>
                    <div class="kpi-square" style="border-left-color: #38bdf8;">
                        <div class="kpi-square-title">Ranking</div>
                        <div class="kpi-square-value" style="font-size:17px;">{ranking_display}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)

            hazard = df_mun["hazard_index"].values[0]
            exposure = df_mun["exposure_index"].values[0]
            vulnerability = df_mun["vulnerability_index"].values[0]

            col1.metric("Hazard", round(hazard,3))
            col2.metric("Exposure", round(exposure,3))
            col3.metric("Vulnerability", round(vulnerability,3))

            st.markdown(
            '<p style="color:white; font-size:18px; font-weight: 500; ">DecomposiÃ§Ã£o dos SubÃ­ndices</p>',
            unsafe_allow_html=True
            )

            sub1, sub2, sub3 = st.columns(3)

            with sub1:
                st.markdown("**Hazard**")

                hazard_df = pd.DataFrame({
                    "VariÃ¡veis": [
                        "DÃ©ficit HÃ­drico",
                        "Variabilidade da PrecipitaÃ§Ã£o",
                        "Variabilidade do Vento",
                        "Amplitude TÃ©rmica"
                        ],
                    "Valor": [
                        df_mun["def_mean"].values[0],
                        df_mun["ppt_std"].values[0],
                        df_mun["ws_std"].values[0],
                        df_mun["dtr_mean"].values[0]
                        ]
                })

                st.markdown(styled_table(hazard_df), unsafe_allow_html=True)
            
            with sub2:
                st.markdown("**Exposure**")

                exposure_df = pd.DataFrame({
                    "VariÃ¡veis": [
                        "Empregos Industriais per capita",
                        "Empresas Industriais per capita"
                        ],
                    "Valor": [
                        df_mun["empregos_pc"].values[0],
                        df_mun["empresas_pc"].values[0]
                        ]
                })

                st.markdown(styled_table(exposure_df), unsafe_allow_html=True)

            with sub3:
                st.markdown("**Vulnerability**")

                vuln_df = pd.DataFrame({
                    "VariÃ¡veis": [
                        "Intensidade EnergÃ©tica",
                        "Sensibilidade da ProduÃ§Ã£o AgrÃ­cola",
                        "ResiliÃªncia da Renda"
                    ],
                    "Valor": [
                        df_mun["energia_pc_norm"].values[0],
                        df_mun["agro_pc_norm"].values[0],
                        df_mun["pib_pc_inv"].values[0]
                    ]
                })

                st.markdown(styled_table(vuln_df), unsafe_allow_html=True)

            col_chart, col_text = st.columns([1.2, 1])

            with col_chart:

                fig = go.Figure()

                fig.add_trace(go.Scatterpolar(
                    r=[hazard, exposure, vulnerability],
                    theta=["Hazard","Exposure","Vulnerability"],
                    fill='toself',
                    fillcolor='rgba(251,146,60,0.4)',
                    line=dict(color='#fb923c'),
                    name="MunicÃ­pio",
                    hovertemplate='<b>%{theta}</b><br>%{r:.2f}<extra></extra>'
                ))

                # Add mesoregion comparison
                if "mesoregiao" in df_mun.columns and not df_mun["mesoregiao"].isna().all():
                    meso = df_mun["mesoregiao"].values[0]
                    if meso in mesoregiao_indices["mesoregiao"].values:
                        meso_data = mesoregiao_indices[mesoregiao_indices["mesoregiao"] == meso].iloc[0]
                        fig.add_trace(go.Scatterpolar(
                            r=[meso_data["hazard_avg"], meso_data["exposure_avg"], meso_data["vulnerability_avg"]],
                            theta=["Hazard","Exposure","Vulnerability"],
                            fill='toself',
                            fillcolor='rgba(56,189,248,0.2)',
                            line=dict(color='#38bdf8'),
                            name=f"MÃ©dia da MesoregiÃ£o: {meso.title()}",
                            hovertemplate='<b>%{theta}</b><br>%{r:.2f}<extra></extra>'
                        ))

                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="white"),
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0,1],
                            tickfont=dict(color="#9ca3af")
                        )
                    ),
                    showlegend=True,
                    legend=dict(
                        x=0.75,
                        y=1.0,
                        bgcolor='rgba(0,0,0,0)',
                        bordercolor='#4b5563',
                        borderwidth=1,
                        font=dict(color="white")
                    )
                )

                st.plotly_chart(fig, use_container_width=True)

            with col_text:

                texto = gerar_texto_insight(df, df_mun)

                st.markdown(f"""
                <div style="
                    background-color:#111827;
                    padding:20px;
                    border-radius:10px;
                    border-left:4px solid #fb923c;
                    margin-top:25px;
                    color:#e5e7eb;
                    font-size:15px;
                    line-height:1.5;
                    ">
                        {texto}

                """, unsafe_allow_html=True)

# =========================================================
# TAB 1 - ECONOMIC IMPACT 
# =========================================================

with tab1:

    st.header("Economic Impact")

# =========================================================
# TAB 2 - STATISTICAL INSIGHTS 
# =========================================================

with tab2:

    # DISTRIBUIÃ‡ÃƒO DO RISCO
    st.markdown("**DistribuiÃ§Ã£o do Risco ClimÃ¡tico**")
    col_chart, col_text = st.columns([1.2, 1])

    with col_chart:

        fig_dist = px.histogram(
            df,
            x="risk_norm",
            nbins=30,
            opacity=0.85
        )

        fig_dist.update_traces(
            hovertemplate=
            "Ãndice de Risco ClimÃ¡tico (faixa): %{x}<br>" +
            "MunicÃ­pios: %{y}<extra></extra>"
        )

        fig_dist.update_layout(
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            font=dict(color="white"),
            xaxis=dict(
                title="Ãndice de Risco ClimÃ¡tico",
                title_font=dict(color="white"),
                tickfont=dict(color="white")
            ),
            yaxis=dict(
                title="NÃºmero de MunicÃ­pios",
                title_font=dict(color="white"),
                tickfont=dict(color="white")
            )
        )

        st.plotly_chart(fig_dist, use_container_width=True)

        # MÃ‰TRICAS ESTATÃSTICAS
        col1, col2, col3 = st.columns(3)

        col1.metric("MÃ©dia", round(df["risk_norm"].mean(), 3))
        col2.metric("Desvio PadrÃ£o", round(df["risk_norm"].std(), 3))
        col3.metric("Assimetria", round(df["risk_norm"].skew(), 3))

        # INTERPRETAÃ‡ÃƒO
        mean = df["risk_norm"].mean()
        std = df["risk_norm"].std()
        skew = df["risk_norm"].skew()
    
        # interpretaÃ§Ã£o da assimetria
        if skew > 0.5:
            skew_text = "assimetria positiva, indicando concentraÃ§Ã£o de municÃ­pios em nÃ­veis mais baixos de risco, com poucos municÃ­pios apresentando valores elevados"
        elif skew < -0.5:
            skew_text = "assimetria negativa, sugerindo concentraÃ§Ã£o em nÃ­veis mais altos de risco"
        else:
            skew_text = "distribuiÃ§Ã£o aproximadamente simÃ©trica"

        # interpretaÃ§Ã£o da dispersÃ£o
        if std > 0.15:
            disp_text = "elevada heterogeneidade entre os municÃ­pios"
        else:
            disp_text = "baixa dispersÃ£o, indicando relativa homogeneidade entre os municÃ­pios"
    
    with col_text:
        st.markdown(f"""
        <div style="
            background-color:#111827;
            padding:18px;
            border-radius:10px;
            border-left:4px solid #38bdf8;
            margin-top:15px;
            color:#e5e7eb;
            font-size:15px;
            line-height:1.5;
        "> 
                             
        A distribuiÃ§Ã£o do risco climÃ¡tico industrial em Santa Catarina apresenta <b>{skew_text}</b>, 

        Observa-se tambÃ©m <b>{disp_text}</b>

        Esse padrÃ£o indica que o risco climÃ¡tico industrial tende a se concentrar em um conjunto restrito de municÃ­pios, enquanto a maior parte apresenta nÃ­veis reduzidos de risco relativo.
        
        """, unsafe_allow_html=True)
    
    # MISMATCH INDEX
    st.markdown("**Estrutura do Risco (Mismatch)**")

    # CÃ¡lculo do mismatch
    df["mismatch_std"] = df[[
        "hazard_index",
        "exposure_index",
        "vulnerability_index"
    ]].std(axis=1)

    # Threshold
    threshold = df["mismatch_std"].quantile(0.75)

    # Share
    high_mismatch_share = (df["mismatch_std"] > threshold).mean()

    col_chart, col_text = st.columns([1.2, 1])

    with col_chart:

        fig_mismatch = px.histogram(
            df,
            x="mismatch_std",
            nbins=30,
            opacity=0.85
        )

        fig_mismatch.update_traces(
            hovertemplate=
            "Desbalanceamento (faixa): %{x}<br>" +
            "MunicÃ­pios: %{y}<extra></extra>",
            marker=dict(color="#60a5fa")
        )

        fig_mismatch.update_layout(
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            font=dict(color="white"),
            xaxis=dict(
                title="Desbalanceamento entre Hazard, Exposure e Vulnerability",
                title_font=dict(color="white"),
                tickfont=dict(color="white")
            ),
            yaxis=dict(
                title="NÃºmero de MunicÃ­pios",
                title_font=dict(color="white"),
                tickfont=dict(color="white")
            )
        )

        st.plotly_chart(fig_mismatch, use_container_width=True)
        
        st.metric(
            "% MunicÃ­pios com Alto Mismatch",
            f"{high_mismatch_share*100:.1f}%"
        )

    with col_text:

        st.markdown(f"""
        <div style="
            background-color:#111827;
            padding:18px;
            border-radius:10px;
            border-left:4px solid #fb923c;
            margin-top:15px;
            color:#e5e7eb;
            font-size:15px;
            line-height:1.5;
        ">

        O indicador de mismatch captura o desbalanceamento entre hazard, exposure e vulnerability.

        Cerca de <b>{high_mismatch_share*100:.1f}%</b> dos municÃ­pios apresentam forte desbalanceamento entre essas dimensÃµes, com uma elevada e outra muito reduzida.

        Devido Ã  estrutura multiplicativa do Ã­ndice, isso tende a comprimir o risco climÃ¡tico industrial, mesmo na presenÃ§a de pressÃµes relevantes.

        Isso sugere a existÃªncia de <b>risco climÃ¡tico latente</b>, especialmente em contextos de baixa exposiÃ§Ã£o industrial.

        """, unsafe_allow_html=True)

    # =========================
    # SECTION 2: ECONOMIC INSIGHTS (Correlations)
    # =========================

    st.markdown("**CorrelaÃ§Ã£o entre SubÃ­ndices**")

    col1, col2 = st.columns([1.2, 1])

    with col1:

        # CORRELAÃ‡ÃƒO â€” SUBÃNDICES
        corr_sub = df[[
            "hazard_index",
            "exposure_index",
            "vulnerability_index",
        ]].corr()

        labels_sub = {
            "hazard_index": "Hazard",
            "exposure_index": "Exposure",
            "vulnerability_index": "Vulnerability"
        }

        corr_sub = corr_sub.rename(index=labels_sub, columns=labels_sub)

        fig_corr = px.imshow(
            corr_sub,
            text_auto=True,
            aspect="auto"
        )
        fig_corr.update_traces(
            hovertemplate=
            "%{y} Ã— %{x}<br>" +
            "CorrelaÃ§Ã£o: %{z:.2f}<extra></extra>"
        )

        fig_corr.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"),
            margin=dict(l=0, r=0, t=30, b=0),
            height=350,
            xaxis=dict(tickfont=dict(color="white")),
            yaxis=dict(tickfont=dict(color="white")),
            
        )

        st.plotly_chart(fig_corr, use_container_width=True)

    with col2:
        # TEXTO INTERPRETATIVO

        corr_no_diag = corr_sub.where(~np.eye(corr_sub.shape[0],dtype=bool))
        
        # Maior positiva
        max_pos = corr_no_diag.unstack().idxmax()
        val_pos = corr_no_diag.loc[max_pos[0], max_pos[1]]

        # Maior negativa
        max_neg = corr_no_diag.unstack().idxmin()
        val_neg = corr_no_diag.loc[max_neg[0], max_neg[1]]

        st.markdown(f"""
        <div style="
            background-color:#111827;
            padding:18px;
            border-radius:10px;
            border-left:4px solid #38bdf8;
            margin-top:15px;
            color:#e5e7eb;
            font-size:15px;
            line-height:1.5;
        ">

        A maior correlaÃ§Ã£o positiva ocorre entre <b>{max_pos[0]}</b> e <b>{max_pos[1]}</b> 
        (correlaÃ§Ã£o = {val_pos:.2f}), indicando que essas dimensÃµes tendem a se elevar conjuntamente entre os municÃ­pios, refletindo possÃ­veis padrÃµes estruturais compartilhados.

        Por outro lado, observa-se uma relaÃ§Ã£o inversa mais intensa entre <b>{max_neg[0]}</b> e <b>{max_neg[1]}</b> 
        (correlaÃ§Ã£o = {val_neg:.2f}), sugerindo que municÃ­pios com maior intensidade em uma dessas dimensÃµes 
        tendem a apresentar nÃ­veis mais baixos na outra.

        Do ponto de vista analÃ­tico, essa relaÃ§Ã£o nÃ£o implica causalidade direta, 
        mas sugere que esses componentes podem estar associados a caracterÃ­sticas econÃ´micas ou territoriais comuns.


        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("**CorrelaÃ§Ã£o entre VariÃ¡veis Estruturais**")
    col1, col2 = st.columns([1.2, 1], gap="small")
    with col1:
        # CORRELAÃ‡ÃƒO â€” VARIÃVEIS INTERNAS

        vars_cols = [
            # Hazard
            "def_mean", "ppt_std", "ws_std", "dtr_mean",
            # Exposure
            "empregos_pc", "empresas_pc",
            # Vulnerability
            "energia_pc_norm", "agro_pc_norm", "pib_pc_inv"
        ]

        corr_vars = df[vars_cols].corr()

        # Labels amigÃ¡veis
        labels_vars = {
            "def_mean": "DÃ©ficit hÃ­drico",
            "ppt_std": "Variabilidade da precipitaÃ§Ã£o",
            "ws_std": "Variabilidade do vento",
            "dtr_mean": "Amplitude tÃ©rmica",
            "empregos_pc": "Empregos industriais per capita",
            "empresas_pc": "Empresas industriais per capita",
            "energia_pc_norm": "Intensidade energÃ©tica",
            "agro_pc_norm": "Sensibilidade da produÃ§Ã£o agrÃ­cola",
            "pib_pc_inv": "ResiliÃªncia da renda"
        }

        corr_vars = corr_vars.rename(index=labels_vars, columns=labels_vars)

        fig_corr2 = px.imshow(
            corr_vars,
            text_auto=False,
            aspect="auto"
        )
        fig_corr2.update_traces(
            hovertemplate=
            "%{y} Ã— %{x}<br>" +
            "CorrelaÃ§Ã£o: %{z:.2f}<extra></extra>"
        )

        fig_corr2.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"),
            margin=dict(l=0, r=0, t=80, b=0, pad=0), 
            height=400,

            xaxis=dict(
                tickfont=dict(color="white"),
                constrain="domain"),
            yaxis=dict(tickfont=dict(color="white"),
                constrain="domain"),

            coloraxis_colorbar=dict(
                orientation="h",
                x=0.5,
                xanchor="center",
                y=1,          
                len=1.2,
                thickness=12,
                tickfont=dict(color="white", size=11)
            )
        )
        fig_corr2.update_xaxes(
            tickangle=40,   # ou 30 no mÃ¡ximo
            tickfont=dict(size=10)
        )
        st.plotly_chart(fig_corr2, use_container_width=True)
   
    with col2:
        # INSIGHT AVANÃ‡ADO
        st.markdown(f"""
        <div style="
            background-color:#111827;
            padding:18px;
            border-radius:10px;
            border-left:4px solid #fb923c;
            margin-top:15px;
            color:#e5e7eb;
            font-size:15px;
            line-height:1.5;
        ">

        A estrutura de correlaÃ§Ã£o evidencia como os determinantes do risco interagem entre si.  

        RelaÃ§Ãµes mais fortes sugerem maior associaÃ§Ã£o entre fatores climÃ¡ticos e econÃ´micos, 
        enquanto correlaÃ§Ãµes mais baixas indicam maior autonomia entre as dimensÃµes.

        Do ponto de vista analÃ­tico, isso reforÃ§a a necessidade de abordagens multidimensionais 
        na avaliaÃ§Ã£o do risco climÃ¡tico industrial.

        </div>
        """, unsafe_allow_html=True)

# =======================
# RODAPÃ‰
# =======================
st.markdown("""
<hr style="margin-top:40px; margin-bottom:10px; border:0.5px solid #374151;">

<p style="
    text-align:center;
    color:#6b7280;
    font-size:12px;
">
Â©Â© 2026 Climate Risk Index â€” Rebecca Lorandi Silveira Lara. For research and analytical purposes.
</p>
""", unsafe_allow_html=True)

