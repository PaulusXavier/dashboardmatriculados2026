import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO INICIAL
st.set_page_config(page_title="Triagem Estratégica CAS", layout="wide", page_icon="⚖️")

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
    .alerta-vulnerabilidade {
        background-color: #fff1f2; border: 2px solid #be123c; color: #9f1239;
        padding: 15px; border-radius: 10px; font-weight: bold; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LÓGICA DE RANKING ESTRATÉGICO ---
@st.cache_data
def load_and_score_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None, None
    
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Limpeza total
        for col in df.columns:
            df[col] = df[col].fillna("-").astype(str).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', '', ' ', 'NULL'], '-')
        
        df_fam = df[df["NOME DO RESPONSÁVEL"] != "-"].drop_duplicates(subset=["NOME DO RESPONSÁVEL"]).copy()
        
        def calcular_pontuacao_estrategica(row):
            pts = 0
            
            # 1. BLOCO DE TRABALHO (PESO MÁXIMO PARA ORGANIZAR A FILA)
            # Se não trabalha, ganha 1000 pontos para garantir que fique acima de quem trabalha
            trabalha = str(row["EXERCE ATIVIDADE REMUNERADA:"])
            if "NÃO" in trabalha: 
                pts += 1000 
            
            # 2. RENDA (PESO DE ESCALA)
            renda = str(row["RENDA FAMILIAR TOTAL"])
            if "ATÉ R$ 606" in renda or "DE R$ 606" in renda: pts += 500
            elif "DE R$ 607" in renda: pts += 200
            
            # 3. NÚMERO DE PESSOAS NA CASA
            membros = len(df[df["NOME DO RESPONSÁVEL"] == row["NOME DO RESPONSÁVEL"]])
            pts += (membros * 20)
            
            # 4. IDOSO
            try:
                idade = int(''.join(filter(str.isdigit, str(row["IDADE DO RESPONSÁVEL"]))))
                if idade >= 60: pts += 50
            except: pass
            
            # 5. PCD
            if "SIM" in str(row["PESSOA COM DEFICIÊNCIA (RESPONSÁVEL)"]) or "SIM" in str(row["PCD (PARTICIPANTE)"]):
                pts += 50
                
            return pts, membros

        resultados = df_fam.apply(calcular_pontuacao_estrategica, axis=1)
        df_fam["PONTUACAO"], df_fam["QTD_MEMBROS"] = zip(*resultados)
        
        # ORDENAÇÃO FINAL: Do maior risco (Desempregado + Pobre) para o menor
        df_fam = df_fam.sort_values(by="PONTUACAO", ascending=False)
        
        return df, df_fam
    except Exception as e:
        st.error(f"Erro: {e}")
        return None, None

df_geral, df_fam = load_and_score_data()

if df_geral is not None:
    # --- 4. INTERFACE ---
    st.markdown('<div class="main-header"><h1>Painel de Priorização Social CAS</h1></div>', unsafe_allow_html=True)
    
    st.info("📌 **ORDEM DE PRIORIDADE:** 1º Desempregados (por renda) ➔ 2º Empregados (por renda) ➔ Critérios de Família/PcD/Idoso.")

    # Dropdown Principal
    lista_nomes = df_fam["NOME DO RESPONSÁVEL"].tolist()
    selecionado = st.selectbox("🎯 Localizar Responsável (Ordenado pela Nova Regra):", ["-- SELECIONE PARA ANALISAR --"] + lista_nomes)

    if selecionado != "-- SELECIONE PARA ANALISAR --":
        st.divider()
        
        dados_f = df_geral[df_geral["NOME DO RESPONSÁVEL"] == selecionado]
        resumo = df_fam[df_fam["NOME DO RESPONSÁVEL"] == selecionado].iloc[0]

        # MENSAGEM DE ALERTA DE VULNERABILIDADE
        situacao_trab = "DESEMPREGADO(A)" if "NÃO" in resumo["EXERCE ATIVIDADE REMUNERADA:"] else "TRABALHANDO"
        st.markdown(f"""
            <div class="alerta-vulnerabilidade">
                🚨 ANÁLISE DE RISCO: {selecionado}<br>
                <span style='font-size:0.85rem; font-weight:normal;'>
                Status: {situacao_trab} | Renda: {resumo['RENDA FAMILIAR TOTAL']} | Família: {resumo['QTD_MEMBROS']} pessoas.
                </span>
            </div>
        """, unsafe_allow_html=True)

        # Exibição do Prontuário em Grid
        st.subheader("📖 Ficha Socioeconômica")
        grid = st.columns(4)
        for i, col in enumerate(df_geral.columns):
            with grid[i % 4]:
                st.markdown(f'''<div class="info-card">
                    <div class="label-title">{col}</div>
                    <div class="value-text">{dados_f.iloc[0][col]}</div>
                </div>''', unsafe_allow_html=True)

        st.write("---")
        st.write(f"### 👨‍👩‍👧‍👦 Composição Familiar ({len(dados_f)} integrantes)")
        st.table(dados_f[["NOME DO PARTICIPANTE (ATIVIDADES)", "ATIVIDADE DESEJADA", "IDADE (PARTICIPANTE)"]])

    # --- 5. EXPORTAÇÃO (LATERAL) ---
    st.sidebar.header("📋 Relatório de Urgência")
    if st.sidebar.button("➕ Adicionar à Lista"):
        if selecionado != "-- SELECIONE PARA ANALISAR --":
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

    if st.session_state.lista_exportacao:
        st.sidebar.write(f"Selecionados: {len(st.session_state.lista_exportacao)}")
        if st.sidebar.button("📥 Baixar Excel"):
            df_exp = df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(st.session_state.lista_exportacao)]
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df_exp.to_excel(writer, index=False)
            st.sidebar.download_button("Salvar Relatório", buf.getvalue(), "Relatorio_Prioridade_CAS.xlsx")
else:
    st.warning("Verifique se o arquivo 'Planilha Matriculados' está na mesma pasta do código.")
