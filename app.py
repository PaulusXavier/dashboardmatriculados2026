import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Inteligência Social", layout="wide", page_icon="📊")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS DE ALTO CONTRASTE ---
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
    .kpi-value { color: #1e3a8a; font-size: 2.6rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LIMPEZA (REVISÃO TOTAL DOS GRÁFICOS) ---
@st.cache_data
def load_and_clean_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        # Carrega os dados garantindo que tudo seja lido como texto inicialmente
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
        
        # LIMPEZA RIGOROSA: Resolve Turnos (Noturno/Tarde) e categorias duplicadas
        for col in df.columns:
            # Remove espaços no início/fim e espaços duplos no meio
            df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
            # Unifica valores vazios ou erros de leitura
            df[col] = df[col].replace(['NAN', 'NONE', '', ' '], 'NÃO INFORMADO')
        return df
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
        return None

df_base = load_and_clean_data()

if df_base is not None:
    # Nomes exatos das colunas conforme sua planilha
    COL_PARTICIPANTE = "NOME DO PARTICIPANTE (ATIVIDADES)"
    COL_RESPONSAVEL = "NOME DO RESPONSÁVEL"
    COL_TRAMPO = "EXERCE ATIVIDADE REMUNERADA:"
    COL_RENDA = "RENDA FAMILIAR TOTAL"
    
    # Índices das 22 colunas solicitadas
    idx_alvo = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. CONTADORES (RECUPERAÇÃO DOS 292 REGISTROS) ---
    # Contamos cada linha que tem um responsável como uma unidade de atendimento familiar
    df_familias_validas = df_base[df_base[COL_RESPONSAVEL] != "NÃO INFORMADO"]
    total_familias = len(df_familias_validas) 
    total_participantes = len(df_base[df_base[COL_PARTICIPANTE] != "NÃO INFORMADO"])

    st.markdown('<div class="main-header"><h1>Painel de Inteligência Social | CAS</h1><p>Congresso 2026 - Auditoria e Diagnóstico</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Total de Famílias</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Total de Participantes</div><div class="kpi-value">{total_participantes}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Lista de Exportação</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS ---
    st.write("---")
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        op_t = sorted(df_base[COL_TRAMPO].unique())
        sel_t = st.multiselect("Trabalho Remunerado", op_t, default=op_t)
    with f2:
        op_r = sorted(df_base[COL_RENDA].unique())
        sel_r = st.multiselect("Renda Familiar", op_r, default=op_r)
    
    df_f = df_familias_validas[(df_familias_validas[COL_TRAMPO].isin(sel_t)) & (df_familias_validas[COL_RENDA].isin(sel_r))]
    
    with f3:
        # Resolve o TypeError garantindo que tudo seja String antes de ordenar
        nomes_limpos = sorted([str(n) for n in df_f[COL_RESPONSAVEL].unique()])
        selecionado = st.selectbox("🎯 Selecionar Responsável:", ["SELECIONE..."] + nomes_limpos)

    # --- 6. FICHA E EXPORTAÇÃO ---
    if selecionado != "SELECIONE...":
        st.write("---")
        dados_f = df_f[df_f[COL_RESPONSAVEL] == selecionado].iloc[0]
        
        c_t, c_b = st.columns([3, 1])
        c_t.subheader(f"📂 Prontuário: {selecionado}")
        
        if selecionado not in st.session_state.lista_exportacao:
            if c_b.button("➕ Adicionar para Relatório"):
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()
        else:
            if c_b.button("❌ Remover da Lista"):
                st.session_state.lista_exportacao.remove(selecionado)
                st.rerun()

        with st.expander("👁️ Ver Dados Detalhados", expanded=True):
            grid = st.columns(4)
            for i, col_nm in enumerate(df_base.columns):
                with grid[i % 4]:
                    st.markdown(f'''<div style="background:white; padding:8px; border-radius:5px; border:1px solid #ddd; margin-bottom:5px;">
                        <small style="color:#888; font-weight:bold;">{col_nm}</small><br>
                        <b style="font-size:0.85rem;">{dados_f[col_nm]}</b>
                    </div>''', unsafe_allow_html=True)

    # --- 7. GRÁFICOS UNIFICADOS (REVISÃO DE QUANTIDADE) ---
    st.write("---")
    st.subheader("📊 Diagnóstico Situacional (Quantificação Absoluta)")
    
    

    g_layout = st.columns(2)
    colunas_graficos = [df_base.columns[i] for i in idx_alvo if i < len(df_base.columns)]

    for idx, col_nome in enumerate(colunas_graficos):
        with g_layout[idx % 2]:
            # Agrupamento e contagem
            contagem = df_f[col_nome].value_counts().reset_index()
            contagem.columns = [col_nome, 'QTD']
            contagem = contagem.sort_values(by='QTD', ascending=True)

            fig = px.bar(
                contagem, y=col_nome, x='QTD', orientation='h',
                title=f"INDICADOR: {col_nome}",
                color='QTD', color_continuous_scale='icefire', text='QTD'
            )
            fig.update_layout(
                height=350, showlegend=False, coloraxis_showscale=False,
                margin=dict(l=0, r=50, t=40, b=20),
                yaxis={'categoryorder':'total ascending'}
            )
            fig.update_traces(textposition='outside', textfont=dict(weight='bold', color='black'))
            st.plotly_chart(fig, use_container_width=True)

    # --- 8. DOWNLOAD (SIDEBAR) ---
    if st.session_state.lista_exportacao:
        st.sidebar.markdown("---")
        df_exp = df_base[df_base[COL_RESPONSAVEL].isin(st.session_state.lista_exportacao)]
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        st.sidebar.download_button("🚀 Baixar Relatório Selecionado", buf.getvalue(), "Relatorio_CAS_Unificado.xlsx", use_container_width=True)
else:
    st.error("Planilha não encontrada. Verifique o arquivo na pasta.")
