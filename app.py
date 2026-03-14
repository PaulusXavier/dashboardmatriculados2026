import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Inteligência Social", layout="wide", page_icon="🧠")

# Inicialização da lista de exportação
if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS DESIGN PREMIUM (Cores Fortes e Contraste) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f1f5f9; }
    .main-header {
        background: linear-gradient(135deg, #020617 0%, #1e3a8a 100%);
        padding: 35px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px;
    }
    .data-card { background: white; padding: 12px; border-radius: 10px; border: 2px solid #e2e8f0; margin-bottom: 8px; }
    .label-card { color: #475569; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; }
    .value-card { color: #0f172a; font-size: 0.85rem; font-weight: 700; }
    .stButton>button { background-color: #1e3a8a; color: white; border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LIMPEZA (BLINDAGEM CONTRA DADOS INCONSISTENTES) ---
@st.cache_data
def load_and_clean_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        
        # Limpa nomes de colunas
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        
        # Limpeza agressiva: remove espaços, converte para string e maiúsculo
        for col in df.columns:
            df[col] = df[col].fillna("NÃO INFORMADO").astype(str).str.strip().str.upper()
            
        return df.replace("NAN", "NÃO INFORMADO").replace("", "NÃO INFORMADO")
    except Exception as e:
        st.error(f"Erro ao processar planilha: {e}")
        return None

df_base = load_and_clean_data()

if df_base is not None:
    # DEFINIÇÃO DAS COLUNAS PELO NOME (Baseado no seu arquivo)
    COL_RESPONSAVEL = "NOME DO RESPONSÁVEL"
    COL_TRAMPO = "EXERCE ATIVIDADE REMUNERADA:"
    COL_RENDA = "RENDA FAMILIAR TOTAL"
    
    # Índices para os 22 gráficos solicitados
    indices_graficos = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. BARRA LATERAL: EXPORTAÇÃO ---
    st.sidebar.title("📤 Exportar Famílias")
    st.sidebar.write(f"Selecionadas: **{len(st.session_state.lista_exportacao)}**")
    
    if st.session_state.lista_exportacao:
        if st.sidebar.button("🗑️ Limpar Seleção"):
            st.session_state.lista_exportacao = []
            st.rerun()
            
        df_exp = df_base[df_base[COL_RESPONSAVEL].isin(st.session_state.lista_exportacao)]
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        
        st.sidebar.download_button("🚀 Baixar Excel Selecionado", output.getvalue(), "Relatorio_CAS_Triagem.xlsx", use_container_width=True)

    # --- 5. TOPO: FILTROS SOCIOECONÔMICOS ---
    st.markdown('<div class="main-header"><h1>Painel de Inteligência Social CAS</h1><p>Análise de Vulnerabilidade e Seleção de Famílias</p></div>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        f_trampo = st.multiselect("🛠️ Trabalha?", sorted(df_base[COL_TRAMPO].unique()), default=df_base[COL_TRAMPO].unique())
    with c2:
        f_renda = st.multiselect("💰 Faixa de Renda:", sorted(df_base[COL_RENDA].unique()), default=df_base[COL_RENDA].unique())
    
    # Filtragem Base
    df_filtrado = df_base[df_base[COL_TRAMPO].isin(f_trampo) & df_base[COL_RENDA].isin(f_renda)]
    
    with c3:
        # TRATAMENTO DO ERRO TYPEERROR: Converte para string antes de ordenar
        lista_nomes = sorted([str(x) for x in df_filtrado[COL_RESPONSAVEL].unique() if x != "NÃO INFORMADO"])
        selecionado = st.selectbox("🎯 Selecionar Responsável Familiar:", ["SELECIONE UM NOME..."] + lista_nomes)

    # --- 6. FICHA TÉCNICA E SELEÇÃO ---
    if selecionado != "SELECIONE UM NOME...":
        st.write("---")
        chefe = df_filtrado[df_filtrado[COL_RESPONSAVEL] == selecionado].iloc[0]
        
        col_txt, col_btn = st.columns([3, 1])
        col_txt.subheader(f"👤 Família de {selecionado}")
        
        if selecionado not in st.session_state.lista_exportacao:
            if col_btn.button("➕ Adicionar para Exportar"):
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()
        else:
            st.success("✅ Esta família está na sua lista de exportação.")
            if col_btn.button("❌ Remover da Lista"):
                st.session_state.lista_exportacao.remove(selecionado)
                st.rerun()

        with st.expander("📄 Ver Detalhes Completos da Família", expanded=True):
            cols = st.columns(4)
            for i, col_name in enumerate(df_base.columns):
                with cols[i % 4]:
                    st.markdown(f'''<div class="data-card">
                        <div class="label-card">{col_name}</div>
                        <div class="value-card">{chefe[col_name]}</div>
                    </div>''', unsafe_allow_html=True)

    # --- 7. GRÁFICOS (QUANTIFICAÇÃO COM CORES FORTES) ---
    st.write("---")
    st.subheader("📊 Estatísticas da População Filtrada")
    st.caption("Gráficos automáticos das 22 colunas estratégicas.")

    g_cols = st.columns(2)
    # Pega os nomes das colunas pelos índices que você forneceu
    colunas_graficos = [df_base.columns[i] for i in indices_graficos if i < len(df_base.columns)]

    for idx, col_nome in enumerate(colunas_graficos):
        with g_cols[idx % 2]:
            dados = df_filtrado[col_nome].value_counts().reset_index()
            dados.columns = [col_nome, 'QTD']
            
            # Gráfico com escala ICEFIRE (cores fortes: azul escuro, bordeaux e preto)
            fig = px.bar(
                dados, y=col_nome, x='QTD', orientation='h',
                title=f"DISTRIBUIÇÃO: {col_nome}",
                color='QTD', color_continuous_scale='icefire', text='QTD'
            )
            fig.update_layout(height=350, showlegend=False, coloraxis_showscale=False)
            fig.update_traces(textposition='outside', textfont=dict(weight='bold', color='black'))
            st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Arquivo não encontrado. Verifique se a planilha está na pasta correta.")
