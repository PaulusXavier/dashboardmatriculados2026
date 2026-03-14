import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Socioeconômico Famílias CAS", layout="wide", page_icon="🏠")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS CUSTOMIZADO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f1f5f9; }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%);
        padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;
    }
    .info-card {
        background: white; padding: 10px; border-radius: 8px; border-bottom: 3px solid #cbd5e1;
        margin-bottom: 8px; min-height: 65px;
    }
    .label-title { color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; }
    .value-text { color: #0f172a; font-size: 0.85rem; font-weight: 600; margin-top: 2px; }
    .status-alerta {
        background-color: #fef2f2; border: 1px solid #f87171; color: #991b1b;
        padding: 15px; border-radius: 10px; font-weight: bold; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LIMPEZA (SUBSTITUINDO NAN POR TRAÇO) ---
@st.cache_data
def load_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            # Substituindo qualquer variação de vazio ou NAN por um traço "-"
            df[col] = df[col].replace(['NAN', 'NONE', '', ' ', 'NULL'], '-')
        
        # Base de Responsáveis Únicos (Famílias)
        df_unicos = df[df["NOME DO RESPONSÁVEL"] != "-"].drop_duplicates(subset=["NOME DO RESPONSÁVEL"])
        
        return df, df_unicos
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
        return None, None

df_geral, df_unicos = load_data()

if df_geral is not None:
    # --- 4. FILTROS LATERAIS ---
    st.sidebar.header("🔍 Critérios de Triagem")
    
    col_trab = "EXERCE ATIVIDADE REMUNERADA:"
    col_renda = "RENDA FAMILIAR TOTAL"
    col_benef = "A FAMÍLIA RECEBE ALGUM TIPO DE BENEFÍCIO"

    f_trab = st.sidebar.multiselect("Trabalha?", sorted(list(df_unicos[col_trab].unique())), default=list(df_unicos[col_trab].unique()))
    f_renda = st.sidebar.multiselect("Renda:", sorted(list(df_unicos[col_renda].unique())), default=list(df_unicos[col_renda].unique()))
    f_benef = st.sidebar.multiselect("Benefício:", sorted(list(df_unicos[col_benef].unique())), default=list(df_unicos[col_benef].unique()))

    # Filtragem
    df_filtrado = df_unicos[
        (df_unicos[col_trab].isin(f_trab)) & 
        (df_unicos[col_renda].isin(f_renda)) &
        (df_unicos[col_benef].isin(f_benef))
    ].copy()

    # Ordenação por Vulnerabilidade (Não trabalha + Sem benefício = Topo)
    df_filtrado['VULN'] = df_filtrado.apply(lambda r: 0 if "NÃO" in r[col_trab] and "NÃO" in r[col_benef] else 1, axis=1)
    df_filtrado = df_filtrado.sort_values('VULN')

    # --- 5. INTERFACE ---
    st.markdown('<div class="main-header"><h1>Socioeconômico Famílias CAS</h1></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    c1.metric("Unidades Familiares", len(df_filtrado))
    c2.metric("Total de Matrículas", len(df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(df_filtrado["NOME DO RESPONSÁVEL"])]))

    lista_nomes = [n for n in df_filtrado["NOME DO RESPONSÁVEL"].tolist() if n != "-"]
    selecionado = st.selectbox("🎯 Selecionar Responsável:", ["SELECIONE UM NOME..."] + lista_nomes)

    # --- 6. PRONTUÁRIO ---
    if selecionado != "SELECIONE UM NOME...":
        st.write("---")
        familia_data = df_geral[df_geral["NOME DO RESPONSÁVEL"] == selecionado]
        dados_base = familia_data.iloc[0]

        if "NÃO" in dados_base[col_trab] and "NÃO" in dados_base[col_benef]:
            st.markdown(f'<div class="status-alerta">🚨 ALERTA: Esta família está em situação de vulnerabilidade (Sem Trabalho e Sem Benefício).</div>', unsafe_allow_html=True)

        ctit, cbtn = st.columns([3, 1])
        ctit.subheader(f"🏠 Ficha Social: {selecionado}")
        
        if cbtn.button("🚀 Adicionar para Exportar"):
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

        st.write("### 📄 Dados Cadastrais Completos")
        grid = st.columns(4)
        for i, coluna in enumerate(df_geral.columns.tolist()):
            with grid[i % 4]:
                st.markdown(f'''<div class="info-card">
                    <div class="label-title">{coluna}</div>
                    <div class="value-text">{dados_base[coluna]}</div>
                </div>''', unsafe_allow_html=True)

        st.write("---")
        st.write(f"### 👨‍👩‍👧‍👦 Integrantes no CAS ({len(familia_data)})")
        st.table(familia_data[["NOME DO PARTICIPANTE (ATIVIDADES)", "IDADE (PARTICIPANTE)", "ATIVIDADE DESEJADA", "TURNO"]])

    # --- 7. EXPORTAÇÃO ---
    if st.session_state.lista_exportacao:
        st.sidebar.write("---")
        st.sidebar.subheader("📦 Lista de Saída")
        df_exp = df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(st.session_state.lista_exportacao)]
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        st.sidebar.download_button("📥 Baixar Planilha", buf.getvalue(), "Relatorio_CAS_2026.xlsx", use_container_width=True)
        if st.sidebar.button("🗑️ Limpar"):
            st.session_state.lista_exportacao = []
            st.rerun()
else:
    st.info("Carregue a planilha para iniciar o diagnóstico.")
