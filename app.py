import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Sistema Unificado", layout="wide", page_icon="🧠")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN DE ALTO CONTRASTE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f1f5f9; }
    .main-header {
        background: linear-gradient(135deg, #020617 0%, #1e3a8a 100%);
        padding: 30px; border-radius: 20px; color: white; text-align: center; margin-bottom: 20px;
    }
    .kpi-box {
        background: white; padding: 20px; border-radius: 15px; border: 2px solid #1e3a8a;
        text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .kpi-title { color: #64748b; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; }
    .kpi-value { color: #1e3a8a; font-size: 2.2rem; font-weight: 800; }
    .data-card { background: white; padding: 10px; border-radius: 8px; border: 1px solid #cbd5e1; margin-bottom: 5px; }
    .label-card { color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; }
    .value-card { color: #0f172a; font-size: 0.8rem; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LIMPEZA (REVISÃO DE DADOS) ---
@st.cache_data
def load_and_clean_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        
        # Limpeza profunda: Resolve erro de "Noturno" e "Tarde" duplicados ou errados
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', '', ' '], 'NÃO INFORMADO')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

df_base = load_and_clean_data()

if df_base is not None:
    # DEFINIÇÃO DE COLUNAS (Índices exatos da sua tabela)
    COL_PARTICIPANTE = df_base.columns[0]   # Coluna A
    COL_RESPONSAVEL = df_base.columns[16]  # Coluna Q (Nome do Responsável)
    COL_TRAMPO = "EXERCE ATIVIDADE REMUNERADA:"
    COL_RENDA = "RENDA FAMILIAR TOTAL"
    
    # Lista das 22 colunas solicitadas (B, C, E, G, H, J, K, L, N, R, S, T, U, V, X, Y, AB, AC, AD, AF, AH, AL)
    # Ajustado conforme a estrutura de índices da sua planilha CSV enviada
    idx_alvo = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. CONTADORES NO TOPO ---
    # Unidade Familiar = Registros únicos na coluna de Responsável
    df_familias_unicas = df_base[df_base[COL_RESPONSAVEL] != "NÃO INFORMADO"]
    total_familias = len(df_familias_unicas[COL_RESPONSAVEL].unique())
    total_participantes = len(df_base[df_base[COL_PARTICIPANTE] != "NÃO INFORMADO"])

    st.markdown('<div class="main-header"><h1>Painel Unificado de Gestão Social | CAS</h1></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Total de Famílias</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Total de Participantes</div><div class="kpi-value">{total_participantes}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Exportação Ativa</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS SOCIOECONÓMICOS ---
    st.write("---")
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        op_t = sorted(df_base[COL_TRAMPO].unique())
        sel_t = st.multiselect("Status de Trabalho", op_t, default=op_t)
    with f2:
        op_r = sorted(df_base[COL_RENDA].unique())
        sel_r = st.multiselect("Faixa de Renda", op_r, default=op_r)
    
    # Filtro aplicado sobre a base de famílias
    df_f = df_familias_unicas[(df_familias_unicas[COL_TRAMPO].isin(sel_t)) & (df_familias_unicas[COL_RENDA].isin(sel_r))]
    
    with f3:
        nomes_resp = sorted([str(n) for n in df_f[COL_RESPONSAVEL].unique()])
        selecionado = st.selectbox("🔍 Pesquisar Família (Responsável):", ["SELECIONE..."] + nomes_resp)

    # --- 6. FICHA DO RESPONSÁVEL E SELEÇÃO ---
    if selecionado != "SELECIONE...":
        st.write("---")
        dados = df_f[df_f[COL_RESPONSAVEL] == selecionado].iloc[0]
        
        c_t, c_b = st.columns([3, 1])
        c_t.subheader(f"📄 Prontuário: {selecionado}")
        
        if selecionado not in st.session_state.lista_exportacao:
            if c_b.button("➕ Adicionar para Relatório"):
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()
        else:
            if c_b.button("❌ Remover da Lista"):
                st.session_state.lista_exportacao.remove(selecionado)
                st.rerun()

        with st.expander("👁️ Ver Dados Completos da Família", expanded=True):
            grid = st.columns(4)
            for i, col in enumerate(df_base.columns):
                with grid[i % 4]:
                    st.markdown(f'<div class="data-card"><div class="label-card">{col}</div><div class="value-card">{dados[col]}</div></div>', unsafe_allow_html=True)

    # --- 7. GRÁFICOS ANALÍTICOS UNIFICADOS (REVISÃO DE QUANTIDADE) ---
    st.write("---")
    st.subheader("📊 Diagnóstico Situacional (Quantificação Absoluta)")
    
    # Loop para gerar os 22 gráficos das colunas solicitadas
    cols_visual = st.columns(2)
    colunas_graficos = [df_base.columns[i] for i in idx_alvo if i < len(df_base.columns)]

    for idx, col_nome in enumerate(colunas_graficos):
        with cols_visual[idx % 2]:
            # Contagem precisa: Garante que os números batem com a tabela
            contagem = df_f[col_nome].value_counts().reset_index()
            contagem.columns = [col_nome, 'CONT']
            contagem = contagem.sort_values(by='CONT', ascending=False)
            
            fig = px.bar(
                contagem, y=col_nome, x='CONT', orientation='h',
                title=f"INDICADOR: {col_nome}",
                color='CONT', color_continuous_scale='icefire', text='CONT'
            )
            fig.update_layout(
                height=350, showlegend=False, coloraxis_showscale=False,
                margin=dict(l=0, r=50, t=40, b=20),
                yaxis={'categoryorder':'total ascending'}
            )
            fig.update_traces(textposition='outside', textfont=dict(weight='bold', color='black'))
            st.plotly_chart(fig, use_container_width=True)

    # --- 8. EXPORTAÇÃO (SIDEBAR) ---
    if st.session_state.lista_exportacao:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📥 Relatório")
        df_exp = df_base[df_base[COL_RESPONSAVEL].isin(st.session_state.lista_exportacao)]
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        st.sidebar.download_button("🚀 Baixar Excel das Selecionadas", buf.getvalue(), "Relatorio_CAS.xlsx", use_container_width=True)

else:
    st.error("Planilha 'Planilha Matriculados' não encontrada no servidor.")
