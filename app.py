import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Sociodemográfico - SETRABES/CAS", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .card-leitura {
        background-color: #f1f5f9;
        padding: 22px;
        border-radius: 12px;
        border: 2px solid #1e3a8a;
        margin-bottom: 15px;
    }
    .texto-preto { color: #000000 !important; font-size: 16px; font-weight: 600; }
    .titulo-card { color: #1e3a8a !important; font-weight: bold; font-size: 19px; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; }
    .metric-container {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white; padding: 25px; border-radius: 15px; text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO E NORMALIZAÇÃO (CORREÇÃO DO ERRO DE CONTAGEM)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Ajuste o nome do arquivo abaixo se necessário
CAMINHO = os.path.join(BASE_DIR, "Planilha Matriculados.xlsx")

@st.cache_data
def carregar_dados_limpos(caminho):
    if not os.path.exists(caminho): return None
    try:
        # Se for CSV (como o que você subiu), usamos read_csv. Se for Excel, read_excel.
        if caminho.endswith('.csv'):
            df = pd.read_csv(caminho, dtype=str)
        else:
            df = pd.read_excel(caminho, dtype=str)
    except:
        return None

    # Limpeza de nomes de colunas
    df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    
    # --- CORREÇÃO DO ERRO DE CONTAGEM (COLUNA T - NOME DO RESPONSÁVEL) ---
    col_resp = "NOME DO RESPONSÁVEL:"
    if col_resp in df.columns:
        # Remove espaços extras e padroniza para MAIÚSCULAS
        df[col_resp] = df[col_resp].str.strip().str.upper()
    
    return df

df = carregar_dados_limpos(CAMINHO)

if df is not None:
    # Mapeamento de Colunas
    col_resp = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trampo = "EXERCE ATIVIDADE REMUNERADA:"
    col_nacionalidade = "NACIONALIDADE:"
    col_est_civil = "ESTADO CIVIL:"
    
    # CRIAÇÃO DA BASE DE RESPONSÁVEIS ÚNICOS (MÉTRICA REAL)
    # Aqui é onde garantimos que os 292 (ou número real) apareçam corretamente
    df_unicos = df.drop_duplicates(subset=[col_resp]).copy()

    # --- INDICADORES DE TOPO ---
    st.write("### 📊 Estatísticas Consolidadas (Coluna T)")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="metric-container"><h4>👨‍👩‍👧‍👦 Total de Famílias (Responsáveis Únicos)</h4><h2 style="font-size: 48px;">{len(df_unicos)}</h2></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-container"><h4>📝 Total de Indivíduos Matriculados</h4><h2 style="font-size: 48px;">{len(df)}</h2></div>', unsafe_allow_html=True)

    st.write("---")

    # --- BARRA LATERAL: FILTROS ---
    st.sidebar.header("⚖️ Filtros de Prioridade")
    
    rank_map = {"SEM RENDA": 0, "ATÉ R$ 405,26": 1, "DE R$ 405,26 A R$ 810,50": 2, "DE R$ 810,50 A R$ 1.215,76": 3}
    
    f_renda = st.sidebar.selectbox("Renda Familiar:", ["Todos"] + list(rank_map.keys()))
    
    # Filtragem
    df_lista = df_unicos.copy()
    if f_renda != "Todos":
        df_lista = df_lista[df_lista[col_renda] == f_renda]
    
    # Ordenar por vulnerabilidade
    df_lista['rank'] = df_lista[col_renda].map(lambda x: rank_map.get(str(x).upper(), 99))
    lista_nomes = df_lista.sort_values(by=['rank', col_resp])[col_resp].tolist()
    
    selecionado = st.sidebar.selectbox("👤 Buscar Responsável:", ["Selecione..."] + lista_nomes)

    # --- PAINEL PRINCIPAL ---
    if selecionado != "Selecione...":
        dados_familia = df[df[col_resp] == selecionado]
        chefe = df_unicos[df_unicos[col_resp] == selecionado].iloc[0]

        # CARDS COM ALTO CONTRASTE (Letra Preta)
        r1, r2 = st.columns(2)
        with r1:
            st.markdown(f"""<div class="card-leitura"><div class="titulo-card">📍 Localização</div>
                <p class="texto-preto"><b>Endereço:</b> {chefe.get('ENDEREÇO COMPLETO:', 'N/A')}</p>
                <p class="texto-preto"><b>Bairro:</b> {chefe.get('BAIRRO:', 'N/A')}</p>
                <p class="texto-preto"><b>Nacionalidade:</b> {chefe.get(col_nacionalidade, 'N/A')}</p></div>""", unsafe_allow_html=True)
        with r2:
            st.markdown(f"""<div class="card-leitura"><div class="titulo-card">💰 Socioeconômico</div>
                <p class="texto-preto"><b>Renda:</b> {chefe.get(col_renda, 'N/A')}</p>
                <p class="texto-preto"><b>Trabalha:</b> {chefe.get(col_trampo, 'N/A')}</p>
                <p class="texto-preto"><b>Estado Civil:</b> {chefe.get(col_est_civil, 'N/A')}</p></div>""", unsafe_allow_html=True)

        # EXPANSÃO TOTAL DAS 56 COLUNAS
        with st.expander("📂 CLIQUE AQUI PARA VER TODOS OS 56 CAMPOS DA TABELA (EXPANSÃO TOTAL)", expanded=False):
            st.dataframe(dados_familia, use_container_width=True)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                dados_familia.to_excel(writer, index=False)
            st.download_button(f"📥 Baixar Ficha de {selecionado}", output.getvalue(), f"{selecionado}.xlsx")

    # --- GRÁFICOS (PRECISÃO TOTAL BASEADA NO RESPONSÁVEL) ---
    st.write("###")
    st.divider()
    st.markdown("## 📊 Perfil dos Responsáveis Familiares (Coluna T)")
    
    

    g1, g2 = st.columns(2)
    with g1:
        fig1 = px.bar(df_unicos['GÊNERO:'].value_counts().reset_index(), x='GÊNERO:', y='count', text='count', 
                     title="Gênero dos Chefes de Família", color_discrete_sequence=['#1e3a8a'])
        fig1.update_traces(textposition='outside')
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        fig2 = px.bar(df_unicos[col_renda].value_counts().reset_index(), x=col_renda, y='count', text='count', 
                     title="Distribuição de Renda (Por Família)", color_discrete_sequence=['#be123c'])
        fig2.update_traces(textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)

    g3, g4 = st.columns(2)
    with g3:
        fig3 = px.bar(df_unicos[col_nacionalidade].value_counts().reset_index(), x=col_nacionalidade, y='count', text='count', 
                     title="Nacionalidade das Famílias", color_discrete_sequence=['#f59e0b'])
        fig3.update_traces(textposition='outside')
        st.plotly_chart(fig3, use_container_width=True)
    with g4:
        fig4 = px.bar(df_unicos[col_est_civil].value_counts().reset_index(), x=col_est_civil, y='count', text='count', 
                     title="Estado Civil dos Responsáveis", color_discrete_sequence=['#10b981'])
        fig4.update_traces(textposition='outside')
        st.plotly_chart(fig4, use_container_width=True)

else:
    st.error("⚠️ Planilha não encontrada ou erro na leitura.")
