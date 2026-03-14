import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão CAS/SETRABES", layout="wide")

st.markdown("""
    <style>
    .card-vulnerabilidade { padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 2px solid #e2e8f0; background-color: #f8fafc; }
    .status-alerta { border-left: 10px solid #be123c; }
    .titulo-principal { color: #1e3a8a; text-align: center; font-weight: bold; margin-bottom: 5px; }
    .subtitulo { text-align: center; color: #64748b; margin-bottom: 30px; }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO DOS DADOS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAMINHO = os.path.join(BASE_DIR, "Planilha Matriculados.xlsx")

@st.cache_data
def carregar_dados_sociais(caminho):
    if not os.path.exists(caminho): return None
    try:
        df = pd.read_excel(caminho, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        return df
    except Exception: return None

df = carregar_dados_sociais(CAMINHO)

if df is not None:
    # Mapeamento de Colunas Críticas
    col_resp = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_genero = "GÊNERO:"
    col_benef_status = "A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:"
    col_benef_qual = "QUAL PROGRAMA SOCIAL:"
    col_moradia = "SITUAÇÃO DA MORADIA:"
    
    st.markdown("<h1 class='titulo-principal'>Sociodemográfico das Famílias Matriculadas</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitulo'>Painel Técnico de Monitoramento e Triagem Social</p>", unsafe_allow_html=True)

    # --- SEÇÃO DE EXPORTAÇÃO (SIDEBAR) ---
    st.sidebar.header("📤 Exportação de Dados")
    df_unicos = df.drop_duplicates(subset=[col_resp])
    
    selecionados_export = st.sidebar.multiselect(
        "Selecionar famílias para exportar:", 
        options=df_unicos[col_resp].unique().tolist()
    )

    if selecionados_export:
        df_para_baixar = df[df[col_resp].isin(selecionados_export)]
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_para_baixar.to_excel(writer, index=False, sheet_name='Relatorio_CAS')
        
        st.sidebar.download_button(
            label="📥 Baixar Excel Selecionado",
            data=output.getvalue(),
            file_name="relatorio_familias_matriculadas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.sidebar.success(f"{len(selecionados_export)} núcleos prontos.")

    # --- CONSULTA INDIVIDUAL ---
    st.write("### 🔍 Consulta por Responsável Familiar")
    nome_selecionado = st.selectbox("Pesquisar nome:", ["Selecione um nome..."] + df_unicos[col_resp].tolist())
    
    if nome_selecionado != "Selecione um nome...":
        dados_f = df[df[col_resp] == nome_selecionado]
        st.markdown(f'''<div class="card-vulnerabilidade status-alerta">
            <b>Responsável:</b> {nome_selecionado} | 
            <b>Renda Familiar:</b> {dados_f[col_renda].iloc[0]} | 
            <b>Moradia:</b> {dados_f[col_moradia].iloc[0] if col_moradia in df.columns else "N/A"}
        </div>''', unsafe_allow_html=True)
        
        with st.expander("👁️ Ver Ficha Técnica Completa (Todas as 56 Colunas)"):
            st.dataframe(dados_f)

    # --- GRÁFICOS DE DADOS SENSÍVEIS (QUANTITATIVOS) ---
    st.divider()
    st.write("### 📊 Quantitativos Socioeconómicos (Gestão)")

    # Linha 1: Gênero e Renda
    c1, c2 = st.columns(2)
    with c1:
        # Quantidade de Gênero (Apenas dos Responsáveis)
        fig_gen = px.bar(df_unicos[col_genero].value_counts().reset_index(), 
                         x=col_genero, y='count', text='count', 
                         title="Distribuição de Gênero (Chefes de Família)",
                         color_discrete_sequence=['#2563eb'])
        fig_gen.update_traces(textposition='outside')
        st.plotly_chart(fig_gen, use_container_width=True)

    with c2:
        # Quantidade por Renda
        fig_ren = px.bar(df[col_renda].value_counts().reset_index(), 
                         x=col_renda, y='count', text='count',
                         title="Quantitativo por Faixa de Renda",
                         color_discrete_sequence=['#dc2626'])
        fig_ren.update_traces(textposition='outside')
        st.plotly_chart(fig_ren, use_container_width=True)

    # Linha 2: Benefícios e Moradia
    c3, c4 = st.columns(2)
    with c3:
        # Benefícios Sociais
        fig_ben = px.bar(df[col_benef_status].value_counts().reset_index(), 
                         x=col_benef_status, y='count', text='count',
                         title="Famílias em Programas Sociais (Sim/Não)",
                         color_discrete_sequence=['#16a34a'])
        fig_ben.update_traces(textposition='outside')
        st.plotly_chart(fig_ben, use_container_width=True)

    with c4:
        # Moradia
        if col_moradia in df.columns:
            fig_mor = px.bar(df[col_moradia].value_counts().reset_index(), 
                             x=col_moradia, y='count', text='count',
                             title="Situação de Moradia (Propriedade/Aluguel)",
                             color_discrete_sequence=['#7c3aed'])
            fig_mor.update_traces(textposition='outside')
            st.plotly_chart(fig_mor, use_container_width=True)

    # Gráfico de Tipos de Benefícios (Se a coluna existir)
    if col_benef_qual in df.columns:
        st.write("#### Detalhamento de Programas Sociais Ativos")
        # Filtrar apenas quem recebe e remover nulos
        df_q = df[df[col_benef_qual].notna()]
        fig_q = px.bar(df_q[col_benef_qual].value_counts().reset_index(), 
                       x='count', y=col_benef_qual, orientation='h', 
                       text='count', title="Quantitativo por Tipo de Benefício")
        st.plotly_chart(fig_q, use_container_width=True)

else:
    st.error("Erro: Arquivo 'Planilha Matriculados.xlsx' não encontrado.")
