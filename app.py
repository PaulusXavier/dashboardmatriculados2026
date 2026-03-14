import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO INICIAL
st.set_page_config(page_title="Triagem de Vulnerabilidade CAS", layout="wide", page_icon="⚖️")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN E ALERTAS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #dc2626 100%);
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

# --- 3. CARREGAMENTO E CÁLCULO DE VULNERABILIDADE ---
@st.cache_data
def load_and_score_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None, None
    
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Limpeza
        for col in df.columns:
            df[col] = df[col].fillna("-").astype(str).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', '', ' ', 'NULL'], '-')
        
        # Criar base de famílias
        df_fam = df[df["NOME DO RESPONSÁVEL"] != "-"].drop_duplicates(subset=["NOME DO RESPONSÁVEL"]).copy()
        
        # Função de Pontuação conforme sua solicitação
        def calcular_vulnerabilidade(row):
            pts = 0
            # 1. Trabalho (Peso Principal)
            if "NÃO" in str(row["EXERCE ATIVIDADE REMUNERADA:"]): pts += 30
            
            # 2. Renda Familiar
            if "DE R$ 606" in str(row["RENDA FAMILIAR TOTAL"]) or "ATÉ R$ 606" in str(row["RENDA FAMILIAR TOTAL"]): pts += 25
            elif "DE R$ 607" in str(row["RENDA FAMILIAR TOTAL"]): pts += 15
            
            # 3. Número de pessoas no domicílio (Contagem direta na planilha geral)
            membros = len(df[df["NOME DO RESPONSÁVEL"] == row["NOME DO RESPONSÁVEL"]])
            pts += (membros * 5) # 5 pontos por pessoa na casa
            
            # 4. Idoso (Baseado na idade do responsável ou colunas de idoso)
            try:
                idade = int(''.join(filter(str.isdigit, str(row["IDADE DO RESPONSÁVEL"]))))
                if idade >= 60: pts += 20
            except: pass
            
            # 5. PcD (Pessoa com Deficiência)
            if "SIM" in str(row["PESSOA COM DEFICIÊNCIA (RESPONSÁVEL)"]) or "SIM" in str(row["PCD (PARTICIPANTE)"]):
                pts += 25
                
            return pts, membros

        # Aplicar pontuação
        resultados = df_fam.apply(calcular_vulnerabilidade, axis=1)
        df_fam["PONTUACAO"], df_fam["QTD_MEMBROS"] = zip(*resultados)
        
        # Ordenar: Maior pontuação primeiro
        df_fam = df_fam.sort_values(by="PONTUACAO", ascending=False)
        
        return df, df_fam
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        return None, None

df_geral, df_fam = load_and_score_data()

if df_geral is not None:
    # --- 4. FILTROS LATERAIS ---
    st.sidebar.header("⚖️ Filtros de Prioridade")
    f_trab = st.sidebar.multiselect("Trabalhando?", sorted(df_fam["EXERCE ATIVIDADE REMUNERADA:"].unique()), default=list(df_fam["EXERCE ATIVIDADE REMUNERADA:"].unique()))
    f_renda = st.sidebar.multiselect("Renda?", sorted(df_fam["RENDA FAMILIAR TOTAL"].unique()), default=list(df_fam["RENDA FAMILIAR TOTAL"].unique()))
    
    df_filtrado = df_fam[(df_fam["EXERCE ATIVIDADE REMUNERADA:"].isin(f_trab)) & (df_fam["RENDA FAMILIAR TOTAL"].isin(f_renda))]

    # --- 5. INTERFACE PRINCIPAL ---
    st.markdown('<div class="main-header"><h1>Panorama de Vulnerabilidade CAS</h1></div>', unsafe_allow_html=True)
    
    st.info("📊 A lista abaixo está organizada automaticamente: Quem mais precisa de atenção aparece primeiro.")
    
    # Dropdown de Nomes
    lista_nomes = df_filtrado["NOME DO RESPONSÁVEL"].tolist()
    selecionado = st.selectbox("🎯 Selecionar Família (Ordenada por Risco):", ["-- SELECIONE --"] + lista_nomes)

    if selecionado != "-- SELECIONE --":
        st.divider()
        
        # Coleta dados para o Alerta
        dados_f = df_geral[df_geral["NOME DO RESPONSÁVEL"] == selecionado]
        resumo = df_fam[df_fam["NOME DO RESPONSÁVEL"] == selecionado].iloc[0]
        
        # MENSAGEM DE ALERTA DE VULNERABILIDADE
        if resumo["PONTUACAO"] > 40:
            motivos = []
            if "NÃO" in resumo["EXERCE ATIVIDADE REMUNERADA:"]: motivos.append("Desemprego")
            if resumo["QTD_MEMBROS"] > 3: motivos.append(f"Família Numerosa ({resumo['QTD_MEMBROS']} pessoas)")
            if "SIM" in str(resumo["PESSOA COM DEFICIÊNCIA (RESPONSÁVEL)"]): motivos.append("Presença de PcD")
            
            st.markdown(f"""
                <div class="status-alerta-critico">
                    🚨 ATENÇÃO: Família em Alta Vulnerabilidade!<br>
                    <span style='font-size:0.9rem; font-weight:normal;'>
                    Pontuação de Risco: {resumo['PONTUACAO']} | Fatores detectados: {', '.join(motivos)}
                    </span>
                </div>
            """, unsafe_allow_html=True)

        # Exibição do Prontuário
        st.subheader(f"🏠 Ficha: {selecionado}")
        grid = st.columns(4)
        for i, col in enumerate(df_geral.columns):
            with grid[i % 4]:
                st.markdown(f'''<div class="info-card">
                    <div class="label-title">{col}</div>
                    <div class="value-text">{dados_f.iloc[0][col]}</div>
                </div>''', unsafe_allow_html=True)

        st.write("---")
        st.write(f"### 👨‍👩‍👧‍👦 Pessoas no Domicílio ({len(dados_f)})")
        st.table(dados_f[["NOME DO PARTICIPANTE (ATIVIDADES)", "ATIVIDADE DESEJADA", "IDADE (PARTICIPANTE)"]])

    # --- 6. EXPORTAÇÃO ---
    st.sidebar.write("---")
    if st.sidebar.button("🚀 Adicionar à Lista de Urgência"):
        if selecionado != "-- SELECIONE --":
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

    if st.session_state.lista_exportacao:
        st.sidebar.write(f"Na lista: {len(st.session_state.lista_exportacao)}")
        if st.sidebar.button("📥 Baixar Excel de Urgência"):
            df_exp = df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(st.session_state.lista_exportacao)]
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df_exp.to_excel(writer, index=False)
            st.sidebar.download_button("Clique aqui para salvar", buf.getvalue(), "Urgencia_Social.xlsx")
else:
    st.warning("Verifique se o arquivo 'Planilha Matriculados' está na pasta.")
