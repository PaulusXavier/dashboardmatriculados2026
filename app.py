import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA COM ESTÉTICA MODERNA
st.set_page_config(page_title="CAS | Inteligência Social", layout="wide")

# CSS AVANÇADO: Cores Slate, Navy e Crimson para autoridade e clareza
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .stApp { background-color: #f1f5f9; }
    
    /* Header Estilizado */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    /* Cards de Informação */
    .glass-card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        transition: transform 0.2s;
    }
    .glass-card:hover { transform: translateY(-5px); border-color: #3b82f6; }

    /* Rótulos e Dados */
    .data-label { color: #64748b; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; }
    .data-value { color: #0f172a; font-size: 1.1rem; font-weight: 700; line-height: 1.2; }
    
    /* Tags de Vulnerabilidade */
    .badge-critical { background-color: #fee2e2; color: #dc2626; padding: 4px 12px; border-radius: 9999px; font-size: 0.8rem; font-weight: 800; }
    
    /* Estilização da Sidebar */
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO E LOGICA DE RANKING
@st.cache_data
def load_data():
    arquivo = "Planilha Matriculados.xlsx - Planilha1.csv"
    if os.path.exists(arquivo):
        df = pd.read_csv(arquivo, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        return df
    return None

df_geral = load_data()

if df_geral is not None:
    col_t = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trab = "EXERCE ATIVIDADE REMUNERADA:"

    # Mapeamento de Vulnerabilidade (Maior para Menor)
    rank_renda = {
        "SEM RENDA": 1,
        "ATÉ R$ 405,26": 2,
        "DE R$ 405,26 A R$ 810,50": 3,
        "DE R$ 810,50 A R$ 1.215,76": 4,
        "DE R$ 1.215,76 A R$ 1.621,00 (TRÊS QUARTOS A UM SALÁRIO MÍNIMO)": 5
    }

    # Base de Responsáveis
    df_resp = df_geral[df_geral[col_t].notna()].copy()
    df_resp['rank'] = df_resp[col_renda].map(lambda x: rank_renda.get(str(x).strip(), 99))

    # --- SIDEBAR DESIGN ---
    st.sidebar.markdown("### 🛡️ Gestão Social")
    st.sidebar.info("A lista abaixo está ordenada pelo maior índice de vulnerabilidade.")
    
    f_renda = st.sidebar.multiselect("Filtrar por Faixa de Renda:", options=list(rank_renda.keys()), default=list(rank_renda.keys()))
    
    # Aplica filtro e ordena
    df_filtrado = df_resp[df_resp[col_renda].isin(f_renda)]
    lista_ordenada = df_filtrado.sort_values(by=['rank', col_t])[col_t].unique().tolist()
    
    selecionado = st.sidebar.selectbox("🔎 Localizar Responsável:", ["Selecione..."] + lista_ordenada)

    # --- ÁREA PRINCIPAL ---
    st.markdown('<div class="main-header"><h1>Dossiê de Vulnerabilidade Socioeconômica</h1><p>Monitoramento e Triagem de Famílias em Risco</p></div>', unsafe_allow_html=True)

    if selecionado != "Selecione...":
        chefe = df_resp[df_resp[col_t] == selecionado].iloc[0]
        familia = df_geral[df_geral[col_t] == selecionado]
        
        # Alerta de Prioridade
        if chefe['rank'] <= 2:
            st.markdown(f'<div class="alerta-vulnerabilidade" style="background:#fef2f2; border:1px solid #ef4444; color:#b91c1c; padding:15px; border-radius:12px; margin-bottom:20px; font-weight:bold; text-align:center;">🚨 ATENÇÃO: Família em Prioridade Máxima de Atendimento</div>', unsafe_allow_html=True)

        # GRID DE CARDS COM DESIGN MELHORADO
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"""<div class="glass-card">
                <div class="data-label">📍 Identificação e Local</div>
                <div class="data-value">{selecionado}</div>
                <hr style="margin:10px 0; border:0; border-top:1px solid #eee;">
                <div class="data-label">Bairro</div>
                <div class="data-value">{chefe.get('BAIRRO:', 'N/A')}</div>
                <div class="data-label" style="margin-top:10px;">Endereço</div>
                <div class="data-value" style="font-size:0.9rem;">{chefe.get('ENDEREÇO COMPLETO:', 'N/A')}</div>
            </div>""", unsafe_allow_html=True)

        with c2:
            st.markdown(f"""<div class="glass-card">
                <div class="data-label">💰 Vulnerabilidade Econômica</div>
                <div class="data-value"><span class="badge-critical">{chefe.get(col_renda, 'N/A')}</span></div>
                <hr style="margin:10px 0; border:0; border-top:1px solid #eee;">
                <div class="data-label">Vínculo de Trabalho</div>
                <div class="data-value">{chefe.get(col_trab, 'N/A')}</div>
                <div class="data-label" style="margin-top:10px;">Moradia</div>
                <div class="data-value">{chefe.get('SITUAÇÃO DA MORADIA:', 'N/A')}</div>
            </div>""", unsafe_allow_html=True)

        with c3:
            st.markdown(f"""<div class="glass-card">
                <div class="data-label">🛡️ Assistência Social</div>
                <div class="data-label">Recebe Benefício?</div>
                <div class="data-value">{chefe.get('A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:', 'N/A')}</div>
                <hr style="margin:10px 0; border:0; border-top:1px solid #eee;">
                <div class="data-label">Programas Ativos</div>
                <div class="data-value" style="font-size:0.9rem;">{chefe.get('INFORMA O(S) PROGRAMA(S):', 'Nenhum')}</div>
                <div class="data-label" style="margin-top:10px;">Composição</div>
                <div class="data-value">{chefe.get('NÚMERO DE PESSOAS NO GRUPO FAMILIAR:', 'N/A')}</div>
            </div>""", unsafe_allow_html=True)

        # TABELA DE EXPANSÃO TOTAL (DESIGN CLEAN)
        st.subheader("👥 Composição Familiar Detalhada")
        with st.expander("Expandir para visualizar todos os 56 campos e dependentes", expanded=True):
            st.dataframe(familia, use_container_width=True)
            
            # Exportação
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                familia.to_excel(writer, index=False)
            st.download_button(f"📥 Exportar Dossiê de {selecionado}", buf.getvalue(), f"{selecionado}.xlsx")

    else:
        st.markdown("""
            <div style="text-align:center; padding:100px; color:#64748b;">
                <h3>Aguardando Seleção</h3>
                <p>Utilize a barra lateral para filtrar e selecionar uma família por ordem de prioridade.</p>
            </div>
        """, unsafe_allow_html=True)
else:
    st.error("Arquivo de dados não encontrado.")
