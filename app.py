import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Gestão Unificada", layout="wide", page_icon="📊")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN DE ALTO IMPACTO (CONGRESSO) ---
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

# --- 3. LEITURA E PADRONIZAÇÃO DOS DADOS ---
@st.cache_data
def load_and_clean_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
        
        # Limpeza em todos os campos para evitar erros de Turno/Categorias
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', '', ' '], 'NÃO INFORMADO')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return None

df_base = load_and_clean_data()

if df_base is not None:
    # DEFINIÇÃO DE COLUNAS (Foco na Coluna Q - Índice 16)
    COL_PARTICIPANTE = df_base.columns[0]   # Coluna A
    COL_RESPONSAVEL = df_base.columns[16]  # Coluna Q
    
    # Lista das 22 colunas estratégicas para os gráficos
    idx_alvo = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. CONTADORES REVISADOS (292 FAMÍLIAS) ---
    # Filtramos as linhas onde o Nome do Responsável (Coluna Q) está presente
    df_familias = df_base[df_base[COL_RESPONSAVEL] != "NÃO INFORMADO"]
    total_familias = len(df_familias) # Contagem direta: 292 famílias
    total_participantes = len(df_base[df_base[COL_PARTICIPANTE] != "NÃO INFORMADO"])

    st.markdown('<div class="main-header"><h1>Painel CAS | Sistema Unificado</h1><p>Análise de Dados Baseada na Coluna Q (Responsáveis)</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Total de Famílias</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Total de Participantes</div><div class="kpi-value">{total_participantes}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Prontuários p/ Baixar</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS E BUSCA ---
    st.write("---")
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        c_trampo = "EXERCE ATIVIDADE REMUNERADA:"
        op_t = sorted(df_base[c_trampo].unique())
        sel_t = st.multiselect("Filtrar Trabalho:", op_t, default=op_t)
    with f2:
        c_renda = "RENDA FAMILIAR TOTAL"
        op_r = sorted(df_base[c_renda].unique())
        sel_r = st.multiselect("Filtrar Renda:", op_r, default=op_r)
    
    # Dados que alimentam os gráficos e a busca
    df_f = df_familias[(df_familias[c_trampo].isin(sel_t)) & (df_familias[c_renda].isin(sel_r))]
    
    with f3:
        # Força string para evitar erro no sorted
        nomes_lista = sorted([str(n) for n in df_f[COL_RESPONSAVEL].unique()])
        selecionado = st.selectbox("🔍 Localizar Responsável (Coluna Q):", ["SELECIONE..."] + nomes_lista)

    # --- 6. FICHA TÉCNICA UNIFICADA ---
    if selecionado != "SELECIONE...":
        st.write("---")
        dados = df_f[df_f[COL_RESPONSAVEL] == selecionado].iloc[0]
        
        c_tit, c_btn = st.columns([3, 1])
        c_tit.subheader(f"📄 Prontuário: {selecionado}")
        
        if selecionado not in st.session_state.lista_exportacao:
            if c_btn.button("➕ Incluir no Relatório"):
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()
        else:
            if c_btn.button("❌ Remover da Lista"):
                st.session_state.lista_exportacao.remove(selecionado)
                st.rerun()

        with st.expander("👁️ Ver Dados Completos da Unidade Familiar", expanded=True):
            grid = st.columns(4)
            for i, col_name in enumerate(df_base.columns):
                with grid[i % 4]:
                    st.markdown(f'''<div style="background:white; padding:8px; border-radius:5px; border:1px solid #ddd; margin-bottom:5px;">
                        <small style="color:#64748b; font-weight:bold;">{col_name}</small><br>
                        <b style="font-size:0.85rem;">{dados[col_name]}</b>
                    </div>''', unsafe_allow_html=True)

    # --- 7. REVISÃO GERAL DOS 22 GRÁFICOS ---
    st.write("---")
    st.subheader("📊 Diagnóstico Situacional (Auditoria de Dados)")
    st.info("Todos os gráficos consideram as 292 famílias identificadas na Coluna Q.")

    

    cols_layout = st.columns(2)
    colunas_graficos = [df_base.columns[i] for i in idx_alvo if i < len(df_base.columns)]

    for idx, col_nome in enumerate(colunas_graficos):
        with cols_layout[idx % 2]:
            # Contagem baseada nas famílias filtradas
            contagem = df_f[col_nome].value_counts().reset_index()
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
        st.sidebar.download_button("🚀 Baixar Excel das Selecionadas", buf.getvalue(), "Relatorio_CAS.xlsx", use_container_width=True)
else:
    st.error("Planilha não encontrada. Certifique-se de que o arquivo está na pasta.")
