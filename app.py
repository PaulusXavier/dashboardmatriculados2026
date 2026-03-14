import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO INICIAL
st.set_page_config(page_title="Gestão CAS - Prontuário Direto", layout="wide", page_icon="🏠")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA ORGANIZAÇÃO DOS QUADROS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f1f5f9; }
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #3b82f6 100%);
        padding: 1.5rem; border-radius: 0.8rem; color: white; text-align: center; margin-bottom: 2rem;
    }
    .section-header {
        background-color: #ffffff; padding: 10px 15px; border-left: 5px solid #3b82f6;
        border-radius: 4px; font-weight: 800; color: #1e293b; margin: 20px 0 10px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .info-card {
        background: white; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0;
        margin-bottom: 8px; min-height: 65px;
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
        
        # Base de Famílias Únicas
        df_fam = df[df["NOME DO RESPONSÁVEL"] != "-"].drop_duplicates(subset=["NOME DO RESPONSÁVEL"]).copy()
        
        # Pontuação Interna para manter o Ranking de Vulnerabilidade na lista
        def rank_interno(row):
            pts = 0
            membros = len(df[df["NOME DO RESPONSÁVEL"] == row["NOME DO RESPONSÁVEL"]])
            pts += (membros * 10)
            if "SIM" in str(row["PESSOA COM DEFICIÊNCIA (RESPONSÁVEL)"]) or "SIM" in str(row["PCD (PARTICIPANTE)"]): pts += 50
            return pts
        
        df_fam["RANK"] = df_fam.apply(rank_interno, axis=1)
        return df, df_fam
    except Exception as e:
        st.error(f"Erro: {e}")
        return None, None

df_geral, df_fam = load_data()

if df_geral is not None:
    # --- 4. FILTROS MANUAIS NA ESQUERDA ---
    st.sidebar.header("🛠️ Seu Cruzamento")
    f_trab = st.sidebar.multiselect("Status de Trabalho:", sorted(df_fam["EXERCE ATIVIDADE REMUNERADA:"].unique()), default=list(df_fam["EXERCE ATIVIDADE REMUNERADA:"].unique()))
    f_renda = st.sidebar.multiselect("Faixa de Renda:", sorted(df_fam["RENDA FAMILIAR TOTAL"].unique()), default=list(df_fam["RENDA FAMILIAR TOTAL"].unique()))

    # Aplicar o cruzamento que você fizer
    df_filtrado = df_fam[
        (df_fam["EXERCE ATIVIDADE REMUNERADA:"].isin(f_trab)) & 
        (df_fam["RENDA FAMILIAR TOTAL"].isin(f_renda))
    ].sort_values(by="RANK", ascending=False)

    # --- 5. PAINEL PRINCIPAL ---
    st.markdown('<div class="main-header"><h1>Painel Socioeconômico CAS</h1></div>', unsafe_allow_html=True)
    
    lista_nomes = df_filtrado["NOME DO RESPONSÁVEL"].tolist()
    selecionado = st.selectbox(f"🎯 Selecionar entre as {len(lista_nomes)} famílias filtradas:", ["-- SELECIONE --"] + lista_nomes)

    if selecionado != "-- SELECIONE --":
        dados_familia = df_geral[df_geral["NOME DO RESPONSÁVEL"] == selecionado]
        principal = dados_familia.iloc[0]

        # --- QUADRO 1: DADOS DO RESPONSÁVEL E ENDEREÇO ---
        st.markdown('<div class="section-header">📍 IDENTIFICAÇÃO E LOCALIZAÇÃO DA FAMÍLIA</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        
        # Mapeando colunas comuns de endereço (ajuste os nomes se forem diferentes na sua planilha)
        col_end = [c for c in df_geral.columns if "ENDEREÇO" in c or "RUA" in c][0]
        col_bairro = [c for c in df_geral.columns if "BAIRRO" in c][0]
        col_tel = [c for c in df_geral.columns if "CONTATO" in c or "TELEFONE" in c or "CELULAR" in c][0]

        with c1:
            st.markdown(f'<div class="info-card"><div class="label-title">Responsável</div><div class="value-text">{selecionado}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="info-card"><div class="label-title">Endereço</div><div class="value-text">{principal[col_end]}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="info-card"><div class="label-title">Bairro</div><div class="value-text">{principal[col_bairro]}</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="info-card"><div class="label-title">Contato</div><div class="value-text">{principal[col_tel]}</div></div>', unsafe_allow_html=True)

        # --- QUADRO 2: DADOS SOCIOECONÔMICOS ---
        st.markdown('<div class="section-header">⚖️ PERFIL SOCIOECONÔMICO</div>', unsafe_allow_html=True)
        grid_socio = st.columns(4)
        cols_socio = ["RENDA FAMILIAR TOTAL", "EXERCE ATIVIDADE REMUNERADA:", "BENEFÍCIO:", "PESSOA COM DEFICIÊNCIA (RESPONSÁVEL)"]
        # Filtra apenas as que existem na planilha para não dar erro
        cols_existentes = [c for c in cols_socio if c in df_geral.columns]
        
        for i, col in enumerate(cols_existentes):
            with grid_socio[i % 4]:
                st.markdown(f'<div class="info-card"><div class="label-title">{col}</div><div class="value-text">{principal[col]}</div></div>', unsafe_allow_html=True)

        # --- QUADRO 3: PARTICIPANTES ---
        st.markdown('<div class="section-header">👨‍👩‍👧‍👦 PARTICIPANTES VINCULADOS (MATRÍCULAS)</div>', unsafe_allow_html=True)
        st.table(dados_familia[["NOME DO PARTICIPANTE (ATIVIDADES)", "IDADE (PARTICIPANTE)", "ATIVIDADE DESEJADA", "TURNO"]])

    # --- 6. EXPORTAÇÃO ---
    st.sidebar.write("---")
    if st.sidebar.button("➕ Adicionar à Exportação"):
        if selecionado != "-- SELECIONE --":
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

    if st.session_state.lista_exportacao:
        st.sidebar.success(f"{len(st.session_state.lista_exportacao)} famílias na lista")
        if st.sidebar.button("📥 Baixar Planilha"):
            df_exp = df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(st.session_state.lista_exportacao)]
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df_exp.to_excel(writer, index=False)
            st.sidebar.download_button("Salvar Excel", buf.getvalue(), "Relatorio_CAS.xlsx")
else:
    st.info("Aguardando arquivo 'Planilha Matriculados'...")
