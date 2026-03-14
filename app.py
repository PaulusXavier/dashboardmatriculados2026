import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Sociodemográfico - CAS/SETRABES", layout="wide")

# Estilização para Contraste e Leitura
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    /* Cards de Localização e Dados com fundo claro e letra preta */
    .card-leitura {
        background-color: #f1f5f9;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #3b82f6;
        margin-bottom: 15px;
    }
    .texto-preto { color: #000000 !important; font-size: 16px; }
    .titulo-card { color: #1e3a8a !important; font-weight: bold; font-size: 18px; margin-bottom: 10px; border-bottom: 1px solid #cbd5e1; }
    
    /* Indicadores do Topo */
    .metric-container {
        background-color: #1e3a8a;
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO DOS DADOS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO = os.path.join(BASE_DIR, "Planilha Matriculados.xlsx")

@st.cache_data
def carregar_dados(caminho):
    if not os.path.exists(caminho): return None
    df = pd.read_excel(caminho, dtype=str)
    df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    return df

df = carregar_dados(CAMINHO)

if df is not None:
    # Colunas principais
    col_resp = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trampo = "EXERCE ATIVIDADE REMUNERADA:"
    col_moradia = "SITUAÇÃO DA MORADIA:"
    col_benef = "A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:"
    
    # Criar base apenas de Responsáveis para Gráficos Precisos
    df_unicos = df.drop_duplicates(subset=[col_resp]).copy()
    total_responsaveis = len(df_unicos)
    total_matriculados = len(df)

    # --- INDICADORES DE TOPO ---
    c_meta1, c_meta2 = st.columns(2)
    with c_meta1:
        st.markdown(f'<div class="metric-container"><h3>👨‍👩‍👧‍👦 Total de Famílias (Responsáveis)</h3><h2>{total_responsaveis}</h2></div>', unsafe_allow_html=True)
    with c_meta2:
        st.markdown(f'<div class="metric-container"><h3>📝 Total de Pessoas Matriculadas</h3><h2>{total_matriculados}</h2></div>', unsafe_allow_html=True)

    st.write("---")

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Triagem de Vulnerabilidade")
    rank_map = {"SEM RENDA": 0, "ATÉ R$ 405,26": 1, "DE R$ 405,26 A R$ 810,50": 2, "DE R$ 810,50 A R$ 1.215,76": 3}
    
    f_renda = st.sidebar.selectbox("Renda Familiar:", ["Todos"] + list(rank_map.keys()))
    
    df_lista = df_unicos.copy()
    if f_renda != "Todos":
        df_lista = df_lista[df_lista[col_renda] == f_renda]
    
    # Ordenar por vulnerabilidade
    df_lista['rank'] = df_lista[col_renda].map(lambda x: rank_map.get(str(x).upper(), 99))
    lista_nomes = df_lista.sort_values(by=['rank', col_resp])[col_resp].tolist()
    
    selecionado = st.sidebar.selectbox("👤 Responsável Familiar:", ["Selecione..."] + lista_nomes)

    # --- PAINEL PRINCIPAL ---
    st.markdown("<h1 style='text-align:center;'>Sociodemográfico das Famílias Matriculadas</h1>", unsafe_allow_html=True)
    
    if selecionado != "Selecione...":
        dados_f = df[df[col_resp] == selecionado]
        chefe = df_unicos[df_unicos[col_resp] == selecionado].iloc[0]

        # Painel de Cards com alta visibilidade (Fundo claro, letra preta)
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown(f"""
            <div class="card-leitura">
                <div class="titulo-card">🏠 Localização</div>
                <p class="texto-preto"><b>Endereço:</b> {chefe.get('ENDEREÇO COMPLETO:', 'N/A')}</p>
                <p class="texto-preto"><b>Bairro:</b> {chefe.get('BAIRRO:', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_c2:
            st.markdown(f"""
            <div class="card-leitura">
                <div class="titulo-card">💰 Dados do Responsável</div>
                <p class="texto-preto"><b>Renda Familiar:</b> {chefe.get(col_renda, 'N/A')}</p>
                <p class="texto-preto"><b>Trabalha:</b> {chefe.get(col_trampo, 'N/A')}</p>
                <p class="texto-preto"><b>Beneficiário:</b> {chefe.get(col_benef, 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

        st.write("#### 👥 Integrantes do Núcleo Familiar")
        st.dataframe(dados_f[['NOME:', 'IDADE:', 'GÊNERO:', 'GRAU DE PARENTESCO:']], use_container_width=True, hide_index=True)

        # EXPANSÃO TOTAL DA TABELA
        with st.expander("📂 CLIQUE AQUI PARA VER TODOS OS 56 CAMPOS DA TABELA (EXPANSÃO TOTAL)", expanded=False):
            st.write("### Ficha Técnica Detalhada")
            st.dataframe(dados_f, use_container_width=True)

        # Botão de Exportação
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            dados_f.to_excel(writer, index=False)
        st.download_button(f"📥 Exportar Dados de {selecionado}", output.getvalue(), f"{selecionado}.xlsx")

    # --- GRÁFICOS (BASEADOS APENAS NOS RESPONSÁVEIS) ---
    st.write("###")
    st.divider()
    st.markdown("## 📊 Diagnóstico Geral (Base: Responsáveis Familiares)")
    st.info(f"Os gráficos abaixo representam as {total_responsaveis} famílias únicas cadastradas.")

    g1, g2 = st.columns(2)
    with g1:
        fig1 = px.bar(df_unicos['GÊNERO:'].value_counts().reset_index(), x='GÊNERO:', y='count', text='count', 
                     title="Gênero dos Responsáveis", color_discrete_sequence=['#1e3a8a'])
        fig1.update_traces(textposition='outside')
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        fig2 = px.bar(df_unicos[col_renda].value_counts().reset_index(), x=col_renda, y='count', text='count', 
                     title="Distribuição de Renda Familiar", color_discrete_sequence=['#be123c'])
        fig2.update_traces(textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)

    g3, g4 = st.columns(2)
    with g3:
        fig3 = px.bar(df_unicos[col_benef].value_counts().reset_index(), x=col_benef, y='count', text='count', 
                     title="Recebe Algum Benefício?", color_discrete_sequence=['#16a34a'])
        fig3.update_traces(textposition='outside')
        st.plotly_chart(fig3, use_container_width=True)
    with g4:
        if col_moradia in df_unicos.columns:
            fig4 = px.bar(df_unicos[col_moradia].value_counts().reset_index(), x=col_moradia, y='count', text='count', 
                         title="Situação de Moradia", color_discrete_sequence=['#7c3aed'])
            fig4.update_traces(textposition='outside')
            st.plotly_chart(fig4, use_container_width=True)

else:
    st.error("Planilha não encontrada. Verifique o arquivo 'Planilha Matriculados.xlsx'.")
