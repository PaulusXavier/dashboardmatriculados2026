import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Prontuário de Vulnerabilidade", layout="wide", page_icon="🗂️")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA EXIBIÇÃO DE DADOS COMPLETOS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #020617 0%, #1e3a8a 100%);
        padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;
    }
    .info-card {
        background: white; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0;
        margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.02);
    }
    .label-title { color: #64748b; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; }
    .value-text { color: #0f172a; font-size: 0.85rem; font-weight: 600; }
    .vulnerabilidade-critica { border-left: 8px solid #dc2626; background-color: #fef2f2; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO DOS DADOS ---
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
            df[col] = df[col].replace(['NAN', 'NONE', ''], 'NÃO INFORMADO')
        
        # Base de Famílias Únicas (292)
        df_unicos = df[df["NOME DO RESPONSÁVEL"] != "NÃO INFORMADO"].drop_duplicates(subset=["NOME DO RESPONSÁVEL"])
        return df, df_unicos
    except Exception as e:
        st.error(f"Erro: {e}")
        return None, None

df_geral, df_unicos = load_data()

if df_geral is not None:
    # --- 4. SIDEBAR (FILTROS LATERAIS AUMENTADOS) ---
    st.sidebar.header("🎯 Filtros de Seleção")
    
    # Filtro 1: Trabalho
    op_trab = sorted(df_unicos["EXERCE ATIVIDADE REMUNERADA:"].unique())
    f_trab = st.sidebar.multiselect("Está Trabalhando?", op_trab, default=op_trab)
    
    # Filtro 2: Renda
    op_renda = sorted(df_unicos["RENDA FAMILIAR TOTAL"].unique())
    f_renda = st.sidebar.multiselect("Faixa de Renda:", op_renda, default=op_renda)
    
    # Filtro 3: Benefício
    op_benef = sorted(df_unicos["A FAMÍLIA RECEBE ALGUM TIPO DE BENEFÍCIO"].unique())
    f_benef = st.sidebar.multiselect("Recebe Benefício?", op_benef, default=op_benef)

    # Aplicação dos Filtros
    df_f = df_unicos[
        (df_unicos["EXERCE ATIVIDADE REMUNERADA:"].isin(f_trab)) & 
        (df_unicos["RENDA FAMILIAR TOTAL"].isin(f_renda)) &
        (df_unicos["A FAMÍLIA RECEBE ALGUM TIPO DE BENEFÍCIO"].isin(f_benef))
    ]

    # Ordenação por Vulnerabilidade (Quem NÃO trabalha e NÃO tem benefício sobe)
    df_f['ORDEM'] = df_f["EXERCE ATIVIDADE REMUNERADA:"].apply(lambda x: 0 if "NÃO" in x else 1)
    df_f = df_f.sort_values('ORDEM').drop(columns=['ORDEM'])

    # --- 5. BUSCA E KPIs ---
    st.markdown('<div class="main-header"><h1>Painel de Triagem e Prontuário Social</h1></div>', unsafe_allow_html=True)
    
    k1, k2 = st.columns(2)
    k1.metric("Famílias Filtradas", len(df_f))
    k2.metric("Participantes Totais", len(df_geral))

    lista_nomes = sorted(df_f["NOME DO RESPONSÁVEL"].unique())
    selecionado = st.selectbox("🔍 Selecione o Nome do Responsável (Ordenado por Vulnerabilidade):", ["SELECIONE..."] + lista_nomes)

    # --- 6. ABERTURA TOTAL DE INFORMAÇÕES (PRONTUÁRIO) ---
    if selecionado != "SELECIONE...":
        st.write("---")
        
        # Puxa a família toda
        familia = df_geral[df_geral["NOME DO RESPONSÁVEL"] == selecionado]
        dados_principais = familia.iloc[0]
        
        # Identificador de Vulnerabilidade Crítica
        is_critico = "NÃO" in str(dados_principais["EXERCE ATIVIDADE REMUNERADA:"]) and "NÃO" in str(dados_principais["A FAMÍLIA RECEBE ALGUM TIPO DE BENEFÍCIO"])
        
        c_tit, c_exp = st.columns([3, 1])
        with c_tit:
            st.subheader(f"🗂️ Prontuário Completo: {selecionado}")
            if is_critico:
                st.markdown('<div class="status-vulneravel" style="background:#fee2e2; color:#991b1b; padding:10px; border-radius:10px; font-weight:bold; border:1px solid #f87171">🚨 ALTA VULNERABILIDADE: Sem Renda e Sem Benefício</div>', unsafe_allow_html=True)
        
        with c_exp:
            if st.button("🚀 Adicionar à Exportação"):
                if selecionado not in st.session_state.lista_exportacao:
                    st.session_state.lista_exportacao.append(selecionado)
                    st.rerun()

        # --- EXIBIÇÃO DE TODAS AS COLUNAS DA TABELA ---
        st.write("### 📄 Todas as Informações Registradas")
        todas_colunas = df_geral.columns.tolist()
        
        # Divide em 3 colunas para caber tudo sem rolar muito
        col_a, col_b, col_c = st.columns(3)
        for i, col in enumerate(todas_colunas):
            valor = dados_principais[col]
            # Seleciona qual coluna visual o dado vai aparecer
            target = col_a if i % 3 == 0 else col_b if i % 3 == 1 else col_c
            target.markdown(f'''<div class="info-card">
                <div class="label-title">{col}</div>
                <div class="value-text">{valor}</div>
            </div>''', unsafe_allow_html=True)

        st.write("---")
        st.write(f"### 👨‍👩‍👧‍👦 Participantes Vinculados ({len(familia)})")
        st.table(familia[["NOME DO PARTICIPANTE (ATIVIDADES)", "IDADE (PARTICIPANTE)", "ATIVIDADE DESEJADA", "TURNO"]])

    # --- 7. GESTÃO DE EXPORTAÇÃO ---
    if st.session_state.lista_exportacao:
        st.sidebar.write("---")
        st.sidebar.subheader("📦 Lista de Exportação")
        st.sidebar.write(f"{len(st.session_state.lista_exportacao)} famílias prontas.")
        
        if st.sidebar.button("🗑️ Limpar Lista"):
            st.session_state.lista_exportacao = []
            st.rerun()
            
        df_export = df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(st.session_state.lista_exportacao)]
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False)
        
        st.sidebar.download_button("📥 Baixar Excel Completo", buf.getvalue(), "Relatorio_Detalhado_CAS.xlsx", use_container_width=True)

else:
    st.error("Planilha não encontrada. Certifique-se de que o arquivo está no repositório.")
