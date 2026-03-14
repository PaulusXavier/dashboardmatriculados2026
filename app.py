import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO
st.set_page_config(page_title="Gestão Sociodemográfica - CAS", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .card-info {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-left: 8px solid #1e40af;
    }
    .header-card { font-size: 18px; font-weight: bold; color: #1e40af; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 15px; }
    .alerta-vulnerabilidade {
        background: linear-gradient(90deg, #be123c 0%, #fb7185 100%);
        color: white; padding: 15px; border-radius: 10px; text-align: center;
        font-weight: bold; font-size: 20px; margin-bottom: 25px;
    }
    .texto-preto { color: #000000 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO DE DADOS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO = os.path.join(BASE_DIR, "Planilha Matriculados.xlsx - Planilha1.csv")

@st.cache_data
def carregar_dados(caminho):
    if not os.path.exists(caminho): return None
    try:
        df = pd.read_csv(caminho, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        return df
    except: return None

df_geral = carregar_dados(CAMINHO)

if df_geral is not None:
    # Definição de Colunas
    col_resp = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trampo = "EXERCE ATIVIDADE REMUNERADA:"
    col_benef = "A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:"
    col_moradia = "SITUAÇÃO DA MORADIA:"

    # Criar base apenas de Responsáveis (Linhas com Coluna T preenchida)
    df_responsaveis = df_geral[df_geral[col_resp].notna() & (df_geral[col_resp].str.strip() != "")].copy()

    # Ranking de Renda para Ordenação (Vulneráveis Primeiro)
    rank_map = {"SEM RENDA": 0, "ATÉ R$ 405,26": 1, "DE R$ 405,26 A R$ 810,50": 2, "DE R$ 810,50 A R$ 1.215,76": 3}
    
    # --- BARRA LATERAL: FILTROS TÉCNICOS ---
    st.sidebar.title("🛡️ Filtros de Triagem")
    
    f_renda = st.sidebar.selectbox("Filtrar por Renda:", ["Todos"] + list(rank_map.keys()))
    f_trampo = st.sidebar.selectbox("Filtrar por Ocupação:", ["Todos"] + sorted(df_responsaveis[col_trampo].unique().tolist()))

    # Aplicação dos Filtros na base de responsáveis
    df_filtrado = df_responsaveis.copy()
    if f_renda != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_renda] == f_renda]
    if f_trampo != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_trampo] == f_trampo]

    # Ordenação por Vulnerabilidade
    df_filtrado['rank'] = df_filtrado[col_renda].map(lambda x: rank_map.get(str(x).upper(), 99))
    lista_nomes = df_filtrado.sort_values(by=['rank', col_resp])[col_resp].tolist()

    selecionado = st.sidebar.selectbox("🎯 Selecione o Responsável:", ["Selecione..."] + lista_nomes)

    # --- ÁREA PRINCIPAL ---
    st.markdown("<h1 style='color: #1e3a8a;'>Sociodemográfico das Famílias - CAS</h1>", unsafe_allow_html=True)

    if selecionado != "Selecione...":
        dados_familia = df_geral[df_geral[col_resp] == selecionado]
        chefe = df_responsaveis[df_responsaveis[col_resp] == selecionado].iloc[0]
        renda_at = str(chefe[col_renda]).upper()

        # Alerta de Risco Máximo
        if rank_map.get(renda_at, 99) <= 1:
            st.markdown(f'<div class="alerta-vulnerabilidade">🚨 PRIORIDADE SOCIAL: Família em situação de {renda_at}</div>', unsafe_allow_html=True)

        # Painel de Cards
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="card-info">
                <div class="header-card">📍 Localização e Contato</div>
                <p class="texto-preto">Endereço: {chefe.get('ENDEREÇO COMPLETO:', 'N/A')}</p>
                <p class="texto-preto">Bairro: {chefe.get('BAIRRO:', 'N/A')}</p>
                <p class="texto-preto">Contato: {chefe.get('CONTATO:', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="card-info">
                <div class="header-card">💰 Status Socioeconômico</div>
                <p class="texto-preto">Renda Total: {renda_at}</p>
                <p class="texto-preto">Trabalha? {chefe.get(col_trampo, 'N/A')}</p>
                <p class="texto-preto">Benefício Social: {chefe.get(col_benef, 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

        # Composição Familiar
        st.subheader("👥 Composição Familiar")
        st.dataframe(dados_familia[['NOME:', 'IDADE:', 'GÊNERO:', 'GRAU DE PARENTESCO:']], use_container_width=True, hide_index=True)

        # Gestão de Dados e Exportação
        st.divider()
        col_exp1, col_exp2 = st.columns([1, 2])
        
        with col_exp1:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                dados_familia.to_excel(writer, index=False, sheet_name='Ficha_Social')
            st.download_button(
                label="📥 Exportar Ficha em Excel",
                data=output.getvalue(),
                file_name=f"Ficha_{selecionado.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with col_exp2:
            with st.expander("🔍 Ver todos os 56 campos da planilha"):
                st.dataframe(dados_familia, use_container_width=True)

    # --- COMPLEMENTO ESTATÍSTICO (RODAPÉ) ---
    st.write("###")
    st.divider()
    st.markdown("<h2 style='text-align: center; color: #475569;'>📊 Visão Geral do Cadastro (Base Responsáveis)</h2>", unsafe_allow_html=True)
    
    

    g1, g2 = st.columns(2)
    with g1:
        fig1 = px.bar(df_responsaveis['GÊNERO:'].value_counts().reset_index(), 
                     x='GÊNERO:', y='count', text='count', 
                     title="Gênero dos Responsáveis", color_discrete_sequence=['#3b82f6'])
        fig1.update_traces(textposition='outside')
        st.plotly_chart(fig1, use_container_width=True)
        
    with g2:
        fig2 = px.bar(df_responsaveis[col_renda].value_counts().reset_index(), 
                     x=col_renda, y='count', text='count', 
                     title="Distribuição de Renda", color_discrete_sequence=['#e11d48'])
        fig2.update_traces(textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)

else:
    st.error("⚠️ Planilha não detectada. Verifique o arquivo no repositório.")
