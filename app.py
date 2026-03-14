import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO
st.set_page_config(page_title="Gestão Sociodemográfica - CAS", layout="wide")

st.markdown("""
    <style>
    /* Estilização Geral */
    .main { background-color: #f8fafc; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    
    /* Cards de Informação */
    .card-info {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .header-card { font-size: 18px; font-weight: bold; color: #1e40af; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 15px; }
    
    /* Alerta de Vulnerabilidade */
    .alerta-vulnerabilidade {
        background: linear-gradient(90deg, #be123c 0%, #fb7185 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 20px;
        margin-bottom: 25px;
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
    # Mapeamento de Colunas
    col_resp = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trampo = "EXERCE ATIVIDADE REMUNERADA:"
    col_moradia = "SITUAÇÃO DA MORADIA:"
    col_benef = "A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:"
    col_end = "ENDEREÇO COMPLETO:"
    col_bairro = "BAIRRO:"

    # Ranking de Renda para Ordenação
    rank_map = {"SEM RENDA": 0, "ATÉ R$ 405,26": 1, "DE R$ 405,26 A R$ 810,50": 2, "DE R$ 810,50 A R$ 1.215,76": 3}

    # --- BARRA LATERAL: FILTROS TÉCNICOS ---
    st.sidebar.image("https://www.setrab.am.gov.br/wp-content/uploads/2021/03/logo-setrab.png", width=180) # Logo Ilustrativa
    st.sidebar.title("🛡️ Filtros de Triagem")
    
    f_renda = st.sidebar.selectbox("Filtrar por Renda:", ["Todos"] + list(rank_map.keys()))
    f_trampo = st.sidebar.selectbox("Filtrar por Ocupação:", ["Todos"] + (df[col_trampo].unique().tolist() if col_trampo in df.columns else []))

    # Aplicação dos Filtros
    df_filtrado = df.copy()
    if f_renda != "Todos": df_filtrado = df_filtrado[df_filtrado[col_renda] == f_renda]
    if f_trampo != "Todos": df_filtrado = df_filtrado[df_filtrado[col_trampo] == f_trampo]

    # Lista de Responsáveis (Ordenada pela Maior Vulnerabilidade)
    df_lista = df_filtrado[[col_resp, col_renda]].drop_duplicates(subset=[col_resp])
    df_lista['rank'] = df_lista[col_renda].map(lambda x: rank_map.get(str(x).upper(), 99))
    lista_nomes = df_lista.sort_values(by=['rank', col_resp])[col_resp].tolist()

    st.sidebar.divider()
    selecionado = st.sidebar.selectbox("🎯 Selecione o Responsável:", ["Selecione..."] + lista_nomes)

    # --- ÁREA PRINCIPAL ---
    st.markdown("<h1 style='color: #1e3a8a;'>Sociodemográfico das Famílias Matriculadas</h1>", unsafe_allow_html=True)
    
    if selecionado != "Selecione...":
        dados_f = df[df[col_resp] == selecionado]
        renda_at = str(dados_f[col_renda].iloc[0]).upper()

        # Alerta de Risco Máximo
        if rank_map.get(renda_at, 99) <= 1:
            st.markdown(f'<div class="alerta-vulnerabilidade">🚨 PRIORIDADE SOCIAL: Família em situação de {renda_at}</div>', unsafe_allow_html=True)

        # Painel de Cards (Design Melhorado)
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown(f"""
            <div class="card-info">
                <div class="header-card">📍 Localização e Contato</div>
                <p><b>Endereço:</b> {dados_f[col_end].iloc[0] if col_end in dados_f.columns else 'Não informado'}</p>
                <p><b>Bairro:</b> {dados_f[col_bairro].iloc[0] if col_bairro in dados_f.columns else 'Não informado'}</p>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="card-info">
                <div class="header-card">💰 Status Socioeconômico</div>
                <p><b>Renda Total:</b> {renda_at}</p>
                <p><b>Trabalha?</b> {dados_f[col_trampo].iloc[0] if col_trampo in dados_f.columns else 'N/A'}</p>
                <p><b>Programa Social:</b> {dados_f[col_benef].iloc[0] if col_benef in dados_f.columns else 'N/A'}</p>
            </div>
            """, unsafe_allow_html=True)

        # Composição Familiar
        st.subheader("👥 Composição Familiar")
        st.dataframe(dados_f[['NOME:', 'IDADE:', 'GÊNERO:', 'GRAU DE PARENTESCO:']], use_container_width=True, hide_index=True)

        # Botão de Exportação Individual (Correção do Erro)
        st.divider()
        st.write("### 📋 Gestão de Dados")
        col_exp1, col_exp2 = st.columns([1, 2])
        
        with col_exp1:
            try:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    dados_f.to_excel(writer, index=False, sheet_name='Ficha_Social')
                st.download_button(
                    label="📥 Exportar Ficha em Excel",
                    data=output.getvalue(),
                    file_name=f"Ficha_{selecionado.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error("Erro ao gerar Excel. Verifique se o pacote 'xlsxwriter' está instalado.")

        with col_exp2:
            with st.expander("🔍 Ver todos os 56 campos da planilha"):
                st.dataframe(dados_f)

    # --- COMPLEMENTO ESTATÍSTICO (RODAPÉ) ---
    st.write("###")
    st.divider()
    st.markdown("<h2 style='text-align: center; color: #475569;'>📊 Visão Geral do Cadastro (Censo CAS)</h2>", unsafe_allow_html=True)
    
    
    
    g1, g2 = st.columns(2)
    with g1:
        # Gênero dos Responsáveis
        df_gen = df.drop_duplicates(subset=[col_resp])
        fig1 = px.bar(df_gen['GÊNERO:'].value_counts().reset_index(), 
                     x='GÊNERO:', y='count', text='count', 
                     title="Gênero dos Responsáveis", 
                     color_discrete_sequence=['#3b82f6'])
        fig1.update_traces(textposition='outside')
        st.plotly_chart(fig1, use_container_width=True)
        
    with g2:
        # Distribuição de Renda
        fig2 = px.bar(df[col_renda].value_counts().reset_index(), 
                     x=col_renda, y='count', text='count', 
                     title="Quantitativo de Renda", 
                     color_discrete_sequence=['#e11d48'])
        fig2.update_traces(textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)

    g3, g4 = st.columns(2)
    with g3:
        # Benefícios
        fig3 = px.bar(df[col_benef].value_counts().reset_index(), 
                     x=col_benef, y='count', text='count', 
                     title="Recebe Benefício?", 
                     color_discrete_sequence=['#10b981'])
        fig3.update_traces(textposition='outside')
        st.plotly_chart(fig3, use_container_width=True)

    with g4:
        # Moradia
        if col_moradia in df.columns:
            fig4 = px.bar(df[col_moradia].value_counts().reset_index(), 
                         x=col_moradia, y='count', text='count', 
                         title="Situação de Moradia", 
                         color_discrete_sequence=['#8b5cf6'])
            fig4.update_traces(textposition='outside')
            st.plotly_chart(fig4, use_container_width=True)

else:
    st.error("⚠️ Planilha não detectada. Por favor, carregue o arquivo 'Planilha Matriculados.xlsx' no repositório.")
