import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Sociodemográfico - SETRABES/CAS", layout="wide")

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

# 2. CARREGAMENTO E CONTAGEM BRUTA (COLUNA T)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO = os.path.join(BASE_DIR, "Planilha Matriculados.xlsx")

@st.cache_data
def carregar_dados_reais(caminho):
    if not os.path.exists(caminho): return None
    try:
        # Tenta ler como Excel (XLSX) ou CSV conforme o arquivo disponível
        if caminho.endswith('.csv'):
            df = pd.read_csv(caminho, dtype=str)
        else:
            df = pd.read_excel(caminho, dtype=str)
    except:
        return None

    # Limpeza apenas dos nomes das colunas
    df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    return df

df = carregar_dados_reais(CAMINHO)

if df is not None:
    col_resp = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_nacionalidade = "NACIONALIDADE:"
    col_est_civil = "ESTADO CIVIL:"
    col_trampo = "EXERCE ATIVIDADE REMUNERADA:"

    # --- LÓGICA DE CONTAGEM SOLICITADA ---
    # Consideramos 'Responsável' qualquer linha onde a Coluna T não esteja vazia
    df_responsaveis = df[df[col_resp].notna() & (df[col_resp].str.strip() != "")].copy()
    
    total_familias = len(df_responsaveis)
    total_pessoas = len(df)

    # --- INDICADORES DE TOPO ---
    st.write("### 📊 Contagem Real por Linha Preenchida (Coluna T)")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="metric-container"><h4>👨‍👩‍👧‍👦 Total de Famílias (Linhas na Coluna T)</h4><h2 style="font-size: 48px;">{total_familias}</h2></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-container"><h4>📝 Total Geral de Matriculados</h4><h2 style="font-size: 48px;">{total_pessoas}</h2></div>', unsafe_allow_html=True)

    st.write("---")

    # --- BARRA LATERAL: FILTROS ---
    st.sidebar.header("⚖️ Filtros de Prioridade")
    rank_map = {"SEM RENDA": 0, "ATÉ R$ 405,26": 1, "DE R$ 405,26 A R$ 810,50": 2, "DE R$ 810,50 A R$ 1.215,76": 3}
    
    f_renda = st.sidebar.selectbox("Renda Familiar:", ["Todos"] + list(rank_map.keys()))
    
    # Filtragem baseada na lista de responsáveis
    df_lista = df_responsaveis.copy()
    if f_renda != "Todos":
        df_lista = df_lista[df_lista[col_renda] == f_renda]
    
    # Ordenar por vulnerabilidade para facilitar a triagem
    df_lista['rank'] = df_lista[col_renda].map(lambda x: rank_map.get(str(x).upper(), 99))
    lista_nomes = df_lista.sort_values(by=['rank', col_resp])[col_resp].unique().tolist()
    
    selecionado = st.sidebar.selectbox("👤 Buscar Responsável:", ["Selecione..."] + lista_nomes)

    # --- PAINEL PRINCIPAL ---
    if selecionado != "Selecione...":
        # Aqui pegamos os dados da família desse responsável específico
        dados_familia = df[df[col_resp] == selecionado]
        # Pegamos a primeira ocorrência para os cards
        chefe = dados_familia.iloc[0]

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown(f"""<div class="card-leitura"><div class="titulo-card">📍 Localização</div>
                <p class="texto-preto"><b>Endereço:</b> {chefe.get('ENDEREÇO COMPLETO:', 'N/A')}</p>
                <p class="texto-preto"><b>Bairro:</b> {chefe.get('BAIRRO:', 'N/A')}</p>
                <p class="texto-preto"><b>Nacionalidade:</b> {chefe.get(col_nacionalidade, 'N/A')}</p></div>""", unsafe_allow_html=True)
        with col_r2:
            st.markdown(f"""<div class="card-leitura"><div class="titulo-card">💰 Perfil Econômico</div>
                <p class="texto-preto"><b>Renda:</b> {chefe.get(col_renda, 'N/A')}</p>
                <p class="texto-preto"><b>Trabalha:</b> {chefe.get(col_trampo, 'N/A')}</p>
                <p class="texto-preto"><b>Estado Civil:</b> {chefe.get(col_est_civil, 'N/A')}</p></div>""", unsafe_allow_html=True)

        # EXPANSÃO TOTAL DAS 56 COLUNAS
        with st.expander("📂 CLIQUE AQUI PARA VER TODOS OS 56 CAMPOS DA TABELA (EXPANSÃO TOTAL)", expanded=False):
            st.dataframe(dados_familia, use_container_width=True)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                dados_familia.to_excel(writer, index=False)
            st.download_button(f"📥 Baixar Dados - {selecionado}", output.getvalue(), f"{selecionado}.xlsx")

    # --- GRÁFICOS (BASEADOS NA CONTAGEM POR LINHA DA COLUNA T) ---
    st.write("###")
    st.divider()
    st.markdown(f"## 📊 Diagnóstico Estratégico das {total_familias} Famílias")

    

    g1, g2 = st.columns(2)
    with g1:
        fig1 = px.bar(df_responsaveis['GÊNERO:'].value_counts().reset_index(), x='GÊNERO:', y='count', text='count', 
                     title="Gênero (Responsáveis)", color_discrete_sequence=['#1e3a8a'])
        fig1.update_traces(textposition='outside')
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        fig2 = px.bar(df_responsaveis[col_renda].value_counts().reset_index(), x=col_renda, y='count', text='count', 
                     title="Renda Familiar", color_discrete_sequence=['#be123c'])
        fig2.update_traces(textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)

    g3, g4 = st.columns(2)
    with g3:
        fig3 = px.bar(df_responsaveis[col_nacionalidade].value_counts().reset_index(), x=col_nacionalidade, y='count', text='count', 
                     title="Nacionalidade", color_discrete_sequence=['#f59e0b'])
        fig3.update_traces(textposition='outside')
        st.plotly_chart(fig3, use_container_width=True)
    with g4:
        fig4 = px.bar(df_responsaveis[col_est_civil].value_counts().reset_index(), x=col_est_civil, y='count', text='count', 
                     title="Estado Civil", color_discrete_sequence=['#10b981'])
        fig4.update_traces(textposition='outside')
        st.plotly_chart(fig4, use_container_width=True)

else:
    st.error("⚠️ Planilha não detectada ou erro no carregamento.")
