import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Socioeconômico Famílias CAS", layout="wide", page_icon="🏠")

# Inicializa lista de exportação se não existir
if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN DE PRONTUÁRIO SOCIAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f1f5f9; }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%);
        padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;
    }
    .info-card {
        background: white; padding: 10px; border-radius: 8px; border-bottom: 3px solid #cbd5e1;
        margin-bottom: 8px; min-height: 65px;
    }
    .label-title { color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; }
    .value-text { color: #0f172a; font-size: 0.85rem; font-weight: 600; margin-top: 2px; }
    .status-alerta {
        background-color: #fef2f2; border: 1px solid #f87171; color: #991b1b;
        padding: 15px; border-radius: 10px; font-weight: bold; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. PROCESSAMENTO DE DADOS (LÓGICA UNIFICADA) ---
@st.cache_data
def load_and_clean_data():
    # Busca por arquivos Excel ou CSV na pasta
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos:
        return None, None
    
    path = arquivos[0]
    try:
        # Carrega os dados
        if path.endswith('.csv'):
            df = pd.read_csv(path, dtype=str)
        else:
            df = pd.read_excel(path, dtype=str)
        
        # Padroniza nomes das colunas (Maiúsculas e sem espaços)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Limpeza Geral: Remove espaços e troca vazios/NaN por "-"
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', '', ' ', 'NULL'], '-')
        
        # CRIAÇÃO DA BASE DE FAMÍLIAS (292 Responsáveis Únicos)
        # Removemos duplicatas para ter 1 linha por família nas estatísticas e filtros
        df_familias = df[df["NOME DO RESPONSÁVEL"] != "-"].drop_duplicates(subset=["NOME DO RESPONSÁVEL"])
        
        return df, df_familias
    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
        return None, None

df_geral, df_familias = load_and_clean_data()

if df_geral is not None:
    # --- 4. BARRA LATERAL: FILTROS DE VULNERABILIDADE ---
    st.sidebar.header("🔍 Triagem Socioeconômica")
    
    # Identificando colunas chave (ajustado para bater com sua planilha)
    col_trab = "EXERCE ATIVIDADE REMUNERADA:"
    col_renda = "RENDA FAMILIAR TOTAL"
    col_benef = [c for c in df_geral.columns if "BENEFÍCIO" in c][0] # Busca dinâmica

    f_trab = st.sidebar.multiselect("Trabalha?", sorted(df_familias[col_trab].unique()), default=list(df_familias[col_trab].unique()))
    f_renda = st.sidebar.multiselect("Renda Familiar:", sorted(df_familias[col_renda].unique()), default=list(df_familias[col_renda].unique()))
    f_benef = st.sidebar.multiselect("Recebe Benefício?", sorted(df_familias[col_benef].unique()), default=list(df_familias[col_benef].unique()))

    # Aplicação do Filtro
    df_filtrado = df_familias[
        (df_familias[col_trab].isin(f_trab)) & 
        (df_familias[col_renda].isin(f_renda)) &
        (df_familias[col_benef].isin(f_benef))
    ].copy()

    # Lógica de Vulnerabilidade: Quem está "NÃO" em trabalho e "NÃO" em benefício vai para o topo
    def calcular_risco(row):
        if "NÃO" in str(row[col_trab]) and "NÃO" in str(row[col_benef]):
            return 0 # Risco Alto
        return 1

    df_filtrado['ORDEM_RISCO'] = df_filtrado.apply(calcular_risco, axis=1)
    df_filtrado = df_filtrado.sort_values('ORDEM_RISCO')

    # --- 5. CABEÇALHO E MÉTRICAS ---
    st.markdown('<div class="main-header"><h1>Socioeconômico Famílias CAS</h1></div>', unsafe_allow_html=True)
    
    m1, m2 = st.columns(2)
    m1.metric("Unidades Familiares (Responsáveis)", len(df_filtrado))
    m2.metric("Matrículas Vinculadas ao Grupo", len(df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(df_filtrado["NOME DO RESPONSÁVEL"])]))

    # Seleção do Responsável
    lista_final_nomes = [n for n in df_filtrado["NOME DO RESPONSÁVEL"].tolist() if n != "-"]
    selecionado = st.selectbox("🎯 Selecione o Responsável para Prontuário Social:", ["-- SELECIONE UM NOME NA LISTA --"] + lista_final_nomes)

    # --- 6. PRONTUÁRIO SOCIAL DETALHADO ---
    if selecionado != "-- SELECIONE UM NOME NA LISTA --":
        st.write("---")
        
        # Dados da Família
        familia_data = df_geral[df_geral["NOME DO RESPONSÁVEL"] == selecionado]
        dados_base = familia_data.iloc[0]

        # Alerta visual de Risco
        if "NÃO" in dados_base[col_trab] and "NÃO" in dados_base[col_benef]:
            st.markdown(f'<div class="status-alerta">🚨 ALERTA SOCIAL: Família sem atividade remunerada e sem benefícios. Prioridade de Atendimento.</div>', unsafe_allow_html=True)

        c_tit, c_exp = st.columns([3, 1])
        c_tit.subheader(f"🏠 Unidade Familiar: {selecionado}")
        
        if c_exp.button("🚀 Adicionar à Lista de Exportação"):
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

        # GRID DE DADOS (RAIO-X DE TODAS AS COLUNAS)
        st.write("### 📖 Cadastro Socioeconômico Completo")
        cols_grid = st.columns(4)
        for i, nome_col in enumerate(df_geral.columns):
            with cols_grid[i % 4]:
                st.markdown(f'''<div class="info-card">
                    <div class="label-title">{nome_col}</div>
                    <div class="value-text">{dados_base[nome_col]}</div>
                </div>''', unsafe_allow_html=True)

        # TABELA DE DEPENDENTES
        st.write(f"### 👨‍👩‍👧‍👦 Participantes Matriculados nesta Família ({len(familia_data)})")
        st.table(familia_data[["NOME DO PARTICIPANTE (ATIVIDADES)", "IDADE (PARTICIPANTE)", "ATIVIDADE DESEJADA", "TURNO"]])

    # --- 7. SISTEMA DE EXPORTAÇÃO ---
    if st.session_state.lista_exportacao:
        st.sidebar.write("---")
        st.sidebar.subheader("📦 Relatório Gerado")
        df_saida = df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(st.session_state.lista_exportacao)]
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_saida.to_excel(writer, index=False, sheet_name='Familias_CAS')
        
        st.sidebar.download_button("📥 Baixar Excel das Selecionadas", output.getvalue(), "Relatorio_CAS_Socioeconomico.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        
        if st.sidebar.button("🗑️ Limpar Lista de Seleção"):
            st.session_state.lista_exportacao = []
            st.rerun()

else:
    st.warning("⚠️ Planilha não encontrada. Certifique-se de que o arquivo 'Planilha Matriculados' está na mesma pasta do código.")
