import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Gestão Socioassistencial", layout="wide", page_icon="🧠")

# Inicialização da lista de exportação no estado da sessão
if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN TÉCNICO E ALTO CONTRASTE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f1f5f9; }
    .main-header {
        background: linear-gradient(135deg, #020617 0%, #1e3a8a 100%);
        padding: 30px; border-radius: 20px; color: white; text-align: center; margin-bottom: 20px;
    }
    .kpi-box {
        background: white; padding: 20px; border-radius: 15px; border: 2px solid #1e3a8a;
        text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .kpi-title { color: #64748b; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; }
    .kpi-value { color: #1e3a8a; font-size: 2.2rem; font-weight: 800; }
    .data-card { background: white; padding: 10px; border-radius: 8px; border: 1px solid #cbd5e1; margin-bottom: 5px; }
    .label-card { color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; }
    .value-card { color: #0f172a; font-size: 0.8rem; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E NORMALIZAÇÃO DE DADOS ---
@st.cache_data
def load_and_clean_data():
    # Procura por qualquer ficheiro Excel ou CSV que contenha "Planilha Matriculados"
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        # Limpa nomes das colunas (remove espaços e quebras de linha)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        # Normaliza todos os dados para maiúsculas e remove espaços extras
        for col in df.columns:
            df[col] = df[col].fillna("NÃO INFORMADO").astype(str).str.strip().str.upper()
        return df.replace("NAN", "NÃO INFORMADO").replace("", "NÃO INFORMADO")
    except Exception as e:
        st.error(f"Erro no processamento dos dados: {e}")
        return None

df_base = load_and_clean_data()

if df_base is not None:
    # MAPEAMENTO DE COLUNAS CHAVE
    COL_PARTICIPANTE = df_base.columns[0]   # Coluna A
    COL_RESPONSAVEL = "NOME DO RESPONSÁVEL" # Coluna T (Nome do Responsável)
    COL_TRAMPO = "EXERCE ATIVIDADE REMUNERADA:"
    COL_RENDA = "RENDA FAMILIAR TOTAL"
    
    # Índices das 22 colunas solicitadas para gráficos
    idx_graficos = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. INDICADORES NO TOPO (KPIs) ---
    # Famílias: Considera apenas as linhas onde a Coluna T (Responsável) está preenchida
    df_familias_unicas = df_base[df_base[COL_RESPONSAVEL] != "NÃO INFORMADO"]
    total_familias = len(df_familias_unicas)
    
    # Participantes: Total de inscritos na Coluna A
    total_participantes = len(df_base[df_base[COL_PARTICIPANTE] != "NÃO INFORMADO"])

    st.markdown('<div class="main-header"><h1>Painel de Inteligência Familiar | CAS</h1></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Famílias no CAS</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Participantes Ativos</div><div class="kpi-value">{total_participantes}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Selecionados para Exportar</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS SOCIOECONÓMICOS (TRIAGEM) ---
    st.write("---")
    st.subheader("🔍 Triagem de Vulnerabilidade")
    f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
    
    with f_col1:
        op_trampo = sorted(df_base[COL_TRAMPO].unique())
        sel_trampo = st.multiselect("Status de Emprego", op_trampo, default=op_trampo)
    
    with f_col2:
        op_renda = sorted(df_base[COL_RENDA].unique())
        sel_renda = st.multiselect("Faixa de Renda", op_renda, default=op_renda)

    # Aplicação do filtro para encontrar os responsáveis
    df_filtrado = df_familias_unicas[(df_familias_unicas[COL_TRAMPO].isin(sel_trampo)) & (df_familias_unicas[COL_RENDA].isin(sel_renda))]
    
    with f_col3:
        lista_busca = sorted([str(n) for n in df_filtrado[COL_RESPONSAVEL].unique()])
        selecionado = st.selectbox("🎯 Localizar Responsável Familiar:", ["SELECIONE UM NOME..."] + lista_busca)

    # --- 6. FICHA TÉCNICA E SELEÇÃO PARA EXPORTAR ---
    if selecionado != "SELECIONE UM NOME...":
        st.write("---")
        dados_familia = df_filtrado[df_filtrado[COL_RESPONSAVEL] == selecionado].iloc[0]
        
        c_tit, c_btn = st.columns([3, 1])
        c_tit.subheader(f"📂 Ficha de Unidade Familiar: {selecionado}")
        
        if selecionado not in st.session_state.lista_exportacao:
            if c_btn.button("➕ Adicionar à Lista de Exportação"):
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()
        else:
            st.info("✅ Esta família já está na sua lista de exportação.")
            if c_btn.button("❌ Remover da Lista"):
                st.session_state.lista_exportacao.remove(selecionado)
                st.rerun()

        with st.expander("📄 Visualizar Prontuário Completo desta Linha", expanded=True):
            grid = st.columns(4)
            for i, col in enumerate(df_base.columns):
                with grid[i % 4]:
                    st.markdown(f'<div class="data-card"><div class="label-card">{col}</div><div class="value-card">{dados_familia[col]}</div></div>', unsafe_allow_html=True)

    # --- 7. DIAGNÓSTICO ESTATÍSTICO (GRÁFICOS NO FINAL) ---
    st.write("---")
    st.subheader("📊 Diagnóstico Situacional do Território")
    st.info("Os gráficos abaixo quantificam os dados das famílias que passam pelos filtros acima.")
    
    

    g_layout = st.columns(2)
    cols_graficos = [df_base.columns[i] for i in idx_graficos if i < len(df_base.columns)]

    for idx, nome_col in enumerate(cols_graficos):
        with g_layout[idx % 2]:
            contagem = df_filtrado[nome_col].value_counts().reset_index()
            contagem.columns = [nome_col, 'QUANTIDADE']
            
            # Gráfico de barras horizontais com cor ICEFIRE (Alta visibilidade)
            fig = px.bar(
                contagem, y=nome_col, x='QUANTIDADE', orientation='h',
                title=f"DISTRIBUIÇÃO: {nome_col}",
                color='QUANTIDADE', color_continuous_scale='icefire', text='QUANTIDADE'
            )
            fig.update_layout(
                height=350, showlegend=False, coloraxis_showscale=False,
                margin=dict(l=0, r=40, t=40, b=20)
            )
            fig.update_traces(textposition='outside', textfont=dict(weight='bold', color='black'))
            st.plotly_chart(fig, use_container_width=True)

    # --- 8. BARRA LATERAL PARA EXPORTAÇÃO ---
    if st.session_state.lista_exportacao:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📥 Relatório de Triagem")
        st.sidebar.write(f"Total: {len(st.session_state.lista_exportacao)} famílias.")
        
        df_final = df_base[df_base[COL_RESPONSAVEL].isin(st.session_state.lista_exportacao)]
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, index=False)
        
        st.sidebar.download_button("🚀 Baixar Excel das Selecionadas", output.getvalue(), "Relatorio_CAS_Triagem.xlsx", use_container_width=True)
        if st.sidebar.button("🗑️ Limpar Lista"):
            st.session_state.lista_exportacao = []
            st.rerun()
else:
    st.error("Planilha não encontrada. Verifique o nome do ficheiro.")
