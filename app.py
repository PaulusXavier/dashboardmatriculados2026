import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Inteligência Social", layout="wide", page_icon="🧠")

# Inicialização do "Carrinho de Exportação" no estado da sessão
if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN PREMIUM E CORES FORTES ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #020617 0%, #1e3a8a 100%);
        padding: 35px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px;
    }
    .stButton>button { border-radius: 10px; font-weight: 700; height: 3em; width: 100%; }
    .data-card { background: white; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 8px; }
    .label-card { color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; }
    .value-card { color: #0f172a; font-size: 0.8rem; font-weight: 700; }
    .sidebar-export { background: #f1f5f9; padding: 15px; border-radius: 12px; border: 1px solid #cbd5e1; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E NORMALIZAÇÃO (TRATAMENTO DE DADOS INCONSISTENTES) ---
@st.cache_data
def load_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        # Limpa espaços e padroniza para evitar duplicidade por erro de digitação
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
        return df.replace("NAN", "NÃO INFORMADO").replace("", "NÃO INFORMADO")
    except Exception as e:
        st.error(f"Erro Crítico: {e}")
        return None

df_base = load_data()

if df_base is not None:
    # MAPEAMENTO POR ÍNDICE (Garante que o gráfico funcione mesmo com nomes mudando)
    # B=1, C=2, E=4, G=6, H=7, J=9, K=10, L=11, N=13, R=17, S=18, T=19, U=20, V=21, X=23, Y=24, AB=27, AC=28, AD=29, AF=31, AH=33, AL=37
    indices_graficos = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]
    
    # Colunas de Filtro (Identificadas pelos nomes que você deu)
    COL_RESPONSAVEL = "NOME DO RESPONSÁVEL"
    COL_TRAMPO = "EXERCE ATIVIDADE REMUNERADA:"
    COL_RENDA = "RENDA FAMILIAR TOTAL"

    # --- 4. SIDEBAR: GESTÃO DE EXPORTAÇÃO ---
    st.sidebar.markdown("### 🚀 Exportar Selecionados")
    st.sidebar.write(f"Famílias na lista: **{len(st.session_state.lista_exportacao)}**")
    
    if st.session_state.lista_exportacao:
        if st.sidebar.button("🗑️ Limpar Lista"):
            st.session_state.lista_exportacao = []
            st.rerun()
            
        # Preparar arquivo para download
        df_export = df_base[df_base[COL_RESPONSAVEL].isin(st.session_state.lista_exportacao)]
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Triagem_CAS')
        
        st.sidebar.download_button(
            label="📥 BAIXAR EXCEL AGORA",
            data=output.getvalue(),
            file_name="Relatorio_Vulnerabilidade_CAS.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.sidebar.info("Adicione famílias para exportar o relatório.")

    # --- 5. TOPO: FILTROS E BUSCA ---
    st.markdown('<div class="main-header"><h1>Gestão de Vulnerabilidade Familiar | CAS</h1></div>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        op_trampo = sorted(df_base[COL_TRAMPO].unique())
        f_trampo = st.multiselect("🛠️ Trabalha?", op_trampo, default=op_trampo)
    with c2:
        op_renda = sorted(df_base[COL_RENDA].unique())
        f_renda = st.multiselect("💰 Renda Familiar:", op_renda, default=op_renda)
    
    df_filtrado = df_base[df_base[COL_TRAMPO].isin(f_trampo) & df_base[COL_RENDA].isin(f_renda)]
    
    with c3:
        lista_nomes = sorted(df_filtrado[COL_RESPONSAVEL].unique())
        selecionado = st.selectbox("🎯 Selecionar Responsável Familiar:", ["SELECIONE UM NOME..."] + lista_nomes)

    # --- 6. FICHA DO RESPONSÁVEL E BOTÃO DE SELEÇÃO ---
    if selecionado != "SELECIONE UM NOME...":
        st.write("---")
        # Pega a primeira linha desse responsável para a ficha técnica
        chefe = df_filtrado[df_filtrado[COL_RESPONSAVEL] == selecionado].iloc[0]
        
        col_info, col_sel = st.columns([3, 1])
        with col_info:
            st.subheader(f"👤 {selecionado}")
        with col_sel:
            if selecionado not in st.session_state.lista_exportacao:
                if st.button("➕ Adicionar para Relatório"):
                    st.session_state.lista_exportacao.append(selecionado)
                    st.rerun()
            else:
                st.success("✅ Família na Lista")
                if st.button("❌ Remover da Lista"):
                    st.session_state.lista_exportacao.remove(selecionado)
                    st.rerun()

        # Grid de Detalhes
        with st.expander("🔍 VER FICHA COMPLETA", expanded=True):
            cols = st.columns(4)
            for i, col_name in enumerate(df_base.columns):
                with cols[i % 4]:
                    st.markdown(f'''<div class="data-card">
                        <div class="label-card">{col_name}</div>
                        <div class="value-card">{chefe[col_name]}</div>
                    </div>''', unsafe_allow_html=True)

    # --- 7. GRÁFICOS (QUANTIFICAÇÃO NA BASE DA PÁGINA) ---
    st.write("---")
    st.subheader("📊 Diagnóstico Estatístico da População Filtrada")
    
    g_cols = st.columns(2)
    colunas_graficos = [df_base.columns[i] for i in indices_graficos if i < len(df_base.columns)]

    for idx, col_nome in enumerate(colunas_graficos):
        with g_cols[idx % 2]:
            dados = df_filtrado[col_nome].value_counts().reset_index()
            dados.columns = [col_nome, 'CONT']
            
            fig = px.bar(
                dados, y=col_nome, x='CONT', orientation='h',
                title=f"DISTRIBUIÇÃO: {col_nome}",
                color='CONT', color_continuous_scale='icefire', text='CONT'
            )
            fig.update_layout(height=350, showlegend=False, coloraxis_showscale=False, font=dict(size=10))
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Planilha não detectada. Por favor, carregue o arquivo no sistema.")
