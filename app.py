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
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 40px; border-radius: 20px; color: white; text-align: center;
        margin-bottom: 25px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .kpi-box {
        background: white; padding: 20px; border-radius: 15px;
        text-align: center; border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .kpi-title { color: #64748b; font-size: 11px; font-weight: 800; text-transform: uppercase; }
    .kpi-value { color: #1e3a8a; font-size: 28px; font-weight: 800; }
    .data-grid-item {
        background: white; padding: 12px; border-radius: 10px;
        border: 1px solid #e2e8f0; margin-bottom: 8px; transition: 0.3s;
    }
    .data-grid-item:hover { border-color: #3b82f6; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .label-grid { color: #94a3b8; font-size: 9px; font-weight: 800; text-transform: uppercase; }
    .value-grid { color: #1e293b; font-size: 12px; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNÇÃO PARA EVITAR KEYERROR (Busca Inteligente) ---
def get_col(df, keywords):
    """Busca uma coluna que contenha as palavras-chave, ignorando maiúsculas e espaços."""
    for col in df.columns:
        if any(kw.upper() in col.upper() for kw in keywords):
            return col
    return None

# --- 4. CARREGAMENTO DOS DADOS ---
@st.cache_data
def load_data():
    # Tenta carregar o CSV que você subiu ou o Excel do OneDrive
    arquivos_locais = [f for f in os.listdir('.') if 'Planilha Matriculados' in f]
    path_onedrive = r"C:\Users\paulo\OneDrive\Documentos\CAS\Planilha Matriculados\Planilha Matriculados.xlsx"
    
    try:
        if arquivos_locais:
            nome_arq = arquivos_locais[0]
            df = pd.read_csv(nome_arq, dtype=str) if nome_arq.endswith('.csv') else pd.read_excel(nome_arq, dtype=str)
        elif os.path.exists(path_onedrive):
            df = pd.read_excel(path_onedrive, dtype=str)
        else:
            return None
        
        # Limpeza básica: remove espaços extras dos nomes das colunas
        df.columns = [str(c).strip() for c in df.columns]
        return df.fillna("—").replace("nan", "—")
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        return None

df_base = load_data()

if df_base is not None:
    # MAPEAMENTO DINÂMICO (Resolve o KeyError)
    C_PARTICIPANTE = get_col(df_base, ["NOME DO PARTICIPANTE"])
    C_RESPONSAVEL = get_col(df_base, ["NOME DO RESPONSÁVEL"])
    C_RENDA = get_col(df_base, ["RENDA FAMILIAR TOTAL", "RENDA FAMILIAR MENSAL"])
    C_TRAMPO = get_col(df_base, ["EXERCE ATIVIDADE REMUNERADA"])
    C_MORADIA = get_col(df_base, ["SITUAÇÃO DE MORADIA"])
    C_BAIRRO = get_col(df_base, ["BAIRRO"])
    C_ATIVIDADE = get_col(df_base, ["ATIVIDADE DESEJADA"])

    # Verificação de colunas críticas
    if not C_RESPONSAVEL or not C_RENDA:
        st.error("Não foi possível identificar as colunas principais. Verifique os títulos da sua planilha.")
        st.stop()

    # Processamento para métricas de Vulnerabilidade (Agrupado por Família)
    df_familias = df_base[df_base[C_RESPONSAVEL] != "—"].drop_duplicates(subset=[C_RESPONSAVEL])
    
    # --- 5. SIDEBAR (FILTROS) ---
    st.sidebar.header("🛡️ Filtros de Vulnerabilidade")
    
    opcoes_trampo = sorted(df_base[C_TRAMPO].unique())
    f_trampo = st.sidebar.multiselect("Trabalha?", opcoes_trampo, default=opcoes_trampo)
    
    opcoes_renda = sorted(df_base[C_RENDA].unique())
    f_renda = st.sidebar.multiselect("Faixa de Renda:", opcoes_renda, default=opcoes_renda)

    # Aplicação dos Filtros
    df_filtrado_geral = df_base[df_base[C_TRAMPO].isin(f_trampo) & df_base[C_RENDA].isin(f_renda)]
    df_filtrado_familias = df_familias[df_familias[C_TRAMPO].isin(f_trampo) & df_familias[C_RENDA].isin(f_renda)]

    # --- 6. DASHBOARD ---
    st.markdown('<div class="main-header"><h1>CAS | Inteligência Social</h1><p>Monitoramento de Vulnerabilidade Familiar</p></div>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Participantes</div><div class="kpi-value">{len(df_filtrado_geral)}</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Famílias</div><div class="kpi-value">{len(df_filtrado_familias)}</div></div>', unsafe_allow_html=True)
    
    # Cálculo de desempregados (baseado na coluna de atividade remunerada)
    sem_trampo = df_filtrado_familias[df_filtrado_familias[C_TRAMPO].str.contains("NÃO", case=False, na=False)].shape[0]
    m3.markdown(f'<div class="kpi-box"><div class="kpi-title">🚫 Responsável S/ Trabalho</div><div class="kpi-value">{sem_trampo}</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="kpi-box"><div class="kpi-title">📥 Exportar</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    st.write("---")
    
    # Gráficos
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("📊 Distribuição de Renda")
        fig_renda = px.bar(df_filtrado_familias[C_RENDA].value_counts().reset_index(), 
                           x=C_RENDA, y='count', color=C_RENDA, color_discrete_sequence=px.colors.qualitative.Prism)
        st.plotly_chart(fig_renda, use_container_width=True)
    
    with g2:
        st.subheader("💼 Status de Emprego (Chefes de Família)")
        fig_pie = px.pie(df_filtrado_familias, names=C_TRAMPO, hole=0.4, color_discrete_sequence=["#ef4444", "#10b981"])
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- 7. BUSCA INDIVIDUAL ---
    st.write("---")
    selecionado = st.selectbox("🔍 Detalhar Família (Pesquisar Responsável):", ["Selecione..."] + sorted(df_filtrado_familias[C_RESPONSAVEL].tolist()))

    if selecionado != "Selecione...":
        chefe = df_filtrado_familias[df_filtrado_familias[C_RESPONSAVEL] == selecionado].iloc[0]
        membros = df_base[df_base[C_RESPONSAVEL] == selecionado]

        col_tit, col_btn = st.columns([3, 1])
        col_tit.subheader(f"Prontuário: {selecionado}")
        
        if selecionado not in st.session_state.lista_exportacao:
            if col_btn.button("➕ Adicionar para Relatório"):
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()
        else:
            if col_btn.button("✅ Na Lista (Remover?)"):
                st.session_state.lista_exportacao.remove(selecionado)
                st.rerun()

        # Grid de Detalhes
        with st.expander("📄 Ver Ficha Socioeconômica Completa", expanded=True):
            grid_cols = st.columns(4)
            for i, coluna in enumerate(df_base.columns):
                with grid_cols[i % 4]:
                    st.markdown(f'<div class="data-grid-item"><div class="label-grid">{coluna}</div><div class="value-grid">{chefe[coluna]}</div></div>', unsafe_allow_html=True)

        st.markdown(f"#### 👨‍👩‍👧‍👦 Membros da Família Matriculados ({len(membros)})")
        st.table(membros[[C_PARTICIPANTE, C_ATIVIDADE, "IDADE (PARTICIPANTE)"]])

    # --- 8. EXPORTAÇÃO ---
    if st.session_state.lista_exportacao:
        st.sidebar.write("---")
        if st.sidebar.button("🗑️ Limpar Lista"):
            st.session_state.lista_exportacao = []
            st.rerun()
        
        df_exp = df_base[df_base[C_RESPONSAVEL].isin(st.session_state.lista_exportacao)]
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        st.sidebar.download_button("🚀 Baixar Relatório das Famílias", output.getvalue(), "Relatorio_CAS.xlsx", use_container_width=True)

else:
    st.error("Arquivo 'Planilha Matriculados' não encontrado. Verifique se o arquivo está na mesma pasta do script.")
