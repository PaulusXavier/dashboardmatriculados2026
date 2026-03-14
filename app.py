import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS 2026 | Painel Unificado", layout="wide", page_icon="📊")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA APRESENTAÇÃO PROFISSIONAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #020617 0%, #1e3a8a 100%);
        padding: 40px; border-radius: 20px; color: white; text-align: center; margin-bottom: 30px;
    }
    .kpi-box {
        background: white; padding: 25px; border-radius: 15px; border-left: 5px solid #1e3a8a;
        text-align: center; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    .kpi-title { color: #64748b; font-size: 0.9rem; font-weight: 800; text-transform: uppercase; }
    .kpi-value { color: #1e3a8a; font-size: 3rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LIMPEZA DOS DADOS ---
@st.cache_data
def load_and_clean_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos:
        return None
    path = arquivos[0]
    try:
        # Carrega os dados garantindo leitura como texto
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        
        # Limpa nomes das colunas
        df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
        
        # Limpeza rigorosa para unificar categorias (Turnos, Renda, etc)
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', '', ' '], 'NÃO INFORMADO')
        return df
    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        return None

df_base = load_and_clean_data()

if df_base is not None:
    # DEFINIÇÃO DAS COLUNAS CHAVE (ÂNCORA: COLUNA Q)
    COL_PARTICIPANTE = "NOME DO PARTICIPANTE (ATIVIDADES)" # Coluna A
    COL_RESPONSAVEL = "NOME DO RESPONSÁVEL"               # Coluna Q
    
    # Índices exatos das 22 colunas solicitadas para os gráficos
    idx_graficos = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. CONTADORES (LOGICA: LINHA COM NOME NA COLUNA Q = FAMÍLIA) ---
    # Filtramos apenas as linhas onde a Coluna Q está preenchida
    df_familias = df_base[df_base[COL_RESPONSAVEL] != "NÃO INFORMADO"]
    total_familias = len(df_familias) # CONTARÁ EXATAMENTE AS 292 LINHAS
    
    total_participantes = len(df_base[df_base[COL_PARTICIPANTE] != "NÃO INFORMADO"])

    st.markdown('<div class="main-header"><h1>Painel CAS 2026 | Sistema Unificado</h1><p>Controle de Matrículas e Diagnóstico Social</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Unidades Familiares (Coluna Q)</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Total de Participantes</div><div class="kpi-value">{total_participantes}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Prontuários p/ Exportar</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS ---
    st.write("---")
    f_c1, f_c2, f_c3 = st.columns([1, 1, 2])
    
    col_t = "EXERCE ATIVIDADE REMUNERADA:"
    col_r = "RENDA FAMILIAR TOTAL"
    
    with f_c1:
        op_t = sorted(df_base[col_t].unique()) if col_t in df_base.columns else ["NÃO INFORMADO"]
        sel_t = st.multiselect("Filtro: Trabalho", op_t, default=op_t)
    with f_c2:
        op_r = sorted(df_base[col_r].unique()) if col_r in df_base.columns else ["NÃO INFORMADO"]
        sel_r = st.multiselect("Filtro: Renda", op_r, default=op_r)

    # Aplicação do filtro sobre a base de famílias
    df_f = df_familias[(df_familias[col_t].isin(sel_t)) & (df_familias[col_r].isin(sel_r))]
    
    with f_c3:
        # Garantindo que a lista de busca venha apenas das famílias válidas
        nomes_lista = sorted([str(n) for n in df_f[COL_RESPONSAVEL].unique()])
        selecionado = st.selectbox("🔍 Pesquisar por Responsável (Coluna Q):", ["SELECIONE..."] + nomes_lista)

    # --- 6. FICHA TÉCNICA ---
    if selecionado != "SELECIONE...":
        st.write("---")
        dados_f = df_f[df_f[COL_RESPONSAVEL] == selecionado].iloc[0]
        
        c_tit, c_btn = st.columns([3, 1])
        c_tit.subheader(f"📄 Dados da Família: {selecionado}")
        
        if selecionado not in st.session_state.lista_exportacao:
            if c_btn.button("➕ Adicionar à Exportação"):
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()
        else:
            if c_btn.button("❌ Remover da Lista"):
                st.session_state.lista_exportacao.remove(selecionado)
                st.rerun()

        with st.expander("👁️ Prontuário Completo desta Linha", expanded=True):
            grid = st.columns(4)
            for i, col_nm in enumerate(df_base.columns):
                with grid[i % 4]:
                    st.markdown(f'''<div style="background:white; padding:8px; border-radius:5px; border:1px solid #ddd; margin-bottom:5px;">
                        <small style="color:#64748b; font-weight:bold;">{col_nm}</small><br>
                        <b style="font-size:0.85rem;">{dados_f[col_nm]}</b>
                    </div>''', unsafe_allow_html=True)

    # --- 7. GRÁFICOS ANALÍTICOS (BASE: 292 FAMÍLIAS) ---
    st.write("---")
    st.subheader("📊 Diagnóstico dos Indicadores Sociais")
    st.info("Gráficos baseados na contagem absoluta das linhas de responsáveis (Coluna Q).")

    

    lay_g = st.columns(2)
    lista_col_vis = [df_base.columns[i] for i in idx_graficos if i < len(df_base.columns)]

    for idx, nome_col in enumerate(lista_col_vis):
        with lay_g[idx % 2]:
            contagem = df_f[nome_col].value_counts().reset_index()
            contagem.columns = [nome_col, 'CONT']
            contagem = contagem.sort_values(by='CONT', ascending=True)

            fig = px.bar(
                contagem, y=nome_col, x='CONT', orientation='h',
                title=f"INDICADOR: {nome_col}",
                color='CONT', color_continuous_scale='icefire', text='CONT'
            )
            fig.update_layout(
                height=350, showlegend=False, coloraxis_showscale=False,
                margin=dict(l=0, r=50, t=40, b=20),
                yaxis={'categoryorder':'total ascending'}
            )
            fig.update_traces(textposition='outside', textfont=dict(weight='bold', color='black'))
            st.plotly_chart(fig, use_container_width=True)

    # --- 8. EXPORTAÇÃO ---
    if st.session_state.lista_exportacao:
        st.sidebar.markdown("---")
        df_exp = df_base[df_base[COL_RESPONSAVEL].isin(st.session_state.lista_exportacao)]
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        st.sidebar.download_button("🚀 Baixar Excel Selecionado", buf.getvalue(), "Relatorio_CAS_2026.xlsx", use_container_width=True)
else:
    st.error("Planilha 'Planilha Matriculados' não encontrada. Verifique o arquivo no GitHub.")
