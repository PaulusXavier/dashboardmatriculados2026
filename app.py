import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS 2026 | Gestão Social", layout="wide", page_icon="📊")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN DE ALTO IMPACTO (CORES SÓBRIAS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f1f5f9; }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 40px; border-radius: 20px; color: white; text-align: center; margin-bottom: 30px;
    }
    .kpi-box {
        background: #ffffff; padding: 25px; border-radius: 15px; border-bottom: 5px solid #1e40af;
        text-align: center; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    .kpi-title { color: #475569; font-size: 0.9rem; font-weight: 800; text-transform: uppercase; }
    .kpi-value { color: #1e293b; font-size: 3rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LIMPEZA DOS DADOS ---
@st.cache_data
def load_and_clean_data():
    # Busca o arquivo no repositório
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
        
        # Limpeza para evitar categorias duplicadas (Ex: "MANHÃ" e "MANHÃ ")
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', ''], 'NÃO INFORMADO')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

df_base = load_and_clean_data()

if df_base is not None:
    # DEFINIÇÃO DAS COLUNAS MESTRAS
    COL_RESP = "NOME DO RESPONSÁVEL"
    COL_PART = "NOME DO PARTICIPANTE (ATIVIDADES)"
    
    # Índices dos 22 indicadores para os gráficos
    idx_graficos = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. CONTADORES (LÓGICA DOS 292 E GERAL) ---
    # Famílias: Contagem de linhas preenchidas na coluna de Responsável
    df_familias_validas = df_base[df_base[COL_RESP] != "NÃO INFORMADO"]
    total_familias = len(df_familias_validas) 

    # Participantes: Todas as pessoas individuais
    df_participantes_validos = df_base[df_base[COL_PART] != "NÃO INFORMADO"]
    total_participantes = len(df_participantes_validos)

    st.markdown('<div class="main-header"><h1>Painel CAS 2026 | Sistema Unificado</h1><p>Gestão por Unidades Familiares e Monitoramento de Participantes</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Total de Famílias</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Participantes Ativos</div><div class="kpi-value">{total_participantes}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Lista de Exportação</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS BALIZADOS ---
    st.write("---")
    f1, f2, f3 = st.columns([1, 1, 2])
    
    with f1:
        col_renda = "RENDA FAMILIAR TOTAL"
        op_renda = sorted(df_base[col_renda].unique())
        sel_renda = st.multiselect("Renda Familiar:", op_renda, default=op_renda)
    
    with f2:
        col_trabalho = "EXERCE ATIVIDADE REMUNERADA:"
        op_trab = sorted(df_base[col_trabalho].unique())
        sel_trab = st.multiselect("Atividade Remunerada:", op_trab, default=op_trab)

    # Filtro inteligente: Mostra os participantes que pertencem às famílias filtradas
    df_filtrado = df_base[(df_base[col_renda].isin(sel_renda)) & (df_base[col_trabalho].isin(sel_trab))]

    with f3:
        lista_busca = sorted([str(n) for n in df_filtrado[COL_RESP].unique() if n != "NÃO INFORMADO"])
        selecionado = st.selectbox("🔍 Pesquisar Família (Responsável):", ["SELECIONE..."] + lista_busca)

    # --- 6. FICHA TÉCNICA ---
    if selecionado != "SELECIONE...":
        st.write("---")
        df_membros = df_filtrado[df_filtrado[COL_RESP] == selecionado]
        dados_fam = df_membros.iloc[0]
        
        c_tit, c_btn = st.columns([3, 1])
        c_tit.subheader(f"📄 Prontuário Familiar: {selecionado}")
        
        if c_btn.button("➕ Adicionar ao Relatório"):
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

        with st.expander("👁️ Ver Membros e Dados Socioeconômicos", expanded=True):
            st.markdown(f"**Esta família possui {len(df_membros)} participante(s):**")
            st.table(df_membros[[COL_PART, "ATIVIDADE DESEJADA", "TURNO"]])
            st.json(dados_fam.to_dict())

    # --- 7. GRÁFICOS ANALÍTICOS (CORES SÓBRIAS) ---
    st.write("---")
    st.subheader("📊 Diagnóstico dos 22 Indicadores Sociais")

    

    lay_g = st.columns(2)
    colunas_vis = [df_base.columns[i] for i in idx_graficos if i < len(df_base.columns)]

    for idx, col_nome in enumerate(colunas_vis):
        with lay_g[idx % 2]:
            contagem = df_filtrado[col_nome].value_counts().reset_index()
            contagem.columns = [col_nome, 'CONT']
            contagem = contagem.sort_values(by='CONT', ascending=True)

            # Escala Sunsetdark para elegância e contraste em projetores
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
            fig.update_traces(textposition='outside', marker_line_color='rgb(8,48,107)', marker_line_width=1)
            st.plotly_chart(fig, use_container_width=True)

    # --- 8. EXPORTAÇÃO ---
    if st.session_state.lista_exportacao:
        st.sidebar.markdown("---")
        df_exp = df_base[df_base[COL_RESP].isin(st.session_state.lista_exportacao)]
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        st.sidebar.download_button("🚀 Baixar Excel das Famílias", buf.getvalue(), "Relatorio_CAS_2026.xlsx", use_container_width=True)
else:
    st.error("Planilha 'Planilha Matriculados' não encontrada. Verifique o arquivo no GitHub.")
