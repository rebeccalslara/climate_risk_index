# ============================================
# STREAMLIT DASHBOARD - CLIMATE RISK INDEX SC
# ============================================

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import unicodedata
import uuid
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
    background-color: #171717 !important;
    border: none !important;
    color: white !important;
    padding: 0.55rem 0.75rem !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    margin: 0 0 0.75rem 0 !important;
    text-align: left !important;
    box-shadow: none !important;
}

[data-testid="stSidebar"] button:hover {
    background-color: #1f2937 !important;
    color: #93c5fd !important;
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
# FUNÇÕES
# =========================

def normalize_text(text):
    if pd.isna(text):
        return text
    
    text = str(text)

    text = text.replace("-", " ")
    text = text.replace("'", " ")

    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    
    return " ".join(text.upper().split())

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
                cell_value = f"{cell_value:.3f}"
            html_table += f'<td style="padding: 8px; background-color: {hex_color}; color: white; font-size: {font_size}; border: none;">{cell_value}</td>'
        html_table += '</tr>'
    
    html_table += '</table>'
    
    return html_table

def format_brl(value):
    if pd.isna(value):
        return "-"
    abs_value = abs(value)
    sign = "-" if value < 0 else ""
    if abs_value >= 1_000_000_000:
        return f"{sign}R$ {abs_value / 1_000_000_000:.2f} bi"
    if abs_value >= 1_000_000:
        return f"{sign}R$ {abs_value / 1_000_000:.2f} mi"
    if abs_value >= 1_000:
        return f"{sign}R$ {abs_value / 1_000:.1f} mil"
    return f"{sign}R$ {abs_value:.0f}"

def format_pp(value):
    if pd.isna(value):
        return "-"
    return f"{value:+.3f} pp"

def format_index_delta(value):
    if pd.isna(value):
        return "-"
    return f"{value:+.3f}"

def impact_card(title, value, subtitle, color="#4292c6"):
    st.markdown(f"""
    <div style="
        background-color:#111827;
        border-left:4px solid {color};
        border-radius:8px;
        padding:16px 18px;
        min-height:118px;
        display:flex;
        flex-direction:column;
        justify-content:center;
    ">
        <div style="font-size:12px; color:#9ca3af; margin-bottom:6px;">{title}</div>
        <div style="font-size:24px; color:white; font-weight:700; line-height:1.2;">{value}</div>
        <div style="font-size:12px; color:#d1d5db; margin-top:8px; line-height:1.35;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def animated_plotly_chart(fig, height=420, frame_duration=70, transition_duration=35):
    plot_id = f"plotly_{uuid.uuid4().hex}"
    html = fig.to_html(
        include_plotlyjs="cdn",
        full_html=False,
        auto_play=False,
        div_id=plot_id,
        config={"responsive": True, "displayModeBar": False}
    )
    html += f"""
    <script>
    setTimeout(function() {{
        var plot = document.getElementById("{plot_id}");
        if (plot && plot._transitionData && plot._transitionData._frames.length > 0) {{
            Plotly.animate(plot, null, {{
                frame: {{duration: {frame_duration}, redraw: true}},
                transition: {{duration: {transition_duration}}},
                fromcurrent: false,
                mode: "immediate"
            }});
        }}
    }}, 120);
    </script>
    """
    components.html(html, height=height)

# =========================
# PATHS (COMPATÍVEL COM STREAMLIT CLOUD)
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent

data_path = BASE_DIR / "output" / "dashboard_dataset_2002_2023.csv"
economic_impact_path = BASE_DIR / "output" / "economic_impact_dashboard_municipal_year_2002_2021.csv"
hazard_norm_path = BASE_DIR / "data" / "data_handling" / "hazard_normalized_2002_2023.csv"
shapefile_path = BASE_DIR / "data" / "raw_data" / "shapes" / "SC_Municipios_2025.shp"
mesoregiao_path = BASE_DIR / "data" / "raw_data" / "shapes" / "42MEE250GC_SIR.shp"

# =========================
# LOAD DATA
# =========================

@st.cache_data
def load_data(data_mtime):
    df = pd.read_csv(data_path)
    hazard_norm_cols = ["def_mean_norm", "ppt_std_norm", "ws_std_norm", "dtr_mean_norm"]
    missing_hazard_norm_cols = [col for col in hazard_norm_cols if col not in df.columns]
    if missing_hazard_norm_cols:
        if hazard_norm_path.exists():
            hazard_norm = pd.read_csv(hazard_norm_path)
            hazard_norm["municipio"] = hazard_norm["municipio"].apply(normalize_text)
            hazard_norm["ano"] = pd.to_numeric(hazard_norm["ano"], errors="coerce").astype(int)
            df["municipio"] = df["municipio"].apply(normalize_text)
            df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype(int)
            df = df.merge(
                hazard_norm[["municipio", "ano"] + hazard_norm_cols],
                on=["municipio", "ano"],
                how="left"
            )
        else:
            st.error(
                "The dashboard dataset is missing normalized hazard columns. "
                "Regenerate output/dashboard_dataset_2002_2023.csv with script/climate_risk_index.py."
            )
            st.stop()
    gdf = gpd.read_file(shapefile_path, engine="pyogrio")
    gdf["geometry"] = gdf["geometry"].simplify(0.01)
    gdf_meso = gpd.read_file(mesoregiao_path, engine="pyogrio")
    return df, gdf, gdf_meso

df_all, gdf_map, gdf_meso = load_data(data_path.stat().st_mtime)

@st.cache_data
def load_economic_impact(economic_mtime):
    impact = pd.read_csv(economic_impact_path)
    impact["municipio"] = impact["municipio"].apply(normalize_text)
    impact["municipio_nome"] = impact["municipio"].str.title()
    impact["ano"] = pd.to_numeric(impact["ano"], errors="coerce").astype(int)
    return impact

df_econ = None
if economic_impact_path.exists():
    df_econ = load_economic_impact(economic_impact_path.stat().st_mtime)

# =========================
# DETECTAR COLUNA MUNICÍPIO
# =========================

possible_cols = ["NM_MUN", "NOME_MUN", "NM_MUNICIP", "municipio", "name"]

col_municipio = None
for col in gdf_map.columns:
    if col.upper() in [c.upper() for c in possible_cols]:
        col_municipio = col
        break

if col_municipio is None:
    st.error(f"Colunas disponíveis: {list(gdf_map.columns)}")
    st.stop()

gdf_map["municipio"] = gdf_map[col_municipio].apply(normalize_text)
df_all["municipio"] = df_all["municipio"].apply(normalize_text)

# =========================
# SIDEBAR - FIXED NAVIGATION
# =========================

# ABOUT BUTTON
if st.sidebar.button("About", use_container_width=True):
    st.session_state["show_about"] = not st.session_state.get("show_about", False)

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
# BUILD MESOREGIÃO INDICES
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
    Este projeto apresenta uma <b>adaptação do índice de risco climático do IPCC (AR5)</b> para o contexto industrial dos municípios de Santa Catarina. O modelo segue o framework conceitual amplamente utilizado na literatura de risco climático, no qual o risco é definido como a interação entre três dimensões fundamentais:
    </p>
    
    <div style="text-align:center; margin:20px 0;">
        <span style="font-size:20px; font-weight:500; color:white;">
            Risk = Hazard × Exposure × Vulnerability
        </span>
    </div>
    
    <p style="color:#e5e7eb; line-height:1.6;">
    Essa formulação, adotada por organismos internacionais como o IPCC e o UNDRR, entende o risco como um fenômeno sistêmico, resultante da combinação entre condições climáticas adversas, a exposição de ativos econômicos e a vulnerabilidade estrutural dos sistemas analisados. A formulação multiplicativa implica que a ausência ou baixa intensidade de qualquer componente reduz significativamente o risco total, evitando compensações indevidas entre fatores.
    </p>
    
    <p style="color:#e5e7eb; line-height:1.6;">
    Neste trabalho, o modelo foi adaptado para capturar especificamente o <b>risco climático sobre a estrutura produtiva industrial municipal</b>, incorporando variáveis que refletem a dinâmica regional.
    </p>
    
    <blockquote style="color:#9ca3af; border-left:3px solid #4292c6; padding-left:15px; margin:15px 0;">
    O índice resultante representa o <b>nível relativo de risco climático associado à atividade industrial municipal</b>. Valores variam entre 0 e 1, sendo que os mais elevados indicam maior suscetibilidade a impactos econômicos decorrentes de choques climáticos.
    </blockquote>
    
    <h3 style="color:#a50f15;">Construção dos índices</h3>
    
    <h4 style="color:#a50f15;">Hazard (Perigo climático)</h4>
    <p style="color:#e5e7eb; line-height:1.6;">
    O índice de hazard foi construído a partir de variáveis climáticas que capturam tanto a variabilidade quanto a ocorrência de extremos, incluindo déficit hídrico médio (<code>def_mean</code>), variabilidade da precipitação (<code>ppt_std</code>), variabilidade da velocidade do vento (<code>ws_std</code>) e amplitude térmica diária (<code>dtr_mean</code>).
    </p>
    
    <p style="color:#e5e7eb; line-height:1.6;">
    A agregação combina a média dessas variáveis, representando as condições climáticas estruturais, com o valor máximo, de modo a incorporar eventos extremos. Essa abordagem está alinhada com a literatura climática, que destaca o papel desproporcional de eventos extremos na geração de danos econômicos, especialmente em sistemas industriais sensíveis a choques abruptos.
    </p>
    
    <h4 style="color:#a50f15;">Exposure (Exposição)</h4>
    <p style="color:#e5e7eb; line-height:1.6;">
    O índice de exposição mensura o grau em que a atividade econômica municipal está sujeita a riscos climáticos, utilizando indicadores normalizados de empregos industriais per capita (<code>empregos_pc_norm</code>) e número de empresas per capita (<code>empresas_pc_norm</code>).
    </p>
    
    <p style="color:#e5e7eb; line-height:1.6;">
    A utilização de métricas per capita e sua agregação por média simples permitem capturar a <b>intensidade relativa da atividade industrial exposta</b>, garantindo comparabilidade entre municípios com diferentes escalas populacionais.
    </p>
    
    <h4 style="color:#a50f15;">Vulnerability (Vulnerabilidade)</h4>
    <p style="color:#e5e7eb; line-height:1.6;">
    A vulnerabilidade reflete a sensibilidade climática e energética e a capacidade adaptativa da renda, sendo composta por três dimensões principais: intensidade energética industrial per capita (<code>energia_pc_norm</code>), valor da produção agrícola per capita (<code>agro_pc_norm</code>) e renda per capita (<code>pib_pc_inv</code>).
    </p>
    
    <p style="color:#e5e7eb; line-height:1.6;">
    Esse conjunto de variáveis captura a sensibilidade dos municípios a choques energéticos e climáticos, bem como sua capacidade adaptativa, aproximada pela renda disponível para resposta e reconstrução. A agregação foi realizada por meio de média simples, assumindo contribuição equilibrada entre os fatores estruturais.
    </p>
    
    <hr style="border:0.5px solid #374151; margin:20px 0;">
    
    <div style="display:flex; gap:20px;">
        <div style="flex:1;">
            <h4 style="color:#a50f15;">Nota sobre os dados</h4>
            <p style="color:#9ca3af; font-size:13px; line-height:1.6;">
            Os dados utilizados são provenientes de bases oficiais e amplamente reconhecidas, incluindo TerraClimate (variáveis climáticas), SIDRA/IBGE (indicadores econômicos), RAIS (estrutura produtiva), CELESC (dados energéticos) e IPEADATA (Indices de deflação).
            </p>
            <p style="color:#9ca3af; font-size:13px; line-height:1.6;">
            Todas as variáveis foram previamente tratadas, normalizadas e harmonizadas ao nível municipal, assegurando consistência e comparabilidade entre as unidades de análise.
            </p>
        </div>
        <div style="flex:1;">
            <h4 style="color:#a50f15;">Considerações finais</h4>
            <p style="color:#9ca3af; font-size:13px; line-height:1.6;">
            O índice proposto constitui uma ferramenta analítica para a identificação de <b>hotspots de risco climático industrial em Santa Catarina</b>, podendo subsidiar a formulação de políticas públicas, estratégias de adaptação e análises econômicas regionais sob a perspectiva das mudanças climáticas.
            </p>
            <p style="color:#9ca3af; font-size:13px; line-height:1.6;">
            Trata-se de uma medida relativa, adaptada ao contexto regional, que mantém aderência ao arcabouço conceitual do IPCC.
            </p>
        </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

# SIDEBAR CONTROLS
municipios = sorted(df["municipio_nome"].unique())

municipio_selecionado = st.sidebar.selectbox(
    "Selecione um município:",
    ["Todos"] + municipios
)

modo_analise = st.sidebar.radio(
    "Modo de análise:",
    ["Individual", "Comparação"]
)

# Segundo município (apenas se comparação)
if modo_analise == "Comparação":
    municipio_2 = st.sidebar.selectbox(
        "Selecione o segundo município:",
        municipios
    )
else:
    municipio_2 = None

# =========================
# TÍTULO
# =========================

st.title("Indice de Risco Climático Industrial de Santa Catarina")

# =========================
# FUNÇÃO PARA ANÁLISE
# =========================

def gerar_texto_insight(df, df_mun):

    # =========================
    # VARIÁVEIS BASE
    # =========================
    risk = df_mun["risk_norm"].values[0]
    hazard = df_mun["hazard_index"].values[0]
    exposure = df_mun["exposure_index"].values[0]
    vulnerability = df_mun["vulnerability_index"].values[0]

    # =========================
    # CLASSIFICAÇÃO RELATIVA (QUANTIL)
    # =========================
    p33 = df["risk_norm"].quantile(0.33)
    p66 = df["risk_norm"].quantile(0.66)

    if risk > p66:
        nivel = "alto"
    elif risk > p33:
        nivel = "moderado"
    else:
        nivel = "baixo"

    # posição no estado
    posicao = (df["risk_norm"] < risk).mean()

    if posicao > 0.66:
        pos_text = "entre os municípios de maior risco no estado"
    elif posicao > 0.33:
        pos_text = "em posição intermediária no estado"
    else:
        pos_text = "entre os municípios de menor risco no estado"

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
    # VARIÁVEL DOMINANTE
    # =========================
    if main_driver == "Hazard":
        vars_dict = {
            "déficit hídrico": df_mun["def_mean_norm"].values[0],
            "variabilidade da precipitação": df_mun["ppt_std_norm"].values[0],
            "variabilidade do vento": df_mun["ws_std_norm"].values[0],
            "amplitude térmica": df_mun["dtr_mean_norm"].values[0]
        }

    elif main_driver == "Exposure":
        vars_dict = {
            "empregos industriais per capita": df_mun["empregos_pc_norm"].values[0],
            "empresas industriais per capita": df_mun["empresas_pc_norm"].values[0]
        }

    else:
        vars_dict = {
            "intensidade energética": df_mun["energia_pc_norm"].values[0],
            "sensibilidade da produção agrícola": df_mun["agro_pc_norm"].values[0],
            "resiliência da renda": df_mun["pib_pc_inv"].values[0]
        }

    main_variable = max(vars_dict, key=vars_dict.get)

    # =========================
    # LÓGICA DE POLÍTICA (AJUSTE EXPOSURE)
    # =========================
    if main_driver == "Exposure":

        # segundo driver
        drivers_sorted = sorted(drivers.items(), key=lambda x: x[1], reverse=True)
        second_driver = drivers_sorted[1][0]

        # variável dominante do segundo driver
        if second_driver == "Hazard":
            second_vars = {
                "déficit hídrico": df_mun["def_mean_norm"].values[0],
                "variabilidade da precipitação": df_mun["ppt_std_norm"].values[0],
                "variabilidade do vento": df_mun["ws_std_norm"].values[0],
                "amplitude térmica": df_mun["dtr_mean_norm"].values[0]
            }
        else:
            second_vars = {
                "intensidade energética": df_mun["energia_pc_norm"].values[0],
                "sensibilidade da produção agrícola": df_mun["agro_pc_norm"].values[0],
                "resiliência da renda": df_mun["pib_pc_inv"].values[0]
            }

        second_variable = max(second_vars, key=second_vars.get)

        politica_texto = f"""
Do ponto de vista econômico, o risco reflete principalmente o volume de atividade exposta. 
Nesse contexto, políticas devem atuar sobre **{second_driver.lower()}**, 
especialmente em **{second_variable}**, reduzindo a sensibilidade a choques climáticos.
"""

    else:

        politica_texto = f"""
Do ponto de vista econômico, isso sugere que intervenções direcionadas a **{main_driver.lower()}**, 
especialmente sobre **{main_variable}**, tendem a gerar maior efetividade na mitigação do risco climático industrial.
"""

    # =========================
    # ANULAÇÃO
    # =========================
    if drivers[min_driver] < 0.1:
        anulacao_texto = f"""
Observa-se que a dimensão **{min_driver}** apresenta valor muito reduzido, 
atuando como fator limitante do risco agregado. Na formulação multiplicativa 
do índice, essa baixa intensidade contribui para **atenuar o risco total**, 
mesmo na presença de valores mais elevados nas demais dimensões.
"""
    else:
        anulacao_texto = ""

    # =========================
    # TEXTO FINAL
    # =========================
    texto = f"""
O município apresenta um nível **{nivel} de risco climático industrial** 
(índice = {risk:.3f}), situando-se {pos_text}.

A decomposição do índice indica que o principal fator de risco é **{main_driver}**, 
com destaque para **{main_variable}** como principal componente explicativo dentro dessa dimensão.

{politica_texto}

{anulacao_texto}
"""

    return texto

# =========================
# TABS - NEW STRUCTURE
# =========================

tab0, tab1 = st.tabs(["Analysis", "Economic Impact"])

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

        # ORDENAÇÃO
        top10 = ranking.sort_values("risk_norm", ascending=False).head(10)
        bottom10 = ranking.sort_values("risk_norm", ascending=True).head(10)

        # MAIOR RISCO
        st.markdown("**Municípios de Maior Risco**")

        fig_top = px.bar(
            top10.sort_values("risk_norm", ascending=True),  
            x="risk_norm",
            y="municipio",
            orientation="h",
            color="risk_norm",
            color_continuous_scale="OrRd", 
            labels={"risk_norm": "Índice de Risco Climático"}
        )

        fig_top.update_traces(
            hovertemplate="<b>%{y}</b><br>Índice de Risco Climático: %{x:.3f}<extra></extra>"
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
        st.markdown("**Municípios de Menor Risco**")

        fig_bot = px.bar(
            bottom10.sort_values("risk_norm", ascending=True),
            x="risk_norm",
            y="municipio",
            orientation="h",
            color="risk_norm",
            color_continuous_scale="Blues", 
            labels={"risk_norm": "Índice de Risco Climático"}
        )

        fig_bot.update_traces(
            hovertemplate="<b>%{y}</b><br>Índice de Risco Climático: %{x:.3f}<extra></extra>"
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
        st.markdown("**Distribuição Geográfica**")
        container = st.container(border=False)
        with container:
            fig = px.choropleth(
                gdf_final,
                geojson=gdf_final.geometry,
                locations=gdf_final.index,
                color="risk_norm",
                color_continuous_scale="Reds",
                hover_name="municipio",
                labels={"risk_norm": "Índice de Risco Climático"},
            
            )

            fig.update_geos(
                fitbounds="locations",
                visible=False,
                bgcolor='rgba(0,0,0,0)' 
            )

            fig.update_traces(
                hovertemplate="<b>%{hovertext}</b><br>Índice de Risco Climático: %{z:.3f}<extra></extra>"
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
                    title=dict(text="Índice de Risco Climático", font=dict(color="white", size=12)),
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
        <b>Interpretação dos Dados</b><br><br>
        Municípios de maior risco combinam níveis elevados de hazard climático, alta exposição da atividade industrial e maior vulnerabilidade.
        
        Já municípios de menor risco apresentam menor suscetibilidade a impactos climáticos, seja por menor exposição, melhores condições estruturais ou menor intensidade de eventos climáticos. 
        Como o índice de risco é construído de forma multiplicativa, valores próximos de zero em qualquer uma das dimensões reduzem significativamente o risco total.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # =========================
    # SECTION 2: DETAILED ANALYSIS
    # =========================

    st.subheader("Análise Detalhada por Município")

    # CASO 1 — TODOS
    if municipio_selecionado == "Todos" and modo_analise == "Individual":
        st.markdown(
            '<p style="color:#9ca3af; font-size:13px; font-style:italic;">Selecione um município na barra lateral para visualizar a análise detalhada.</p>',
            unsafe_allow_html=True
        )

    # CASO 3 — COMPARAÇÃO
    elif modo_analise == "Comparação":

        if municipio_selecionado == municipio_2:
            st.warning("Selecione dois municípios diferentes para comparação.")
        
        else:
            df_mun1 = df[df["municipio_nome"] == municipio_selecionado]
            df_mun2 = df[df["municipio_nome"] == municipio_2]

            colA, colB = st.columns(2)

            # FUNÇÃO REUTILIZÁVEL
            def render_municipio(df_mun, nome, show_tables=True, show_charts=True):

                risk = df_mun["risk_norm"].values[0]
                hazard = df_mun["hazard_index"].values[0]
                exposure = df_mun["exposure_index"].values[0]
                vulnerability = df_mun["vulnerability_index"].values[0]

                # 🔹 garantir normalização para o ranking
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
                ranking_display_temp = f"{posicao_temp}º / {total_municipios_temp}<br><span style='font-size:11px;'>(Maior risco = 1°)</span>" if posicao_temp != "-" else "-"

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
                    '<p style="color:white; font-size:18px; font-weight: 500; ">Decomposição dos Subíndices</p>',
                    unsafe_allow_html=True
                    )

                    sub1, sub2, sub3 = st.columns(3)

                    with sub1:
                        st.markdown("**Hazard**")

                        hazard_df = pd.DataFrame({
                            "Variáveis": [
                                "Déficit Hídrico",
                                "Variabilidade da Precipitação",
                                "Variabilidade do Vento",
                                "Amplitude Térmica"
                                ],
                            "Valor": [
                                df_mun["def_mean_norm"].values[0],
                                df_mun["ppt_std_norm"].values[0],
                                df_mun["ws_std_norm"].values[0],
                                df_mun["dtr_mean_norm"].values[0]
                                ]
                        })

                        st.markdown(styled_table(hazard_df), unsafe_allow_html=True)
                    
                    with sub2:
                        st.markdown("**Exposure**")

                        exposure_df = pd.DataFrame({
                            "Variáveis": [
                                "Empregos Industriais per capita",
                                "Empresas Industriais per capita"
                                ],
                            "Valor": [
                                df_mun["empregos_pc_norm"].values[0],
                                df_mun["empresas_pc_norm"].values[0]
                                ]
                        })

                        st.markdown(styled_table(exposure_df), unsafe_allow_html=True)

                    with sub3:
                        st.markdown("**Vulnerability**")

                        vuln_df = pd.DataFrame({
                            "Variáveis": [
                                "Intensidade Energética",
                                "Sensibilidade da Produção Agrícola",
                                "Resiliência da Renda"
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
                        name="Município",
                        hovertemplate='<b>%{theta}</b><br>%{r:.3f}<extra></extra>'
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
                                name=f"Média da Mesoregião: {meso.title()}",
                                hovertemplate='<b>%{theta}</b><br>%{r:.3f}<extra></extra>'
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

            # Exibe título e tabelas lado a lado
            st.markdown(
                '<p style="color:white; font-size:18px; font-weight: 500; ">Decomposição dos Subíndices</p>',
                unsafe_allow_html=True
            )

            sub1, sub2, sub3, sub4, sub5, sub6 = st.columns(6)

            # Tabelas para municipio 1
            with sub1:
                st.markdown("**Hazard**")
                hazard_df = pd.DataFrame({
                    "Variáveis": [
                        "Déficit Hídrico",
                        "Variabilidade da Precipitação",
                        "Variabilidade do Vento",
                        "Amplitude Térmica"
                    ],
                    "Valor": [
                        df_mun1["def_mean_norm"].values[0],
                        df_mun1["ppt_std_norm"].values[0],
                        df_mun1["ws_std_norm"].values[0],
                        df_mun1["dtr_mean_norm"].values[0]
                    ]
                })
                st.markdown(styled_table(hazard_df, font_size="12px"), unsafe_allow_html=True)

            with sub2:
                st.markdown("**Exposure**")
                exposure_df = pd.DataFrame({
                    "Variáveis": [
                        "Empregos Industriais per capita",
                        "Empresas Industriais per capita"
                    ],
                    "Valor": [
                        df_mun1["empregos_pc_norm"].values[0],
                        df_mun1["empresas_pc_norm"].values[0]
                    ]
                })
                st.markdown(styled_table(exposure_df, font_size="12px"), unsafe_allow_html=True)

            with sub3:
                st.markdown("**Vulnerability**")
                vuln_df = pd.DataFrame({
                    "Variáveis": [
                        "Intensidade Energética",
                        "Sensibilidade da Produção Agrícola",
                        "Resiliência da Renda"
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
                    "Variáveis": [
                        "Déficit Hídrico",
                        "Variabilidade da Precipitação",
                        "Variabilidade do Vento",
                        "Amplitude Térmica"
                    ],
                    "Valor": [
                        df_mun2["def_mean_norm"].values[0],
                        df_mun2["ppt_std_norm"].values[0],
                        df_mun2["ws_std_norm"].values[0],
                        df_mun2["dtr_mean_norm"].values[0]
                    ]
                })
                st.markdown(styled_table(hazard_df, font_size="12px"), unsafe_allow_html=True)

            with sub5:
                st.markdown("**Exposure**")
                exposure_df = pd.DataFrame({
                    "Variáveis": [
                        "Empregos Industriais per capita",
                        "Empresas Industriais per capita"
                    ],
                    "Valor": [
                        df_mun2["empregos_pc_norm"].values[0],
                        df_mun2["empresas_pc_norm"].values[0]
                    ]
                })
                st.markdown(styled_table(exposure_df, font_size="12px"), unsafe_allow_html=True)

            with sub6:
                st.markdown("**Vulnerability**")
                vuln_df = pd.DataFrame({
                    "Variáveis": [
                        "Intensidade Energética",
                        "Sensibilidade da Produção Agrícola",
                        "Resiliência da Renda"
                    ],
                    "Valor": [
                        df_mun2["energia_pc_norm"].values[0],
                        df_mun2["agro_pc_norm"].values[0],
                        df_mun2["pib_pc_inv"].values[0]
                    ]
                })
                st.markdown(styled_table(vuln_df, font_size="12px"), unsafe_allow_html=True)

            # Exibe gráficos lado a lado
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                fig1 = go.Figure()
                fig1.add_trace(go.Scatterpolar(
                    r=[hazard1, exposure1, vulnerability1],
                    theta=["Hazard","Exposure","Vulnerability"],
                    fill='toself',
                    fillcolor='rgba(251,146,60,0.4)',
                    line=dict(color='#fb923c'),
                    name="Município",
                    hovertemplate='<b>%{theta}</b><br>%{r:.3f}<extra></extra>'
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
                            name=f"Média da Mesoregião",
                            hovertemplate='<b>%{theta}</b><br>%{r:.3f}<extra></extra>'
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
                    name="Município",
                    hovertemplate='<b>%{theta}</b><br>%{r:.3f}<extra></extra>'
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
                            name=f"Média da Mesoregião",
                            hovertemplate='<b>%{theta}</b><br>%{r:.3f}<extra></extra>'
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

    # CASO 2 — INDIVIDUAL
     
    else:

        df_mun = df[df["municipio_nome"] == municipio_selecionado]

        if not df_mun.empty:

            # 🔹 garantir normalização
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
            
            ranking_display = f"{posicao}º / {total_municipios}<br><span style='font-size:11px;'>(Maior risco = 1°)</span>" if posicao != "-" else "-"

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
            '<p style="color:white; font-size:18px; font-weight: 500; ">Decomposição dos Subíndices</p>',
            unsafe_allow_html=True
            )

            sub1, sub2, sub3 = st.columns(3)

            with sub1:
                st.markdown("**Hazard**")

                hazard_df = pd.DataFrame({
                    "Variáveis": [
                        "Déficit Hídrico",
                        "Variabilidade da Precipitação",
                        "Variabilidade do Vento",
                        "Amplitude Térmica"
                        ],
                    "Valor": [
                        df_mun["def_mean_norm"].values[0],
                        df_mun["ppt_std_norm"].values[0],
                        df_mun["ws_std_norm"].values[0],
                        df_mun["dtr_mean_norm"].values[0]
                        ]
                })

                st.markdown(styled_table(hazard_df), unsafe_allow_html=True)
            
            with sub2:
                st.markdown("**Exposure**")

                exposure_df = pd.DataFrame({
                    "Variáveis": [
                        "Empregos Industriais per capita",
                        "Empresas Industriais per capita"
                        ],
                    "Valor": [
                        df_mun["empregos_pc_norm"].values[0],
                        df_mun["empresas_pc_norm"].values[0]
                        ]
                })

                st.markdown(styled_table(exposure_df), unsafe_allow_html=True)

            with sub3:
                st.markdown("**Vulnerability**")

                vuln_df = pd.DataFrame({
                    "Variáveis": [
                        "Intensidade Energética",
                        "Sensibilidade da Produção Agrícola",
                        "Resiliência da Renda"
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
                    name="Município",
                    hovertemplate='<b>%{theta}</b><br>%{r:.3f}<extra></extra>'
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
                            name=f"Média da Mesoregião: {meso.title()}",
                            hovertemplate='<b>%{theta}</b><br>%{r:.3f}<extra></extra>'
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

    if df_econ is None:
        st.warning(
            "Os resultados de impacto econômico não foram encontrados. "
            "Execute script/economic_impact.py para gerar o arquivo usado no painel."
        )
    else:
        econ_years = sorted(df_econ["ano"].dropna().astype(int).unique())
        available_impact_years = [year for year in econ_years if year >= 2003]

        if ano_selecionado not in available_impact_years:
            st.warning("Dados indisponíveis para este ano. O impacto econômico está disponível apenas para 2003-2021.")
        elif municipio_selecionado == "Todos":
            st.info("Selecione um município na barra lateral para visualizar as estimativas de impacto econômico.")
        else:
            econ_year = ano_selecionado
            econ_municipio = municipio_selecionado
            econ_year_df = df_econ[df_econ["ano"] == econ_year].copy()
            econ_row = econ_year_df[econ_year_df["municipio_nome"] == econ_municipio]

            render_economic_details = False

            if econ_row.empty:
                st.info("Não há dados econômicos disponíveis para esta combinação de município e ano.")
            else:
                econ_row = econ_row.iloc[0]

                required_impact_cols = [
                    "risk_change",
                    "estimated_gdp_risk_impact_brl",
                    "estimated_agro_risk_impact_brl",
                    "estimated_industrial_indirect_impact_brl"
                ]
                pre_creation_municipalities = {"BALNEARIO RINCAO", "PESCARIA BRAVA"}

                if econ_row[required_impact_cols].isna().any():
                    if normalize_text(econ_municipio) in pre_creation_municipalities:
                        st.warning(
                            f"Dados indisponíveis para {econ_municipio} em {econ_year}. "
                            "Este município foi criado depois do início da série econômica."
                        )
                    else:
                        st.warning(
                            "Não foi possível calcular o impacto econômico para este ano porque a comparação "
                            "com o ano anterior ou alguma variável econômica está indisponível."
                        )
                else:
                    render_economic_details = True

            if render_economic_details:
                previous_year = int(econ_row["previous_ano"]) if pd.notna(econ_row["previous_ano"]) else None
                period_label = f"{previous_year}-{econ_year}" if previous_year else f"{econ_year}"

                risk_change = econ_row["risk_change"]
                hazard_change = econ_row["hazard_change"]
                gdp_impact = econ_row["estimated_gdp_risk_impact_brl"]
                agro_impact = econ_row["estimated_agro_risk_impact_brl"]
                industrial_spillover = econ_row["estimated_industrial_indirect_impact_brl"]

                st.markdown(f"""
                <div style="margin:8px 0 16px 0;">
                    <div style="color:#9ca3af; font-size:12px; text-transform:uppercase; letter-spacing:0.06em;">
                        Resumo do impacto econômico
                    </div>
                    <div style="color:white; font-size:26px; font-weight:700; margin-top:4px;">
                        {econ_municipio} · {period_label}
                    </div>
                    <div style="color:#d1d5db; font-size:14px; margin-top:8px; line-height:1.45;">
                        Valores estimados representam efeitos associados pelos modelos de painel com efeitos fixos,
                        não prova causal direta. Os valores monetários são estimativas de comunicação derivadas
                        dos efeitos percentuais do modelo e das bases econômicas locais. Dados econômicos disponíveis até 2021.
                    </div>
                </div>
                """, unsafe_allow_html=True)

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    impact_card(
                        "Mudança no risco climático",
                        format_index_delta(risk_change),
                        f"Índice sem PIB, variação vs. ano anterior",
                        "#4292c6"
                    )
                with c2:
                    impact_card(
                        "Impacto associado no PIB",
                        format_brl(gdp_impact),
                        f"{format_pp(econ_row['gdp_risk_percent_points'])} na taxa de crescimento",
                        "#fb923c"
                    )
                with c3:
                    impact_card(
                        "Canal agropecuário",
                        format_brl(agro_impact),
                        f"{format_pp(econ_row['agro_risk_percent_points'])} no VA Agro",
                        "#fb923c"
                    )
                with c4:
                    impact_card(
                        "Spillover industrial",
                        format_brl(industrial_spillover),
                        f"{format_pp(econ_row['industrial_indirect_percent_points'])} via agro",
                        "#38bdf8"
                    )

                st.markdown("<br>", unsafe_allow_html=True)

                chart_col, text_col = st.columns([1.25, 0.95])

                with chart_col:
                    impact_channels = pd.DataFrame({
                        "Canal": [
                            "PIB associado ao risco",
                            "VA Agro associado ao risco",
                            "Spillover industrial"
                        ],
                        "Impacto (R$)": [
                            econ_row["estimated_gdp_risk_impact_brl"],
                            econ_row["estimated_agro_risk_impact_brl"],
                            econ_row["estimated_industrial_indirect_impact_brl"]
                        ],
                        "Percentual": [
                            econ_row["gdp_risk_percent_points"],
                            econ_row["agro_risk_percent_points"],
                            econ_row["industrial_indirect_percent_points"]
                        ]
                    })
                    impact_channels["Percentual Label"] = impact_channels["Percentual"].apply(
                        lambda value: "-" if pd.isna(value) else f"{value:+.3f} pp"
                    )
                    impact_chart_values = impact_channels["Impacto (R$)"].dropna()
                    impact_chart_min = min(0, impact_chart_values.min()) if not impact_chart_values.empty else -1
                    impact_chart_max = max(0, impact_chart_values.max()) if not impact_chart_values.empty else 1
                    impact_chart_padding = max((impact_chart_max - impact_chart_min) * 0.15, 1)

                    channel_colors = ["#fb923c", "#4292c6", "#38bdf8"]
                    animation_steps = np.linspace(0, 1, 9)
                    fig_impacts = go.Figure(
                        data=[
                            go.Bar(
                                x=impact_channels["Canal"],
                                y=impact_channels["Impacto (R$)"],
                                marker_color=channel_colors,
                                customdata=impact_channels["Percentual Label"],
                                hovertemplate="%{x}<br>Impacto: R$ %{y:,.0f}<br>Efeito: %{customdata}<extra></extra>"
                            )
                        ],
                        frames=[
                            go.Frame(
                                data=[
                                    go.Bar(
                                        x=impact_channels["Canal"],
                                        y=impact_channels["Impacto (R$)"] * step,
                                        marker_color=channel_colors,
                                        customdata=impact_channels["Percentual Label"],
                                        hovertemplate="%{x}<br>Impacto: R$ %{y:,.0f}<br>Efeito: %{customdata}<extra></extra>"
                                    )
                                ],
                                name=f"{step:.2f}"
                            )
                            for step in animation_steps
                        ]
                    )
                    fig_impacts.update_layout(
                        height=385,
                        showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=90, r=20, t=10, b=82),
                        font=dict(color="white"),
                        xaxis=dict(
                            title="",
                            tickfont=dict(color="white"),
                            showticklabels=True,
                            showline=True,
                            showgrid=False,
                            linecolor="white",
                            ticks="outside",
                            tickcolor="white",
                            automargin=True
                        ),
                        yaxis=dict(
                            title="Impacto estimado (R$)",
                            title_font=dict(color="white"),
                            title_standoff=34,
                            tickfont=dict(color="white"),
                            showticklabels=True,
                            showline=True,
                            showgrid=False,
                            linecolor="white",
                            ticks="outside",
                            tickcolor="white",
                            automargin=True,
                            range=[
                                impact_chart_min - impact_chart_padding,
                                impact_chart_max + impact_chart_padding
                            ]
                        )
                    )
                    animated_plotly_chart(fig_impacts, height=415, frame_duration=115, transition_duration=60)

                with text_col:
                    direction_text = "aumentou" if pd.notna(risk_change) and risk_change > 0 else "diminuiu"
                    gdp_direction = "perda" if pd.notna(gdp_impact) and gdp_impact < 0 else "ganho associado"
                    agro_direction = "perda" if pd.notna(agro_impact) and agro_impact < 0 else "ganho associado"

                    st.markdown(f"""
                    <div style="
                        background-color:#111827;
                        border-radius:8px;
                        padding:18px;
                        border-left:4px solid #f97316;
                        color:#e5e7eb;
                        font-size:14px;
                        line-height:1.55;
                    ">
                        Entre {previous_year if previous_year else "-"} e {econ_year}, o índice de risco climático
                        {direction_text} <b>{format_index_delta(risk_change)}</b> em {econ_municipio}.
                        Pelos modelos estimados, essa mudança está associada a uma {gdp_direction} de
                        <b>{format_brl(gdp_impact)}</b> no PIB e a uma {agro_direction} de
                        <b>{format_brl(agro_impact)}</b> no valor adicionado agropecuário.
                        <br><br>
                        O canal industrial é apresentado como spillover: o modelo não encontrou efeito direto
                        robusto do risco sobre a indústria, mas encontrou associação positiva entre crescimento
                        agropecuário e crescimento industrial.
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<div style='margin-top:-12px; margin-bottom:-12px; color:white;'><b>Progressão das Estimativas do Modelo</b></div>", unsafe_allow_html=True)
                mun_series = df_econ[df_econ["municipio_nome"] == econ_municipio].copy()
                mun_series = mun_series.sort_values("ano")
                mun_story = mun_series[(mun_series["ano"] >= 2003) & (mun_series["ano"] <= econ_year)].copy()
                mun_story["risk_change_label"] = mun_story["risk_change"].apply(
                    lambda value: "-" if pd.isna(value) else f"{value:+.3f}"
                )
                story_years = mun_story["ano"].dropna().astype(int).tolist()
                risk_values = mun_story["risk_change"].dropna()
                impact_values = mun_story["estimated_gdp_risk_impact_brl"].dropna()
                risk_min = min(0, risk_values.min()) if not risk_values.empty else -0.1
                risk_max = max(0, risk_values.max()) if not risk_values.empty else 0.1
                risk_padding = max((risk_max - risk_min) * 0.15, 0.01)
                impact_min = min(0, impact_values.min()) if not impact_values.empty else -1
                impact_max = max(0, impact_values.max()) if not impact_values.empty else 1
                impact_padding = max((impact_max - impact_min) * 0.15, 1)

                fig_series = go.Figure()
                fig_series.add_trace(go.Scatter(
                    x=mun_story["ano"],
                    y=mun_story["risk_change"],
                    customdata=mun_story["risk_change_label"],
                    mode="lines+markers",
                    name="Mudança no risco",
                    line=dict(color="#38bdf8", width=3),
                    hovertemplate="Ano: %{x}<br>Mudança no risco: %{customdata}<extra></extra>"
                ))
                fig_series.add_trace(go.Bar(
                    x=mun_story["ano"],
                    y=mun_story["estimated_gdp_risk_impact_brl"],
                    name="Impacto associado no PIB (R$)",
                    marker_color="#fb923c",
                    opacity=0.65,
                    yaxis="y2",
                    hovertemplate="Ano: %{x}<br>Impacto PIB: R$ %{y:,.0f}<extra></extra>"
                ))
                fig_series.frames = [
                    go.Frame(
                        data=[
                            go.Scatter(
                                x=mun_story[mun_story["ano"] <= year]["ano"],
                                y=mun_story[mun_story["ano"] <= year]["risk_change"],
                                customdata=mun_story[mun_story["ano"] <= year]["risk_change_label"],
                                mode="lines+markers",
                                line=dict(color="#38bdf8", width=3),
                                hovertemplate="Ano: %{x}<br>Mudança no risco: %{customdata}<extra></extra>"
                            ),
                            go.Bar(
                                x=mun_story[mun_story["ano"] <= year]["ano"],
                                y=mun_story[mun_story["ano"] <= year]["estimated_gdp_risk_impact_brl"],
                                marker_color="#fb923c",
                                opacity=0.65,
                                yaxis="y2",
                                hovertemplate="Ano: %{x}<br>Impacto PIB: R$ %{y:,.0f}<extra></extra>"
                            )
                        ],
                        name=str(year)
                    )
                    for year in story_years
                ]
                fig_series.update_layout(
                    height=335,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=90, r=95, t=6, b=34),
                    font=dict(color="white"),
                    legend=dict(orientation="h", y=1.08, x=0, font=dict(color="white")),
                    xaxis=dict(
                        title="",
                        tickfont=dict(color="white"),
                        showticklabels=True,
                        showline=True,
                        linecolor="white",
                        showgrid=False,
                        ticks="outside",
                        tickcolor="white",
                        range=[
                            (min(story_years) - 0.5) if story_years else 2002.5,
                            (max(story_years) + 0.5) if story_years else 2021.5
                        ],
                        dtick=1
                    ),
                    yaxis=dict(
                        title="Mudança no risco",
                        title_font=dict(color="white"),
                        title_standoff=34,
                        tickfont=dict(color="white"),
                        tickformat=".3f",
                        showticklabels=True,
                        showline=True,
                        linecolor="white",
                        showgrid=False,
                        zeroline=False,
                        ticks="outside",
                        tickcolor="white",
                        automargin=True,
                        range=[risk_min - risk_padding, risk_max + risk_padding]
                    ),
                    yaxis2=dict(
                        title="Impacto PIB (R$)",
                        title_font=dict(color="white"),
                        title_standoff=34,
                        overlaying="y",
                        side="right",
                        tickfont=dict(color="white"),
                        showticklabels=True,
                        showline=True,
                        linecolor="white",
                        showgrid=False,
                        zeroline=False,
                        ticks="outside",
                        tickcolor="white",
                        automargin=True,
                        range=[impact_min - impact_padding, impact_max + impact_padding]
                    )
                )
                animated_plotly_chart(fig_series, height=390, frame_duration=190, transition_duration=90)

                model_col1, model_col2 = st.columns(2)

                with model_col1:
                    st.markdown("""
                    <div style="
                        background-color:#111827;
                        border-left:4px solid #fb923c;
                        border-radius:8px;
                        padding:16px 18px;
                        min-height:185px;
                        color:#e5e7eb;
                        font-size:14px;
                        line-height:1.5;
                    ">
                        <div style="color:white; font-size:16px; font-weight:700; margin-bottom:8px;">
                            Modelo 1: PIB municipal
                        </div>
                        <div style="color:#d1d5db; margin-bottom:10px;">
                            Estima como a mudança no risco climático industrial está associada ao crescimento do PIB real municipal.
                        </div>
                        <div style="font-family:monospace; color:#fbbf24; font-size:13px; line-height:1.45;">
                            Δlog(PIB real)<sub>it</sub> = β·Risco sem PIB<sub>i,t-1</sub><br>
                            + γ·Δlog(VA industrial)<sub>it</sub><br>
                            + FE município + FE ano
                        </div>
                        <div style="color:#9ca3af; margin-top:10px; font-size:12px;">
                            Controle: crescimento do Valor Adicionado Industrial. O risco entra defasado em um ano.
                            <br>
                            Erros-padrão clusterizados por município.
                        </div>
                        <div style="color:#e5e7eb; margin-top:12px; font-size:13px;">
                            <b>Coeficiente do risco:</b> -0.056<br>
                            <b>p-value:</b> 0.035
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with model_col2:
                    st.markdown("""
                    <div style="
                        background-color:#111827;
                        border-left:4px solid #4292c6;
                        border-radius:8px;
                        padding:16px 18px;
                        min-height:185px;
                        color:#e5e7eb;
                        font-size:14px;
                        line-height:1.5;
                    ">
                        <div style="color:white; font-size:16px; font-weight:700; margin-bottom:8px;">
                            Modelo 2: Canal agropecuário
                        </div>
                        <div style="color:#d1d5db; margin-bottom:10px;">
                            Testa se o risco climático aparece primeiro na produção agropecuária, como possível canal de transmissão.
                        </div>
                        <div style="font-family:monospace; color:#93c5fd; font-size:13px; line-height:1.45;">
                            Δlog(VA agro)<sub>it</sub> = β·Risco sem PIB<sub>i,t-1</sub><br>
                            + FE município + FE ano
                        </div>
                        <div style="color:#9ca3af; margin-top:10px; font-size:12px;">
                            Sem controles adicionais, para observar diretamente a associação entre risco climático e crescimento agropecuário.
                            <br>
                            Erros-padrão clusterizados por município.
                        </div>
                        <div style="color:#e5e7eb; margin-top:12px; font-size:13px;">
                            <b>Coeficiente do risco:</b> -0.374<br>
                            <b>p-value:</b> 0.000003
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("""
                <p style="color:#e5e7eb; font-size:15px; line-height:1.55; margin-top:14px;">
                    O Índice de Risco Climático é economicamente relevante. Quando o índice aumenta,
                    o crescimento do PIB municipal no ano seguinte tende a ser menor, e o canal agropecuário
                    aparece como um dos mecanismos de transmissão mais fortes.
                </p>
                """, unsafe_allow_html=True)

# =======================
# RODAPÉ
# =======================
st.markdown("""
<hr style="margin-top:40px; margin-bottom:10px; border:0.5px solid #374151;">

<p style="
    text-align:center;
    color:#6b7280;
    font-size:12px;
">
©© 2026 Climate Risk Index — Rebecca Lorandi Silveira Lara. For research and analytical purposes.
</p>
""", unsafe_allow_html=True)


