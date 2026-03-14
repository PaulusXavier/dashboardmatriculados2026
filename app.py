import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO INICIAL
st.set_page_config(page_title="Gestão CAS - Painel do Gestor", layout="wide", page_icon="⚖️")

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
    .alerta-vulnerabilidade {
        background-color: #fff1f2; border-left: 5px solid #ef4444; color: #991b1b;
        padding: 15px; border-radius: 8px; font-weight: bold; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E CÁLCULO DE PESO PARA O RANKING ---
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
        
        df_fam = df[df["NOME DO RESPONSÁVEL"] != "-"].drop_duplicates(subset=["NOME DO RESPONSÁVEL"]).copy()
        
        # Ranking interno (para organizar a lista que você filtrará)
        def calcular_prioridade_interna(row):
            pts = 0
            membros = len(df[df["NOME DO RESPONSÁVEL"] == row["NOME DO RESPONSÁVEL"]])
            pts += (membros * 10)
            if "SIM" in str(row["PESSOA COM DEFICIÊNCIA (RESPONSÁVEL)"]) or "SIM" in str(row["PCD (PARTICIPANTE)"]): pts += 50
            try:
                idade = int(''.join(filter(str.isdigit, str(row["IDADE DO RESPONSÁVEL"]))))
                if idade >= 60: pts += 30
            except: pass
            return pts, membros

        df_fam["PONTOS"], df_fam["QTD_MEMBROS"] = zip(*df_fam.apply(calcular_prioridade_interna, axis=1))
        return df, df_fam
    except Exception as e:
        st.error(f"Erro: {e}")
        return None, None

df_geral, df_fam = load_data()

if df_geral is not None:
    # --- 4. FILTROS LATERAIS (VOCÊ FAZ O CRUZAMENTO AQUI) ---
    st.sidebar.header("🛠️ Seu Cruzamento de Dados")
    
    # Filtro 1: Trabalho
    opcoes_trab = sorted(df_fam["EXERCE ATIVIDADE REMUNERADA:"].unique())
    f_trab = st.sidebar.multiselect("1. Status de Trabalho:", opcoes_trab, default=opcoes_trab)
    
    # Filtro 2: Renda
    opcoes_renda = sorted(df_fam["RENDA FAMILIAR TOTAL"].unique())
    f_renda = st.sidebar.multiselect("2. Faixa de Renda:", opcoes_renda, default=opcoes_renda)

    # Aplicação do seu cruzamento manual
    df_filtrado = df_fam[
        (df_fam["EXERCE ATIVIDADE REMUNERADA:"].isin(f_trab)) & 
        (df_fam["RENDA FAMILIAR TOTAL"].isin(f_renda))
    ].sort_values(by="PONTOS", ascending=False)

    # --- 5. INTERFACE PRINCIPAL ---
    st.markdown('<div class="main-header"><h1>Painel de Gestão e Cruzamento CAS</h1></div>', unsafe_allow_html=True)
    
    st.write(f"🔍 Resultado do seu cruzamento: **{len(df_filtrado)} famílias encontradas.**")
    
    # Dropdown de nomes (já organizado pela maior vulnerabilidade dentro do seu filtro)
    lista_nomes = df_filtrado["NOME DO RESPONSÁVEL"].tolist()
    selecionado = st.selectbox("🎯 Selecionar Família para Analisar Prontuário:", ["-- SELECIONE NA LISTA --"] + lista_nomes)

    if selecionado != "-- SELECIONE NA LISTA --":
        st.divider()
        dados_f = df_geral[df_geral["NOME DO RESPONSÁVEL"] == selecionado]
        resumo = df_fam[df_fam["NOME DO RESPONSÁVEL"] == selecionado].iloc[0]

        # Alerta Automático de Vulnerabilidade
        if resumo["PONTOS"] > 30:
            st.markdown(f"""
                <div class="alerta-vulnerabilidade">
                    🚨 ANÁLISE DE VULNERABILIDADE: {selecionado}<br>
                    <span style='font-size:0.85rem; font-weight:normal;'>
                    Renda: {resumo['RENDA FAMILIAR TOTAL']} | Membros: {resumo['QTD_MEMBROS']} | Pontuação Interna: {resumo['PONTOS']}
                    </span>
                </div>
            """, unsafe_allow_html=True)

        # Ficha Técnica
        st.subheader("📖 Prontuário Completo")
        grid = st.columns(4)
        for i, col in enumerate(df_geral.columns):
            with grid[i % 4]:
                st.markdown(f'''<div class="info-card">
                    <div class="label-title">{col}</div>
                    <div class="value-text">{dados_f.iloc[0][col]}</div>
                </div>''', unsafe_allow_html=True)

        st.write("---")
        st.write(f"### 👨‍👩‍👧‍👦 Integrantes no CAS ({len(dados_f)})")
        st.table(dados_f[["NOME DO PARTICIPANTE (ATIVIDADES)", "ATIVIDADE DESEJADA", "IDADE (PARTICIPANTE)"]])

    # --- 6. EXPORTAÇÃO ---
    st.sidebar.write("---")
    if st.sidebar.button("➕ Adicionar aos Favoritos"):
        if selecionado != "-- SELECIONE NA LISTA --":
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

    if st.session_state.lista_exportacao:
        st.sidebar.write(f"📦 Itens na lista: {len(st.session_state.lista_exportacao)}")
        if st.sidebar.button("📥 Baixar Relatório"):
            df_exp = df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(st.session_state.lista_exportacao)]
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df_exp.to_excel(writer, index=False)
            st.sidebar.download_button("Salvar em Excel", buf.getvalue(), "Cruzamento_CAS.xlsx")
else:
    st.info("Aguardando arquivo 'Planilha Matriculados'...")
