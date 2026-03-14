import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS - Análise de Vulnerabilidade", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    /* Estilo das Caixinhas (Cards) */
    .card-cas {
        background-color: #f8fafc;
        padding: 20px;
        border-radius: 12px;
        border-left: 10px solid #1e3a8a;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 20px;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.05);
    }
    .texto-preto { color: #000000 !important; font-size: 16px; font-weight: 700; margin-bottom: 4px; }
    .label-info { color: #475569 !important; font-size: 12px; text-transform: uppercase; font-weight: bold; }
    .titulo-secao { color: #1e3a8a !important; font-weight: 900; font-size: 26px; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# 2. FUNÇÃO DE CARREGAMENTO INTELIGENTE
@st.cache_data
def carregar_dados_flexivel():
    # Lista de possíveis nomes de arquivo no servidor
    arquivos = [
        "Planilha Matriculados.xlsx - Planilha1.csv",
        "Planilha Matriculados.xlsx",
        "Planilha_Matriculados.csv"
    ]
    
    for nome in arquivos:
        if os.path.exists(nome):
            try:
                if nome.endswith('.csv'):
                    df = pd.read_csv(nome, dtype=str)
                else:
                    df = pd.read_excel(nome, dtype=str)
                # Limpa nomes de colunas
                df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
                return df
            except:
                continue
    return None

df_geral = carregar_dados_flexivel()

# Se não encontrar o arquivo automaticamente, permite o upload manual
if df_geral is None:
    st.warning("⚠️ Arquivo padrão não encontrado no servidor.")
    arquivo_upload = st.file_uploader("Por favor, carregue a planilha 'Planilha Matriculados' aqui:", type=["csv", "xlsx"])
    if arquivo_upload:
        if arquivo_upload.name.endswith('.csv'):
            df_geral = pd.read_csv(arquivo_upload, dtype=str)
        else:
            df_geral = pd.read_excel(arquivo_upload, dtype=str)
        df_geral.columns = [str(c).strip().replace('\n', ' ') for c in df_geral.columns]

# --- PROCESSAMENTO DOS DADOS ---
if df_geral is not None:
    # Mapeamento de colunas cruciais
    col_t = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trabalho = "EXERCE ATIVIDADE REMUNERADA:"
    col_beneficio = "A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:"
    col_moradia = "SITUAÇÃO DA MORADIA:"
    
    # Criar base de responsáveis (Apenas linhas onde a Coluna T está preenchida)
    df_resp = df_geral[df_geral[col_t].notna() & (df_geral[col_t].str.strip() != "")].copy()

    # --- SIDEBAR (FILTROS) ---
    st.sidebar.header("⚖️ Filtros de Vulnerabilidade")
    
    # Filtro de Renda (Ordenado por criticidade)
    ordem_renda = [
        "SEM RENDA", 
        "ATÉ R$ 405,26", 
        "DE R$ 405,26 A R$ 810,50", 
        "DE R$ 810,50 A R$ 1.215,76",
        "DE R$ 1.215,76 A R$ 1.621,00 (TRÊS QUARTOS A UM SALÁRIO MÍNIMO)"
    ]
    rendas_na_planilha = df_resp[col_renda].unique()
    opcoes_renda = ["Todos"] + [r for r in ordem_renda if r in rendas_na_planilha]
    f_renda = st.sidebar.selectbox("Renda Familiar:", opcoes_renda)
    
    # Filtro de Trabalho
    opcoes_trabalho = ["Todos"] + sorted(df_resp[col_trabalho].unique().astype(str).tolist())
    f_trabalho = st.sidebar.selectbox("Situação de Trabalho:", opcoes_trabalho)

    # Filtrar nomes para o seletor de responsável
    df_filtrado = df_resp.copy()
    if f_renda != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_renda] == f_renda]
    if f_trabalho != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_trabalho] == f_trabalho]

    lista_nomes = sorted(df_filtrado[col_t].unique().tolist())
    selecionado = st.sidebar.selectbox(f"👤 Selecione o Responsável ({len(lista_nomes)}):", ["Selecione..."] + lista_nomes)

    # --- ÁREA PRINCIPAL ---
    if selecionado != "Selecione...":
        # Extrair dados da linha do responsável (Pela Coluna T)
        dados_resp = df_resp[df_resp[col_t] == selecionado].iloc[0]
        # Extrair todos os membros da família
        dados_familia = df_geral[df_geral[col_t] == selecionado]

        st.markdown(f"<div class='titulo-secao'>Dossiê de Vulnerabilidade: {selecionado}</div>", unsafe_allow_html=True)
        st.write(" ")

        # CAIXINHAS DE DADOS (CARDS)
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown(f"""<div class="card-cas">
                <p class="label-info">📍 Endereço e Localização</p>
                <p class="texto-preto">Bairro: {dados_resp.get('BAIRRO:', 'N/A')}</p>
                <p class="texto-preto">Rua/Nº: {dados_resp.get('ENDEREÇO COMPLETO:', 'N/A')}</p>
                <p class="texto-preto">Moradia: {dados_resp.get(col_moradia, 'N/A')}</p>
            </div>""", unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""<div class="card-cas">
                <p class="label-info">💰 Situação Econômica</p>
                <p class="texto-preto">Renda: {dados_resp.get(col_renda, 'N/A')}</p>
                <p class="texto-preto">Trabalho: {dados_resp.get(col_trabalho, 'N/A')}</p>
                <p class="texto-preto">Contatos: {dados_resp.get('CONTATO:', 'N/A')}</p>
            </div>""", unsafe_allow_html=True)
            
        with c3:
            st.markdown(f"""<div class="card-cas">
                <p class="label-info">🛡️ Assistência e Benefícios</p>
                <p class="texto-preto">Possui Benefício? {dados_resp.get(col_beneficio, 'N/A')}</p>
                <p class="texto-preto">Quais? {dados_resp.get('INFORMA O(S) PROGRAMA(S):', 'Nenhum')}</p>
                <p class="texto-preto">Nº de Pessoas: {dados_resp.get('NÚMERO DE PESSOAS NO GRUPO FAMILIAR:', 'N/A')}</p>
            </div>""", unsafe_allow_html=True)

        # TABELA DE EXPANSÃO TOTAL
        st.write("---")
        st.subheader("🔍 Detalhamento Correlacionado (Membros da Família)")
        with st.expander("CLIQUE AQUI PARA VER AS 56 COLUNAS DE TODOS OS DEPENDENTES", expanded=False):
            st.dataframe(dados_familia, use_container_width=True)
            
            # Exportação
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                dados_familia.to_excel(writer, index=False)
            st.download_button(f"📥 Baixar Relatório Completo - {selecionado}", buffer.getvalue(), f"Ficha_{selecionado}.xlsx")

    else:
        st.info("👈 Use os filtros na lateral esquerda para localizar a família por renda ou situação de trabalho.")
else:
    st.error("❌ Não foi possível carregar a base de dados. Verifique se o arquivo está no GitHub ou faça o upload manual acima.")
