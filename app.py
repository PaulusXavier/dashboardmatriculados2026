import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS 2026 | Gestão Social", layout="wide", page_icon="📊")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA APRESENTAÇÃO (CONGRESSO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #020617 0%, #1e3a8a 100%);
        padding: 40px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px;
    }
    .kpi-box {
        background: white; padding: 25px; border-radius: 15px; border-left: 5px solid #1e3a8a;
        text-align: center; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    .kpi-title { color: #64748b; font-size: 0.9rem; font-weight: 800; text-transform: uppercase; margin-bottom: 10px; }
    .kpi-value { color: #1e3a8a; font-size: 3rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LIMPEZA AUDITADA ---
@st.cache_data
def load_and_clean_data():
    # Procura o arquivo na pasta raiz
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        
        # Limpa nomes das colunas (tira espaços e quebras de linha)
        df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
        
        # REVISÃO DE TODOS OS DADOS (Para todos os gráficos)
        for col in df.columns:
            # Remove espaços extras (trim) e converte para MAIÚSCULO
            df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
            # Unifica nulos para o grupo "NÃO INFORMADO"
            df[col] = df[col].replace(['NAN', 'NONE', '', ' '], 'NÃO INFORMADO')
            
        return df
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        return None

df_base = load_and_clean_data()

if df_base is not None:
    # DEFINIÇÃO DAS COLUNAS ÂNCORA
    COL_PARTICIPANTE = "NOME DO PARTICIPANTE (ATIVIDADES)" # Coluna A
    COL_RESPONSAVEL = "NOME DO RESPONSÁVEL"               # Coluna Q
    
    # Índices das 22 colunas solicitadas para os gráficos (Revisados conforme sua planilha)
    idx_graficos = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. CONTADORES REVISADOS (PROVA REAL: 292 FAMÍLIAS) ---
    # Família = Qualquer linha que tenha o Nome do Responsável (Coluna Q)
    df_familias = df_base[df_base[COL_RESPONSAVEL] != "NÃO INFORMADO"]
    total_familias = len(df_familias) # GARANTE OS 292
    
    total_participantes = len(df_base[df_base[COL_PARTICIPANTE] != "NÃO INFORMADO"])

    st.markdown('<div class="main-header"><h1>Painel CAS 2026 | Sistema Unificado</h1><p>Diagnóstico Socioassistencial em Tempo Real</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Famílias Identificadas (Col. Q)</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Participantes Ativos</div><div class="kpi-value">{total_participantes}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Lista de Exportação</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS E PESQUISA ---
    st.write("---")
    f_c1, f_c2, f_c3 = st.columns([1, 1, 2])
    
    col_t = "EXERCE ATIVIDADE REMUNERADA:"
    col_r = "RENDA FAMILIAR TOTAL"
    
    with f_c1:
        op_t = sorted(df_base[col_t].unique())
        sel_t = st.multiselect("Atividade Remunerada:", op_t, default=op_t)
    with f_c2:
        op_r = sorted(df_base[col_r].unique())
        sel_r = st.multiselect("Renda Familiar:", op_r, default=op_r)

    # Aplicando filtro nos dados
    df_filtrado = df_familias[(df_familias[col_t].isin(sel_t)) & (df_familias[col_r].isin(sel_r))]
    
    with f_c3:
        # Resolve erro alfabético (TypeError) garantindo que tudo seja string
        nomes_busca = sorted([str(n) for n in df_filtrado[COL_RESPONSAVEL].unique()])
        selecionado = st.selectbox("🔍 Pesquisar Prontuário por Responsável:", ["SELECIONE UM NOME..."] + nomes_busca)

    # --- 6. FICHA TÉCNICA E ADICIONAR ---
    if selecionado != "SELECIONE UM NOME...":
        st.write("---")
        # Pega a primeira ocorrência do nome selecionado
        dados_f = df_filtrado[df_filtrado[COL_RESPONSAVEL] == selecionado].iloc[0]
        
        c_titulo, c_botao = st.columns([3, 1])
        c_titulo.subheader(f"📄 Dados da Família: {selecionado}")
        
        if selecionado not in st.session_state.lista_exportacao:
            if c_botao.button("➕ Adicionar para Relatório"):
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()
        else:
            if c_botao.button("❌ Remover da Lista"):
                st.session_state.lista_exportacao.remove(selecionado)
                st.rerun()

        with st.expander("👁️ Ver Ficha de Matrícula Completa", expanded=True):
            grid = st.columns(4)
            for i, c_name in enumerate(df_base.columns):
                with grid[i % 4]:
                    st.markdown(f'''<div style="background:white; padding:10px; border-radius:8px; border:1px solid #e2e8f0; margin-bottom:8px;">
                        <small style="color:#94a3b8; font-weight:800; font-size:0.65rem;">{c_name}</small><br>
                        <span style="color:#1e293b; font-weight:700; font-size:0.85rem;">{dados_f[c_name]}</span>
                    </div>''', unsafe_allow_html=True)

    # --- 7. REVISÃO DOS 22 GRÁFICOS (BASE DE FAMÍLIAS) ---
    st.write("---")
    st.subheader("📊 Diagnóstico dos Indicadores Sociais")
    st.info("Nota: Todos os gráficos unificam categorias e refletem os dados vinculados às famílias (Coluna Q).")

    

    colunas_vis = st.columns(2)
    # Lista de nomes das colunas baseado nos índices alvo
    lista_colunas_graficos = [df_base.columns[i] for i in idx_graficos if i < len(df_base.columns)]

    for idx, nome_col in enumerate(lista_colunas_graficos):
        with colunas_vis[idx % 2]:
            # Contagem real e limpa
            contagem = df_filtrado[nome_col].value_counts().reset_index()
            contagem.columns = [nome_col, 'CONT']
            contagem = contagem.sort_values(by='CONT', ascending=True)

            fig = px.bar(
                contagem, y=nome_col, x='CONT', orientation='h',
                title=f"DISTRIBUIÇÃO: {nome_col}",
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
        st.sidebar.subheader("📥 Exportação")
        df_exp = df_base[df_base[COL_RESPONSAVEL].isin(st.session_state.lista_exportacao)]
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        st.sidebar.download_button("🚀 Baixar Relatório Selecionado", buf.getvalue(), "Relatorio_CAS_2026.xlsx", use_container_width=True)

else:
    st.error("Planilha 'Planilha Matriculados' não encontrada na raiz do repositório.")
