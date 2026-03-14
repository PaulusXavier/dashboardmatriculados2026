import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO INICIAL
st.set_page_config(page_title="Gestão CAS", layout="wide", page_icon="🏠")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
        padding: 2rem; border-radius: 1rem; color: white; text-align: center; margin-bottom: 2rem;
    }
    .info-card {
        background: white; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0;
        margin-bottom: 8px; min-height: 70px;
    }
    .label-title { color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; }
    .value-text { color: #1e293b; font-size: 0.85rem; font-weight: 600; margin-top: 4px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LIMPEZA ---
@st.cache_data
def load_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None, None
    
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Limpeza: Espaços e troca de vazios por "-"
        for col in df.columns:
            df[col] = df[col].fillna("-").astype(str).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', '', ' ', 'NULL'], '-')
        
        # Base de Responsáveis Únicos
        df_familias = df[df["NOME DO RESPONSÁVEL"] != "-"].drop_duplicates(subset=["NOME DO RESPONSÁVEL"])
        
        return df, df_familias
    except Exception as e:
        st.error(f"Erro: {e}")
        return None, None

df_geral, df_familias = load_data()

if df_geral is not None:
    # --- 4. CABEÇALHO ---
    st.markdown('<div class="main-header"><h1>Painel Socioeconômico CAS</h1></div>', unsafe_allow_html=True)
    
    # --- 5. SELEÇÃO DE RESPONSÁVEL (Acesso Direto) ---
    lista_nomes = sorted(df_familias["NOME DO RESPONSÁVEL"].unique().tolist())
    selecionado = st.selectbox("🎯 Localizar Responsável para Prontuário Social:", ["-- SELECIONE UM NOME NA LISTA --"] + lista_nomes)

    # --- 6. PRONTUÁRIO DETALHADO ---
    if selecionado != "-- SELECIONE UM NOME NA LISTA --":
        st.write("---")
        
        # Dados da Família
        familia_rows = df_geral[df_geral["NOME DO RESPONSÁVEL"] == selecionado]
        principal = familia_rows.iloc[0]

        st.subheader(f"🏠 Ficha Social: {selecionado}")
        
        # Grid Dinâmico (Todas as colunas da planilha viram cartões)
        st.write("### 📖 Cadastro Socioeconômico")
        grid = st.columns(4)
        for i, col in enumerate(df_geral.columns):
            with grid[i % 4]:
                st.markdown(f'''<div class="info-card">
                    <div class="label-title">{col}</div>
                    <div class="value-text">{principal[col]}</div>
                </div>''', unsafe_allow_html=True)

        st.write("---")
        # Listagem de quem desta família está inscrito
        st.write(f"### 👨‍👩‍👧‍👦 Integrantes desta Família em Atividade ({len(familia_rows)})")
        st.table(familia_rows[["NOME DO PARTICIPANTE (ATIVIDADES)", "ATIVIDADE DESEJADA", "TURNO", "IDADE (PARTICIPANTE)"]])

    # --- 7. EXPORTAÇÃO NA LATERAL ---
    st.sidebar.header("📋 Exportação")
    if st.sidebar.button("➕ Adicionar Atual à Lista"):
        if selecionado != "-- SELECIONE UM NOME NA LISTA --":
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

    if st.session_state.lista_exportacao:
        st.sidebar.write(f"Itens selecionados: {len(st.session_state.lista_exportacao)}")
        if st.sidebar.button("📥 Baixar Excel"):
            df_exp = df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(st.session_state.lista_exportacao)]
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df_exp.to_excel(writer, index=False)
            st.sidebar.download_button("Clique para salvar", buf.getvalue(), "Relatorio_CAS.xlsx")
        
        if st.sidebar.button("🗑️ Limpar Tudo"):
            st.session_state.lista_exportacao = []
            st.rerun()
else:
    st.info("Aguardando detecção da 'Planilha Matriculados' na pasta.")
