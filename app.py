import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dashboard CAS - SETRABES", layout="wide")

# Estilo para leitura clara e contraste
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

# 2. CARREGAMENTO E FILTRAGEM (LÓGICA DA COLUNA T)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Tenta localizar o arquivo (Excel ou CSV)
NOME_ARQUIVO = "Planilha Matriculados.xlsx"
CAMINHO = os.path.join(BASE_DIR, NOME_ARQUIVO)

@st.cache_data
def carregar_dados_robustos(caminho):
    # Verificação de existência do arquivo para evitar o TypeError
    if not os.path.exists(caminho):
        # Se não achar o .xlsx, tenta procurar o .csv que o Streamlit pode ter gerado
        caminho_csv = caminho.replace(".xlsx", ".xlsx - Planilha1.csv")
        if not os.path.exists(caminho_csv):
            return None, None
        caminho = caminho_csv

    try:
        if caminho.endswith('.csv'):
            df = pd.read_csv(caminho, dtype=str)
        else:
            df = pd.read_excel(caminho, dtype=str)
        
        # Limpeza de nomes de colunas
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        
        # REGRA SOLICITADA: Base baseada na Coluna T (NOME DO RESPONSÁVEL:)
        col_t = "NOME DO RESPONSÁVEL:"
        if col_t in df.columns:
            # Filtra apenas linhas onde a coluna T não está vazia
            df_estatistico = df[df[col_t].notna() & (df[col_t].str.strip() != "")].copy()
            return df, df_estatistico
        return df, df
    except Exception as e:
        return None, None

# Desempacotamento seguro
df_geral, df_estatistico = carregar_dados_robustos(CAMINHO)

if df_geral is not None and df_estatistico is not None:
    # Nomes das colunas para os gráficos
    col_t = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_nacionalidade = "NACIONALIDADE:"
    col_est_civil = "ESTADO CIVIL:"
    col_genero = "GÊNERO:" 

    # Indicadores de Topo
    st.write("### 📊 Estatísticas Consolidadas")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="metric-container"><h4>👨‍👩‍👧‍👦 Total de Responsáveis (Coluna T Preenchida)</h4><h2 style="font-size: 50px;">{len(df_estatistico)}</h2></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-container"><h4>📝 Total de Matrículas (Geral)</h4><h2 style="font-size: 50px;">{len(df_geral)}</h2></div>', unsafe_allow_html=True)

    st.write("---")

    # Barra Lateral
    st.sidebar.header("🔍 Busca por Responsável")
    nomes_unicos = sorted(df_estatistico[col_t].unique().tolist())
    selecionado = st.sidebar.selectbox("Escolha um nome:", ["Selecione..."] + nomes_unicos)

    if selecionado != "Selecione...":
        dados_f = df_geral[df_geral[col_t] == selecionado]
        chefe = df_estatistico[df_estatistico[col_t] == selecionado].iloc[0]

        # Cards com letras Pretas (Contraste Máximo)
        r1, r2 = st.columns(2)
        with r1:
            st.markdown(f"""<div class="card-leitura"><div class="titulo-card">🏠 Identificação</div>
                <p class="texto-preto"><b>Nome:</b> {selecionado}</p>
                <p class="texto-preto"><b>Nacionalidade:</b> {chefe.get(col_nacionalidade, 'N/A')}</p>
                <p class="texto-preto"><b>Bairro:</b> {chefe.get('BAIRRO:', 'N/A')}</p></div>""", unsafe_allow_html=True)
        with r2:
            st.markdown(f"""<div class="card-leitura"><div class="titulo-card">💰 Dados Sociais</div>
                <p class="texto-preto"><b>Renda:</b> {chefe.get(col_renda, 'N/A')}</p>
                <p class="texto-preto"><b>Estado Civil:</b> {chefe.get(col_est_civil, 'N/A')}</p>
                <p class="texto-preto"><b>Trabalha:</b> {chefe.get('EXERCE ATIVIDADE REMUNERADA:', 'N/A')}</p></div>""", unsafe_allow_html=True)

        with st.expander("📂 CLIQUE PARA EXPANSÃO TOTAL (56 CAMPOS)", expanded=False):
            st.dataframe(dados_f, use_container_width=True)

    # GRÁFICOS BASEADOS EXCLUSIVAMENTE NA LINHA DO RESPONSÁVEL (COLUNA T)
    st.write("###")
    st.divider()
    st.markdown(f"## 📊 Perfil Sociodemográfico ({len(df_estatistico)} Famílias)")
    
    

    g1, g2 = st.columns(2)
    with g1:
        # Gênero
        fig1 = px.bar(df_estatistico[col_genero].value_counts().reset_index(), 
                     x=col_genero, y='count', text='count', title="Gênero dos Responsáveis", 
                     color_discrete_sequence=['#1e3a8a'])
        fig1.update_traces(textposition='outside')
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        # Renda
        fig2 = px.bar(df_estatistico[col_renda].value_counts().reset_index(), 
                     x=col_renda, y='count', text='count', title="Renda Familiar", 
                     color_discrete_sequence=['#be123c'])
        fig2.update_traces(textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)

    g3, g4 = st.columns(2)
    with g3:
        # Nacionalidade
        fig3 = px.bar(df_estatistico[col_nacionalidade].value_counts().reset_index(), 
                     x=col_nacionalidade, y='count', text='count', title="Nacionalidade", 
                     color_discrete_sequence=['#f59e0b'])
        fig3.update_traces(textposition='outside')
        st.plotly_chart(fig3, use_container_width=True)
    with g4:
        # Estado Civil
        fig4 = px.bar(df_estatistico[col_est_civil].value_counts().reset_index(), 
                     x=col_est_civil, y='count', text='count', title="Estado Civil", 
                     color_discrete_sequence=['#10b981'])
        fig4.update_traces(textposition='outside')
        st.plotly_chart(fig4, use_container_width=True)

else:
    st.error("ERRO: O arquivo 'Planilha Matriculados.xlsx' não foi encontrado ou está inacessível. Verifique se o nome do arquivo no GitHub/Streamlit Cloud está idêntico.")
