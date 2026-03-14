import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO INICIAL
st.set_page_config(page_title="Gestão Social CAS", layout="wide", page_icon="⚖️")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN E ALERTAS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #ef4444 100%);
        padding: 2rem; border-radius: 1rem; color: white; text-align: center; margin-bottom: 2rem;
    }
    .info-card {
        background: white; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0;
        margin-bottom: 8px; min-height: 70px;
    }
    .label-title { color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; }
    .value-text { color: #1e293b; font-size: 0.85rem; font-weight: 600; margin-top: 4px; }
    .status-vulneravel {
        background-color: #fff1f2; border: 2px solid #f43f5e; color: #9f1239;
        padding: 20px; border-radius: 12px; font-weight: bold; margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LÓGICA DE RISCO ---
@st.cache_data
def load_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None, None
    
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Limpeza e Padronização
        for col in df.columns:
            df[col] = df[col].fillna("-").astype(str).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', '', ' ', 'NULL'], '-')
        
        # Base de Famílias (Responsáveis Únicos)
        df_fam = df[df["NOME DO RESPONSÁVEL"] != "-"].drop_duplicates(subset=["NOME DO RESPONSÁVEL"]).copy()
        
        # --- CÁLCULO DE VULNERABILIDADE (SISTEMA DE PONTOS) ---
        def calcular_pontos(row):
            pontos = 0
            # Critério 1: Sem trabalho
            if "NÃO" in str(row["EXERCE ATIVIDADE REMUNERADA:"]): pontos += 10
            # Critério 2: Renda Baixa (Salário Mínimo ou Meio Salário)
            if "DE R$ 606" in str(row["RENDA FAMILIAR TOTAL"]) or "ATÉ R$ 606" in str(row["RENDA FAMILIAR TOTAL"]): pontos += 15
            # Critério 3: PCD (Participante ou Responsável)
            if "SIM" in str(row["PESSOA COM DEFICIÊNCIA (RESPONSÁVEL)"]) or "SIM" in str(row["PCD (PARTICIPANTE)"]): pontos += 20
            # Critério 4: Idoso (Responsável com 60 anos ou mais)
            try:
                idade_res = int(''.join(filter(str.isdigit, str(row["IDADE DO RESPONSÁVEL"]))))
                if idade_res >= 60: pontos += 15
            except: pass
            return pontos

        df_fam["PONTOS_RISCO"] = df_fam.apply(calcular_pontos, axis=1)
        # Ordena: Mais vulneráveis no topo
        df_fam = df_fam.sort_values(by="PONTOS_RISCO", ascending=False)
        
        return df, df_fam
    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        return None, None

df_geral, df_fam = load_data()

if df_geral is not None:
    # --- 4. FILTROS NA LATERAL ---
    st.sidebar.header("🔍 Critérios de Triagem")
    f_trab = st.sidebar.multiselect("Status de Trabalho:", sorted(df_fam["EXERCE ATIVIDADE REMUNERADA:"].unique()), default=list(df_fam["EXERCE ATIVIDADE REMUNERADA:"].unique()))
    f_renda = st.sidebar.multiselect("Faixa de Renda:", sorted(df_fam["RENDA FAMILIAR TOTAL"].unique()), default=list(df_fam["RENDA FAMILIAR TOTAL"].unique()))
    
    # Aplicar Filtros
    df_filtrado = df_fam[(df_fam["EXERCE ATIVIDADE REMUNERADA:"].isin(f_trab)) & (df_fam["RENDA FAMILIAR TOTAL"].isin(f_renda))]

    # --- 5. CABEÇALHO ---
    st.markdown('<div class="main-header"><h1>Painel de Vulnerabilidade Social CAS</h1></div>', unsafe_allow_html=True)
    
    # --- 6. SELEÇÃO DE RESPONSÁVEL ---
    # A lista já vem ordenada por quem tem mais pontos de risco
    lista_nomes = df_filtrado["NOME DO RESPONSÁVEL"].tolist()
    st.info(f"💡 A lista abaixo está ordenada por PRIORIDADE (Mais vulneráveis primeiro).")
    selecionado = st.selectbox("🎯 Selecionar Família para Avaliação:", ["-- SELECIONE NA LISTA (ORDEM DE RISCO) --"] + lista_nomes)

    # --- 7. PRONTUÁRIO COM ALERTAS ---
    if selecionado != "-- SELECIONE NA LISTA (ORDEM DE RISCO) --":
        st.divider()
        dados_familia = df_geral[df_geral["NOME DO RESPONSÁVEL"] == selecionado]
        principal = dados_familia.iloc[0]
        pontos = df_fam[df_fam["NOME DO RESPONSÁVEL"] == selecionado]["PONTOS_RISCO"].values[0]

        # MENSAGEM DE ALERTA DINÂMICA
        if pontos >= 20:
            alertas = []
            if "NÃO" in principal["EXERCE ATIVIDADE REMUNERADA:"]: alertas.append("SEM ATIVIDADE REMUNERADA")
            if "SIM" in principal["PESSOA COM DEFICIÊNCIA (RESPONSÁVEL)"] or "SIM" in principal["PCD (PARTICIPANTE)"]: alertas.append("PRESENÇA DE PcD")
            if "ATÉ R$ 606" in principal["RENDA FAMILIAR TOTAL"]: alertas.append("RENDA CRÍTICA")
            
            st.markdown(f"""
                <div class="status-vulneravel">
                    🚨 ALERTA DE ALTA VULNERABILIDADE (Pontuação: {pontos})<br>
                    <small>Fatores de Risco: {', '.join(alertas)}</small>
                </div>
            """, unsafe_allow_html=True)

        st.subheader(f"🏠 Ficha de Atendimento: {selecionado}")
        
        # Grid de Detalhes
        grid = st.columns(4)
        for i, col in enumerate(df_geral.columns):
            with grid[i % 4]:
                st.markdown(f'''<div class="info-card">
                    <div class="label-title">{col}</div>
                    <div class="value-text">{principal[col]}</div>
                </div>''', unsafe_allow_html=True)

        st.write("---")
        st.write(f"### 👨‍👩‍👧‍👦 Integrantes no CAS ({len(dados_familia)})")
        st.table(dados_familia[["NOME DO PARTICIPANTE (ATIVIDADES)", "ATIVIDADE DESEJADA", "TURNO", "IDADE (PARTICIPANTE)"]])

    # --- 8. EXPORTAÇÃO ---
    st.sidebar.write("---")
    if st.sidebar.button("➕ Adicionar aos Favoritos"):
        if selecionado != "-- SELECIONE NA LISTA (ORDEM DE RISCO) --":
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

    if st.session_state.lista_exportacao:
        st.sidebar.write(f"Selecionados: {len(st.session_state.lista_exportacao)}")
        if st.sidebar.button("📥 Gerar Planilha de Urgência"):
            df_exp = df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(st.session_state.lista_exportacao)]
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df_exp.to_excel(writer, index=False)
            st.sidebar.download_button("Clique para Baixar", buf.getvalue(), "Urgencia_Social.xlsx")
else:
    st.error("Planilha 'Planilha Matriculados' não encontrada.")
