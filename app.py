import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Inteligência Social Premium", layout="wide")

# Inicializa o "Carrinho de Exportação"
if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# CSS PARA DESIGN PREMIUM E ANÁLISE ROBUSTA
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f1f5f9; }
    
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 35px; border-radius: 20px; color: white; text-align: center;
        margin-bottom: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    
    .kpi-box {
        background: white; padding: 22px; border-radius: 18px;
        text-align: center; border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .kpi-title { color: #64748b; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { color: #1e3a8a; font-size: 30px; font-weight: 800; }

    .data-grid-item {
        background: #ffffff; padding: 14px; border-radius: 12px;
        border: 1px solid #e2e8f0; margin-bottom: 10px; min-height: 85px;
        transition: 0.3s;
    }
    .data-grid-item:hover { border-color: #3b82f6; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    
    .label-grid { color: #94a3b8; font-size: 10px; font-weight: 800; text-transform: uppercase; margin-bottom: 4px; }
    .value-grid { color: #0f172a; font-size: 13px; font-weight: 700; line-height: 1.3; }
    
    .stButton>button { border-radius: 12px; font-weight: 700; height: 3em; }
    .badge-vulnerabilidade {
        background-color: #fee2e2; color: #dc2626; padding: 8px 18px;
        border-radius: 50px; font-weight: 800; border: 1px solid #fca5a5;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO E LIMPEZA
@st.cache_data
def load_and_clean_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    
    # Tenta carregar CSV ou Excel
    df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
    
    # Limpeza de nomes de colunas
    df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    
    # Substituir nulos por traço
    df = df.fillna("—").replace("nan", "—").replace("NaN", "—")
    return df

df_base = load_and_clean_data()

if df_base is not None:
    # Identificação das Colunas (Ajuste conforme sua planilha exata)
    col_t = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trampo = "EXERCE ATIVIDADE REMUNERADA:" # O filtro que você pediu

    # CÁLCULOS TOTAIS
    df_responsaveis_total = df_base[df_base[col_t] != "—"]
    total_familias = df_responsaveis_total.shape[0]
    total_pessoas = df_base.shape[0]

    # RANKING DE PRIORIDADE (Vulnerabilidade)
    rank_map = {
        "SEM RENDA": 0, 
        "ATÉ R$ 405,26": 1, 
        "DE R$ 405,26 A R$ 810,50": 2, 
        "DE R$ 810,50 A R$ 1.215,76": 3,
        "DE R$ 1.215,76 A R$ 1.621,00 (TRÊS QUARTOS A UM SALÁRIO MÍNIMO)": 4
    }

    # PAINEL SUPERIOR
    st.markdown('<div class="main-header"><h1>Painel Técnico de Vulnerabilidade Social</h1><p>Monitoramento Estratégico de Famílias Matriculadas</p></div>', unsafe_allow_html=True)

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👨‍👩‍👧‍👦 Total de Famílias</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Total Geral de Pessoas</div><div class="kpi-value">{total_pessoas}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📥 Selecionados para Exportar</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    st.write(" ")

    # --- SIDEBAR: FILTROS ROBUSTOS ---
    st.sidebar.markdown("## ⚙️ Filtros Socioeconômicos")
    
    # 1. Filtro de Renda
    f_renda = st.sidebar.multiselect("Filtrar Renda:", options=list(rank_map.keys()), default=list(rank_map.keys()))
    
    # 2. Filtro de Atividade Remunerada (PERMANECE CONFORME PEDIDO)
    opcoes_trampo = sorted(df_base[col_trampo].unique().tolist())
    f_trampo = st.sidebar.multiselect("Atividade Remunerada:", options=opcoes_trampo, default=opcoes_trampo)

    # Lógica de Ordenação e Filtragem
    df_resp_filt = df_responsaveis_total.copy()
    df_resp_filt['rank'] = df_resp_filt[col_renda].map(lambda x: rank_map.get(x, 99))
    
    # Aplica os filtros
    mask = (df_resp_filt[col_renda].isin(f_renda)) & (df_resp_filt[col_trampo].isin(f_trampo))
    df_lista = df_resp_filt[mask].sort_values(by=['rank', col_t])
    
    lista_nomes = df_lista[col_t].unique().tolist()
    selecionado = st.sidebar.selectbox("🎯 Selecionar Responsável:", ["Selecione..."] + lista_nomes)

    # Botões de Exportação em Massa na Sidebar
    st.sidebar.write("---")
    if st.session_state.lista_exportacao:
        if st.sidebar.button("🗑️ Limpar Lista"):
            st.session_state.lista_exportacao = []
            st.rerun()
        
        df_massa = df_base[df_base[col_t].isin(st.session_state.lista_exportacao)]
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_massa.to_excel(writer, index=False)
        st.sidebar.download_button("🚀 EXPORTAR SELECIONADOS", output.getvalue(), "Relatorio_Vulnerabilidade.xlsx")

    # --- EXIBIÇÃO DOS DADOS ---
    if selecionado != "Selecione...":
        chefe = df_resp_filt[df_resp_filt[col_t] == selecionado].iloc[0]
        familia = df_base[df_base[col_t] == selecionado]

        # Cabeçalho da Ficha
        c_nome, c_check = st.columns([3, 1])
        with c_nome:
            st.markdown(f"## 👤 {selecionado}")
            st.markdown(f"<span class='badge-vulnerabilidade'>{chefe.get(col_renda, '—')}</span>", unsafe_allow_html=True)
        with c_check:
            if selecionado not in st.session_state.lista_exportacao:
                if st.button("➕ Adicionar à Lista"):
                    st.session_state.lista_exportacao.append(selecionado)
                    st.rerun()
            else:
                if st.button("✅ Na Lista (Remover?)"):
                    st.session_state.lista_exportacao.remove(selecionado)
                    st.rerun()

        st.write(" ")

        # RESUMO ROBUSTO (3 Cards Principais)
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown(f'<div class="kpi-box"><div class="kpi-title">📍 Localização</div><div class="value-grid">{chefe.get("BAIRRO:", "—")}</div><div class="value-grid" style="font-size:11px">{chefe.get("ENDEREÇO COMPLETO:", "—")}</div></div>', unsafe_allow_html=True)
        with r2:
            st.markdown(f'<div class="kpi-box"><div class="kpi-title">💰 Status de Trabalho</div><div class="value-grid">{chefe.get(col_trampo, "—")}</div><div class="value-grid" style="font-size:11px"><b>Moradia:</b> {chefe.get("SITUAÇÃO DA MORADIA:", "—")}</div></div>', unsafe_allow_html=True)
        with r3:
            st.markdown(f'<div class="kpi-box"><div class="kpi-title">🛡️ Assistência</div><div class="value-grid"><b>Beneficiário:</b> {chefe.get("A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:", "—")}</div><div class="value-grid" style="font-size:11px"><b>Pessoas:</b> {chefe.get("NÚMERO DE PESSOAS NO GRUPO FAMILIAR:", "—")}</div></div>', unsafe_allow_html=True)

        # 4. EXPANSÃO COMPLETA (4 COLUNAS - TODOS OS DADOS)
        st.write("---")
        with st.expander("🔍 ANÁLISE SOCIOECONÔMICA COMPLETA (TODAS AS 56 COLUNAS)", expanded=True):
            st.markdown("### Ficha Técnica Detalhada")
            cols = st.columns(4)
            colunas_total = df_base.columns.tolist()
            
            for i, coluna in enumerate(colunas_total):
                with cols[i % 4]:
                    valor_final = chefe.get(coluna, "—")
                    st.markdown(f"""
                        <div class="data-grid-item">
                            <div class="label-grid">{coluna}</div>
                            <div class="value-grid">{valor_final}</div>
                        </div>
                    """, unsafe_allow_html=True)

            st.write("#### 👥 Composição do Grupo Familiar (Linhas Correlacionadas)")
            st.dataframe(familia, use_container_width=True)

    else:
        st.info("Utilize os filtros socioeconômicos na barra lateral para localizar uma família.")
else:
    st.error("Planilha 'Planilha Matriculados' não detectada no repositório.")
