import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão de Vulnerabilidade CAS", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .card-vulnerabilidade {
        background-color: #f1f5f9;
        padding: 20px;
        border-radius: 12px;
        border-left: 8px solid #1e3a8a;
        margin-bottom: 15px;
    }
    .texto-preto { color: #000000 !important; font-size: 16px; font-weight: 600; }
    .titulo-card { color: #1e3a8a !important; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
    .stCheckbox { background-color: #e2e8f0; padding: 10px; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO DOS DADOS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO = os.path.join(BASE_DIR, "Planilha Matriculados.xlsx - Planilha1.csv")

@st.cache_data
def carregar_dados_brutos(caminho):
    if not os.path.exists(caminho): return None
    try:
        df = pd.read_csv(caminho, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        return df
    except: return None

df_geral = carregar_dados_brutos(CAMINHO)

if df_geral is not None:
    col_t = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trabalha = "EXERCE ATIVIDADE REMUNERADA:"

    # Base de Responsáveis (Coluna T preenchida)
    df_responsaveis = df_geral[df_geral[col_t].notna() & (df_geral[col_t].str.strip() != "")].copy()

    st.title("📋 Triagem e Exportação de Famílias")
    st.write("Selecione os critérios abaixo, marque as famílias desejadas e exporte a lista completa.")

    # --- FILTROS LATERAIS ---
    st.sidebar.header("🎯 Filtros de Vulnerabilidade")
    f_renda = st.sidebar.selectbox("Filtrar por Renda:", ["Todos"] + sorted(df_responsaveis[col_renda].unique().tolist()))
    f_trampo = st.sidebar.selectbox("Está Trabalhando?", ["Todos"] + sorted(df_responsaveis[col_trabalha].unique().tolist()))

    # Aplicar filtros à base de responsáveis
    df_filtrado = df_responsaveis.copy()
    if f_renda != "Todos": df_filtrado = df_filtrado[df_filtrado[col_renda] == f_renda]
    if f_trampo != "Todos": df_filtrado = df_filtrado[df_filtrado[col_trabalha] == f_trampo]

    # --- SISTEMA DE MARCAÇÃO (CHECKBOX) ---
    st.subheader(f"🔍 Famílias Encontradas: {len(df_filtrado)}")
    
    # Criamos um container para a lista de marcação
    selecionados = []
    
    col1, col2 = st.columns([1, 1])
    
    # Dividimos a lista em duas colunas para facilitar a visualização
    nomes_lista = sorted(df_filtrado[col_t].unique().tolist())
    metade = len(nomes_lista) // 2
    
    with col1:
        for nome in nomes_lista[:metade]:
            if st.checkbox(nome, key=nome):
                selecionados.append(nome)
                
    with col2:
        for nome in nomes_lista[metade:]:
            if st.checkbox(nome, key=nome):
                selecionados.append(nome)

    # --- ÁREA DE EXPORTAÇÃO E DETALHES ---
    st.divider()
    st.subheader(f"📦 Cesta de Exportação: {len(selecionados)} família(s) marcada(s)")

    if selecionados:
        # Filtra os dados de TODOS os membros das famílias marcadas
        df_exportar = df_geral[df_geral[col_t].isin(selecionados)]

        c_exp1, c_exp2 = st.columns([1, 2])
        
        with c_exp1:
            # Botão de Exportação em Lote
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_exportar.to_excel(writer, index=False, sheet_name='Familias_Selecionadas')
            
            st.download_button(
                label="📥 EXPORTAR FAMÍLIAS MARCADAS (EXCEL)",
                data=output.getvalue(),
                file_name="exportacao_vulnerabilidade_cas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with c_exp2:
            st.warning(f"O arquivo conterá todos os dados (56 colunas) de todos os membros das {len(selecionados)} famílias selecionadas.")

        # Mostrar um resumo rápido das famílias marcadas antes de exportar
        with st.expander("👁️ Pré-visualizar dados das famílias marcadas", expanded=False):
            st.dataframe(df_exportar[[col_t, "NOME:", col_renda, col_trabalha]], use_container_width=True)

    else:
        st.info("Marque as caixas de seleção acima para adicionar famílias à lista de exportação.")

    # --- VISUALIZAÇÃO DE FICHA INDIVIDUAL (OPCIONAL) ---
    if len(selecionados) == 1:
        st.divider()
        st.subheader(f"📄 Ficha Detalhada: {selecionados[0]}")
        chefe = df_responsaveis[df_responsaveis[col_t] == selecionados[0]].iloc[0]
        
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            st.markdown(f"""<div class="card-vulnerabilidade">
                <p class="titulo-card">📍 Localização</p>
                <p class="texto-preto">Bairro: {chefe.get('BAIRRO:', 'N/A')}</p>
                <p class="texto-preto">Endereço: {chefe.get('ENDEREÇO COMPLETO:', 'N/A')}</p></div>""", unsafe_allow_html=True)
        with c_f2:
            st.markdown(f"""<div class="card-vulnerabilidade">
                <p class="titulo-card">💰 Renda e Trabalho</p>
                <p class="texto-preto">Renda: {chefe.get(col_renda, 'N/A')}</p>
                <p class="texto-preto">Trabalha: {chefe.get(col_trabalha, 'N/A')}</p></div>""", unsafe_allow_html=True)

else:
    st.error("Planilha não encontrada. Verifique o arquivo.")
