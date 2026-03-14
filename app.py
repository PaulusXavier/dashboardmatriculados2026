import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO INICIAL
st.set_page_config(page_title="Socioeconômico Famílias CAS", layout="wide", page_icon="🏠")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN PROFISSIONAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #3b82f6 100%);
        padding: 2rem; border-radius: 1rem; color: white; text-align: center; margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    .info-card {
        background: white; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0;
        margin-bottom: 10px; min-height: 70px; transition: transform 0.2s;
    }
    .info-card:hover { transform: translateY(-2px); border-color: #3b82f6; }
    .label-title { color: #64748b; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; }
    .value-text { color: #1e293b; font-size: 0.9rem; font-weight: 600; margin-top: 4px; }
    .status-alerta {
        background-color: #fef2f2; border-left: 5px solid #ef4444; color: #991b1b;
        padding: 1rem; border-radius: 0.5rem; font-weight: 600; margin-bottom: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E TRATAMENTO RIGOROSO ---
@st.cache_data
def load_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None, None
    
    path = arquivos[0]
    try:
        # Carrega a planilha
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        
        # 1. Padroniza colunas
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # 2. Limpeza profunda: Remove espaços extras e troca NaNs por "-"
        for col in df.columns:
            df[col] = df[col].fillna("-").astype(str).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', '', ' ', 'NULL', 'UNDEFINED'], '-')
        
        # 3. Identifica as 292 Famílias (Responsáveis Únicos)
        # Ignora quem não tem nome e remove duplicatas exatas de nome para o contador
        df_unicos = df[df["NOME DO RESPONSÁVEL"] != "-"].drop_duplicates(subset=["NOME DO RESPONSÁVEL"])
        
        return df, df_unicos
    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        return None, None

df_geral, df_unicos = load_data()

if df_geral is not None:
    # --- 4. ÁREA DE FILTROS ---
    st.sidebar.header("🔍 Triagem de Famílias")
    
    # Mapeamento de colunas principais
    col_trab = "EXERCE ATIVIDADE REMUNERADA:"
    col_renda = "RENDA FAMILIAR TOTAL"
    # Busca automática para a coluna de benefício que pode ter espaços no final
    col_benef = [c for c in df_geral.columns if "BENEFÍCIO" in c][0]

    f_trab = st.sidebar.multiselect("Trabalha?", sorted(df_unicos[col_trab].unique()), default=list(df_unicos[col_trab].unique()))
    f_renda = st.sidebar.multiselect("Renda:", sorted(df_unicos[col_renda].unique()), default=list(df_unicos[col_renda].unique()))
    f_benef = st.sidebar.multiselect("Benefício:", sorted(df_unicos[col_benef].unique()), default=list(df_unicos[col_benef].unique()))

    # Aplicação do Filtro
    df_filtrado = df_unicos[
        (df_unicos[col_trab].isin(f_trab)) & 
        (df_unicos[col_renda].isin(f_renda)) &
        (df_unicos[col_benef].isin(f_benef))
    ]

    # --- 5. DASHBOARD PRINCIPAL ---
    st.markdown('<div class="main-header"><h1>Socioeconômico Famílias CAS</h1></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    # Aqui aparecerá as 292 famílias (ou o total filtrado)
    c1.metric("Unidades Familiares (Responsáveis)", len(df_filtrado))
    c2.metric("Matrículas Totais Ativas", len(df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(df_filtrado["NOME DO RESPONSÁVEL"])]))

    lista_nomes = sorted(df_filtrado["NOME DO RESPONSÁVEL"].unique().tolist())
    selecionado = st.selectbox("🎯 Localizar Responsável:", ["-- SELECIONE PARA VER O PRONTUÁRIO --"] + lista_nomes)

    # --- 6. PRONTUÁRIO SOCIAL ---
    if selecionado != "-- SELECIONE PARA VER O PRONTUÁRIO --":
        st.write("---")
        
        # Busca todas as matrículas dessa família
        dados_familia = df_geral[df_geral["NOME DO RESPONSÁVEL"] == selecionado]
        principal = dados_familia.iloc[0]

        # Alerta de Risco Social
        if "NÃO" in principal[col_trab] and "NÃO" in principal[col_benef]:
            st.markdown('<div class="status-alerta">⚠️ ALERTA: Esta família não possui renda formal nem benefícios. Prioridade Máxima.</div>', unsafe_allow_html=True)

        col_t, col_e = st.columns([3, 1])
        col_t.subheader(f"🏠 Ficha da Família: {selecionado}")
        
        if col_e.button("🚀 Adicionar p/ Exportação"):
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

        # Grid Dinâmico (Todas as colunas da planilha viram cartões)
        st.write("### 📖 Informações Cadastrais")
        colunas = df_geral.columns.tolist()
        grid = st.columns(4)
        for i, col in enumerate(colunas):
            with grid[i % 4]:
                st.markdown(f'''<div class="info-card">
                    <div class="label-title">{col}</div>
                    <div class="value-text">{principal[col]}</div>
                </div>''', unsafe_allow_html=True)

        st.write("---")
        st.write(f"### 👨‍👩‍👧‍👦 Integrantes no CAS ({len(dados_familia)})")
        st.table(dados_familia[["NOME DO PARTICIPANTE (ATIVIDADES)", "IDADE (PARTICIPANTE)", "ATIVIDADE DESEJADA", "TURNO"]])

    # --- 7. EXPORTAÇÃO ---
    if st.session_state.lista_exportacao:
        st.sidebar.write("---")
        st.sidebar.subheader("📦 Exportar Selecionados")
        df_exp = df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(st.session_state.lista_exportacao)]
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        
        st.sidebar.download_button("📥 Baixar Excel", output.getvalue(), "Relatorio_CAS.xlsx", use_container_width=True)
        if st.sidebar.button("🗑️ Limpar Lista"):
            st.session_state.lista_exportacao = []
            st.rerun()
else:
    st.info("Aguardando detecção do arquivo 'Planilha Matriculados'...")
