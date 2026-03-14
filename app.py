import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Sociodemográfico - CAS/SETRABES", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    /* Cards com alto contraste: Fundo claro, borda azul, letra preta */
    .card-leitura {
        background-color: #f1f5f9;
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #1e3a8a;
        margin-bottom: 15px;
    }
    .texto-preto { color: #000000 !important; font-size: 16px; font-weight: 500; margin-bottom: 8px; }
    .titulo-card { color: #1e3a8a !important; font-weight: bold; font-size: 18px; margin-bottom: 12px; border-bottom: 2px solid #cbd5e1; }
    
    /* Indicadores de Topo */
    .metric-container {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white; padding: 20px; border-radius: 15px; text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO DOS DADOS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# O Streamlit Cloud geralmente converte Excel para CSV internamente ou lê o XLSX se as libs estiverem no requirements
CAMINHO = os.path.join(BASE_DIR, "Planilha Matriculados.xlsx")

@st.cache_data
def carregar_dados(caminho):
    if not os.path.exists(caminho): return None
    # Tenta ler Excel, se falhar tenta CSV (ajuste comum em servidores)
    try:
        df = pd.read_excel(caminho, dtype=str)
    except:
        df = pd.read_csv(caminho, dtype=str)
    
    df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    return df

df = carregar_dados(CAMINHO)

if df is not None:
    # MAPEAMENTO EXATO SEGUNDO SUA PLANILHA
    col_resp = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trampo = "EXERCE ATIVIDADE REMUNERADA:"
    col_moradia = "SITUAÇÃO DA MORADIA:"
    col_benef = "A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:"
    col_nacionalidade = "NACIONALIDADE:"
    col_est_civil = "ESTADO CIVIL:"
    col_qual_benef = "INFORMA O(S) PROGRAMA(S):"
    
    # Base Única de Responsáveis para Gráficos Precisos
    df_unicos = df.drop_duplicates(subset=[col_resp]).copy()

    # --- INDICADORES DE TOPO ---
    st.write("### 📊 Estatísticas de Gestão CAS")
    c_meta1, c_meta2 = st.columns(2)
    with c_meta1:
        st.markdown(f'<div class="metric-container"><h4>👨‍👩‍👧‍👦 Total de Famílias (Responsáveis)</h4><h2 style="font-size: 45px;">{len(df_unicos)}</h2></div>', unsafe_allow_html=True)
    with c_meta2:
        st.markdown(f'<div class="metric-container"><h4>📝 Total de Pessoas Matriculadas</h4><h2 style="font-size: 45px;">{len(df)}</h2></div>', unsafe_allow_html=True)

    st.write("---")

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Critérios de Triagem")
    rank_map = {"SEM RENDA": 0, "ATÉ R$ 405,26": 1, "DE R$ 405,26 A R$ 810,50": 2, "DE R$ 810,50 A R$ 1.215,76": 3}
    
    f_renda = st.sidebar.selectbox("Filtrar por Renda:", ["Todos"] + list(rank_map.keys()))
    f_trampo = st.sidebar.selectbox("Filtrar por Trabalho:", ["Todos", "SIM", "NÃO"])
    
    df_lista = df_unicos.copy()
    if f_renda != "Todos": df_lista = df_lista[df_lista[col_renda] == f_renda]
    if f_trampo != "Todos": df_lista = df_lista[df_lista[col_trampo] == f_trampo]
    
    # Ordenação por vulnerabilidade
    df_lista['rank'] = df_lista[col_renda].map(lambda x: rank_map.get(str(x).upper(), 99))
    lista_nomes = df_lista.sort_values(by=['rank', col_resp])[col_resp].tolist()
    
    selecionado = st.sidebar.selectbox("👤 Selecionar Responsável:", ["Selecione..."] + lista_nomes)

    # --- PAINEL PRINCIPAL ---
    st.markdown("<h1 style='text-align:center; color: #1e3a8a;'>Sociodemográfico das Famílias Matriculadas</h1>", unsafe_allow_html=True)
    
    if selecionado != "Selecione...":
        dados_familia = df[df[col_resp] == selecionado]
        chefe = df_unicos[df_unicos[col_resp] == selecionado].iloc[0]

        # Cards com Leitura Reforçada
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="card-leitura">
                <div class="titulo-card">🏠 Identificação e Localização</div>
                <p class="texto-preto"><b>Endereço:</b> {chefe.get('ENDEREÇO COMPLETO:', 'N/A')}</p>
                <p class="texto-preto"><b>Bairro:</b> {chefe.get('BAIRRO:', 'N/A')}</p>
                <p class="texto-preto"><b>Nacionalidade:</b> {chefe.get(col_nacionalidade, 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""
            <div class="card-leitura">
                <div class="titulo-card">💰 Dados do Responsável</div>
                <p class="texto-preto"><b>Renda Familiar:</b> {chefe.get(col_renda, 'N/A')}</p>
                <p class="texto-preto"><b>Trabalha?</b> {chefe.get(col_trampo, 'N/A')}</p>
                <p class="texto-preto"><b>Estado Civil:</b> {chefe.get(col_est_civil, 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

        # TABELA DE EXPANSÃO TOTAL (TODOS OS 56 CAMPOS)
        st.write("---")
        with st.expander("📂 CLIQUE AQUI PARA VER TODOS OS 56 CAMPOS DA TABELA (EXPANSÃO TOTAL)", expanded=False):
            st.markdown("### Ficha Cadastral Completa")
            st.dataframe(dados_familia, use_container_width=True)
            
            # Exportação
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                dados_familia.to_excel(writer, index=False)
            st.download_button(f"📥 Baixar Ficha de {selecionado}", output.getvalue(), f"{selecionado}.xlsx")

    # --- GRÁFICOS (QUANTITATIVOS REAIS POR RESPONSÁVEL) ---
    st.write("###")
    st.divider()
    st.markdown("## 📊 Diagnóstico Geral (Base: Responsáveis Familiares)")
    
    

    # Linha 1: Gênero e Renda
    g1, g2 = st.columns(2)
    with g1:
        fig1 = px.bar(df_unicos['GÊNERO:'].value_counts().reset_index(), x='GÊNERO:', y='count', text='count', 
                     title="Gênero dos Responsáveis", color_discrete_sequence=['#1e3a8a'])
        fig1.update_traces(textposition='outside')
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        fig2 = px.bar(df_unicos[col_renda].value_counts().reset_index(), x=col_renda, y='count', text='count', 
                     title="Distribuição de Renda", color_discrete_sequence=['#be123c'])
        fig2.update_traces(textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)

    # Linha 2: Nacionalidade e Estado Civil
    g3, g4 = st.columns(2)
    with g3:
        if col_nacionalidade in df_unicos.columns:
            fig3 = px.bar(df_unicos[col_nacionalidade].value_counts().reset_index(), x=col_nacionalidade, y='count', text='count', 
                         title="Nacionalidade das Famílias", color_discrete_sequence=['#f59e0b'])
            fig3.update_traces(textposition='outside')
            st.plotly_chart(fig3, use_container_width=True)
    with g4:
        if col_est_civil in df_unicos.columns:
            fig4 = px.bar(df_unicos[col_est_civil].value_counts().reset_index(), x=col_est_civil, y='count', text='count', 
                         title="Estado Civil dos Responsáveis", color_discrete_sequence=['#10b981'])
            fig4.update_traces(textposition='outside')
            st.plotly_chart(fig4, use_container_width=True)

else:
    st.error("Planilha não encontrada. Verifique o arquivo 'Planilha Matriculados.xlsx'.")
