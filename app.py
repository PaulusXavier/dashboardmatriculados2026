import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO E ESTILO INSTITUCIONAL
st.set_page_config(page_title="Gestão CAS/SETRABES", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .card-info {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .header-card { font-size: 18px; font-weight: bold; color: #1e40af; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 15px; }
    .alerta-vulnerabilidade {
        background: linear-gradient(90deg, #be123c 0%, #fb7185 100%);
        color: white; padding: 15px; border-radius: 10px; text-align: center;
        font-weight: bold; font-size: 20px; margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO DOS DADOS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO = os.path.join(BASE_DIR, "Planilha Matriculados.xlsx")

@st.cache_data
def carregar_dados(caminho):
    if not os.path.exists(caminho): return None
    try:
        df = pd.read_excel(caminho, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        return df
    except: return None

df = carregar_dados(CAMINHO)

if df is not None:
    # Definição de Colunas Chave
    col_resp = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trampo = "EXERCE ATIVIDADE REMUNERADA:"
    col_moradia = "SITUAÇÃO DA MORADIA:"
    col_benef = "A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:"
    col_genero = "GÊNERO:"

    # Criar um DataFrame focado apenas nos Responsáveis (1 linha por família)
    # Isso garante que os gráficos não fiquem confusos ou duplicados
    df_responsaveis = df.drop_duplicates(subset=[col_resp]).copy()

    # Ranking de Renda para ordenação inteligente
    rank_map = {"SEM RENDA": 0, "ATÉ R$ 405,26": 1, "DE R$ 405,26 A R$ 810,50": 2, "DE R$ 810,50 A R$ 1.215,76": 3}
    df_responsaveis['rank'] = df_responsaveis[col_renda].map(lambda x: rank_map.get(str(x).upper(), 99))

    # --- BARRA LATERAL: FILTROS ---
    st.sidebar.title("🛡️ Filtros de Triagem")
    f_renda = st.sidebar.selectbox("Filtrar por Renda:", ["Todos"] + list(rank_map.keys()))
    f_trampo = st.sidebar.selectbox("Filtrar por Trabalho:", ["Todos"] + (df_responsaveis[col_trampo].unique().tolist() if col_trampo in df_responsaveis.columns else []))

    # Aplicar filtros à lista de nomes
    df_lista = df_responsaveis.copy()
    if f_renda != "Todos": df_lista = df_lista[df_lista[col_renda] == f_renda]
    if f_trampo != "Todos": df_lista = df_lista[df_lista[col_trampo] == f_trampo]

    # Lista final ordenada pelos mais vulneráveis
    lista_nomes = df_lista.sort_values(by=['rank', col_resp])[col_resp].tolist()

    st.sidebar.divider()
    selecionado = st.sidebar.selectbox("🎯 Selecione o Responsável:", ["Selecione..."] + lista_nomes)

    # --- ÁREA PRINCIPAL: CONSULTA ---
    st.markdown("<h1 style='color: #1e3a8a;'>Sociodemográfico das Famílias Matriculadas</h1>", unsafe_allow_html=True)
    
    if selecionado != "Selecione...":
        # Dados da família completa para a tabela, mas cards baseados no responsável
        dados_familia_completa = df[df[col_resp] == selecionado]
        dados_chefe = df_responsaveis[df_responsaveis[col_resp] == selecionado].iloc[0]
        
        renda_at = str(dados_chefe[col_renda]).upper()

        # Alerta de Risco
        if rank_map.get(renda_at, 99) <= 1:
            st.markdown(f'<div class="alerta-vulnerabilidade">🚨 PRIORIDADE SOCIAL: Família em situação de {renda_at}</div>', unsafe_allow_html=True)

        # Cards Informativos
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class="card-info"><div class="header-card">📍 Localização</div>
                <p><b>Endereço:</b> {dados_chefe.get('ENDEREÇO COMPLETO:', 'N/A')}</p>
                <p><b>Bairro:</b> {dados_chefe.get('BAIRRO:', 'N/A')}</p></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="card-info"><div class="header-card">💰 Dados do Responsável</div>
                <p><b>Renda:</b> {renda_at}</p>
                <p><b>Trabalha:</b> {dados_chefe.get(col_trampo, 'N/A')}</p>
                <p><b>Benefício Social:</b> {dados_chefe.get(col_benef, 'N/A')}</p></div>""", unsafe_allow_html=True)

        st.subheader("👥 Composição do Núcleo Familiar")
        st.dataframe(dados_familia_completa[['NOME:', 'IDADE:', 'GÊNERO:', 'GRAU DE PARENTESCO:']], use_container_width=True, hide_index=True)

        # Exportação Individual
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            dados_familia_completa.to_excel(writer, index=False)
        st.download_button("📥 Exportar Ficha em Excel", output.getvalue(), f"Ficha_{selecionado}.xlsx")

        with st.expander("🔍 Ver todos os 56 campos da planilha"):
            st.dataframe(dados_familia_completa)

    # --- SEÇÃO DE GRÁFICOS (BASEADA APENAS NOS RESPONSÁVEIS) ---
    st.write("###")
    st.divider()
    st.markdown("<h2 style='text-align: center; color: #475569;'>📊 Perfil Sociodemográfico (Base: Responsáveis Familiares)</h2>", unsafe_allow_html=True)
    st.info("Nota técnica: Os gráficos abaixo contabilizam cada família uma única vez, baseando-se nos dados do responsável.")

    

    g1, g2 = st.columns(2)
    with g1:
        # Gênero
        fig1 = px.bar(df_responsaveis[col_genero].value_counts().reset_index(), 
                     x=col_genero, y='count', text='count', title="Gênero dos Chefes de Família", 
                     color_discrete_sequence=['#3b82f6'])
        fig1.update_traces(textposition='outside')
        st.plotly_chart(fig1, use_container_width=True)
        
    with g2:
        # Renda
        fig2 = px.bar(df_responsaveis[col_renda].value_counts().reset_index(), 
                     x=col_renda, y='count', text='count', title="Quantitativo de Renda Familiar", 
                     color_discrete_sequence=['#e11d48'])
        fig2.update_traces(textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)

    g3, g4 = st.columns(2)
    with g3:
        # Benefícios
        fig3 = px.bar(df_responsaveis[col_benef].value_counts().reset_index(), 
                     x=col_benef, y='count', text='count', title="Famílias com Benefício Social", 
                     color_discrete_sequence=['#10b981'])
        fig3.update_traces(textposition='outside')
        st.plotly_chart(fig3, use_container_width=True)

    with g4:
        # Moradia
        if col_moradia in df_responsaveis.columns:
            fig4 = px.bar(df_responsaveis[col_moradia].value_counts().reset_index(), 
                         x=col_moradia, y='count', text='count', title="Situação de Moradia", 
                         color_discrete_sequence=['#8b5cf6'])
            fig4.update_traces(textposition='outside')
            st.plotly_chart(fig4, use_container_width=True)

else:
    st.error("Planilha não detectada. Verifique o arquivo 'Planilha Matriculados.xlsx'.")
