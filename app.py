import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Gestão Socioassistencial", layout="wide", page_icon="📊")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN DE ALTO CONTRASTE (APRESENTAÇÃO) ---
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
    .kpi-title { color: #64748b; font-size: 0.9rem; font-weight: 800; text-transform: uppercase; }
    .kpi-value { color: #1e3a8a; font-size: 2.8rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LIMPEZA (FOCO NA COLUNA Q) ---
@st.cache_data
def load_and_clean_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        # Lendo o CSV/Excel
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        
        # Padronizando nomes das colunas
        df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
        
        # Limpeza de cada célula para evitar erros nos gráficos (Turnos, Rendas, etc)
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', '', ' '], 'NÃO INFORMADO')
            
        return df
    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        return None

df_base = load_and_clean_data()

if df_base is not None:
    # DEFINIÇÃO DAS COLUNAS COM BASE NA SUA EXPLICAÇÃO
    COL_PARTICIPANTE = df_base.columns[0]   # Coluna A
    COL_RESPONSAVEL = df_base.columns[16]  # Coluna Q (Nome do Responsável)
    COL_TRAMPO = "EXERCE ATIVIDADE REMUNERADA:"
    COL_RENDA = "RENDA FAMILIAR TOTAL"
    
    # Índices exatos para os 22 gráficos (B, C, E, G, H, J, K, L, N, R, S, T, U, V, X, Y, AB, AC, AD, AF, AH, AL)
    idx_alvo = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. CONTADORES DO TOPO (RECUPERAÇÃO DOS 292) ---
    # Família = Linhas onde a Coluna Q não é 'NÃO INFORMADO'
    df_familias_validas = df_base[df_base[COL_RESPONSAVEL] != "NÃO INFORMADO"]
    total_familias = len(df_familias_validas) # Aqui vai bater os seus 292
    
    total_participantes = len(df_base[df_base[COL_PARTICIPANTE] != "NÃO INFORMADO"])

    st.markdown('<div class="main-header"><h1>Painel de Inteligência Social | CAS</h1><p>Diagnóstico Unificado - Versão Congresso</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Total de Famílias (Col. Q)</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Total de Participantes</div><div class="kpi-value">{total_participantes}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Selecionados p/ Exportar</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS E SELEÇÃO ---
    st.write("---")
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        op_t = sorted(df_base[COL_TRAMPO].unique())
        sel_t = st.multiselect("Filtrar por Trabalho:", op_t, default=op_t)
    with f2:
        op_r = sorted(df_base[COL_RENDA].unique())
        sel_r = st.multiselect("Filtrar por Renda:", op_r, default=op_r)
    
    # Aplicando filtros sobre as famílias
    df_filtrado = df_familias_validas[(df_familias_validas[COL_TRAMPO].isin(sel_t)) & (df_familias_validas[COL_RENDA].isin(sel_r))]
    
    with f3:
        # Resolvendo TypeError forçando string
        nomes_lista = sorted([str(n) for n in df_filtrado[COL_RESPONSAVEL].unique()])
        selecionado = st.selectbox("🔍 Buscar Responsável Familiar:", ["SELECIONE UM NOME..."] + nomes_lista)

    # --- 6. FICHA DA FAMÍLIA E EXPORTAÇÃO ---
    if selecionado != "SELECIONE UM NOME...":
        st.write("---")
        # Puxa os dados da linha exata onde o responsável está
        dados_familia = df_filtrado[df_filtrado[COL_RESPONSAVEL] == selecionado].iloc[0]
        
        c_t, c_b = st.columns([3, 1])
        c_t.subheader(f"📂 Prontuário Familiar: {selecionado}")
        
        if selecionado not in st.session_state.lista_exportacao:
            if c_b.button("➕ Adicionar à Lista de Exportação"):
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()
        else:
            if c_b.button("❌ Remover da Lista"):
                st.session_state.lista_exportacao.remove(selecionado)
                st.rerun()

        with st.expander("👁️ Ver Dados Completos desta Família", expanded=True):
            grid = st.columns(4)
            for i, col_name in enumerate(df_base.columns):
                with grid[i % 4]:
                    st.markdown(f'''<div style="background:white; padding:8px; border-radius:5px; border:1px solid #ddd; margin-bottom:5px;">
                        <small style="color:#64748b; font-weight:bold;">{col_name}</small><br>
                        <b style="font-size:0.85rem;">{dados_familia[col_name]}</b>
                    </div>''', unsafe_allow_html=True)

    # --- 7. GRÁFICOS UNIFICADOS (REVISÃO TOTAL DOS 22 INDICADORES) ---
    st.write("---")
    st.subheader("📊 Diagnóstico Situacional das Famílias")
    st.info("Nota: Os gráficos abaixo contabilizam apenas as linhas com responsáveis preenchidos (Famílias).")

    

    g_layout = st.columns(2)
    # Selecionando as colunas pelos índices alvo
    colunas_graficos = [df_base.columns[i] for i in idx_alvo if i < len(df_base.columns)]

    for idx, col_nome in enumerate(colunas_graficos):
        with g_layout[idx % 2]:
            # Conta apenas as linhas filtradas (vínculo real com a família)
            contagem = df_filtrado[col_nome].value_counts().reset_index()
            contagem.columns = [col_nome, 'CONT']
            
            # Ordenação do maior para o menor
            contagem = contagem.sort_values(by='CONT', ascending=True)

            fig = px.bar(
                contagem, y=col_nome, x='CONT', orientation='h',
                title=f"INDICADOR: {col_nome}",
                color='CONT', color_continuous_scale='icefire', text='CONT'
            )
            fig.update_layout(
                height=350, showlegend=False, coloraxis_showscale=False,
                margin=dict(l=0, r=50, t=40, b=20),
                yaxis={'categoryorder':'total ascending'}
            )
            fig.update_traces(textposition='outside', textfont=dict(weight='bold', color='black'))
            st.plotly_chart(fig, use_container_width=True)

    # --- 8. EXPORTAÇÃO (SIDEBAR) ---
    if st.session_state.lista_exportacao:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📤 Área de Exportação")
        df_exp = df_base[df_base[COL_RESPONSAVEL].isin(st.session_state.lista_exportacao)]
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        st.sidebar.download_button("🚀 Baixar Excel das Selecionadas", output.getvalue(), "Relatorio_CAS_Export.xlsx", use_container_width=True)
        if st.sidebar.button("🗑️ Limpar Lista"):
            st.session_state.lista_exportacao = []
            st.rerun()
else:
    st.error("Por favor, verifique se a planilha 'Planilha Matriculados' está na mesma pasta do código.")
