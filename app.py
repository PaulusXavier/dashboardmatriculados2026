import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Sociodemográfico - CAS/SETRABES", layout="wide")

st.markdown("""
    <style>
    .card-painel { padding: 20px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #e2e8f0; }
    .bg-local { background-color: #f0f9ff; border-left: 8px solid #0ea5e9; }
    .bg-eco { background-color: #f0fdf4; border-left: 8px solid #16a34a; }
    .bg-alerta { background-color: #fef2f2; border-left: 8px solid #dc2626; }
    .titulo-sessao { color: #1e3a8a; font-weight: bold; margin-top: 20px; }
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
    # Mapeamento de Colunas
    col_resp = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trampo = "EXERCE ATIVIDADE REMUNERADA:"
    col_moradia = "SITUAÇÃO DA MORADIA:"
    col_benef = "A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:"

    # Ranking de Renda (Morettin & Bussab)
    rank_map = {"SEM RENDA": 0, "ATÉ R$ 405,26": 1, "DE R$ 405,26 A R$ 810,50": 2, "DE R$ 810,50 A R$ 1.215,76": 3}

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Filtros de Vulnerabilidade")
    
    # 1. Filtro de Renda
    opcoes_renda = ["Todos"] + list(rank_map.keys())
    filtro_renda = st.sidebar.selectbox("Critério de Renda:", opcoes_renda)
    
    # 2. Filtro de Emprego
    opcoes_trampo = ["Todos"] + (df[col_trampo].unique().tolist() if col_trampo in df.columns else [])
    filtro_trampo = st.sidebar.selectbox("Está Empregado?", opcoes_trampo)

    # Aplicação dos filtros
    df_filtrado = df.copy()
    if filtro_renda != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_renda] == filtro_renda]
    if filtro_trampo != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_trampo] == filtro_trampo]

    # Ordenação da lista de responsáveis (Vulneráveis primeiro)
    df_lista = df_filtrado[[col_resp, col_renda]].drop_duplicates(subset=[col_resp])
    df_lista['rank'] = df_lista[col_renda].map(lambda x: rank_map.get(str(x).upper(), 99))
    lista_final = df_lista.sort_values(by=['rank', col_resp])[col_resp].tolist()

    # Seletor de Responsável na Barra Lateral
    selecionado = st.sidebar.selectbox("👤 Responsável Familiar:", ["Selecione..."] + lista_final)

    # Exportação na Sidebar
    st.sidebar.divider()
    st.sidebar.write("### 📤 Exportar")
    if selecionado != "Selecione...":
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df[df[col_resp] == selecionado].to_excel(writer, index=False)
        st.sidebar.download_button("Baixar Dados desta Família", output.getvalue(), f"{selecionado}.xlsx")

    # --- PAINEL PRINCIPAL ---
    st.markdown("<h1 style='text-align:center;'>Sociodemográfico das Famílias Matriculadas</h1>", unsafe_allow_html=True)
    
    if selecionado != "Selecione...":
        dados_f = df[df[col_resp] == selecionado]
        
        # Destaque de Risco
        renda_val = dados_f[col_renda].iloc[0]
        if rank_map.get(str(renda_val).upper(), 99) <= 1:
            st.markdown(f'<div class="alerta-prioridade" style="background-color:#be123c; color:white; padding:10px; border-radius:10px; text-align:center; font-weight:bold;">🚨 ATENÇÃO: ALTA VULNERABILIDADE SOCIOECONÔMICA</div>', unsafe_allow_html=True)

        # Cards de Informação
        st.write("###")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'''<div class="card-painel bg-local">
                <h3>🏠 Localização</h3>
                <p><b>Endereço:</b> {dados_f['ENDEREÇO COMPLETO:'].iloc[0]}</p>
                <p><b>Bairro:</b> {dados_f['BAIRRO:'].iloc[0]}</p>
            </div>''', unsafe_allow_html=True)
        with c2:
            st.markdown(f'''<div class="card-painel bg-eco">
                <h3>💰 Dados Econômicos</h3>
                <p><b>Renda:</b> {renda_val}</p>
                <p><b>Empregado:</b> {dados_f[col_trampo].iloc[0] if col_trampo in dados_f.columns else "N/A"}</p>
                <p><b>Programa Social:</b> {dados_f[col_benef].iloc[0] if col_benef in dados_f.columns else "N/A"}</p>
            </div>''', unsafe_allow_html=True)

        # Tabela de Composição
        st.write("#### 👥 Composição do Grupo Familiar")
        st.dataframe(dados_f[['NOME:', 'IDADE:', 'GÊNERO:', 'GRAU DE PARENTESCO:']], use_container_width=True, hide_index=True)

        # TABELA COMPLETA (Puxar tudo)
        with st.expander("🔍 ACESSAR FICHA TÉCNICA COMPLETA (Todas as 56 Colunas)"):
            st.write("Abaixo estão todos os dados brutos cadastrados para esta família:")
            st.dataframe(dados_f)

    # --- GRÁFICOS (COMPLEMENTO NO FINAL) ---
    st.divider()
    st.markdown("<h2 class='titulo-sessao'>📊 Complemento: Análise Estatística Geral</h2>", unsafe_allow_html=True)
    
    g1, g2 = st.columns(2)
    with g1:
        # Gráfico de Gênero
        df_gen = df.drop_duplicates(subset=[col_resp])
        fig1 = px.bar(df_gen['GÊNERO:'].value_counts().reset_index(), x='GÊNERO:', y='count', text='count', title="Gênero dos Responsáveis", color_discrete_sequence=['#3b82f6'])
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        # Gráfico de Renda
        fig2 = px.bar(df[col_renda].value_counts().reset_index(), x=col_renda, y='count', text='count', title="Distribuição de Renda", color_discrete_sequence=['#ef4444'])
        st.plotly_chart(fig2, use_container_width=True)

    g3, g4 = st.columns(2)
    with g3:
        # Gráfico de Benefícios
        fig3 = px.bar(df[col_benef].value_counts().reset_index(), x=col_benef, y='count', text='count', title="Recebe Benefício?", color_discrete_sequence=['#10b981'])
        st.plotly_chart(fig3, use_container_width=True)
    with g4:
        # Gráfico de Moradia
        if col_moradia in df.columns:
            fig4 = px.bar(df[col_moradia].value_counts().reset_index(), x=col_moradia, y='count', text='count', title="Tipo de Moradia", color_discrete_sequence=['#8b5cf6'])
            st.plotly_chart(fig4, use_container_width=True)

else:
    st.error("Planilha 'Planilha Matriculados.xlsx' não encontrada.")
