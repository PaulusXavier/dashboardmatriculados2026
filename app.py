import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO INICIAL
st.set_page_config(page_title="Gestão Vulnerabilidade CAS", layout="wide", page_icon="⚖️")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #b91c1c 100%);
        padding: 2rem; border-radius: 1rem; color: white; text-align: center; margin-bottom: 2rem;
    }
    .info-card {
        background: white; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0;
        margin-bottom: 8px; min-height: 70px;
    }
    .label-title { color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; }
    .value-text { color: #1e293b; font-size: 0.85rem; font-weight: 600; margin-top: 4px; }
    .status-alerta-critico {
        background-color: #fff1f2; border: 2px solid #be123c; color: #9f1239;
        padding: 20px; border-radius: 12px; font-weight: bold; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E CÁLCULO DE VULNERABILIDADE (NOVA HIERARQUIA) ---
@st.cache_data
def load_and_score_data():
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
        
        def calcular_vulnerabilidade(row):
            pts = 0
            
            # 1. CRITÉRIO: RENDA (PESO 1)
            renda_texto = str(row["RENDA FAMILIAR TOTAL"])
            if "ATÉ R$ 606" in renda_texto or "DE R$ 606" in renda_texto: pts += 40
            elif "DE R$ 607" in renda_texto: pts += 20
            
            # 2. CRITÉRIO: QUANTIDADE DE PESSOAS NA CASA (PESO 2)
            membros = len(df[df["NOME DO RESPONSÁVEL"] == row["NOME DO RESPONSÁVEL"]])
            pts += (membros * 8) # 8 pontos por pessoa
            
            # 3. CRITÉRIO: TRABALHANDO OU NÃO (PESO 3)
            if "NÃO" in str(row["EXERCE ATIVIDADE REMUNERADA:"]): pts += 15
            
            # 4. CRITÉRIO: IDOSO (PESO 4)
            try:
                idade = int(''.join(filter(str.isdigit, str(row["IDADE DO RESPONSÁVEL"]))))
                if idade >= 60: pts += 10
            except: pass
            
            # 5. CRITÉRIO: PCD (PESO 5)
            if "SIM" in str(row["PESSOA COM DEFICIÊNCIA (RESPONSÁVEL)"]) or "SIM" in str(row["PCD (PARTICIPANTE)"]):
                pts += 10
                
            return pts, membros

        resultados = df_fam.apply(calcular_vulnerabilidade, axis=1)
        df_fam["PONTUACAO"], df_fam["QTD_MEMBROS"] = zip(*resultados)
        
        # Ordenação pela nova regra
        df_fam = df_fam.sort_values(by="PONTUACAO", ascending=False)
        
        return df, df_fam
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        return None, None

df_geral, df_fam = load_and_score_data()

if df_geral is not None:
    # --- 4. FILTROS ---
    st.sidebar.header("🔍 Triagem Social")
    f_renda = st.sidebar.multiselect("Renda:", sorted(df_fam["RENDA FAMILIAR TOTAL"].unique()), default=list(df_fam["RENDA FAMILIAR TOTAL"].unique()))
    f_trab = st.sidebar.multiselect("Trabalha?", sorted(df_fam["EXERCE ATIVIDADE REMUNERADA:"].unique()), default=list(df_fam["EXERCE ATIVIDADE REMUNERADA:"].unique()))
    
    df_filtrado = df_fam[(df_fam["RENDA FAMILIAR TOTAL"].isin(f_renda)) & (df_fam["EXERCE ATIVIDADE REMUNERADA:"].isin(f_trab))]

    # --- 5. INTERFACE ---
    st.markdown('<div class="main-header"><h1>Panorama de Vulnerabilidade Social CAS</h1></div>', unsafe_allow_html=True)
    
    st.info("📊 Ranking Atualizado: A renda e o número de pessoas na casa agora definem o topo da lista.")
    
    lista_nomes = df_filtrado["NOME DO RESPONSÁVEL"].tolist()
    selecionado = st.selectbox("🎯 Selecionar Família (Prioridade por Renda/Tamanho):", ["-- SELECIONE --"] + lista_nomes)

    if selecionado != "-- SELECIONE --":
        st.divider()
        dados_f = df_geral[df_geral["NOME DO RESPONSÁVEL"] == selecionado]
        resumo = df_fam[df_fam["NOME DO RESPONSÁVEL"] == selecionado].iloc[0]
        
        # MENSAGEM DE ALERTA BASEADA NA NOVA REGRA
        if resumo["PONTUACAO"] > 50:
            st.markdown(f"""
                <div class="status-alerta-critico">
                    🚨 ALERTA DE VULNERABILIDADE CRÍTICA<br>
                    <span style='font-size:0.85rem; font-weight:normal;'>
                    Motivo: Renda Baixa aliada a família de {resumo['QTD_MEMBROS']} pessoas.
                    </span>
                </div>
            """, unsafe_allow_html=True)

        st.subheader(f"🏠 Prontuário: {selecionado}")
        grid = st.columns(4)
        for i, col in enumerate(df_geral.columns):
            with grid[i % 4]:
                st.markdown(f'''<div class="info-card">
                    <div class="label-title">{col}</div>
                    <div class="value-text">{dados_f.iloc[0][col]}</div>
                </div>''', unsafe_allow_html=True)

        st.write("---")
        st.write(f"### 👨‍👩‍👧‍👦 Membros da Família ({len(dados_f)})")
        st.table(dados_f[["NOME DO PARTICIPANTE (ATIVIDADES)", "ATIVIDADE DESEJADA", "TURNO", "IDADE (PARTICIPANTE)"]])

    # --- 6. EXPORTAÇÃO ---
    st.sidebar.write("---")
    if st.sidebar.button("🚀 Adicionar à Lista de Prioridade"):
        if selecionado != "-- SELECIONE --":
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

    if st.session_state.lista_exportacao:
        st.sidebar.write(f"Selecionados: {len(st.session_state.lista_exportacao)}")
        if st.sidebar.button("📥 Baixar Planilha de Urgência"):
            df_exp = df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(st.session_state.lista_exportacao)]
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df_exp.to_excel(writer, index=False)
            st.sidebar.download_button("Salvar Excel", buf.getvalue(), "Relatorio_Prioridade.xlsx")
else:
    st.warning("Aguardando arquivo 'Planilha Matriculados'...")
