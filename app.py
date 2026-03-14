import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dashboard CAS - SETRABES", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .card-leitura {
        background-color: #f8fafc;
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

# 2. CARREGAMENTO E FILTRAGEM PELA COLUNA T
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO = os.path.join(BASE_DIR, "Planilha Matriculados.xlsx")

@st.cache_data
def carregar_dados_estatisticos(caminho):
    if not os.path.exists(caminho): return None
    try:
        # Lê o arquivo (seja CSV ou Excel)
        if caminho.endswith('.csv'): df = pd.read_csv(caminho, dtype=str)
        else: df = pd.read_excel(caminho, dtype=str)
    except: return None

    # Limpeza de nomes de colunas
    df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    
    # REGRA DE OURO: Só conta se a Coluna T (NOME DO RESPONSÁVEL:) estiver preenchida
    col_t = "NOME DO RESPONSÁVEL:"
    if col_t in df.columns:
        # Criamos um DataFrame que contém APENAS as linhas onde o responsável está preenchido
        df_base_estatistica = df[df[col_t].notna() & (df[col_t].str.strip() != "")].copy()
        return df, df_base_estatistica
    return df, df

df_completo, df_responsaveis = carregar_dados_estatisticos(CAMINHO)

if df_completo is not None:
    # Identificação das colunas (conforme sua planilha)
    col_resp = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_nacionalidade = "NACIONALIDADE:"
    col_est_civil = "ESTADO CIVIL:"
    col_genero = "GÊNERO:" # Coluna de gênero do responsável na linha da coluna T
    col_trampo = "EXERCE ATIVIDADE REMUNERADA:"

    # --- INDICADORES DE TOPO ---
    st.write("### 📊 Monitoramento de Impacto Social")
    c1, c2 = st.columns(2)
    with c1:
        # Este número deve bater com seus 292
        st.markdown(f'<div class="metric-container"><h4>👨‍👩‍👧‍👦 Total de Responsáveis (Coluna T Preenchida)</h4><h2 style="font-size: 48px;">{len(df_responsaveis)}</h2></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-container"><h4>📝 Total de Matriculados (Geral)</h4><h2 style="font-size: 48px;">{len(df_completo)}</h2></div>', unsafe_allow_html=True)

    st.write("---")

    # --- BARRA LATERAL: FILTRO DE BUSCA ---
    st.sidebar.header("🔍 Localizar Cadastro")
    # Lista de nomes únicos para o seletor (baseado apenas nos responsáveis válidos)
    nomes_para_busca = sorted(df_responsaveis[col_resp].unique().tolist())
    selecionado = st.sidebar.selectbox("Escolha o Responsável:", ["Selecione..."] + nomes_para_busca)

    # --- PAINEL PRINCIPAL ---
    if selecionado != "Selecione...":
        # Dados de quem foi selecionado (pode ter várias linhas se houver dependentes)
        dados_familia = df_completo[df_completo[col_resp] == selecionado]
        # Pegamos a linha onde o nome dele aparece na Coluna T para os cards
        info_chefe = df_responsaveis[df_responsaveis[col_resp] == selecionado].iloc[0]

        r1, r2 = st.columns(2)
        with r1:
            st.markdown(f"""<div class="card-leitura"><div class="titulo-card">📍 Dados de Identificação</div>
                <p class="texto-preto"><b>Responsável:</b> {selecionado}</p>
                <p class="texto-preto"><b>Bairro:</b> {info_chefe.get('BAIRRO:', 'Não Informado')}</p>
                <p class="texto-preto"><b>Nacionalidade:</b> {info_chefe.get(col_nacionalidade, 'Não Informado')}</p></div>""", unsafe_allow_html=True)
        with r2:
            st.markdown(f"""<div class="card-leitura"><div class="titulo-card">💰 Perfil da Família</div>
                <p class="texto-preto"><b>Renda Familiar:</b> {info_chefe.get(col_renda, 'Não Informado')}</p>
                <p class="texto-preto"><b>Atividade Remunerada:</b> {info_chefe.get(col_trampo, 'Não Informado')}</p>
                <p class="texto-preto"><b>Estado Civil:</b> {info_chefe.get(col_est_civil, 'Não Informado')}</p></div>""", unsafe_allow_html=True)

        # EXPANSÃO 100% PARA AS 56 COLUNAS
        with st.expander("📂 CLIQUE PARA VER TODOS OS 56 CAMPOS DA TABELA (VISUALIZAÇÃO COMPLETA)", expanded=False):
            st.dataframe(dados_familia, use_container_width=True)
            
            # Botão de Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                dados_familia.to_excel(writer, index=False)
            st.download_button(f"📥 Exportar Ficha de {selecionado}", output.getvalue(), f"{selecionado}.xlsx")

    # --- SEÇÃO DE GRÁFICOS (TOTALMENTE BASEADA NA COLUNA T PREENCHIDA) ---
    st.write("###")
    st.divider()
    st.markdown(f"## 📊 Diagnóstico Estatístico (N = {len(df_responsaveis)} Famílias)")
    st.info("Atenção: Os gráficos abaixo contabilizam apenas os dados contidos nas linhas onde a Coluna T (Responsável) está preenchida.")

    

    g1, g2 = st.columns(2)
    with g1:
        # Gênero - Buscando na coluna GÊNERO da linha do responsável
        fig1 = px.bar(df_responsaveis[col_genero].value_counts().reset_index(), x=col_genero, y='count', text='count', 
                     title="Gênero dos Responsáveis", color_discrete_sequence=['#1e3a8a'])
        fig1.update_traces(textposition='outside')
        st.plotly_chart(fig1, use_container_width=True)
    with g2:
        # Renda - Buscando na linha do responsável
        fig2 = px.bar(df_responsaveis[col_renda].value_counts().reset_index(), x=col_renda, y='count', text='count', 
                     title="Renda Familiar Total", color_discrete_sequence=['#be123c'])
        fig2.update_traces(textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)

    g3, g4 = st.columns(2)
    with g3:
        # Nacionalidade - Buscando na linha do responsável
        fig3 = px.bar(df_responsaveis[col_nacionalidade].value_counts().reset_index(), x=col_nacionalidade, y='count', text='count', 
                     title="Nacionalidade dos Responsáveis", color_discrete_sequence=['#f59e0b'])
        fig3.update_traces(textposition='outside')
        st.plotly_chart(fig3, use_container_width=True)
    with g4:
        # Estado Civil - Buscando na linha do responsável
        fig4 = px.bar(df_responsaveis[col_est_civil].value_counts().reset_index(), x=col_est_civil, y='count', text='count', 
                     title="Estado Civil dos Responsáveis", color_discrete_sequence=['#10b981'])
        fig4.update_traces(textposition='outside')
        st.plotly_chart(fig4, use_container_width=True)

else:
    st.error("Não foi possível carregar a base de dados.")
