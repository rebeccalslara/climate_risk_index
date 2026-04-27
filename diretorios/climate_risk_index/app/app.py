# ============================================
# STREAMLIT DASHBOARD - CLIMATE RISK INDEX SC
# ============================================

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
<div style="width:100vw; height:100px; overflow:hidden; margin-left:-1.5rem;">
    <img src="https://upload.wikimedia.org/wikipedia/commons/b/b2/20181204_Warming_stripes_%28global%2C_WMO%2C_1850-2018%29_-_Climate_Lab_Book_%28Ed_Hawkins%29.svg"
         style="width:100%; height:100%; object-fit:cover;">
</div>
""", unsafe_allow_html=True)
# =========================
# DARK MODE
# =========================

st.markdown("""
<style>

/* FUNDO */
[data-testid="stAppViewContainer"] {
    background-color: #0e1117;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background-color: #101010;
}

[data-testid="stSidebar"] * {
    color: white !important;
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

/* REMOVE FUNDO BRANCO DO PLOTLY */
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

    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    
    return text.upper().strip()

# TABELA ESTILIZADA (CORRIGIDA)
def styled_table(df_input):

    df_input = df_input.sort_values("Valor", ascending=False).reset_index(drop=True)

    norm = mcolors.Normalize(
        vmin=df_input["Valor"].min(),
        vmax=df_input["Valor"].max()
    )

    cmap = cm.get_cmap("OrRd")  # mais vermelho/laranja

    def apply_color(row):
        color = cmap(norm(row["Valor"]))

        # escurece para evitar branco
        darkened = (
            color[0] * 0.85,
            color[1] * 0.65,
            color[2] * 0.5,
            1
        )

        hex_color = mcolors.to_hex(darkened)

        return [f"background-color: {hex_color}; color: white"] * len(row)

    styled = df_input.style.apply(apply_color, axis=1)

    styled = styled.set_table_styles([
        {'selector': 'th.row_heading', 'props': [('display', 'none')]},
        {'selector': '.blank', 'props': [('display', 'none')]}
    ])

    return styled

# =========================
# PATHS (COMPATÍVEL COM STREAMLIT CLOUD)
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent

data_path = BASE_DIR / "outputs" / "climate_risk_index_sc_2025_new.csv"
ranking_path = BASE_DIR / "outputs" / "climate_risk_ranking_sc_2025_new.csv"
shapefile_path = BASE_DIR / "data" / "raw_data" / "shapes" / "SC_Municipios_2025.shp"

# =========================
# LOAD DATA
# =========================

@st.cache_data
def load_data():
    df = pd.read_csv(data_path)
    ranking = pd.read_csv(ranking_path)
    gdf = gpd.read_file(shapefile_path, engine="pyogrio")
    gdf["geometry"] = gdf["geometry"].simplify(0.01)
    return df, ranking, gdf

df, ranking, gdf_map = load_data()

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
df["municipio"] = df["municipio"].apply(normalize_text)

gdf_final = gdf_map.merge(df, on="municipio", how="left")
df["municipio_nome"] = df["municipio"].str.title()

# =========================
# SIDEBAR
# =========================
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

st.title("Índice de Risco Climático Industrial de Santa Catarina")

# =========================
# TABS
# =========================

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "About",
    "Overview",
    "Map",
    "Ranking",
    "Analysis",
    "Economic Insights"
])

# =========================
# ABOUT
# =========================

