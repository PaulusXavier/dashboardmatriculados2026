import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dashboard CAS - SETRABES", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .card-leitura {
        background-color: #f1f5f9;
        padding: 22px;
        border-radius: 12px;
        border: 2px solid #1e3a8a;
        margin-bottom: 15px;
    }
    .texto-preto { color: #000000 !important; font-size: 16px; font-weight: 600; }
    .titulo-card { color: #1e3a8a !important; font-weight: bold; font-size: 19px; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; }
    .metric-container {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white; padding: 25px; border-radius: 15px; text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO E FILTRAGEM RIGOROSA PELA COLUNA T
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO = os.path.join(BASE_DIR, "Planilha Matriculados.xlsx - Planilha1.csv")

@st.cache_data
def carregar_dados_robustos(caminho):
    if not os.path.exists(caminho): return None
    # Lendo como CSV conforme o arquivo que você disponibilizou
    df = pd.read_csv(caminho, dtype=str)
    
    # Limpa nomes de colunas (remove espaços e quebras de linha)
    df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    
    # --- REGRA DE OURO SOLICITADA ---
    col_t = "NOME DO RESPONSÁVEL:"
    
    # Criamos a base estatística: APENAS linhas onde a Coluna T não é nula e não é vazia
    # Não usamos 'drop_duplicates' aqui para não sumir ninguém com nome igual
    df_base_estatistica = df[df[col_t].notna() & (df[col_t].str.strip() != "")].copy()
    
    return df, df_base_estatistica

df_geral, df_estatistico = carregar_dados_robustos(CAMINHO)

if df_geral is not None:
    # Mapeamento de colunas baseado na sua planilha
    col_t = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_nacionalidade = "NACIONALIDADE:"
    col_est_civil = "ESTADO CIVIL:"
    col_genero = "GÊNERO:" # Vamos usar o gênero que está na linha do responsável
    
    total_responsaveis = len(df_estatistico)
    total_geral = len(df_geral)

    # --- INDICADORES DE TOPO ---
    st.write("### 📊 Consolidação de Dados CAS")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="metric-container"><h4>👨‍👩‍👧‍👦 Total de Responsáveis (Coluna T)</h4><h2 style="font-size: 50px;">{total_responsaveis}</h2></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-container"><h4>📝 Total de Registros na Planilha</h4><h2 style="font-size: 50px;">{total_geral}</h2></div>', unsafe_allow_html=True)

    st.write("---")

    # --- BARRA LATERAL: BUSCA ---
    st.sidebar.header("🔍 Localizar Responsável")
    # Lista para busca (mantemos unique apenas no seletor para não repetir o nome na lista de clique)
    nomes_busca = sorted(df_estatistico[col_t].unique().tolist())
    selecionado = st.sidebar.selectbox("Selecione o Nome:", ["Selecione..."] + nomes_busca)

    # --- PAINEL DE CONSULTA ---
    if selecionado != "Selecione...":
        # Filtra todas as linhas relacionadas a esse nome para mostrar a família
        dados_familia = df_geral[df_geral[col_t] == selecionado]
        # Pega a linha principal (do responsável) para os cards
        info_principal = df_estatistico[df_estatistico[col_t] == selecionado].iloc[0]

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""<div class="card-leitura"><div class="titulo-card">🏠 Dados de Identificação</div>
                <p class="texto-preto"><b>Nome:</b> {selecionado}</p>
                <p class="texto-preto"><b>Bairro:</b> {info_principal.get('BAIRRO:', 'N/A')}</p>
                <p class="texto-preto"><b>Nacionalidade:</b> {info_principal.get(col_nacionalidade, 'N/A')}</p></div>""", unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""<div class="card-leitura"><div class="titulo-card">💰 Perfil Socioeconômico</div>
                <p class="texto-preto"><b>Renda:</b> {info_principal.get(col_renda, 'N/A')}</p>
                <p class="texto-preto"><b>Estado Civil:</b> {info_principal.get(col_est_civil, 'N/A')}</p>
                <p class="texto-preto"><b>Trabalha:</b> {info_principal.get('EXERCE ATIVIDADE REMUNERADA:', 'N/A')}</p></div>""", unsafe_allow_html=True)

        with st.expander("📂 CLIQUE AQUI PARA EXPANSÃO TOTAL (56 COLUNAS)", expanded=False):
            st.dataframe(dados_familia, use_container_width=True)

    # --- SEÇÃO DE GRÁFICOS ROBUSTOS ---
    st.write("###")
    st.divider()
    st.markdown(f"## 📊 Estatísticas Baseadas em {total_responsaveis} Responsáveis")
    st.info("Regra aplicada: Somente linhas com a Coluna T preenchida são contabilizadas abaixo.")

    

    # Criando os gráficos com a base filtrada
    g1, g2 = st.columns(2)
    with g1:
        # Gênero
        df_gen = df_estatistico[col_genero].value_counts().reset_index()
        fig1 = px.bar(df_gen, x=col_genero, y='count', text='count', title="Gênero do Responsável", color_discrete_sequence=['#1e3a8a'])
        fig1.update_traces(textposition='outside')
        st.plotly_chart(fig1, use_container_width=True)
        
    with g2:
        # Renda
        df_ren = df_estatistico[col_renda].value_counts().reset_index()
        fig2 = px.bar(df_ren, x=col_renda, y='count', text='count', title="Renda Familiar Total", color_discrete_sequence=['#be123c'])
        fig2.update_traces(textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)

    g3, g4 = st.columns(2)
    with g3:
        # Nacionalidade
        df_nac = df_estatistico[col_nacionalidade].value_counts().reset_index()
        fig3 = px.bar(df_nac, x=col_nacionalidade, y='count', text='count', title="Nacionalidade das Famílias", color_discrete_sequence=['#f59e0b'])
        fig3.update_traces(textposition='outside')
        st.plotly_chart(fig3, use_container_width=True)
        
    with g4:
        # Estado Civil
        df_civ = df_estatistico[col_est_civil].value_counts().reset_index()
        fig4 = px.bar(df_civ, x=col_est_civil, y='count', text='count', title="Estado Civil", color_discrete_sequence=['#10b981'])
        fig4.update_traces(textposition='outside')
        st.plotly_chart(fig4, use_container_width=True)

else:
    st.error("Erro ao carregar o arquivo. Verifique se o nome está correto.")
