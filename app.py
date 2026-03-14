import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão de Vulnerabilidade CAS", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .card-vulnerabilidade {
        background-color: #f1f5f9;
        padding: 20px;
        border-radius: 12px;
        border-left: 8px solid #1e3a8a;
        margin-bottom: 15px;
    }
    .texto-preto { color: #000000 !important; font-size: 16px; font-weight: 600; }
    .titulo-card { color: #1e3a8a !important; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
    /* Estilo para a lista de seleção */
    .stCheckbox { background-color: #f8fafc; padding: 5px; border-radius: 5px; border: 1px solid #e2e8f0; margin-bottom: 2px; }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO DOS DADOS (COM TRATAMENTO DE ERRO DE NOME)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def carregar_dados():
    # Lista de nomes que o arquivo pode ter assumido no servidor
    nomes_possiveis = [
        "Planilha Matriculados.xlsx - Planilha1.csv",
        "Planilha Matriculados.xlsx",
        "Planilha_Matriculados.csv"
    ]
    
    for nome in nomes_possiveis:
        caminho = os.path.join(BASE_DIR, nome)
        if os.path.exists(caminho):
            try:
                if nome.endswith('.csv'):
                    df = pd.read_csv(caminho, dtype=str)
                else:
                    df = pd.read_excel(caminho, dtype=str)
                # Limpa nomes de colunas
                df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
                return df
            except:
                continue
    return None

df_geral = carregar_dados()

if df_geral is not None:
    # Colunas base
    col_t = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trabalha = "EXERCE ATIVIDADE REMUNERADA:"

    # Base de Responsáveis (Apenas linhas onde a Coluna T está preenchida)
    df_responsaveis = df_geral[df_geral[col_t].notna() & (df_geral[col_t].str.strip() != "")].copy()

    st.title("📋 Seleção e Exportação de Famílias em Vulnerabilidade")
    st.info(f"Foram identificadas {len(df_responsaveis)} famílias na base de dados.")

    # --- FILTROS LATERAIS ---
    st.sidebar.header("🎯 Critérios de Triagem")
    
    # Filtro de Renda
    rendas = ["Todos"] + sorted(df_responsaveis[col_renda].unique().astype(str).tolist())
    f_renda = st.sidebar.selectbox("Renda Familiar:", rendas)
    
    # Filtro de Atividade Remunerada
    trampos = ["Todos"] + sorted(df_responsaveis[col_trabalha].unique().astype(str).tolist())
    f_trampo = st.sidebar.selectbox("Trabalha?", trampos)

    # Aplicar Filtros
    df_filtrado = df_responsaveis.copy()
    if f_renda != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_renda] == f_renda]
    if f_trampo != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_trabalha] == f_trampo]

    # --- LISTA PARA MARCAÇÃO ---
    st.subheader(f"✅ Marque as famílias para exportar ({len(df_filtrado)} encontradas)")
    
    # Usar session_state para guardar as seleções
    if 'selecionados' not in st.session_state:
        st.session_state.selecionados = set()

    # Opções de marcar/desmarcar todos
    c_btn1, c_btn2 = st.columns(2)
    if c_btn1.button("Limpar Seleções"):
        st.session_state.selecionados = set()
        st.rerun()

    # Exibição da lista com Checkboxes
    nomes_lista = sorted(df_filtrado[col_t].unique().tolist())
    
    col_lista1, col_lista2 = st.columns(2)
    metade = (len(nomes_lista) + 1) // 2
    
    def toggle_selecao(nome):
        if nome in st.session_state.selecionados:
            st.session_state.selecionados.remove(nome)
        else:
            st.session_state.selecionados.add(nome)

    with col_lista1:
        for nome in nomes_lista[:metade]:
            is_checked = nome in st.session_state.selecionados
            if st.checkbox(f"👤 {nome}", value=is_checked, key=f"chk_{nome}"):
                if nome not in st.session_state.selecionados: st.session_state.selecionados.add(nome)
            else:
                if nome in st.session_state.selecionados: st.session_state.selecionados.remove(nome)

    with col_lista2:
        for nome in nomes_lista[metade:]:
            is_checked = nome in st.session_state.selecionados
            if st.checkbox(f"👤 {nome}", value=is_checked, key=f"chk_{nome}"):
                if nome not in st.session_state.selecionados: st.session_state.selecionados.add(nome)
            else:
                if nome in st.session_state.selecionados: st.session_state.selecionados.remove(nome)

    # --- ÁREA DE EXPORTAÇÃO ---
    st.divider()
    qtd_sel = len(st.session_state.selecionados)
    st.subheader(f"📦 Exportação em Lote ({qtd_sel} famílias selecionadas)")

    if qtd_sel > 0:
        # Filtra os dados de TODOS os membros das famílias marcadas na base geral
        df_final = df_geral[df_geral[col_t].isin(st.session_state.selecionados)]

        st.success(f"Pronto para exportar {len(df_final)} registos (incluindo dependentes).")
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Familias_Selecionadas')
        
        st.download_button(
            label="📥 CLIQUE AQUI PARA BAIXAR O EXCEL",
            data=output.getvalue(),
            file_name="relatorio_vulnerabilidade_CAS.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        with st.expander("👁️ Pré-visualizar dados que serão exportados"):
            st.dataframe(df_final, use_container_width=True)
    else:
        st.warning("Nenhuma família selecionada. Marque os nomes na lista acima.")

else:
    st.error("ERRO CRÍTICO: Não foi possível localizar o arquivo de dados. Verifique se o nome do arquivo carregado é 'Planilha Matriculados.xlsx'.")