with tab0:
    st.header("Sobre o Modelo")
    titulo_h2("Metodologia")
    st.markdown("""

Este projeto apresenta uma **adaptação do índice de risco climático do IPCC (AR5)** para o contexto industrial dos municípios de Santa Catarina. O modelo segue o framework conceitual amplamente utilizado na literatura de risco climático, no qual o risco é definido como a interação entre três dimensões fundamentais:
""")

    st.markdown("""
<div style="text-align:center; margin:20px 0;">
    <span style="font-size:20px; font-weight:500; color:white;">
        Risk = Hazard × Exposure × Vulnerability
    </span>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
Essa formulação, adotada por organismos internacionais como o IPCC e o UNDRR, entende o risco como um fenômeno sistêmico, resultante da combinação entre condições climáticas adversas, a exposição de ativos econômicos e a vulnerabilidade estrutural dos sistemas analisados. A formulação multiplicativa implica que a ausência ou baixa intensidade de qualquer componente reduz significativamente o risco total, evitando compensações indevidas entre fatores.

Neste trabalho, o modelo foi adaptado para capturar especificamente o **risco climático sobre a estrutura produtiva industrial municipal**, incorporando variáveis que refletem a dinâmica regional.

> O índice resultante representa o **nível relativo de risco climático associado à atividade industrial municipal**. Valores variam entre 0 e 1, sendo que os mais elevados indicam maior suscetibilidade a impactos econômicos decorrentes de choques climáticos.

""")
    
    titulo_h2("Construção dos índices")
    titulo_h3("Hazard (Perigo climático)")
    st.markdown("""

O índice de hazard foi construído a partir de variáveis climáticas que capturam tanto a variabilidade quanto a ocorrência de extremos, incluindo déficit hídrico médio (`def_mean`), variabilidade da precipitação (`ppt_std`), variabilidade da velocidade do vento (`ws_std`) e amplitude térmica diária (`dtr_mean`).

A agregação combina a média dessas variáveis, representando as condições climáticas estruturais, com o valor máximo, de modo a incorporar eventos extremos. Essa abordagem está alinhada com a literatura climática, que destaca o papel desproporcional de eventos extremos na geração de danos econômicos, especialmente em sistemas industriais sensíveis a choques abruptos.
    """)

    titulo_h3("Exposure (Exposição)")
    st.markdown("""

O índice de exposição mensura o grau em que a atividade econômica municipal está sujeita a riscos climáticos, utilizando indicadores per capita de empregos industriais (`empregos_pc`) e número de empresas (`empresas_pc`).

A utilização de métricas per capita e sua agregação por média simples permitem capturar a **intensidade relativa da atividade industrial exposta**, garantindo comparabilidade entre municípios com diferentes escalas populacionais.
""")
    
    titulo_h3("Vulnerability (Vulnerabilidade)")
    st.markdown("""

A vulnerabilidade reflete a sensibilidade climática e energética e a capacidade adaptativa da renda, sendo composta por três dimensões principais: intensidade energética industrial per capita (`energia_norm`), valor da produção agrícola per capita (`agro_pc_norm`) e renda per capita (`pib_pc_inv`).

Esse conjunto de variáveis captura a sensibilidade dos municípios a choques energéticos e climaticos do setor agrícola, bem como sua capacidade adaptativa, aproximada pela renda disponível para resposta e reconstrução. A agregação foi realizada por meio de média simples, assumindo contribuição equilibrada entre os fatores estruturais.

""")
    
    
    col1, col2 = st.columns([1, 1])
    with col1: 
        st.markdown("""
        <div style="
            font-size:13px; 
            line-height:1.6;
        "> 
        ---
                    
        #### Nota sobre os dados

        Os dados utilizados são provenientes de bases oficiais e amplamente reconhecidas, incluindo TerraClimate (variáveis climáticas), SIDRA/IBGE (indicadores econômicos), RAIS (estrutura produtiva) e CELESC (dados energéticos).

        Todas as variáveis foram previamente tratadas, normalizadas e harmonizadas ao nível municipal, assegurando consistência e comparabilidade entre as unidades de análise.

        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
         <div style="
            color:#GREY; 
            font-size:13px; 
            line-height:1.6;
        "> 
        ---
                        
        #### Considerações finais

        O índice proposto constitui uma ferramenta analítica para a identificação de **hotspots de risco climático industrial em Santa Catarina**, podendo subsidiar a formulação de políticas públicas, estratégias de adaptação e análises econômicas regionais sob a perspectiva das mudanças climáticas.

        Trata-se de uma medida relativa, adaptada ao contexto regional, que mantém aderência ao arcabouço conceitual do IPCC.
        """, unsafe_allow_html=True)
    
