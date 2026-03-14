import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dossiê de Vulnerabilidade - CAS", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    /* Estilo das Caixinhas (Cards) */
    .card-cas {
        background-color: #f8fafc;
        padding: 20px;
        border-radius: 12px;
        border-top: 6px solid #1e3a8a;
        margin-bottom: 15px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.08);
        min-height: 250px;
    }
    .texto-preto { color: #000000 !important; font-size: 15px; font-weight: bold; margin-bottom: 4px; line-height: 1.4; }
    .label-info { color: #1e40af !important; font-size: 12px; text-transform: uppercase; font-weight: 800; border-bottom: 1px solid #e2e8f0; margin-bottom: 10px; display: block; }
    .titulo-principal { color: #1e3a8a; font-weight: 900; font-size: 30px; margin-bottom: 20px; text-align: center; border-bottom: 3px solid #1e3a8a; }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO AUTOMÁTICO
@st.cache_data
def localizar_e_carregar():
    arquivos_na_pasta = os.listdir('.')
    for arquivo in arquivos_na_pasta:
        if "Planilha Matriculados" in arquivo:
            try:
                df = pd.read_csv(arquivo, dtype=str) if arquivo.endswith('.csv') else pd.read_excel(arquivo, dtype=str)
                df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
                return df
            except: continue
    return None

df_geral = localizar_e_carregar()

if df_geral is not None:
    # Mapeamento de Colunas Críticas
    col_t = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trabalho = "EXERCE ATIVIDADE REMUNERADA:"
    
    # Base apenas de responsáveis
    df_resp = df_geral[df_geral[col_t].notna() & (df_geral[col_t].str.strip() != "")].copy()

    # --- SIDEBAR (FILTROS) ---
    st.sidebar.header("⚖️ Triagem de Vulnerabilidade")
    
    # Filtro de Renda
    ordem_renda = ["SEM RENDA", "ATÉ R$ 405,26", "DE R$ 405,26 A R$ 810,50", "DE R$ 810,50 A R$ 1.215,76", "DE R$ 1.215,76 A R$ 1.621,00 (TRÊS QUARTOS A UM SALÁRIO MÍNIMO)"]
    opcoes_renda = ["Todos"] + [r for r in ordem_renda if r in df_resp[col_renda].unique()]
    f_renda = st.sidebar.selectbox("Renda Familiar:", opcoes_renda)
    
    # Filtro de Trabalho
    opcoes_trab = ["Todos"] + sorted(df_resp[col_trabalho].unique().astype(str).tolist())
    f_trab = st.sidebar.selectbox("Situação de Trabalho:", opcoes_trab)

    # Filtragem
    df_filtrado = df_resp.copy()
    if f_renda != "Todos": df_filtrado = df_filtrado[df_filtrado[col_renda] == f_renda]
    if f_trab != "Todos": df_filtrado = df_filtrado[df_filtrado[col_trabalho] == f_trab]

    lista_nomes = sorted(df_filtrado[col_t].unique().tolist())
    selecionado = st.sidebar.selectbox(f"Responsável ({len(lista_nomes)}):", ["Selecione..."] + lista_nomes)

    # --- PAINEL PRINCIPAL ---
    st.markdown("<div class='titulo-principal'>Painel Técnico de Vulnerabilidade Social</div>", unsafe_allow_html=True)

    if selecionado != "Selecione...":
        chefe = df_resp[df_resp[col_t] == selecionado].iloc[0]
        familia = df_geral[df_geral[col_t] == selecionado]

        # EXIBIÇÃO EM QUATRO CAIXINHAS (CARDS)
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)

        with row1_col1:
            st.markdown(f"""<div class="card-cas">
                <span class="label-info">📍 Localização e Contato</span>
                <p class="texto-preto"><b>Responsável:</b> {selecionado}</p>
                <p class="texto-preto"><b>Bairro:</b> {chefe.get('BAIRRO:', 'N/A')}</p>
                <p class="texto-preto"><b>Endereço:</b> {chefe.get('ENDEREÇO COMPLETO:', 'N/A')}</p>
                <p class="texto-preto"><b>Telefone:</b> {chefe.get('CONTATO:', 'Não Informado')}</p>
                <p class="texto-preto"><b>Município:</b> {chefe.get('MUNICÍPIO:', 'N/A')}</p>
            </div>""", unsafe_allow_html=True)

        with row1_col2:
            st.markdown(f"""<div class="card-cas">
                <span class="label-info">💰 Indicadores Econômicos</span>
                <p class="texto-preto"><b>Renda Familiar:</b> {chefe.get(col_renda, 'N/A')}</p>
                <p class="texto-preto"><b>Trabalha?</b> {chefe.get(col_trabalho, 'N/A')}</p>
                <p class="texto-preto"><b>Atividade:</b> {chefe.get('QUAL ATIVIDADE REMUNERADA:', 'N/A')}</p>
                <p class="texto-preto"><b>Moradia:</b> {chefe.get('SITUAÇÃO DA MORADIA:', 'N/A')}</p>
                <p class="texto-preto"><b>Escolaridade:</b> {chefe.get('ESCOLARIDADE:', 'N/A')}</p>
            </div>""", unsafe_allow_html=True)

        with row2_col1:
            st.markdown(f"""<div class="card-cas">
                <span class="label-info">🛡️ Benefícios e Proteção Social</span>
                <p class="texto-preto"><b>Recebe Benefício?</b> {chefe.get('A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:', 'N/A')}</p>
                <p class="texto-preto"><b>Quais Programas:</b> {chefe.get('INFORMA O(S) PROGRAMA(S):', 'Nenhum')}</p>
                <p class="texto-preto"><b>Possui CadÚnico?</b> {chefe.get('A FAMÍLIA POSSUI CADASTRO ÚNICO (CADÚNICO)?', 'N/A')}</p>
                <p class="texto-preto"><b>Nº do NIS:</b> {chefe.get('NÚMERO DO NIS:', 'N/A')}</p>
            </div>""", unsafe_allow_html=True)

        with row2_col2:
            st.markdown(f"""<div class="card-cas">
                <span class="label-info">👥 Composição do Grupo Familiar</span>
                <p class="texto-preto"><b>Total de Pessoas:</b> {chefe.get('NÚMERO DE PESSOAS NO GRUPO FAMILIAR:', 'N/A')}</p>
                <p class="texto-preto"><b>Nacionalidade:</b> {chefe.get('NACIONALIDADE:', 'N/A')}</p>
                <p class="texto-preto"><b>Estado Civil:</b> {chefe.get('ESTADO CIVIL:', 'N/A')}</p>
                <p class="texto-preto"><b>Data de Nascimento:</b> {chefe.get('DATA DE NASCIMENTO:', 'N/A')}</p>
            </div>""", unsafe_allow_html=True)

        # TABELA DE EXPANSÃO (56 COLUNAS)
        st.write("---")
        with st.expander(f"📂 CLIQUE PARA VER TODOS OS DADOS CORRELACIONADOS (Composição Familiar de {selecionado})", expanded=False):
            st.dataframe(familia, use_container_width=True)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                familia.to_excel(writer, index=False)
            st.download_button(f"📥 Baixar Dossiê de {selecionado}", output.getvalue(), f"Dossie_{selecionado}.xlsx")

    else:
        st.info("👈 Use os filtros laterais para encontrar a família e visualizar o dossiê completo.")

else:
    st.error("❌ Arquivo 'Planilha Matriculados' não encontrado.")
