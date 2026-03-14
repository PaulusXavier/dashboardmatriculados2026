import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão de Vulnerabilidade CAS", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .card-cas {
        background-color: #f1f5f9;
        padding: 20px;
        border-radius: 12px;
        border-top: 6px solid #1e3a8a;
        margin-bottom: 15px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    }
    .texto-preto { color: #000000 !important; font-size: 16px; font-weight: bold; margin-bottom: 5px; }
    .label-info { color: #475569 !important; font-size: 13px; font-weight: bold; text-transform: uppercase; }
    .alerta-vulnerabilidade {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #ef4444;
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO AUTOMÁTICO (BUSCA QUALQUER ARQUIVO MATRICULADOS)
@st.cache_data
def localizar_e_carregar():
    # Lista todos os arquivos na pasta atual
    arquivos_na_pasta = os.listdir('.')
    for arquivo in arquivos_na_pasta:
        # Se o arquivo tiver "Planilha Matriculados" no nome
        if "Planilha Matriculados" in arquivo:
            try:
                if arquivo.endswith('.csv'):
                    df = pd.read_csv(arquivo, dtype=str)
                else:
                    df = pd.read_excel(arquivo, dtype=str)
                
                # Limpa nomes de colunas
                df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
                return df
            except:
                continue
    return None

df_geral = localizar_e_carregar()

if df_geral is not None:
    # Colunas cruciais
    col_t = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trabalho = "EXERCE ATIVIDADE REMUNERADA:"
    
    # Base apenas de responsáveis (Filtro da Coluna T preenchida)
    df_resp = df_geral[df_geral[col_t].notna() & (df_geral[col_t].str.strip() != "")].copy()

    # --- SIDEBAR (FILTROS À ESQUERDA) ---
    st.sidebar.header("⚖️ Filtros de Vulnerabilidade")
    
    # 1. Filtro de Renda (Ordenado da maior vulnerabilidade para a menor)
    ordem_renda = ["SEM RENDA", "ATÉ R$ 405,26", "DE R$ 405,26 A R$ 810,50", "DE R$ 810,50 A R$ 1.215,76"]
    opcoes_renda = ["Todos"] + [r for r in ordem_renda if r in df_resp[col_renda].unique()]
    f_renda = st.sidebar.selectbox("Filtro de Renda:", opcoes_renda)
    
    # 2. Filtro de Trabalho (Sim, Não, Temporário...)
    opcoes_trab = ["Todos"] + sorted(df_resp[col_trabalho].unique().astype(str).tolist())
    f_trab = st.sidebar.selectbox("Vínculo de Trabalho:", opcoes_trab)

    # Filtrar a lista de responsáveis com base nos filtros econômicos
    df_filtrado = df_resp.copy()
    if f_renda != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_renda] == f_renda]
    if f_trab != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_trabalho] == f_trab]

    # 3. Filtro do Responsável Familiar
    lista_nomes = sorted(df_filtrado[col_t].unique().tolist())
    selecionado = st.sidebar.selectbox(f"Selecione o Responsável ({len(lista_nomes)}):", ["Selecione..."] + lista_nomes)

    # --- PAINEL DE CAIXINHAS (DIREITA) ---
    st.markdown("<h1 style='color: #1e3a8a;'>Painel Técnico de Vulnerabilidade Social</h1>", unsafe_allow_html=True)

    if selecionado != "Selecione...":
        # Pega a linha do responsável e todas as linhas da família (dependentes)
        chefe = df_resp[df_resp[col_t] == selecionado].iloc[0]
        familia = df_geral[df_geral[col_t] == selecionado]

        # Alerta se for Sem Renda ou Renda Baixa
        if chefe[col_renda] in ["SEM RENDA", "ATÉ R$ 405,26"]:
            st.markdown(f'<div class="alerta-vulnerabilidade">⚠️ ALERTA: Família em situação crítica de vulnerabilidade ({chefe[col_renda]})</div>', unsafe_allow_html=True)

        # LINHA DE CAIXINHAS (CARDS)
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown(f"""<div class="card-cas">
                <p class="label-info">📍 Localização e Contato</p>
                <p class="texto-preto">Bairro: {chefe.get('BAIRRO:', 'N/A')}</p>
                <p class="texto-preto">Endereço: {chefe.get('ENDEREÇO COMPLETO:', 'N/A')}</p>
                <p class="texto-preto">Telefone: {chefe.get('CONTATO:', 'N/A')}</p>
            </div>""", unsafe_allow_html=True)

        with c2:
            st.markdown(f"""<div class="card-cas">
                <p class="label-info">💰 Indicadores Econômicos</p>
                <p class="texto-preto">Renda: {chefe.get(col_renda, 'N/A')}</p>
                <p class="texto-preto">Trabalha? {chefe.get(col_trabalho, 'N/A')}</p>
                <p class="texto-preto">Moradia: {chefe.get('SITUAÇÃO DA MORADIA:', 'N/A')}</p>
            </div>""", unsafe_allow_html=True)

        with c3:
            st.markdown(f"""<div class="card-cas">
                <p class="label-info">🛡️ Benefícios e Grupo</p>
                <p class="texto-preto">Recebe Benefício? {chefe.get('A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:', 'N/A')}</p>
                <p class="texto-preto">Quais? {chefe.get('INFORMA O(S) PROGRAMA(S):', 'Não informado')}</p>
                <p class="texto-preto">Total de Pessoas: {chefe.get('NÚMERO DE PESSOAS NO GRUPO FAMILIAR:', 'N/A')}</p>
            </div>""", unsafe_allow_html=True)

        # TABELA DE EXPANSÃO TOTAL (TODOS OS DADOS CORRELACIONADOS)
        st.write("---")
        st.subheader(f"📂 Dados Detalhados do Grupo Familiar ({len(familia)} pessoas)")
        with st.expander("CLIQUE AQUI PARA EXPANDIR E VER AS 56 COLUNAS DA FAMÍLIA", expanded=False):
            st.dataframe(familia, use_container_width=True)
            
            # Botão para baixar a ficha
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                familia.to_excel(writer, index=False)
            st.download_button(f"📥 Baixar Excel de {selecionado}", output.getvalue(), f"Ficha_{selecionado}.xlsx")

    else:
        st.info("👈 Use os filtros de Renda e Trabalho na esquerda para localizar as famílias.")

else:
    st.error("❌ Erro: Não encontramos nenhum arquivo com o nome 'Planilha Matriculados' na pasta do projeto.")