# =========================
# OVERVIEW
# =========================

with tab1:

    # =========================
    # DISTRIBUIÇÃO DO RISCO
    # =========================

    st.markdown("### Distribuição do Risco Climático")
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
            "Índice de Risco Climático (faixa): %{x}<br>" +
            "Municípios: %{y}<extra></extra>"
        )

        fig_dist.update_layout(
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            font=dict(color="white"),
            xaxis=dict(
                title="Índice de Risco Climático",
                title_font=dict(color="white"),
                tickfont=dict(color="white")
            ),
            yaxis=dict(
                title="Número de Municípios",
                title_font=dict(color="white"),
                tickfont=dict(color="white")
            )
        )

        st.plotly_chart(fig_dist, use_container_width=True)

        # =========================
        # MÉTRICAS ESTATÍSTICAS
        # =========================

        col1, col2, col3 = st.columns(3)

        col1.metric("Média", round(df["risk_norm"].mean(), 3))
        col2.metric("Desvio Padrão", round(df["risk_norm"].std(), 3))
        col3.metric("Assimetria", round(df["risk_norm"].skew(), 3))

        # =========================
        # INTERPRETAÇÃO
        # =========================

        mean = df["risk_norm"].mean()
        std = df["risk_norm"].std()
        skew = df["risk_norm"].skew()
    
        # interpretação da assimetria
        if skew > 0.5:
            skew_text = "assimetria positiva, indicando concentração de municípios em níveis mais baixos de risco, com poucos municípios apresentando valores elevados"
        elif skew < -0.5:
            skew_text = "assimetria negativa, sugerindo concentração em níveis mais altos de risco"
        else:
            skew_text = "distribuição aproximadamente simétrica"

        # interpretação da dispersão
        if std > 0.15:
            disp_text = "elevada heterogeneidade entre os municípios"
        else:
            disp_text = "baixa dispersão, indicando relativa homogeneidade entre os municípios"
    
    with col_text:
        st.markdown(f"""
        <div style="
            background-color:#111827;
            padding:20px;
            border-radius:10px;
            margin-top:20px;
            color:#9ca3af; 
            margin-bottom:8px;
        ">
        <div style="
            color: #4292c6;
            font-size:16px;
            font-weight:600;
            margin-bottom:10px;
        ">
            Interpretação Analítica
        
        <div style="
            color:#white; 
            font-size:14px; 
            line-height:1.6;
        "> 
                             
        A distribuição do risco climático industrial em Santa Catarina apresenta <b>{skew_text}</b>, 

        Observa-se também <b>{disp_text}</b>. Dada a natureza multiplicativa do índice, esse resultado deve ser interpretado com cautela: 
        baixa dispersão pode refletir não apenas homogeneidade, mas também a presença de dimensões sistematicamente reduzidas,
        especialmente baixa exposição industrial, que comprimem o risco agregado.

        Esse padrão reforça a necessidade de abordagens territoriais diferenciadas, 
        uma vez que políticas uniformes tendem a ser menos eficazes em contextos heterogêneos.
        
        """, unsafe_allow_html=True)
    
    # =========================
    # MISMATCH INDEX
    # =========================
    
    st.markdown(" ### Estrutura do Risco (Mismatch)")

    # Cálculo do mismatch (desvio padrão entre os 3 subíndices)
    df["mismatch_std"] = df[[
        "hazard_index",
        "exposure_index_pc",
        "vulnerability_index"
    ]].std(axis=1)

    # Threshold (top 25% mais desbalanceados)
    threshold = df["mismatch_std"].quantile(0.75)

    # Share de municípios com alto mismatch
    high_mismatch_share = (df["mismatch_std"] > threshold).mean()

    # =========================
    # VISUALIZAÇÃO
    # =========================

    col_chart, col_text = st.columns([1.2, 1])

    #  GRÁFICO 
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
            "Municípios: %{y}<extra></extra>",
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
                title="Número de Municípios",
                title_font=dict(color="white"),
                tickfont=dict(color="white")
            )
        )

        st.plotly_chart(fig_mismatch, use_container_width=True)
        
        st.metric(
            "% Municípios com Alto Mismatch",
            f"{high_mismatch_share*100:.1f}%"
        )

    # TEXTO 
    with col_text:

        st.markdown(f"""
        <div style="
            background-color:#111827;
            padding:20px;
            border-radius:10px;
            margin-top:15px;
        ">

        <div style="
            color:#4292c6;
            font-size:16px;
            font-weight:600;
            margin-bottom:10px;
        ">
            Estrutura do Risco

        <div style="
            color:#9ca3af;
            font-size:14px;
            line-height:1.6;
        ">

        O indicador de mismatch captura o desbalanceamento entre hazard, exposure e vulnerability.

        Cerca de <b>{high_mismatch_share*100:.1f}%</b> dos municípios apresentam forte desbalanceamento entre essas dimensões, com uma elevada e outra muito reduzida.

        Devido à estrutura multiplicativa do índice, isso tende a comprimir o risco climático industrial, mesmo na presença de pressões relevantes.

        Isso sugere a existência de **risco climático latente**, especialmente em contextos de baixa exposição industrial.

        """, unsafe_allow_html=True)



