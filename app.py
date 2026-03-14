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

# --- 2. CSS DESIGN PREMIUM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #3b82f6 100%);
        padding: 40px; border-radius: 20px; color: white; text-align: center;
        margin-bottom: 25px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .kpi-box {
        background: white; padding: 20px; border-radius: 15px;
        text-align: center; border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .kpi-title { color: #64748b; font-size: 12px; font-weight: 800; text-transform: uppercase; }
    .kpi-value { color: #1e3a8a; font-size: 28px; font-weight: 800; }
    .data-grid-item {
        background: white; padding: 12px; border-radius: 10px;
        border: 1px solid #e2e8f0; margin-bottom: 8px;
    }
    .label-grid { color: #94a3b8; font-size: 9px; font-weight: 800; text-transform: uppercase; }
    .value-grid { color: #1e293b; font-size: 12px; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO DOS DADOS ---
@st.cache_data
def load_data():
    path = r"C:\Users\paulo\OneDrive\Documentos\CAS\Planilha Matriculados\Planilha Matriculados.xlsx"
    try:
        # Se o arquivo CSV enviado estiver na pasta do script, ele prioriza
        if os.path.exists("Planilha Matriculados.xlsx - Planilha1.csv"):
            df = pd.read_csv("Planilha Matriculados.xlsx - Planilha1.csv", dtype=str)
        elif os.path.exists(path):
            df = pd.read_excel(path, dtype=str)
        else:
            return None
        
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        return df.fillna("—").replace("nan", "—")
    except Exception as e:
        st.error(f"Erro: {e}")
        return None

df_base = load_data()

if df_base is not None:
    # Nomes exatos das colunas baseados no seu arquivo
    col_nome_part = "NOME DO PARTICIPANTE (ATIVIDADES)"
    col_resp = "NOME DO RESPONSÁVEL"
    col_renda = "RENDA FAMILIAR TOTAL"
    col_trampo = "EXERCE ATIVIDADE REMUNERADA:"
    col_moradia = "SITUAÇÃO DE MORADIA"
    col_bairro = "BAIRRO"

    # --- 4. SIDEBAR (FILTROS DE VULNERABILIDADE) ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=70)
    st.sidebar.title("Filtros de Risco")

    # Filtro de Emprego
    status_trampo = sorted(df_base[col_trampo].unique())
    f_trampo = st.sidebar.multiselect("Exerce Atividade Remunerada?", status_trampo, default=status_trampo)

    # Filtro de Renda
    faixas_renda = sorted(df_base[col_renda].unique())
    f_renda = st.sidebar.multiselect("Faixa de Renda Familiar:", faixas_renda, default=faixas_renda)

    # Aplicação dos filtros na base
    mask = (df_base[col_trampo].isin(f_trampo)) & (df_base[col_renda].isin(f_renda))
    df_filtrado = df_base[mask]

    # Famílias únicas filtradas
    df_familias_unicas = df_filtrado[df_filtrado[col_resp] != "—"].drop_duplicates(subset=[col_resp])

    # --- 5. CABEÇALHO E MÉTRICAS ---
    st.markdown('<div class="main-header"><h1>Painel de Vulnerabilidade Social | CAS</h1></div>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Participantes</div><div class="kpi-value">{len(df_filtrado)}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Famílias</div><div class="kpi-value">{len(df_familias_unicas)}</div></div>', unsafe_allow_html=True)
    
    # Cálculo de Desemprego no Filtro Atual
    desempregados = df_familias_unicas[df_familias_unicas[col_trampo].str.contains("NÃO", case=False, na=False)].shape[0]
    m3.markdown(f'<div class="kpi-box"><div class="kpi-title">🚫 Sem Ocupação</div><div class="kpi-value">{desempregados}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="kpi-box"><div class="kpi-title">📥 Para Exportar</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 6. GRÁFICOS ANALÍTICOS ---
    st.write("---")
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("Situação de Trabalho por Família")
        fig_trampo = px.pie(df_familias_unicas, names=col_trampo, hole=0.5, 
                            color_discrete_sequence=["#ef4444", "#10b981"])
        st.plotly_chart(fig_trampo, use_container_width=True)

    with g2:
        st.subheader("Distribuição de Renda")
        fig_renda = px.bar(df_familias_unicas[col_renda].value_counts().reset_index(), 
                           x=col_renda, y='count', color=col_renda, color_discrete_sequence=px.colors.qualitative.Safe)
        fig_renda.update_layout(showlegend=False)
        st.plotly_chart(fig_renda, use_container_width=True)

    # --- 7. BUSCA E DETALHAMENTO ---
    st.write("---")
    lista_busca = sorted(df_familias_unicas[col_resp].tolist())
    selecionado = st.selectbox("🔍 Pesquisar Responsável Familiar:", ["Selecione..."] + lista_busca)

    if selecionado != "Selecione...":
        dados_chefe = df_familias_unicas[df_familias_unicas[col_resp] == selecionado].iloc[0]
        dependentes = df_base[df_base[col_resp] == selecionado]

        col_text, col_btn = st.columns([3, 1])
        col_text.markdown(f"### Família de {selecionado}")
        
        if selecionado not in st.session_state.lista_exportacao:
            if col_btn.button("➕ Adicionar à Lista de Exportação"):
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()
        else:
            if col_btn.button("✅ Remover da Lista"):
                st.session_state.lista_exportacao.remove(selecionado)
                st.rerun()

        # Grid de informações
        with st.expander("📄 Ver Dados Socioeconômicos Completos", expanded=True):
            det_cols = st.columns(4)
            for i, c in enumerate(df_base.columns):
                with det_cols[i % 4]:
                    st.markdown(f'<div class="data-grid-item"><div class="label-grid">{c}</div><div class="value-grid">{dados_chefe[c]}</div></div>', unsafe_allow_html=True)

        st.write("#### 👨‍👩‍👧‍👦 Membros Matriculados nesta Família")
        st.table(dependentes[[col_nome_part, "ATIVIDADE DESEJADA", "IDADE (PARTICIPANTE)"]])

    # --- 8. EXPORTAÇÃO ---
    if st.session_state.lista_exportacao:
        st.sidebar.write("---")
        if st.sidebar.button("🗑️ Limpar Exportação"):
            st.session_state.lista_exportacao = []
            st.rerun()
            
        df_export = df_base[df_base[col_resp].isin(st.session_state.lista_exportacao)]
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False)
        st.sidebar.download_button("🚀 Baixar Relatório (Excel)", output.getvalue(), "Relatorio_CAS.xlsx", use_container_width=True)

else:
    st.error("Planilha não encontrada. Verifique se o nome do arquivo é 'Planilha Matriculados.xlsx' e se ele está no local correto.")
