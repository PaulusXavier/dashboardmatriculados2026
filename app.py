import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão CAS - Prontuário Completo", layout="wide", page_icon="🏠")

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
        background-color: #ffffff; padding: 10px 15px; border-left: 5px solid #3b82f6;
        border-radius: 4px; font-weight: 800; color: #1e293b; margin: 25px 0 10px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .info-card {
        background: white; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0;
        margin-bottom: 8px; min-height: 70px; display: flex; flex-direction: column; justify-content: center;
    }
    .label-title { color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; line-height: 1.2; }
    .value-text { color: #1e293b; font-size: 0.85rem; font-weight: 600; margin-top: 5px; }
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
        
        df_fam = df[df["NOME DO RESPONSÁVEL"] != "-"].drop_duplicates(subset=["NOME DO RESPONSÁVEL"]).copy()
        
        # Ranking de vulnerabilidade para a lista lateral
        def rank_vulnerabilidade(row):
            pts = 0
            membros = len(df[df["NOME DO RESPONSÁVEL"] == row["NOME DO RESPONSÁVEL"]])
            pts += (membros * 10)
            if "SIM" in str(row.get("PESSOA COM DEFICIÊNCIA (RESPONSÁVEL)", "")): pts += 50
            if "NÃO" in str(row.get("EXERCE ATIVIDADE REMUNERADA:", "")): pts += 40
            return pts
        
        df_fam["RANKING"] = df_fam.apply(rank_vulnerabilidade, axis=1)
        return df, df_fam
    except Exception as e:
        st.error(f"Erro ao ler os dados: {e}")
        return None, None

df_geral, df_fam = load_data()

if df_geral is not None:
    # --- 4. SEU CRUZAMENTO (FILTROS NA ESQUERDA) ---
    st.sidebar.header("🛠️ Seu Cruzamento")
    col_trab = "EXERCE ATIVIDADE REMUNERADA:"
    col_renda = "RENDA FAMILIAR TOTAL"
    
    f_trab = st.sidebar.multiselect("Status de Trabalho:", sorted(df_fam[col_trab].unique()), default=list(df_fam[col_trab].unique()))
    f_renda = st.sidebar.multiselect("Faixa de Renda:", sorted(df_fam[col_renda].unique()), default=list(df_fam[col_renda].unique()))

    # Aplicar Filtros e Ordenar por Vulnerabilidade
    df_filtrado = df_fam[
        (df_fam[col_trab].isin(f_trab)) & 
        (df_fam[col_renda].isin(f_renda))
    ].sort_values(by="RANKING", ascending=False)

    # --- 5. TÍTULO ---
    st.markdown('<div class="main-header"><h1>Painel Socioeconômico e Familiar CAS</h1></div>', unsafe_allow_html=True)
    
    lista_nomes = df_filtrado["NOME DO RESPONSÁVEL"].tolist()
    selecionado = st.selectbox(f"🎯 Selecione a Família ({len(lista_nomes)} encontradas):", ["-- SELECIONE --"] + lista_nomes)

    if selecionado != "-- SELECIONE --":
        # Puxa todos os registros que contêm esse responsável
        dados_familia = df_geral[df_geral["NOME DO RESPONSÁVEL"] == selecionado]
        # Pega a primeira linha para os dados gerais do responsável/casa
        principal = dados_familia.iloc[0]

        # --- QUADRO 1: DADOS COMPLETOS DO RESPONSÁVEL (Todas as Colunas) ---
        st.markdown(f'<div class="section-header">📑 DADOS COMPLETOS DO RESPONSÁVEL: {selecionado}</div>', unsafe_allow_html=True)
        
        # Cria um grid para mostrar TODAS as colunas que pertencem ao responsável/família
        cols_grid = st.columns(4)
        for i, coluna in enumerate(df_geral.columns):
            with cols_grid[i % 4]:
                st.markdown(f'''
                    <div class="info-card">
                        <div class="label-title">{coluna}</div>
                        <div class="value-text">{principal[coluna]}</div>
                    </div>
                ''', unsafe_allow_html=True)

        # --- QUADRO 2: DADOS DOS PARTICIPANTES (Todos os familiares) ---
        st.markdown('<div class="section-header">👨‍👩‍👧‍👦 MEMBROS DA FAMÍLIA E PARTICIPAÇÃO NO CAS</div>', unsafe_allow_html=True)
        
        # Mostra a tabela completa dos familiares vinculados
        # Aqui ele mostra todas as colunas relevantes para os participantes
        st.dataframe(dados_familia, use_container_width=True)
        
        st.write("---")
        st.write("💡 *Dica: Você pode rolar a tabela acima para os lados para ver todas as colunas de cada participante.*")

    # --- 6. EXPORTAÇÃO ---
    st.sidebar.write("---")
    if st.sidebar.button("➕ Adicionar para Relatório"):
        if selecionado != "-- SELECIONE --":
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

    if st.session_state.lista_exportacao:
        st.sidebar.success(f"{len(st.session_state.lista_exportacao)} famílias prontas")
        if st.sidebar.button("📥 Gerar Excel Completo"):
            df_exp = df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(st.session_state.lista_exportacao)]
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                df_exp.to_excel(writer, index=False)
            st.sidebar.download_button("Baixar Arquivo", buf.getvalue(), "Relatorio_Familiar_Completo.xlsx")
else:
    st.info("Arquivo 'Planilha Matriculados' não encontrado.")
