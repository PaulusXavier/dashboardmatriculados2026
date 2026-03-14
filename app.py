import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA E DESIGN PREMIUM
st.set_page_config(page_title="CAS | Inteligência Social", layout="wide")

st.markdown("""
    <style>
    /* Importação de fonte moderna */
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
    .stApp { background-color: #f4f7f9; }

    /* Cabeçalho Principal */
    .header-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 30px;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }

    /* Cards Estilizados */
    .info-card {
        background: white;
        padding: 25px;
        border-radius: 18px;
        border: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        margin-bottom: 20px;
        border-top: 5px solid #3b82f6;
    }
    .card-local { border-top-color: #3b82f6; } /* Azul */
    .card-eco { border-top-color: #ef4444; }   /* Vermelho para Alerta */
    .card-social { border-top-color: #10b981; } /* Verde */

    /* Rótulos e Valores */
    .label { color: #64748b; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .value { color: #1e293b; font-size: 16px; font-weight: 600; margin-bottom: 15px; }
    .value-highlight { color: #dc2626; font-weight: 800; font-size: 18px; }

    /* Estilo para Responsável Selecionado */
    .nome-selecionado { color: #1e3a8a; font-weight: 800; font-size: 24px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# 2. FUNÇÃO DE CARREGAMENTO ROBUSTA
@st.cache_data
def carregar_dados():
    # Procura qualquer arquivo que tenha "Planilha Matriculados" no nome
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    
    arquivo_alvo = arquivos[0] # Pega o primeiro encontrado
    try:
        if arquivo_alvo.endswith('.csv'):
            df = pd.read_csv(arquivo_alvo, dtype=str)
        else:
            df = pd.read_excel(arquivo_alvo, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        return df
    except: return None

df_geral = carregar_dados()

if df_geral is not None:
    col_resp = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trabalha = "EXERCE ATIVIDADE REMUNERADA:"

    # Mapeamento de Vulnerabilidade (Quanto menor o número, mais vulnerável)
    rank_renda = {
        "SEM RENDA": 1,
        "ATÉ R$ 405,26": 2,
        "DE R$ 405,26 A R$ 810,50": 3,
        "DE R$ 810,50 A R$ 1.215,76": 4,
        "DE R$ 1.215,76 A R$ 1.621,00 (TRÊS QUARTOS A UM SALÁRIO MÍNIMO)": 5
    }

    # Base apenas de Responsáveis
    df_resp = df_geral[df_geral[col_resp].notna()].copy()
    df_resp['rank'] = df_resp[col_renda].map(lambda x: rank_renda.get(str(x).strip(), 99))

    # --- SIDEBAR ---
    st.sidebar.markdown("### 🔍 Triagem Técnica")
    st.sidebar.write("A lista está ordenada por prioridade social (mais vulneráveis primeiro).")
    
    # Filtros
    f_renda = st.sidebar.multiselect("Filtrar Renda:", options=list(rank_renda.keys()), default=list(rank_renda.keys()))
    
    # Filtragem e Ordenação da Lista
    df_lista = df_resp[df_resp[col_renda].isin(f_renda)]
    lista_final = df_lista.sort_values(by=['rank', col_resp])[col_resp].unique().tolist()
    
    selecionado = st.sidebar.selectbox("Selecione o Responsável:", ["Selecione..."] + lista_final)

    # --- PAINEL PRINCIPAL ---
    st.markdown('<div class="header-container"><h1>Dossiê de Vulnerabilidade Socioeconômica</h1><p>Gestão de Impacto Social - CAS / SETRABES</p></div>', unsafe_allow_html=True)

    if selecionado != "Selecione...":
        chefe = df_resp[df_resp[col_resp] == selecionado].iloc[0]
        familia_toda = df_geral[df_geral[col_resp] == selecionado]

        st.markdown(f'<div class="nome-selecionado">👤 {selecionado}</div>', unsafe_allow_html=True)

        # GRID DE CARDS
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"""<div class="info-card card-local">
                <div class="label">📍 Localização e Contato</div>
                <div class="value"><b>Bairro:</b> {chefe.get('BAIRRO:', 'N/A')}</div>
                <div class="value"><b>Endereço:</b> {chefe.get('ENDEREÇO COMPLETO:', 'N/A')}</div>
                <div class="value"><b>Telefone:</b> {chefe.get('CONTATO:', 'Não informado')}</div>
            </div>""", unsafe_allow_html=True)

        with c2:
            renda_estilo = "value-highlight" if chefe['rank'] <= 2 else "value"
            st.markdown(f"""<div class="info-card card-eco">
                <div class="label">💰 Indicadores Econômicos</div>
                <div class="label">Renda Familiar</div>
                <div class="{renda_estilo}">{chefe.get(col_renda, 'N/A')}</div>
                <div class="value"><b>Trabalha?</b> {chefe.get(col_trabalha, 'N/A')}</div>
                <div class="value"><b>Moradia:</b> {chefe.get('SITUAÇÃO DA MORADIA:', 'N/A')}</div>
            </div>""", unsafe_allow_html=True)

        with c3:
            st.markdown(f"""<div class="info-card card-social">
                <div class="label">🛡️ Proteção Social</div>
                <div class="value"><b>Beneficiário?</b> {chefe.get('A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:', 'N/A')}</div>
                <div class="value"><b>Programas:</b> {chefe.get('INFORMA O(S) PROGRAMA(S):', 'Nenhum')}</div>
                <div class="value"><b>Total no Grupo:</b> {chefe.get('NÚMERO DE PESSOAS NO GRUPO FAMILIAR:', 'N/A')}</div>
            </div>""", unsafe_allow_html=True)

        # TABELA DE EXPANSÃO (56 COLUNAS)
        st.write("---")
        st.subheader("👥 Composição Familiar e Dados Técnicos")
        with st.expander("Expandir para visualizar todos os membros e as 56 colunas", expanded=True):
            st.dataframe(familia_toda, use_container_width=True)
            
            # Exportação
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                familia_toda.to_excel(writer, index=False)
            st.download_button(f"📥 Baixar Dossiê de {selecionado}", buffer.getvalue(), f"Dossie_{selecionado}.xlsx")

    else:
        st.info("Utilize os filtros na lateral para selecionar uma família e visualizar os indicadores.")

else:
    st.error("❌ Erro Crítico: A planilha não foi encontrada na pasta. Certifique-se de que o arquivo Excel ou CSV está no diretório correto.")
