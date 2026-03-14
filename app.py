import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS 2026 | Gestão Social", layout="wide", page_icon="📊")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN SÓBRIO E IMPACTANTE ---
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

# --- 3. CARREGAMENTO COM LIMPEZA DE LINHAS FANTASMA ---
@st.cache_data
def load_and_clean_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # FILTRO MESTRE: Mantém apenas onde o Responsável está preenchido (Garante os 292)
        df = df[df["NOME DO RESPONSÁVEL"].notna()]
        df = df[df["NOME DO RESPONSÁVEL"].str.strip() != ""]
        
        # Limpeza de strings para unificação de categorias
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', ''], 'NÃO INFORMADO')
        return df
    except Exception as e:
        st.error(f"Erro na leitura dos dados: {e}")
        return None

df_base = load_and_clean_data()

if df_base is not None:
    COL_RESP = "NOME DO RESPONSÁVEL"
    COL_PART = "NOME DO PARTICIPANTE (ATIVIDADES)"
    
    # Índices revisados dos 22 indicadores para os gráficos
    idx_graficos = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. CONTADORES REVISADOS ---
    total_familias = len(df_base) # Travado nos 292 após a limpeza
    total_participantes = len(df_base[df_base[COL_PART] != "NÃO INFORMADO"])

    st.markdown('<div class="main-header"><h1>Painel de Gestão CAS 2026</h1><p>Diagnóstico Unificado das Unidades Familiares Atendidas</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Famílias Cadastradas</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Total de Participantes</div><div class="kpi-value">{total_participantes}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Lista de Exportação</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS E PESQUISA ---
    st.write("---")
    f1, f2, f3 = st.columns([1, 1, 2])
    
    with f1:
        col_renda = "RENDA FAMILIAR TOTAL"
        op_renda = sorted(df_base[col_renda].unique())
        sel_renda = st.multiselect("Filtrar Renda:", op_renda, default=op_renda)
    
    with f2:
        col_moradia = "SITUAÇÃO DE MORADIA"
        op_moradia = sorted(df_base[col_moradia].unique())
        sel_moradia = st.multiselect("Filtrar Moradia:", op_moradia, default=op_moradia)

    # Base filtrada para os gráficos
    df_filtrado = df_base[(df_base[col_renda].isin(sel_renda)) & (df_base[col_moradia].isin(sel_moradia))]

    with f3:
        lista_busca = sorted(df_filtrado[COL_RESP].unique())
        selecionado = st.selectbox("🔍 Localizar Família (Pelo Responsável):", ["SELECIONE..."] + lista_busca)

    # --- 6. GRÁFICOS ANALÍTICOS (PALETA ESCURA SUNSETDARK) ---
    st.write("---")
    st.subheader("📊 Diagnóstico Social dos Indicadores")
    st.info("Nota: Os gráficos refletem o perfil socioeconômico de cada matrícula identificada.")

    

    lay_g = st.columns(2)
    colunas_vis = [df_base.columns[i] for i in idx_graficos if i < len(df_base.columns)]

    for idx, col_nome in enumerate(colunas_vis):
        with lay_g[idx % 2]:
            contagem = df_filtrado[col_nome].value_counts().reset_index()
            contagem.columns = [col_nome, 'CONT']
            contagem = contagem.sort_values(by='CONT', ascending=True)

            fig = px.bar(
                contagem, y=col_nome, x='CONT', orientation='h',
                title=f"INDICADOR: {col_nome}",
                color='CONT', color_continuous_scale='Sunsetdark', text='CONT'
            )
            fig.update_layout(
                height=350, showlegend=False, coloraxis_showscale=False,
                margin=dict(l=0, r=50, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            fig.update_traces(textposition='outside', marker_line_color='rgb(15,23,42)', marker_line_width=1)
            st.plotly_chart(fig, use_container_width=True)

    # --- 7. EXPORTAÇÃO ---
    if st.session_state.lista_exportacao:
        st.sidebar.markdown("---")
        df_exp = df_base[df_base[COL_RESP].isin(st.session_state.lista_exportacao)]
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        st.sidebar.download_button("🚀 Baixar Prontuários (Excel)", buf.getvalue(), "Relatorio_CAS_2026.xlsx", use_container_width=True)
else:
    st.error("Erro: Certifique-se de que o arquivo 'Planilha Matriculados' está no repositório.")
