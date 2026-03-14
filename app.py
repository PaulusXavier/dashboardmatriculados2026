import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS 2026 | Sistema Unificado", layout="wide", page_icon="📊")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN PROFISSIONAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #020617 0%, #1e3a8a 100%);
        padding: 40px; border-radius: 20px; color: white; text-align: center; margin-bottom: 30px;
    }
    .kpi-box {
        background: white; padding: 25px; border-radius: 15px; border-left: 5px solid #1e3a8a;
        text-align: center; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    .kpi-title { color: #64748b; font-size: 0.9rem; font-weight: 800; text-transform: uppercase; }
    .kpi-value { color: #1e3a8a; font-size: 3rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO COM INTELIGÊNCIA DE DADOS ---
@st.cache_data
def load_and_clean_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
        
        # Limpeza para evitar duplicidade visual (espaços, minúsculas)
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', ''], 'NÃO INFORMADO')
        return df
    except Exception as e:
        st.error(f"Erro técnico: {e}")
        return None

df_base = load_and_clean_data()

if df_base is not None:
    # COLUNAS MESTRAS
    COL_RESP = "NOME DO RESPONSÁVEL"
    COL_PART = "NOME DO PARTICIPANTE (ATIVIDADES)"
    
    # Índices dos 22 indicadores socioeconômicos
    idx_graficos = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. CÁLCULO DOS INDICADORES (FAMÍLIA VS PARTICIPANTE) ---
    # Famílias Únicas (Baliza)
    df_familias = df_base[df_base[COL_RESP] != "NÃO INFORMADO"]
    total_familias = df_familias[COL_RESP].nunique() 

    # Participantes Ativos (Geral)
    df_participantes = df_base[df_base[COL_PART] != "NÃO INFORMADO"]
    total_participantes = len(df_participantes)

    st.markdown('<div class="main-header"><h1>Painel CAS 2026 | Inteligência de Dados</h1><p>Análise Unificada: Responsáveis como Baliza e Participantes como Fluxo Geral</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Unidades Familiares</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Participantes Ativos</div><div class="kpi-value">{total_participantes}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📈 Média Participante/Família</div><div class="kpi-value">{round(total_participantes/total_familias, 1) if total_familias > 0 else 0}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS BALIZADOS PELO RESPONSÁVEL ---
    st.write("---")
    st.subheader("🔍 Filtros Estratégicos")
    f1, f2, f3 = st.columns([1, 1, 2])
    
    with f1:
        col_renda = "RENDA FAMILIAR TOTAL"
        op_renda = sorted(df_base[col_renda].unique())
        sel_renda = st.multiselect("Renda da Família:", op_renda, default=op_renda)
    
    with f2:
        col_moradia = "SITUAÇÃO DE MORADIA"
        op_moradia = sorted(df_base[col_moradia].unique())
        sel_moradia = st.multiselect("Moradia:", op_moradia, default=op_moradia)

    # A INTELIGÊNCIA: Filtra a base geral usando os critérios da família
    df_filtrado = df_base[(df_base[col_renda].isin(sel_renda)) & (df_base[col_moradia].isin(sel_moradia))]

    with f3:
        lista_busca = sorted([str(n) for n in df_filtrado[COL_RESP].unique() if n != "NÃO INFORMADO"])
        selecionado = st.selectbox("Localizar Família (Nome do Responsável):", ["SELECIONE..."] + lista_busca)

    # --- 6. FICHA TÉCNICA E MEMBROS DA FAMÍLIA ---
    if selecionado != "SELECIONE...":
        st.write("---")
        df_membros = df_filtrado[df_filtrado[COL_RESP] == selecionado]
        dados_resp = df_membros.iloc[0]
        
        c_tit, c_exp = st.columns([3, 1])
        c_tit.subheader(f"📄 Prontuário: Família de {selecionado}")
        
        if c_exp.button("➕ Adicionar Família à Exportação"):
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

        st.info(f"Esta família possui **{len(df_membros)}** participante(s) cadastrado(s) no sistema.")
        
        with st.expander("👁️ Detalhes dos Participantes e Responsável", expanded=True):
            st.table(df_membros[[COL_PART, "ATIVIDADE DESEJADA", "TURNO", "IDADE (PARTICIPANTE)"]])
            st.json(dados_resp.to_dict())

    # --- 7. GRÁFICOS ANALÍTICOS (BALIZADOS) ---
    st.write("---")
    st.subheader("📊 Diagnóstico dos 22 Indicadores Sociais")
    st.markdown("> Os gráficos abaixo mostram o perfil geral de todos os participantes que compõem as famílias filtradas.")

    

    lay_g = st.columns(2)
    colunas_graficos = [df_base.columns[i] for i in idx_graficos if i < len(df_base.columns)]

    for idx, col_nome in enumerate(colunas_graficos):
        with lay_g[idx % 2]:
            contagem = df_filtrado[col_nome].value_counts().reset_index()
            contagem.columns = [col_nome, 'CONT']
            contagem = contagem.sort_values(by='CONT', ascending=True)

            fig = px.bar(
                contagem, y=col_nome, x='CONT', orientation='h',
                title=f"DISTRIBUIÇÃO: {col_nome}",
                color='CONT', color_continuous_scale='Viridis', text='CONT'
            )
            fig.update_layout(height=350, showlegend=False, coloraxis_showscale=False, margin=dict(l=0, r=50, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

    # --- 8. EXPORTAÇÃO ---
    if st.session_state.lista_exportacao:
        st.sidebar.markdown("---")
        df_final = df_base[df_base[COL_RESP].isin(st.session_state.lista_exportacao)]
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False)
        st.sidebar.download_button("🚀 Baixar Relatório das Famílias Selecionadas", buf.getvalue(), "Relatorio_CAS_Unificado.xlsx", use_container_width=True)
else:
    st.error("Por favor, certifique-se de que o arquivo 'Planilha Matriculados' está na mesma pasta do código.")
