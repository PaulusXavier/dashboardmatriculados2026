import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Painel de Gestão Social", layout="wide", page_icon="📊")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN DE ALTO CONTRASTE E VISIBILIDADE ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #020617 0%, #1e3a8a 100%);
        padding: 30px; border-radius: 20px; color: white; text-align: center; margin-bottom: 20px;
    }
    .kpi-box {
        background: white; padding: 20px; border-radius: 15px; border: 2px solid #1e3a8a;
        text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .kpi-title { color: #64748b; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; }
    .kpi-value { color: #1e3a8a; font-size: 2.5rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LIMPEZA RIGOROSA (REVISÃO DE DADOS) ---
@st.cache_data
def load_and_clean_data():
    arquivos = [f for f in os.listdir('.') if f.endswith(('.csv', '.xlsx'))]
    path = next((f for f in arquivos if "Planilha Matriculados" in f), None)
    if not path: return None
    
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        
        # Limpa nomes das colunas
        df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
        
        # LIMPEZA DOS DADOS (Para evitar duplicidade nos gráficos)
        for col in df.columns:
            # Converte para string, remove espaços extras (inclusive no meio) e padroniza
            df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
            # Trata nulos de forma amigável
            df[col] = df[col].replace(['NAN', 'NONE', 'N/A', ''], 'NÃO INFORMADO')
            
        return df
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        return None

df_base = load_and_clean_data()

if df_base is not None:
    # DEFINIÇÃO DE COLUNAS CHAVE (Pelos nomes exatos do seu CSV)
    COL_PARTICIPANTE = "NOME DO PARTICIPANTE (ATIVIDADES)"
    COL_RESPONSAVEL = "NOME DO RESPONSÁVEL"
    COL_TRAMPO = "EXERCE ATIVIDADE REMUNERADA:"
    COL_RENDA = "RENDA FAMILIAR TOTAL"
    
    # Índices das 22 colunas para os gráficos (B, C, E, G, H, J, K, L, N, R, S, T, U, V, X, Y, AB, AC, AD, AF, AH, AL)
    idx_alvo = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. CONTADORES REVISADOS (PRECISÃO TOTAL) ---
    # Contagem de Famílias: Considera apenas registros válidos na coluna de Responsável
    df_familias = df_base[df_base[COL_RESPONSAVEL] != "NÃO INFORMADO"]
    total_familias = df_familias[COL_RESPONSAVEL].nunique()
    
    # Contagem de Participantes: Todos os nomes na Coluna A
    total_participantes = len(df_base[df_base[COL_PARTICIPANTE] != "NÃO INFORMADO"])

    st.markdown('<div class="main-header"><h1>Painel de Controle CAS 2026</h1><p>Sistema de Auditoria e Diagnóstico Social</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Total de Famílias (Únicas)</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Total de Participantes</div><div class="kpi-value">{total_participantes}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Selecionados p/ Exportar</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS SOCIOECONÔMICOS ---
    st.write("---")
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        op_t = sorted(df_base[COL_TRAMPO].unique())
        sel_t = st.multiselect("Atividade Remunerada", op_t, default=op_t)
    with f2:
        op_r = sorted(df_base[COL_RENDA].unique())
        sel_r = st.multiselect("Faixa de Renda", op_r, default=op_r)
    
    # Filtro aplicado sobre a base de famílias para a busca individual
    df_f = df_familias[(df_familias[COL_TRAMPO].isin(sel_t)) & (df_familias[COL_RENDA].isin(sel_r))]
    
    with f3:
        lista_busca = sorted(df_f[COL_RESPONSAVEL].unique())
        selecionado = st.selectbox("🔍 Localizar Responsável Familiar:", ["SELECIONE UM NOME..."] + lista_busca)

    # --- 6. FICHA TÉCNICA E SELEÇÃO ---
    if selecionado != "SELECIONE UM NOME...":
        st.write("---")
        dados_f = df_f[df_f[COL_RESPONSAVEL] == selecionado].iloc[0]
        
        c_tit, c_btn = st.columns([3, 1])
        c_tit.subheader(f"📄 Prontuário Familiar: {selecionado}")
        
        if selecionado not in st.session_state.lista_exportacao:
            if c_btn.button("➕ Adicionar à Lista"):
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()
        else:
            if c_btn.button("❌ Remover da Lista"):
                st.session_state.lista_exportacao.remove(selecionado)
                st.rerun()

        with st.expander("👁️ Ver Dados Completos da Linha", expanded=True):
            cols_grid = st.columns(4)
            for i, col_nm in enumerate(df_base.columns):
                with cols_grid[i % 4]:
                    st.markdown(f'''<div style="background:white; padding:8px; border-radius:5px; border:1px solid #ddd; margin-bottom:5px;">
                        <small style="color:#888; font-weight:bold;">{col_nm}</small><br>
                        <b style="font-size:0.85rem;">{dados_f[col_nm]}</b>
                    </div>''', unsafe_allow_html=True)

    # --- 7. GRÁFICOS ANALÍTICOS UNIFICADOS (REVISÃO COMPLETA) ---
    st.write("---")
    st.subheader("📊 Diagnóstico Situacional (Quantificação Absoluta)")
    st.info("Todos os gráficos foram revisados para unificar categorias semelhantes (Ex: Turnos) e garantir a precisão dos números.")

    

    # Prepara o grid de gráficos
    g_cols = st.columns(2)
    colunas_graficos = [df_base.columns[i] for i in idx_alvo if i < len(df_base.columns)]

    for idx, col_nome in enumerate(colunas_graficos):
        with g_cols[idx % 2]:
            # Contagem absoluta
            contagem = df_f[col_nome].value_counts().reset_index()
            contagem.columns = [col_nome, 'QTD']
            
            # Ordenação: O maior valor SEMPRE fica visível no topo da barra
            contagem = contagem.sort_values(by='QTD', ascending=True) # Ascending True pois o plotly inverte o eixo Y no H bar

            fig = px.bar(
                contagem, y=col_nome, x='QTD', orientation='h',
                title=f"DISTRIBUIÇÃO: {col_nome}",
                color='QTD', color_continuous_scale='icefire', text='QTD'
            )
            fig.update_layout(
                height=350, showlegend=False, coloraxis_showscale=False,
                margin=dict(l=0, r=40, t=40, b=20),
                yaxis={'categoryorder':'total ascending'}
            )
            fig.update_traces(textposition='outside', textfont=dict(weight='bold', color='black'))
            st.plotly_chart(fig, use_container_width=True)

    # --- 8. EXPORTAÇÃO (SIDEBAR) ---
    if st.session_state.lista_exportacao:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📥 Exportar Relatório")
        df_exp = df_base[df_base[COL_RESPONSAVEL].isin(st.session_state.lista_exportacao)]
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        st.sidebar.download_button("🚀 Baixar Excel das Selecionadas", output.getvalue(), "Relatorio_CAS_Unificado.xlsx", use_container_width=True)
        if st.sidebar.button("🗑️ Limpar Lista"):
            st.session_state.lista_exportacao = []
            st.rerun()

else:
    st.error("Planilha 'Planilha Matriculados' não detectada no sistema.")
