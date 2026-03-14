import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão CAS - Visão 360", layout="wide", page_icon="🏠")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f1f5f9; }
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #3b82f6 100%);
        padding: 1.5rem; border-radius: 0.8rem; color: white; text-align: center; margin-bottom: 2rem;
    }
    .section-header {
        background-color: #ffffff; padding: 10px 15px; border-left: 5px solid #2563eb;
        border-radius: 4px; font-weight: 800; color: #1e293b; margin: 25px 0 10px 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .info-card {
        background: white; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0;
        margin-bottom: 8px; min-height: 75px; display: flex; flex-direction: column;
    }
    .label-title { color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; }
    .value-text { color: #1e293b; font-size: 0.85rem; font-weight: 600; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LOGICA DE RANKING ---
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
        
        # Ranking de vulnerabilidade para organizar a lista
        def calcular_rank(row):
            pts = 0
            membros = len(df[df["NOME DO RESPONSÁVEL"] == row["NOME DO RESPONSÁVEL"]])
            pts += (membros * 10)
            if "NÃO" in str(row.get("EXERCE ATIVIDADE REMUNERADA:", "")): pts += 50
            if "ATÉ R$ 606" in str(row.get("RENDA FAMILIAR TOTAL", "")): pts += 40
            return pts
        
        df_fam["RANK"] = df_fam.apply(calcular_rank, axis=1)
        return df, df_fam
    except Exception as e:
        st.error(f"Erro: {e}")
        return None, None

df_geral, df_fam = load_data()

if df_geral is not None:
    # --- 4. SEU CRUZAMENTO (FILTROS NA ESQUERDA) ---
    st.sidebar.header("🛠️ Cruzamento Manual")
    op_trab = sorted(df_fam["EXERCE ATIVIDADE REMUNERADA:"].unique())
    op_renda = sorted(df_fam["RENDA FAMILIAR TOTAL"].unique())
    
    f_trab = st.sidebar.multiselect("Status de Trabalho:", op_trab, default=op_trab)
    f_renda = st.sidebar.multiselect("Faixa de Renda:", op_renda, default=op_renda)

    df_filtrado = df_fam[
        (df_fam["EXERCE ATIVIDADE REMUNERADA:"].isin(f_trab)) & 
        (df_fam["RENDA FAMILIAR TOTAL"].isin(f_renda))
    ].sort_values(by="RANK", ascending=False)

    # --- 5. TÍTULO E BUSCA ---
    st.markdown('<div class="main-header"><h1>Painel de Avaliação Social CAS</h1></div>', unsafe_allow_html=True)
    
    lista_nomes = df_filtrado["NOME DO RESPONSÁVEL"].tolist()
    selecionado = st.selectbox(f"🎯 Famílias Filtradas: {len(lista_nomes)} (Ordenadas por Risco)", ["-- SELECIONE --"] + lista_nomes)

    if selecionado != "-- SELECIONE --":
        # Dados da Família
        dados_f = df_geral[df_geral["NOME DO RESPONSÁVEL"] == selecionado]
        principal = dados_f.iloc[0]

        # --- QUADRO 1: RESPONSÁVEL E LOCALIZAÇÃO (O QUE VOCÊ QUER PRIMEIRO) ---
        st.markdown('<div class="section-header">📍 DADOS DO RESPONSÁVEL E LOCALIZAÇÃO</div>', unsafe_allow_html=True)
        
        # Colunas prioritárias de identificação
        cols_id = ["NOME DO RESPONSÁVEL", "IDADE DO RESPONSÁVEL", "ENDEREÇO", "BAIRRO", "CONTATO", "CPF", "PESSOA COM DEFICIÊNCIA (RESPONSÁVEL)"]
        cols_id = [c for c in cols_id if c in df_geral.columns] # Garante que a coluna existe
        
        c_id = st.columns(4)
        for i, col in enumerate(cols_id):
            with c_id[i % 4]:
                st.markdown(f'<div class="info-card"><div class="label-title">{col}</div><div class="value-text">{principal[col]}</div></div>', unsafe_allow_html=True)

        # --- QUADRO 2: DEMAIS DADOS SOCIOECONÔMICOS ---
        st.markdown('<div class="section-header">⚖️ PERFIL SOCIOECONÔMICO DA FAMÍLIA</div>', unsafe_allow_html=True)
        
        # Mostra o restante das colunas que não apareceram no quadro anterior, exceto as do participante
        cols_socio = [c for c in df_geral.columns if c not in cols_id and "PARTICIPANTE" not in c and "ATIVIDADE" not in c]
        
        if cols_socio:
            c_soc = st.columns(4)
            for i, col in enumerate(cols_socio):
                with c_soc[i % 4]:
                    st.markdown(f'<div class="info-card"><div class="label-title">{col}</div><div class="value-text">{principal[col]}</div></div>', unsafe_allow_html=True)

        # --- QUADRO 3: DADOS DOS PARTICIPANTES (POR ÚLTIMO) ---
        st.markdown('<div class="section-header">👨‍👩‍👧‍👦 DADOS DOS PARTICIPANTES VINCULADOS</div>', unsafe_allow_html=True)
        
        # Filtrando apenas colunas que mencionam participante ou atividade
        cols_part = [c for c in df_geral.columns if "PARTICIPANTE" in c or "ATIVIDADE" in c or "TURNO" in c]
        if not cols_part: cols_part = df_geral.columns # Backup caso as colunas tenham nomes diferentes
        
        st.dataframe(dados_f[cols_part], use_container_width=True)

    # --- 6. EXPORTAÇÃO ---
    st.sidebar.write("---")
    if st.sidebar.button("➕ Adicionar à Lista"):
        if selecionado != "-- SELECIONE --":
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

    if st.session_state.lista_exportacao:
        st.sidebar.write(f"Itens selecionados: {len(st.session_state.lista_exportacao)}")
        if st.sidebar.button("📥 Baixar Excel"):
            df_exp = df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(st.session_state.lista_exportacao)]
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df_exp.to_excel(writer, index=False)
            st.sidebar.download_button("Clique aqui", buf.getvalue(), "Relatorio_CAS.xlsx")
else:
    st.info("Planilha 'Planilha Matriculados' não encontrada na pasta.")
