import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Vulnerabilidade Social - CAS", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    /* Estilo dos Cards (Caixinhas) */
    .card-cas {
        background-color: #f1f5f9;
        padding: 20px;
        border-radius: 12px;
        border-top: 5px solid #1e3a8a;
        margin-bottom: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    .texto-preto { color: #000000 !important; font-size: 16px; font-weight: 600; margin-bottom: 5px; }
    .label-cinza { color: #475569 !important; font-size: 13px; font-weight: bold; text-transform: uppercase; }
    .titulo-painel { color: #1e3a8a !important; font-weight: 800; font-size: 24px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO DOS DADOS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO = "Planilha Matriculados.xlsx - Planilha1.csv"
CAMINHO = os.path.join(BASE_DIR, ARQUIVO)

@st.cache_data
def carregar_dados_vulnerabilidade(caminho):
    if not os.path.exists(caminho): return None
    df = pd.read_csv(caminho, dtype=str)
    df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    return df

df_geral = carregar_dados_vulnerabilidade(CAMINHO)

if df_geral is not None:
    # Nomes exatos das colunas da sua planilha
    col_t = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trabalho = "EXERCE ATIVIDADE REMUNERADA:"
    col_beneficio = "A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:"
    col_quais_benef = "INFORMA O(S) PROGRAMA(S):"
    
    # Base apenas de responsáveis (Coluna T preenchida)
    df_resp = df_geral[df_geral[col_t].notna() & (df_geral[col_t].str.strip() != "")].copy()

    # --- SIDEBAR (FILTROS À ESQUERDA) ---
    st.sidebar.header("⚖️ Filtros de Vulnerabilidade")
    
    # 1. Filtro de Renda (Ordenado por vulnerabilidade)
    ordem_renda = [
        "SEM RENDA", 
        "ATÉ R$ 405,26", 
        "DE R$ 405,26 A R$ 810,50", 
        "DE R$ 810,50 A R$ 1.215,76",
        "DE R$ 1.215,76 A R$ 1.621,00 (TRÊS QUARTOS A UM SALÁRIO MÍNIMO)"
    ]
    # Pega o que existe na planilha e ordena conforme a lista acima
    opcoes_renda = ["Todos"] + [r for r in ordem_renda if r in df_resp[col_renda].unique()]
    f_renda = st.sidebar.selectbox("Renda Mensal:", opcoes_renda)
    
    # 2. Filtro de Trabalho (Sim, Não, Temporário...)
    opcoes_trabalho = ["Todos"] + sorted(df_resp[col_trabalho].unique().astype(str).tolist())
    f_trabalho = st.sidebar.selectbox("Vínculo de Trabalho:", opcoes_trabalho)

    # Aplicar filtros na lista de nomes
    df_filtrado = df_resp.copy()
    if f_renda != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_renda] == f_renda]
    if f_trabalho != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_trabalho] == f_trabalho]

    # 3. Filtro do Responsável (Aparece após os filtros econômicos)
    lista_nomes = sorted(df_filtrado[col_t].unique().tolist())
    selecionado = st.sidebar.selectbox(f"Responsável ({len(lista_nomes)}):", ["Selecione..."] + lista_nomes)

    # --- PAINEL PRINCIPAL (CAIXINHAS À DIREITA) ---
    st.markdown("<h1 style='color: #1e3a8a;'>Análise de Vulnerabilidade Familiar</h1>", unsafe_allow_html=True)

    if selecionado != "Selecione...":
        # Dados da linha do responsável e da família inteira
        chefe = df_resp[df_resp[col_t] == selecionado].iloc[0]
        familia_completa = df_geral[df_geral[col_t] == selecionado]

        st.markdown(f"<div class='titulo-painel'>Responsável: {selecionado}</div>", unsafe_allow_html=True)

        # LINHA 1 DE CAIXINHAS
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class="card-cas">
                <p class="label-cinza">📍 Localização</p>
                <p class="texto-preto">Bairro: {chefe.get('BAIRRO:', 'N/A')}</p>
                <p class="texto-preto">Cidade: {chefe.get('MUNICÍPIO:', 'N/A')}</p>
                <p class="texto-preto">Endereço: {chefe.get('ENDEREÇO COMPLETO:', 'N/A')}</p>
            </div>""", unsafe_allow_html=True)
        
        with c2:
            st.markdown(f"""<div class="card-cas">
                <p class="label-cinza">💰 Economia</p>
                <p class="texto-preto">Renda: {chefe.get(col_renda, 'N/A')}</p>
                <p class="texto-preto">Trabalho: {chefe.get(col_trabalho, 'N/A')}</p>
                <p class="texto-preto">Moradia: {chefe.get('SITUAÇÃO DA MORADIA:', 'N/A')}</p>
            </div>""", unsafe_allow_html=True)
            
        with c3:
            st.markdown(f"""<div class="card-cas">
                <p class="label-cinza">🛡️ Programas Sociais</p>
                <p class="texto-preto">Beneficiário: {chefe.get(col_beneficio, 'N/A')}</p>
                <p class="texto-preto">Programas: {chefe.get(col_quais_benef, 'N/A')}</p>
                <p class="texto-preto">Contatos: {chefe.get('CONTATO:', 'N/A')}</p>
            </div>""", unsafe_allow_html=True)

        # TABELA PARA EXPANDIR
        st.write("---")
        st.subheader("📋 Composição e Dados do Grupo Familiar")
        with st.expander("CLIQUE PARA EXPANDIR E VER TODOS OS DADOS CORRELACIONADOS (56 COLUNAS)", expanded=False):
            st.dataframe(familia_completa, use_container_width=True)
            
            # Botão de exportação
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                familia_completa.to_excel(writer, index=False)
            st.download_button(f"📥 Exportar Ficha de {selecionado}", output.getvalue(), f"Ficha_{selecionado}.xlsx")

    else:
        st.info("👈 Use os filtros de Renda e Trabalho na esquerda para localizar as famílias e ver os dados.")

else:
    st.error("Planilha não encontrada. Verifique o arquivo: Planilha Matriculados.xlsx - Planilha1.csv")
