import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS 2026 | Inteligência Familiar", layout="wide", page_icon="📊")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PROFISSIONAL (TONS ESCUROS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 40px; border-radius: 20px; color: white; text-align: center; margin-bottom: 30px;
    }
    .kpi-box {
        background: white; padding: 25px; border-radius: 15px; border-bottom: 5px solid #1e40af;
        text-align: center; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    .kpi-title { color: #64748b; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; }
    .kpi-value { color: #1e293b; font-size: 2.8rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E FILTRAGEM DE FAMÍLIAS ---
@st.cache_data
def load_and_clean_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Limpeza básica
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', ''], 'NÃO INFORMADO')
        
        # Base de Famílias (Apenas nomes únicos de responsáveis para os gráficos sociais)
        # Isso garante que 1 família = 1 dado no gráfico
        df_familias = df[df["NOME DO RESPONSÁVEL"] != "NÃO INFORMADO"].drop_duplicates(subset=["NOME DO RESPONSÁVEL"])
        
        return df, df_familias
    except Exception as e:
        st.error(f"Erro: {e}")
        return None, None

df_geral, df_familias = load_and_clean_data()

if df_geral is not None:
    COL_RESP = "NOME DO RESPONSÁVEL"
    COL_PART = "NOME DO PARTICIPANTE (ATIVIDADES)"
    
    # Índices dos 22 indicadores socioeconômicos
    idx_graficos = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. KPIs ---
    total_familias = len(df_familias) # Deve cravar em 292
    total_participantes = len(df_geral[df_geral[COL_PART] != "NÃO INFORMADO"])

    st.markdown('<div class="main-header"><h1>Painel de Diagnóstico Social CAS</h1><p>Análise Baseada em Unidades Familiares Únicas</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Famílias (Responsáveis Únicos)</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Participantes Totais</div><div class="kpi-value">{total_participantes}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Lista para Exportação</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS (ATUANDO SOBRE AS FAMÍLIAS) ---
    st.write("---")
    f1, f2, f3 = st.columns([1, 1, 2])
    
    with f1:
        col_renda = "RENDA FAMILIAR TOTAL"
        op_renda = sorted(df_familias[col_renda].unique())
        sel_renda = st.multiselect("Renda Familiar:", op_renda, default=op_renda)
    
    with f2:
        col_benef = "A FAMÍLIA RECEBE ALGUM TIPO DE BENEFÍCIO"
        op_benef = sorted(df_familias[col_benef].unique())
        sel_benef = st.multiselect("Recebe Benefício:", op_benef, default=op_benef)

    # Base filtrada para os gráficos (Censo Familiar)
    df_f_filtrado = df_familias[(df_familias[col_renda].isin(sel_renda)) & (df_familias[col_benef].isin(sel_benef))]

    with f3:
        lista_busca = sorted(df_f_filtrado[COL_RESP].unique())
        selecionado = st.selectbox("🔍 Detalhar Família pelo Responsável:", ["SELECIONE..."] + lista_busca)

    # --- 6. GRÁFICOS SOCIAIS (CENSO DE FAMÍLIAS - CORES ESCURAS) ---
    st.write("---")
    st.subheader("📊 Diagnóstico Social (Base: 1 Gráfico por Família)")

    

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

    # --- 7. DETALHAMENTO E EXPORTAÇÃO ---
    if selecionado != "SELECIONE...":
        st.write("---")
        # Aqui buscamos na base GERAL todos os participantes daquela família
        membros = df_geral[df_geral[COL_RESP] == selecionado]
        st.subheader(f"👨‍👩‍👧‍👦 Composição da Família: {selecionado}")
        st.table(membros[[COL_PART, "ATIVIDADE DESEJADA", "TURNO", "IDADE (PARTICIPANTE)"]])
        
        if st.button("➕ Adicionar Família à Lista de Exportação"):
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

    if st.session_state.lista_exportacao:
        st.sidebar.markdown("---")
        df_exp = df_geral[df_geral[COL_RESP].isin(st.session_state.lista_exportacao)]
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        st.sidebar.download_button("🚀 Baixar Excel das Famílias Selecionadas", buf.getvalue(), "Relatorio_CAS_2026.xlsx", use_container_width=True)
else:
    st.error("Planilha não encontrada.")
