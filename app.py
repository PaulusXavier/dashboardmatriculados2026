import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Sistema de Inteligência Social", layout="wide", page_icon="🧠")

# --- 2. CSS PARA DESIGN PREMIUM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 30px; border-radius: 20px; color: white; text-align: center; margin-bottom: 20px;
    }
    .kpi-container { background: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; text-align: center; }
    .data-card { background: white; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 10px; }
    .label-card { color: #94a3b8; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; }
    .value-card { color: #1e293b; font-size: 0.85rem; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO DOS DADOS (BLINDADO) ---
@st.cache_data
def load_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip() for c in df.columns]
        return df.fillna("Não Informado").replace("nan", "Não Informado")
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return None

df_base = load_data()

if df_base is not None:
    # MAPEAMENTO POR ÍNDICE (Letras para Números)
    # A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7, I=8, J=9, K=10, L=11, M=12, N=13...
    # R=17, S=18, T=19, U=20, V=21, W=22, X=23, Y=24... AB=27, AC=28, AD=29, AE=30, AF=31, AG=32, AH=33... AL=37
    
    COL_RESPONSAVEL = df_base.columns[16] # Coluna Q (Aproximada para Nome do Responsável)
    COL_TRAMPO = df_base.columns[25]      # Coluna Z (Exerce atividade remunerada)
    COL_RENDA = df_base.columns[26]       # Coluna AA (Renda familiar)
    
    # Índices das colunas para os gráficos solicitados
    indices_graficos = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. CABEÇALHO E FILTROS (TOPO DA PÁGINA) ---
    st.markdown('<div class="main-header"><h1>Painel de Vulnerabilidade CAS 2026</h1></div>', unsafe_allow_html=True)
    
    with st.container():
        f1, f2, f3 = st.columns([1, 1, 2])
        with f1:
            opcoes_trampo = sorted(df_base[COL_TRAMPO].unique())
            filtro_trampo = st.multiselect("🛠️ Trabalha?", opcoes_trampo, default=opcoes_trampo)
        with f2:
            opcoes_renda = sorted(df_base[COL_RENDA].unique())
            filtro_renda = st.multiselect("💰 Faixa de Renda:", opcoes_renda, default=opcoes_renda)
        
        # Aplicação dos filtros antes da busca por responsável
        df_filtrado = df_base[df_base[COL_TRAMPO].isin(filtro_trampo) & df_base[COL_RENDA].isin(filtro_renda)]
        
        with f3:
            lista_responsaveis = sorted(df_filtrado[COL_RESPONSAVEL].unique())
            selecionado = st.selectbox("🔍 Pesquisar Responsável Familiar:", ["Selecione..."] + lista_responsaveis)

    # --- 5. FICHA TÉCNICA (CENTRO) ---
    if selecionado != "Selecione...":
        st.write("---")
        chefe = df_filtrado[df_filtrado[COL_RESPONSAVEL] == selecionado].iloc[0]
        st.subheader(f"📄 Prontuário Familiar: {selecionado}")
        
        # Mostrar todas as colunas da família em um grid
        exp_cols = st.columns(4)
        for i, col_name in enumerate(df_base.columns):
            with exp_cols[i % 4]:
                st.markdown(f'''<div class="data-card">
                    <div class="label-card">{col_name}</div>
                    <div class="value-card">{chefe[col_name]}</div>
                </div>''', unsafe_allow_html=True)
        
        st.markdown(f"**Membros da Família:** {len(df_base[df_base[COL_RESPONSAVEL] == selecionado])} pessoa(s) matriculada(s).")

    # --- 6. GRÁFICOS ANALÍTICOS (FINAL DA PÁGINA) ---
    st.write("---")
    st.subheader("📊 Diagnóstico Social (Colunas Selecionadas)")
    st.info("Os gráficos abaixo refletem os filtros de Emprego e Renda aplicados no topo.")

    # Criar grid de gráficos (2 por linha)
    g_cols = st.columns(2)
    
    # Filtrar apenas colunas que existem no arquivo para evitar erros de índice
    colunas_graficos = [df_base.columns[i] for i in indices_graficos if i < len(df_base.columns)]

    for idx, col_nome in enumerate(colunas_graficos):
        with g_cols[idx % 2]:
            # Contagem de dados
            dados_grafico = df_filtrado[col_nome].value_counts().reset_index()
            dados_grafico.columns = [col_nome, 'Frequência']
            
            # Limitar para não poluir
            if len(dados_grafico) > 10:
                dados_grafico = dados_grafico.head(10)

            fig = px.bar(
                dados_grafico, 
                y=col_nome, 
                x='Frequência', 
                orientation='h',
                title=f"Distribuição: {col_nome}",
                color='Frequência',
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Planilha não detectada. Verifique o nome do arquivo.")
