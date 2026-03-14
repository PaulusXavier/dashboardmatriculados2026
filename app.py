import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS 2026 | Gestão Social", layout="wide", page_icon="📊")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN SÓBRIO (CORES ESCURAS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f1f5f9; }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 40px; border-radius: 20px; color: white; text-align: center; margin-bottom: 30px;
    }
    .kpi-box {
        background: white; padding: 25px; border-radius: 15px; border-bottom: 5px solid #1e40af;
        text-align: center; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    .kpi-title { color: #475569; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; }
    .kpi-value { color: #1e293b; font-size: 2.8rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LIMPEZA COM FOCO NO RESPONSÁVEL ---
@st.cache_data
def load_and_clean_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None, None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Limpeza de strings
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', ''], 'NÃO INFORMADO')
        
        # FILTRO DE FAMÍLIAS: Remove vazios e pega apenas 1 linha por Responsável para o Censo Social
        df_limpo = df[df["NOME DO RESPONSÁVEL"] != "NÃO INFORMADO"]
        df_familias = df_limpo.drop_duplicates(subset=["NOME DO RESPONSÁVEL"])
        
        return df, df_familias
    except Exception as e:
        st.error(f"Erro ao processar planilha: {e}")
        return None, None

df_geral, df_familias = load_and_clean_data()

if df_geral is not None:
    COL_RESP = "NOME DO RESPONSÁVEL"
    COL_PART = "NOME DO PARTICIPANTE (ATIVIDADES)"
    
    # Indicadores Socioeconômicos (22 colunas)
    idx_graficos = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. CONTADORES ---
    total_familias = len(df_familias) # Crava nos 292
    total_participantes = len(df_geral[df_geral[COL_PART] != "NÃO INFORMADO"])

    st.markdown('<div class="main-header"><h1>Painel Social CAS 2026</h1><p>Análise Baseada em 292 Unidades Familiares Únicas</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Famílias Únicas</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Participantes Totais</div><div class="kpi-value">{total_participantes}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Lista de Exportação</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS (Atuam na base de famílias) ---
    st.write("---")
    f1, f2, f3 = st.columns([1, 1, 2])
    
    with f1:
        col_renda = "RENDA FAMILIAR TOTAL"
        op_renda = sorted(df_familias[col_renda].unique())
        sel_renda = st.multiselect("Renda Familiar:", op_renda, default=op_renda)
    
    with f2:
        col_trab = "EXERCE ATIVIDADE REMUNERADA:"
        op_trab = sorted(df_familias[col_trab].unique())
        sel_trab = st.multiselect("Trabalho:", op_trab, default=op_trab)

    # Aplicação do filtro na base de famílias para os gráficos
    df_f_filtrado = df_familias[(df_familias[col_renda].isin(sel_renda)) & (df_familias[col_trab].isin(sel_trab))]

    with f3:
        # Correção do erro TypeError: Tratamento de lista vazia
        opcoes_busca = sorted([n for n in df_f_filtrado[COL_RESP].unique() if n != "NÃO INFORMADO"])
        selecionado = st.selectbox("🔍 Localizar Família pelo Responsável:", ["SELECIONE..."] + opcoes_busca)

    # --- 6. GRÁFICOS SOCIAIS (BASE: FAMÍLIAS ÚNICAS) ---
    st.write("---")
    st.subheader("📊 Diagnóstico Socioassistencial (1 dado por Família)")

    

    lay_g = st.columns(2)
    colunas_vis = [df_geral.columns[i] for i in idx_graficos if i < len(df_geral.columns)]

    for idx, col_nome in enumerate(colunas_vis):
        with lay_g[idx % 2]:
            contagem = df_f_filtrado[col_nome].value_counts().reset_index()
            contagem.columns = [col_nome, 'CONT']
            contagem = contagem.sort_values(by='CONT', ascending=True)

            fig = px.bar(
                contagem, y=col_nome, x='CONT', orientation='h',
                title=f"FAMÍLIAS POR: {col_nome}",
                color='CONT', color_continuous_scale='Sunsetdark', text='CONT'
            )
            fig.update_layout(
                height=350, showlegend=False, coloraxis_showscale=False,
                margin=dict(l=0, r=50, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            fig.update_traces(textposition='outside', marker_line_color='rgb(15,23,42)', marker_line_width=1)
            st.plotly_chart(fig, use_container_width=True)

    # --- 7. DETALHAMENTO DOS FILHOS/PARTICIPANTES ---
    if selecionado != "SELECIONE...":
        st.write("---")
        # Busca na base geral todos os membros vinculados àquele responsável
        membros = df_geral[df_geral[COL_RESP] == selecionado]
        st.subheader(f"👨‍👩‍👧‍👦 Membros da Família de {selecionado}")
        st.table(membros[[COL_PART, "ATIVIDADE DESEJADA", "TURNO", "IDADE (PARTICIPANTE)"]])
        
        if st.button("➕ Adicionar Família à Exportação"):
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

    if st.session_state.lista_exportacao:
        st.sidebar.markdown("---")
        df_exp = df_geral[df_geral[COL_RESP].isin(st.session_state.lista_exportacao)]
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        st.sidebar.download_button("🚀 Baixar Excel Selecionado", buf.getvalue(), "Relatorio_CAS_2026.xlsx", use_container_width=True)
else:
    st.error("Planilha 'Planilha Matriculados' não encontrada no repositório.")
