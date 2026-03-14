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
    .metric-box {
        background: white; padding: 1.5rem; border-radius: 0.75rem; 
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); border-bottom: 4px solid #2563eb;
        text-align: center;
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
        
        for col in df.columns:
            df[col] = df[col].fillna("-").astype(str).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', '', ' ', 'NULL'], '-')
        
        # Unidades Familiares (Responsáveis Únicos)
        df_familias = df[df["NOME DO RESPONSÁVEL"] != "-"].drop_duplicates(subset=["NOME DO RESPONSÁVEL"])
        
        return df, df_familias
    except Exception as e:
        st.error(f"Erro: {e}")
        return None, None

df_geral, df_familias = load_data()

if df_geral is not None:
    # --- 4. FILTROS ---
    st.sidebar.header("🔍 Filtros")
    col_trab = "EXERCE ATIVIDADE REMUNERADA:"
    col_renda = "RENDA FAMILIAR TOTAL"
    col_benef = [c for c in df_geral.columns if "BENEFÍCIO" in c][0]

    f_trab = st.sidebar.multiselect("Trabalha?", sorted(df_familias[col_trab].unique()), default=list(df_familias[col_trab].unique()))
    f_renda = st.sidebar.multiselect("Renda:", sorted(df_familias[col_renda].unique()), default=list(df_familias[col_renda].unique()))
    f_benef = st.sidebar.multiselect("Benefício:", sorted(df_familias[col_benef].unique()), default=list(df_familias[col_benef].unique()))

    # Aplicação do Filtro
    df_filtrado_fam = df_familias[
        (df_familias[col_trab].isin(f_trab)) & 
        (df_familias[col_renda].isin(f_renda)) &
        (df_familias[col_benef].isin(f_benef))
    ]
    
    # Participantes vinculados
    total_pessoas = len(df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(df_filtrado_fam["NOME DO RESPONSÁVEL"])])

    # --- 5. DASHBOARD PRINCIPAL ---
    st.markdown('<div class="main-header"><h1>Painel Socioeconômico CAS</h1></div>', unsafe_allow_html=True)
    
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(f"""<div class="metric-box">
            <p style="margin:0; color:#64748b; font-size: 0.9rem; font-weight:bold;">PESSOAS EM ATIVIDADE</p>
            <h2 style="margin:0; color:#1e293b; font-size: 2.5rem;">{total_pessoas}</h2>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="metric-box">
            <p style="margin:0; color:#64748b; font-size: 0.9rem; font-weight:bold;">UNIDADES FAMILIARES</p>
            <h2 style="margin:0; color:#1e293b; font-size: 2.5rem;">{len(df_filtrado_fam)}</h2>
        </div>""", unsafe_allow_html=True)

    # Seleção
    st.write("###")
    lista_nomes = sorted(df_filtrado_fam["NOME DO RESPONSÁVEL"].tolist())
    selecionado = st.selectbox("🎯 Selecionar Responsável:", ["-- SELECIONE UM NOME --"] + lista_nomes)

    # --- 6. PRONTUÁRIO ---
    if selecionado != "-- SELECIONE UM NOME --":
        st.divider()
        familia_rows = df_geral[df_geral["NOME DO RESPONSÁVEL"] == selecionado]
        principal = familia_rows.iloc[0]

        st.subheader(f"🏠 Ficha Social: {selecionado}")
        
        grid = st.columns(4)
        for i, col in enumerate(df_geral.columns):
            with grid[i % 4]:
                st.markdown(f'''<div class="info-card">
                    <div class="label-title">{col}</div>
                    <div class="value-text">{principal[col]}</div>
                </div>''', unsafe_allow_html=True)

        st.write("---")
        st.write(f"### 👨‍👩‍👧‍👦 Membros da Família em Atividade ({len(familia_rows)})")
        st.table(familia_rows[["NOME DO PARTICIPANTE (ATIVIDADES)", "ATIVIDADE DESEJADA", "TURNO", "IDADE (PARTICIPANTE)"]])

    # --- 7. EXPORTAÇÃO ---
    if st.sidebar.button("➕ Adicionar à Exportação"):
        if selecionado != "-- SELECIONE UM NOME --":
            st.session_state.lista_exportacao.append(selecionado)
            st.rerun()

    if st.session_state.lista_exportacao:
        st.sidebar.write("---")
        if st.sidebar.button("📥 Baixar Excel Selecionados"):
            df_exp = df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(st.session_state.lista_exportacao)]
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df_exp.to_excel(writer, index=False)
            st.sidebar.download_button("Clique aqui para baixar", buf.getvalue(), "Relatorio_CAS.xlsx")
else:
    st.info("Planilha não encontrada. Verifique o arquivo 'Planilha Matriculados' na pasta.")