# =========================
# MAPA
# =========================

with tab2:

    fig = px.choropleth(
    gdf_final,
    geojson=gdf_final.geometry,
    locations=gdf_final.index,
    color="risk_norm",
    color_continuous_scale="Reds",
    hover_name="municipio",
    labels={"risk_norm": "Índice de Risco Climático"}  
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
        margin=dict(l=0, r=0, t=0, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

# =========================
# RANKING
# =========================

with tab3:

    st.header("Ranking")

    # ORDENAÇÃO
    top10 = ranking.sort_values("risk_norm", ascending=False).head(10)
    bottom10 = ranking.sort_values("risk_norm", ascending=True).head(10)

    col1, col2 = st.columns(2)

    # =========================
    # MAIOR RISCO
    # =========================
    with col1:
        st.subheader("Municipios de Maior Risco")

        fig_top = px.bar(
            top10.sort_values("risk_norm", ascending=True),  
            x="risk_norm",
            y="municipio",
            orientation="h",
            color="risk_norm",
            color_continuous_scale="OrRd", 
            labels={"risk_norm": "Índice de Risco Climático"}
        )

        fig_top.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_showscale=False,

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

    # =========================
    # MENOR RISCO
    # =========================
    with col2:
        st.subheader("Municipios de Menor Risco")

        fig_bot = px.bar(
            bottom10.sort_values("risk_norm", ascending=True),
            x="risk_norm",
            y="municipio",
            orientation="h",
            color="risk_norm",
            color_continuous_scale="Blues", 
            labels={"risk_norm": "Índice de Risco Climático"}
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
            coloraxis_showscale=False,

            font=dict(color="white"),

            xaxis=dict(
                title_font=dict(color="white"),
                tickfont=dict(color="white")
                )
        )

        st.plotly_chart(fig_bot, use_container_width=True)

    # =========================
    # TEXTO EXPLICATIVO
    # =========================
    st.markdown("""
    ### Interpretação dos Dados

    Municípios de maior risco combinam níveis elevados de hazard climático, alta exposição da atividade industrial e maior vulnerabilidade estrutural.
    Já municípios de menor risco apresentam menor suscetibilidade a impactos climáticos, seja por menor exposição, melhores condições estruturais ou menor intensidade de eventos climáticos. Como o índice de risco é construído de forma multiplicativa, valores próximos de zero em qualquer uma das dimensões reduzem significativamente o risco total. Esse comportamento é observado nos resultados.

    > Um exemplo ilustrativo é o município de **Ouro Verde**, embora apresente níveis relevantes de *Hazard* e *Vulnerability*, sua *Exposure* é praticamente nula, resultando em um risco climático total muito baixo. Esse resultado é consistente com a proposta do índice. Como se trata de um **indicador de risco climático industrial**, municípios com estrutura produtiva industrial reduzida tendem a apresentar baixo risco, independentemente das condições climáticas locais. Em outras palavras, na ausência de ativos econômicos expostos, o impacto potencial de choques climáticos sobre a atividade industrial é limitado.

    A análise comparativa permite identificar **hotspots de risco** e regiões com maior resiliência relativa, auxiliando na formulação de políticas públicas e estratégias de adaptação climática.
    """)
# =========================
# ANALYSIS
# =========================

def gerar_texto_insight(df, df_mun):

    # =========================
    # VARIÁVEIS BASE
    # =========================
    risk = df_mun["risk_norm"].values[0]
    hazard = df_mun["hazard_index"].values[0]
    exposure = df_mun["exposure_index_pc"].values[0]
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
            "déficit hídrico": df_mun["def_mean"].values[0],
            "variabilidade da precipitação": df_mun["ppt_std"].values[0],
            "variabilidade do vento": df_mun["ws_std"].values[0],
            "amplitude térmica": df_mun["dtr_mean"].values[0]
        }

    elif main_driver == "Exposure":
        vars_dict = {
            "empregos industriais per capita": df_mun["empregos_pc"].values[0],
            "empresas industriais per capita": df_mun["empresas_pc"].values[0]
        }

    else:
        vars_dict = {
            "intensidade energética": df_mun["energia_norm"].values[0],
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
                "déficit hídrico": df_mun["def_mean"].values[0],
                "variabilidade da precipitação": df_mun["ppt_std"].values[0],
                "variabilidade do vento": df_mun["ws_std"].values[0],
                "amplitude térmica": df_mun["dtr_mean"].values[0]
            }
        else:
            second_vars = {
                "intensidade energética": df_mun["energia_norm"].values[0],
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
(índice = {risk:.2f}), situando-se {pos_text}.

A decomposição do índice indica que o principal fator de risco é **{main_driver}**, 
com destaque para **{main_variable}** como principal componente explicativo dentro dessa dimensão.

{politica_texto}

{anulacao_texto}
"""

    return texto

with tab4:

    # =========================
    # CASO 1 — TODOS
    # =========================
    if municipio_selecionado == "Todos" and modo_analise == "Individual":
        st.header("Análise por Município")
        st.markdown(
            '<p style="color:#9ca3af; font-size:13px; font-style:italic;">Selecione um município na barra lateral para visualizar a análise detalhada.</p>',
            unsafe_allow_html=True
        )

    # =========================
    # CASO 3 — COMPARAÇÃO
    # =========================
    elif modo_analise == "Comparação":

        if municipio_selecionado == municipio_2:
            st.warning("Selecione dois municípios diferentes para comparação.")
        
        else:
            df_mun1 = df[df["municipio_nome"] == municipio_selecionado]
            df_mun2 = df[df["municipio_nome"] == municipio_2]

            colA, colB = st.columns(2)

            # =========================
            # FUNÇÃO REUTILIZÁVEL
            # =========================
            def render_municipio(df_mun, nome):

                st.markdown(f"### {nome}")

                risk = df_mun["risk_norm"].values[0]
                hazard = df_mun["hazard_index"].values[0]
                exposure = df_mun["exposure_index_pc"].values[0]
                vulnerability = df_mun["vulnerability_index"].values[0]

                st.metric("Risk", round(risk,3))

                c1, c2, c3 = st.columns(3)
                c1.metric("Hazard", round(hazard,3))
                c2.metric("Exposure", round(exposure,3))
                c3.metric("Vulnerability", round(vulnerability,3))

                fig = go.Figure()

                fig.add_trace(go.Scatterpolar(
                    r=[hazard, exposure, vulnerability],
                    theta=["Hazard","Exposure","Vulnerability"],
                    fill='toself',
                    fillcolor='rgba(251,146,60,0.4)',
                    line=dict(color='#fb923c')
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

            # Renderiza lado a lado
            with colA:
                render_municipio(df_mun1, municipio_selecionado)

            with colB:
                render_municipio(df_mun2, municipio_2)

    # =========================
    # CASO 2 — INDIVIDUAL
    # =========================

    else:
        st.header(f"Análise por Município — {municipio_selecionado}")
        df_mun = df[df["municipio_nome"] == municipio_selecionado]

        if not df_mun.empty:

            st.metric("Risk", round(df_mun["risk_norm"].values[0],3))

            col1, col2, col3 = st.columns(3)

            hazard = df_mun["hazard_index"].values[0]
            exposure = df_mun["exposure_index_pc"].values[0]
            vulnerability = df_mun["vulnerability_index"].values[0]

            col1.metric("Hazard", round(hazard,3))
            col2.metric("Exposure", round(exposure,3))
            col3.metric("Vulnerability", round(vulnerability,3))

            st.markdown("### Decomposição dos Subíndices")

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
                        df_mun["def_mean"].values[0],
                        df_mun["ppt_std"].values[0],
                        df_mun["ws_std"].values[0],
                        df_mun["dtr_mean"].values[0]
                        ]
                })

                st.table(styled_table(hazard_df))
            
            with sub2:
                st.markdown("**Exposure**")

                exposure_df = pd.DataFrame({
                    "Variáveis": [
                        "Empregos Industriais per capita",
                        "Empresas Industriais per capita"
                        ],
                    "Valor": [
                        df_mun["empregos_pc"].values[0],
                        df_mun["empresas_pc"].values[0]
                        ]
                })

                st.table(styled_table(exposure_df))

            with sub3:
                st.markdown("**Vulnerability**")

                vuln_df = pd.DataFrame({
                    "Variáveis": [
                        "Intensidade Energética",
                        "Sensibilidade da Produção Agrícola",
                        "Resiliência da Renda"
                    ],
                    "Valor": [
                        df_mun["energia_norm"].values[0],
                        df_mun["agro_pc_norm"].values[0],
                        df_mun["pib_pc_inv"].values[0]
                    ]
                })

                st.table(styled_table(vuln_df))

            st.markdown("### Estrutura do Risco")

            col_chart, col_text = st.columns([1.2, 1])

            with col_chart:

                fig = go.Figure()

                fig.add_trace(go.Scatterpolar(
                    r=[hazard, exposure, vulnerability],
                    theta=["Hazard","Exposure","Vulnerability"],
                    fill='toself',
                    fillcolor='rgba(251,146,60,0.4)',
                    line=dict(color='#fb923c')
                ))

                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="white"),
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0,1],
                            tickfont=dict(color="#9ca3af")  # cinza
                        )
                    )
                )

                st.plotly_chart(fig, use_container_width=True)

            with col_text:

                texto = gerar_texto_insight(df, df_mun)

                # =========================
                # BOX VISUAL
                # =========================
                st.markdown(f"""
                <div style="
                    background-color:#111827;
                    padding:20px;
                    border-radius:10px;
                    border-left:4px solid #fb923c;
                    margin-top:25px;
                    color:#9ca3af;
                    font-size:15px;
                    margin-bottom:8px;
                    font-weight:500;
                    color:#e5e7eb;
                    line-height:1.5;
                    margin:0;
                    ">
                        {texto}

                """, unsafe_allow_html=True)

# ECONOMIC INSIGHTS
# =========================

with tab5:

    st.header("Insights Econômicos")

    st.markdown("### Correlação entre Subíndices")

    col1, col2 = st.columns([1.2, 1])

    with col1:

        # =========================
        # CORRELAÇÃO — SUBÍNDICES
        # =========================
        corr_sub = df[[
            "hazard_index",
            "exposure_index_pc",
            "vulnerability_index",
        ]].corr()

        labels_sub = {
        "hazard_index": "Hazard",
        "exposure_index_pc": "Exposure",
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
            "%{y} × %{x}<br>" +
            "Correlação: %{z:.2f}<extra></extra>"
        )

        fig_corr.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"),
            margin=dict(l=0, r=0, t=30, b=0),
            height=350,
            xaxis=dict( tickfont=dict(color="white")),
            yaxis=dict( tickfont=dict(color="white"))
        )

        st.plotly_chart(fig_corr, use_container_width=True)

    with col2:
        # =========================
        # TEXTO INTERPRETATIVO
        # =========================

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

        A maior correlação positiva ocorre entre <b>{max_pos[0]}</b> e <b>{max_pos[1]}</b> 
        (correlação = {val_pos:.2f}), indicando que essas dimensões tendem a se elevar conjuntamente entre os municípios, refletindo possíveis padrões estruturais compartilhados.

        Por outro lado, observa-se uma relação inversa mais intensa entre <b>{max_neg[0]}</b> e <b>{max_neg[1]}</b> 
        (correlação = {val_neg:.2f}), sugerindo que municípios com maior intensidade em uma dessas dimensões 
        tendem a apresentar níveis mais baixos na outra.

        Do ponto de vista analítico, essa relação não implica causalidade direta, 
        mas sugere que esses componentes podem estar associados a características econômicas ou territoriais comuns.


        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### Correlação entre Variáveis Estruturais")
    col1, col2 = st.columns([1.2, 1])
    with col1:
        # =========================
        # CORRELAÇÃO — VARIÁVEIS INTERNAS
        # =========================

        vars_cols = [
            # Hazard
            "def_mean", "ppt_std", "ws_std", "dtr_mean",
            # Exposure
            "empregos_pc", "empresas_pc",
            # Vulnerability
            "energia_norm", "agro_pc_norm", "pib_pc_inv"
        ]

        corr_vars = df[vars_cols].corr()

        # Labels amigáveis
        labels_vars = {
            "def_mean": "Déficit hídrico",
            "ppt_std": "Variabilidade da precipitação",
            "ws_std": "Variabilidade do vento",
            "dtr_mean": "Amplitude térmica",
            "empregos_pc": "Empregos industriais per capita",
            "empresas_pc": "Empresas industriais per capita",
            "energia_norm": "Intensidade energética",
            "agro_pc_norm": "Sensibilidade da produção agrícola",
            "pib_pc_inv": "Resiliência da renda"
        }

        corr_vars = corr_vars.rename(index=labels_vars, columns=labels_vars)

        fig_corr2 = px.imshow(
            corr_vars,
            text_auto=False,
            aspect="auto"
        )
        fig_corr2.update_traces(
            hovertemplate=
            "%{y} × %{x}<br>" +
            "Correlação: %{z:.2f}<extra></extra>"
        )

        fig_corr2.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"),
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(tickfont=dict(color="white")),
            yaxis=dict(tickfont=dict(color="white"))
        )

        st.plotly_chart(fig_corr2, use_container_width=True)
   
    with col2:
        # =========================
        # INSIGHT AVANÇADO
        # =========================
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

        A estrutura de correlação evidencia como os determinantes do risco interagem entre si.  

        Relações mais fortes sugerem maior associação entre fatores climáticos e econômicos, 
        enquanto correlações mais baixas indicam maior autonomia entre as dimensões.

        Do ponto de vista analítico, isso reforça a necessidade de abordagens multidimensionais 
        na avaliação do risco climático industrial.

        </div>
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