import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Inteligência Social", layout="wide")

# CSS PARA DESIGN PREMIUM, INDICADORES E GRID
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 30px; border-radius: 20px; color: white; text-align: center;
        margin-bottom: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    
    /* Caixas de Indicadores (KPIs) */
    .kpi-box {
        background: white; padding: 20px; border-radius: 15px;
        text-align: center; border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .kpi-title { color: #64748b; font-size: 12px; font-weight: 800; text-transform: uppercase; margin-bottom: 5px; }
    .kpi-value { color: #1e3a8a; font-size: 32px; font-weight: 800; }

    /* Grid de Expansão */
    .data-grid-item {
        background: white; padding: 12px; border-radius: 10px;
        border: 1px solid #f1f5f9; margin-bottom: 8px; min-height: 70px;
    }
    .label-grid { color: #94a3b8; font-size: 9px; font-weight: 800; text-transform: uppercase; }
    .value-grid { color: #1e293b; font-size: 12px; font-weight: 700; }
    
    .glass-card {
        background: white; padding: 20px; border-radius: 15px;
        border: 1px solid #f1f5f9; box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        margin-bottom: 15px; border-top: 4px solid #3b82f6;
    }
    .badge-vulnerabilidade {
        background-color: #fee2e2; color: #dc2626; padding: 6px 14px;
        border-radius: 50px; font-weight: 800; border: 1px solid #fca5a5; font-size: 13px;
    }
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
    
    # Substituir nan e vazios por traço
    df = df.fillna("—").replace("nan", "—").replace("NaN", "—")
    return df

df_base = load_and_clean_data()

if df_base is not None:
    col_t = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trampo = "EXERCE ATIVIDADE REMUNERADA:"

    # --- CÁLCULO DOS INDICADORES TOTAIS (TOPO) ---
    # Famílias: Apenas quem tem a Coluna T preenchida e diferente de traço
    total_familias = df_base[df_base[col_t] != "—"].shape[0]
    # Pessoas: Todas as linhas da planilha
    total_pessoas = df_base.shape[0]

    # RANKING DE VULNERABILIDADE
    rank_map = {
        "SEM RENDA": 0, "ATÉ R$ 405,26": 1, "DE R$ 405,26 A R$ 810,50": 2, 
        "DE R$ 810,50 A R$ 1.215,76": 3, 
        "DE R$ 1.215,76 A R$ 1.621,00 (TRÊS QUARTOS A UM SALÁRIO MÍNIMO)": 4
    }

    # PAINEL PRINCIPAL
    st.markdown('<div class="main-header"><h1>Dossiê Socioeconômico CAS</h1><p>Monitoramento de Vulnerabilidade e Impacto Social</p></div>', unsafe_allow_html=True)

    # EXIBIÇÃO DAS DUAS CAIXAS NO TOPO
    kpi1, kpi2 = st.columns(2)
    with kpi1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👨‍👩‍👧‍👦 Total de Famílias (Responsáveis)</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with kpi2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Total Geral de Pessoas Matriculadas</div><div class="kpi-value">{total_pessoas}</div></div>', unsafe_allow_html=True)

    st.write(" ")

    # SIDEBAR: FILTROS
    st.sidebar.markdown("## 🛡️ Filtros de Triagem")
    f_renda = st.sidebar.multiselect("Renda Familiar:", options=list(rank_map.keys()), default=list(rank_map.keys()))
    
    opcoes_trampo = sorted(df_base[col_trampo].unique().tolist())
    f_trampo = st.sidebar.multiselect("Ocupação:", options=opcoes_trampo, default=opcoes_trampo)

    # Filtragem e Ordenação da lista
    df_resp_only = df_base[df_base[col_t] != "—"].copy()
    df_resp_only['rank'] = df_resp_only[col_renda].map(lambda x: rank_map.get(x, 99))
    
    mask = (df_resp_only[col_renda].isin(f_renda)) & (df_resp_only[col_trampo].isin(f_trampo))
    df_filtrado = df_resp_only[mask].sort_values(by=['rank', col_t])
    
    lista_nomes = df_filtrado[col_t].unique().tolist()
    selecionado = st.sidebar.selectbox("🎯 Localizar Responsável:", ["Selecione..."] + lista_nomes)

    if selecionado != "Selecione...":
        chefe = df_resp_only[df_resp_only[col_t] == selecionado].iloc[0]
        membros = df_base[df_base[col_t] == selecionado]

        # Resumo do Selecionado
        st.markdown(f"<h2 style='color:#0f172a; margin-top:30px;'>👤 {selecionado}</h2>", unsafe_allow_html=True)
        st.markdown(f"<span class='badge-vulnerabilidade'>{chefe.get(col_renda, '—')}</span>", unsafe_allow_html=True)
        
        st.write(" ")
        
        # Cards de Resumo
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown(f'<div class="glass-card"><div class="label-grid">📍 Localização</div><div class="value-grid">{chefe.get("BAIRRO:", "—")}</div><div class="value-grid">{chefe.get("ENDEREÇO COMPLETO:", "—")}</div></div>', unsafe_allow_html=True)
        with r2:
            st.markdown(f'<div class="glass-card"><div class="label-grid">💰 Trabalho</div><div class="value-grid">{chefe.get(col_trampo, "—")}</div><div class="value-grid"><b>Moradia:</b> {chefe.get("SITUAÇÃO DA MORADIA:", "—")}</div></div>', unsafe_allow_html=True)
        with r3:
            st.markdown(f'<div class="glass-card"><div class="label-grid">🛡️ Social</div><div class="value-grid"><b>Pessoas no Grupo:</b> {chefe.get("NÚMERO DE PESSOAS NO GRUPO FAMILIAR:", "—")}</div><div class="value-grid"><b>Programa Social:</b> {chefe.get("A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:", "—")}</div></div>', unsafe_allow_html=True)

        # 4. EXPANSÃO EM 4 COLUNAS
        st.write("---")
        with st.expander("🔍 FICHA TÉCNICA DETALHADA (EXPANSÃO EM 4 COLUNAS)", expanded=True):
            cols = st.columns(4)
            todas_colunas = df_base.columns.tolist()
            
            for i, coluna in enumerate(todas_colunas):
                with cols[i % 4]:
                    valor = chefe.get(coluna, "—")
                    st.markdown(f'<div class="data-grid-item"><div class="label-grid">{coluna}</div><div class="value-grid">{valor}</div></div>', unsafe_allow_html=True)

            st.write("#### 👥 Composição do Grupo Familiar")
            st.dataframe(membros, use_container_width=True)
            
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
                membros.to_excel(writer, index=False)
            st.download_button(f"📥 Baixar Dossiê Completo", buf.getvalue(), f"{selecionado}.xlsx")
    else:
        st.info("Utilize os filtros laterais para localizar famílias e visualizar indicadores.")
else:
    st.error("Planilha não encontrada no repositório.")
