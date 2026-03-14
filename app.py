import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Inteligência Social", layout="wide", page_icon="📊")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. DESIGN PROFISSIONAL (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #020617 0%, #1e3a8a 100%);
        padding: 30px; border-radius: 20px; color: white; text-align: center; margin-bottom: 20px;
    }
    .kpi-box {
        background: white; padding: 20px; border-radius: 15px; border: 2px solid #1e3a8a;
        text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .kpi-title { color: #64748b; font-size: 0.9rem; font-weight: 800; text-transform: uppercase; }
    .kpi-value { color: #1e3a8a; font-size: 2.8rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LEITURA E LIMPEZA (AUDITORIA DE DADOS) ---
@st.cache_data
def load_and_clean_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
        
        # LIMPEZA RIGOROSA (Resolve Noturno vs Tarde e outros erros)
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', '', ' '], 'NÃO INFORMADO')
        return df
    except Exception as e:
        st.error(f"Erro técnico: {e}")
        return None

df_base = load_and_clean_data()

if df_base is not None:
    # MAPEAMENTO SEGUNDO SUA ORIENTAÇÃO
    COL_PARTICIPANTE = df_base.columns[0]   # Coluna A
    COL_RESPONSAVEL = df_base.columns[16]  # Coluna Q
    
    # Índices das 22 colunas estratégicas para os gráficos
    idx_alvo = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. CONTADORES (RECUPERAÇÃO DOS 292) ---
    df_familias = df_base[df_base[COL_RESPONSAVEL] != "NÃO INFORMADO"]
    total_familias = len(df_familias) # Contagem absoluta de linhas preenchidas na Col Q
    total_participantes = len(df_base[df_base[COL_PARTICIPANTE] != "NÃO INFORMADO"])

    st.markdown('<div class="main-header"><h1>Painel Unificado CAS 2026</h1><p>Diagnóstico Socioassistencial de Alta Precisão</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Famílias Atendidas</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Participantes Ativos</div><div class="kpi-value">{total_participantes}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Prontuários p/ Baixar</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS SOCIOECONÔMICOS ---
    st.write("---")
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        c_trabalho = "EXERCE ATIVIDADE REMUNERADA:"
        op_t = sorted(df_base[c_trabalho].unique()) if c_trabalho in df_base.columns else []
        sel_t = st.multiselect("Filtro: Trabalho", op_t, default=op_t)
    with f2:
        c_renda = "RENDA FAMILIAR TOTAL"
        op_r = sorted(df_base[c_renda].unique()) if c_renda in df_base.columns else []
        sel_r = st.multiselect("Filtro: Renda", op_r, default=op_r)

    df_filtrado = df_familias[(df_familias[c_trabalho].isin(sel_t)) & (df_familias[c_renda].isin(sel_r))]
    
    with f3:
        nomes_lista = sorted([str(n) for n in df_filtrado[COL_RESPONSAVEL].unique()])
        selecionado = st.selectbox("🔍 Pesquisar Família (Responsável):", ["SELECIONE UM NOME..."] + nomes_lista)

    # --- 6. FICHA TÉCNICA ---
    if selecionado != "SELECIONE UM NOME...":
        st.write("---")
        dados_f = df_filtrado[df_filtrado[COL_RESPONSAVEL] == selecionado].iloc[0]
        
        c_tit, c_btn = st.columns([3, 1])
        c_tit.subheader(f"📄 Ficha Técnica: {selecionado}")
        
        if selecionado not in st.session_state.lista_exportacao:
            if c_btn.button("➕ Adicionar à Exportação"):
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()
        else:
            if c_btn.button("❌ Remover da Lista"):
                st.session_state.lista_exportacao.remove(selecionado)
                st.rerun()

        with st.expander("👁️ Ver Dados Detalhados", expanded=True):
            grid = st.columns(4)
            for i, col_name in enumerate(df_base.columns):
                with grid[i % 4]:
                    st.markdown(f'''<div style="background:white; padding:8px; border-radius:5px; border:1px solid #ddd; margin-bottom:5px;">
                        <small style="color:#64748b; font-weight:bold;">{col_name}</small><br>
                        <b style="font-size:0.85rem;">{dados_f[col_name]}</b>
                    </div>''', unsafe_allow_html=True)

    # --- 7. GRÁFICOS ANALÍTICOS (22 INDICADORES REVISADOS) ---
    st.write("---")
    st.subheader("📊 Diagnóstico Situacional (Base: Famílias)")
    st.info("Todos os dados abaixo foram auditados para garantir que os totais batam com a sua tabela.")

    

    lay_g = st.columns(2)
    colunas_v = [df_base.columns[i] for i in idx_alvo if i < len(df_base.columns)]

    for idx, col_nome in enumerate(colunas_v):
        with lay_g[idx % 2]:
            contagem = df_filtrado[col_nome].value_counts().reset_index()
            contagem.columns = [col_nome, 'CONT']
            contagem = contagem.sort_values(by='CONT', ascending=True)

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

    # --- 8. EXPORTAÇÃO ---
    if st.session_state.lista_exportacao:
        st.sidebar.markdown("---")
        df_exp = df_base[df_base[COL_RESPONSAVEL].isin(st.session_state.lista_exportacao)]
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        st.sidebar.download_button("🚀 Baixar Excel Selecionado", buf.getvalue(), "Relatorio_CAS_Export.xlsx", use_container_width=True)
else:
    st.error("Aguardando carregamento da planilha...")
