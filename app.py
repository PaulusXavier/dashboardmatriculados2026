import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Gestão de Vulnerabilidade", layout="wide")

# Inicializa o "Carrinho de Exportação" na memória da sessão se não existir
if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# CSS PARA DESIGN E BOTÕES
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 30px; border-radius: 20px; color: white; text-align: center;
        margin-bottom: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    
    .kpi-box {
        background: white; padding: 20px; border-radius: 15px;
        text-align: center; border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .kpi-title { color: #64748b; font-size: 12px; font-weight: 800; text-transform: uppercase; margin-bottom: 5px; }
    .kpi-value { color: #1e3a8a; font-size: 32px; font-weight: 800; }

    .data-grid-item {
        background: white; padding: 12px; border-radius: 10px;
        border: 1px solid #f1f5f9; margin-bottom: 8px; min-height: 70px;
    }
    .label-grid { color: #94a3b8; font-size: 9px; font-weight: 800; text-transform: uppercase; }
    .value-grid { color: #1e293b; font-size: 12px; font-weight: 700; }
    
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO E LIMPEZA
@st.cache_data
def load_and_clean_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
    df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    df = df.fillna("—").replace("nan", "—").replace("NaN", "—")
    return df

df_base = load_and_clean_data()

if df_base is not None:
    col_t = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trampo = "EXERCE ATIVIDADE REMUNERADA:"

    # KPIs TOTAIS
    total_familias = df_base[df_base[col_t] != "—"].shape[0]
    total_pessoas = df_base.shape[0]

    # RANKING
    rank_map = {"SEM RENDA": 0, "ATÉ R$ 405,26": 1, "DE R$ 405,26 A R$ 810,50": 2, "DE R$ 810,50 A R$ 1.215,76": 3}

    st.markdown('<div class="main-header"><h1>Dossiê Socioeconômico CAS</h1><p>Gestão de Vulnerabilidade e Exportação em Massa</p></div>', unsafe_allow_html=True)

    # EXIBIÇÃO KPIs
    k1, k2, k3 = st.columns([1, 1, 1])
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👨‍👩‍👧‍👦 Total Famílias</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Total Pessoas</div><div class="kpi-value">{total_pessoas}</div></div>', unsafe_allow_html=True)
    with k3:
        # Caixa do Carrinho de Exportação
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📥 Selecionados p/ Exportar</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    st.write(" ")

    # SIDEBAR: FILTROS E BOTÃO DE EXPORTAÇÃO GERAL
    st.sidebar.markdown("## 🛡️ Filtros e Lote")
    
    # Botão para Limpar Seleção
    if st.sidebar.button("🗑️ Limpar Lista de Exportação"):
        st.session_state.lista_exportacao = []
        st.rerun()

    # Botão para Exportar tudo que foi marcado
    if st.session_state.lista_exportacao:
        df_export_massa = df_base[df_base[col_t].isin(st.session_state.lista_exportacao)]
        output_massa = BytesIO()
        with pd.ExcelWriter(output_massa, engine='xlsxwriter') as writer:
            df_export_massa.to_excel(writer, index=False)
        st.sidebar.download_button(
            label="🚀 BAIXAR TODOS SELECIONADOS",
            data=output_massa.getvalue(),
            file_name="Exportacao_Massa_CAS.xlsx",
            mime="application/vnd.ms-excel"
        )

    f_renda = st.sidebar.multiselect("Renda:", options=list(rank_map.keys()), default=list(rank_map.keys()))
    df_resp_only = df_base[df_base[col_t] != "—"].copy()
    df_resp_only['rank'] = df_resp_only[col_renda].map(lambda x: rank_map.get(x, 99))
    lista_nomes = df_resp_only[df_resp_only[col_renda].isin(f_renda)].sort_values(by=['rank', col_t])[col_t].unique().tolist()
    
    selecionado = st.sidebar.selectbox("🎯 Localizar Responsável:", ["Selecione..."] + lista_nomes)

    if selecionado != "Selecione...":
        chefe = df_resp_only[df_resp_only[col_t] == selecionado].iloc[0]
        
        # BOTÃO DE MARCAR/DESMARCAR
        c_nome, c_marcar = st.columns([3, 1])
        with c_nome:
            st.markdown(f"## 👤 {selecionado}")
        with c_marcar:
            if selecionado not in st.session_state.lista_exportacao:
                if st.button("➕ Marcar para Exportar"):
                    st.session_state.lista_exportacao.append(selecionado)
                    st.rerun()
            else:
                if st.button("✅ Marcado (Remover?)"):
                    st.session_state.lista_exportacao.remove(selecionado)
                    st.rerun()

        # ... Restante dos Cards (Localização, Trabalho, Social) e a Expansão 4 colunas ...
        # (Mantendo a mesma lógica de cards e a expansão de 4 colunas que fizemos anteriormente)
        r1, r2, r3 = st.columns(3)
        with r1: st.markdown(f'<div class="kpi-box"><div class="label-grid">📍 Bairro</div><div class="value-grid">{chefe.get("BAIRRO:", "—")}</div></div>', unsafe_allow_html=True)
        with r2: st.markdown(f'<div class="kpi-box"><div class="label-grid">💰 Renda</div><div class="value-grid">{chefe.get(col_renda, "—")}</div></div>', unsafe_allow_html=True)
        with r3: st.markdown(f'<div class="kpi-box"><div class="label-grid">🛡️ Pessoas</div><div class="value-grid">{chefe.get("NÚMERO DE PESSOAS NO GRUPO FAMILIAR:", "—")}</div></div>', unsafe_allow_html=True)

        with st.expander("🔍 FICHA TÉCNICA DETALHADA (4 COLUNAS)", expanded=True):
            cols = st.columns(4)
            todas_colunas = df_base.columns.tolist()
            for i, col in enumerate(todas_colunas):
                with cols[i % 4]:
                    st.markdown(f'<div class="data-grid-item"><div class="label-grid">{col}</div><div class="value-grid">{chefe.get(col, "—")}</div></div>', unsafe_allow_html=True)

else:
    st.error("Planilha não encontrada.")
