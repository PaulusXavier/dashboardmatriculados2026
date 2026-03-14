import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS 2026 | Inteligência Social", layout="wide", page_icon="📊")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. ESTILO VISUAL PROFISSIONAL ---
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

# --- 3. CARREGAMENTO E LIMPEZA (LÓGICA DE LINHA = FAMÍLIA) ---
@st.cache_data
def load_and_clean_data():
    # Localiza o arquivo no repositório
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
        
        # Limpeza para unificar gráficos (Turnos, Renda, etc)
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', '', ' '], 'NÃO INFORMADO')
        return df
    except Exception as e:
        st.error(f"Erro ao ler os dados: {e}")
        return None

df_base = load_and_clean_data()

if df_base is not None:
    # DEFINIÇÃO DAS COLUNAS (Coluna Q = Nome do Responsável)
    COL_RESPONSAVEL = "NOME DO RESPONSÁVEL" 
    COL_PARTICIPANTE = "NOME DO PARTICIPANTE (ATIVIDADES)"
    
    # Índices dos 22 indicadores para os gráficos
    idx_alvo = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. CONTADORES (PROVA REAL: 292 FAMÍLIAS) ---
    # Consideramos cada linha preenchida na Coluna Q como uma família
    df_familias = df_base[df_base[COL_RESPONSAVEL] != "NÃO INFORMADO"]
    total_familias = len(df_familias) # Contagem direta por linha
    total_participantes = len(df_base[df_base[COL_PARTICIPANTE] != "NÃO INFORMADO"])

    st.markdown('<div class="main-header"><h1>Painel CAS 2026 | Gestão Unificada</h1><p>Diagnóstico Social Baseado em Unidades Familiares</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Total de Famílias</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Total de Participantes</div><div class="kpi-value">{total_participantes}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Exportação Ativa</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS ---
    st.write("---")
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        c_trab = "EXERCE ATIVIDADE REMUNERADA:"
        op_t = sorted(df_base[c_trab].unique())
        sel_t = st.multiselect("Filtrar Trabalho:", op_t, default=op_t)
    with f2:
        c_renda = "RENDA FAMILIAR TOTAL"
        op_r = sorted(df_base[c_renda].unique())
        sel_r = st.multiselect("Filtrar Renda:", op_r, default=op_r)

    # Dados filtrados mantendo a integridade das famílias
    df_f = df_familias[(df_familias[c_trab].isin(sel_t)) & (df_familias[c_renda].isin(sel_r))]
    
    with f3:
        # Resolve TypeError forçando texto
        nomes_lista = sorted([str(n) for n in df_f[COL_RESPONSAVEL].unique()])
        selecionado = st.selectbox("🔍 Pesquisar Família (Coluna Q):", ["SELECIONE..."] + nomes_lista)

    # --- 6. FICHA DO RESPONSÁVEL ---
    if selecionado != "SELECIONE...":
        st.write("---")
        # Puxa a linha exata daquela família
        dados = df_f[df_f[COL_RESPONSAVEL] == selecionado].iloc[0]
        
        c_tit, c_btn = st.columns([3, 1])
        c_tit.subheader(f"📄 Prontuário da Família: {selecionado}")
        
        if selecionado not in st.session_state.lista_exportacao:
            if c_btn.button("➕ Adicionar à Exportação"):
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()
        else:
            if c_btn.button("❌ Remover da Lista"):
                st.session_state.lista_exportacao.remove(selecionado)
                st.rerun()

        with st.expander("👁️ Detalhes Socioeconômicos da Linha", expanded=True):
            grid = st.columns(4)
            for i, col_name in enumerate(df_base.columns):
                with grid[i % 4]:
                    st.markdown(f'''<div style="background:white; padding:8px; border-radius:5px; border:1px solid #ddd; margin-bottom:5px;">
                        <small style="color:#64748b; font-weight:bold;">{col_name}</small><br>
                        <b style="font-size:0.85rem;">{dados[col_name]}</b>
                    </div>''', unsafe_allow_html=True)

    # --- 7. GRÁFICOS (BASEADOS NAS 292 LINHAS) ---
    st.write("---")
    st.subheader("📊 Diagnóstico dos 22 Indicadores Sociais")
    st.info("Nota: Cada barra reflete a contagem absoluta de famílias conforme os dados da Coluna Q.")

    

    cols_layout = st.columns(2)
    colunas_vis = [df_base.columns[i] for i in idx_alvo if i < len(df_base.columns)]

    for idx, col_nome in enumerate(colunas_vis):
        with cols_layout[idx % 2]:
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
        st.sidebar.download_button("🚀 Baixar Relatório Selecionado", buf.getvalue(), "Relatorio_CAS.xlsx", use_container_width=True)
else:
    st.error("Planilha não encontrada. Verifique os arquivos no seu repositório GitHub.")

else:
    st.error("Planilha 'Planilha Matriculados' não encontrada na raiz do repositório.")
