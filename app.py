import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Sistema de Gestão Social", layout="wide", page_icon="📊")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA APRESENTAÇÃO DE ALTO IMPACTO ---
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
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        
        # Limpa nomes das colunas (remove espaços e quebras de linha)
        df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
        
        # LIMPEZA RIGOROSA: Garante que os gráficos contem corretamente
        for col in df.columns:
            # Remove espaços extras (início, fim e duplos no meio) e padroniza para MAIÚSCULO
            df[col] = df[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
            # Unifica nulos para não "sujar" os gráficos
            df[col] = df[col].replace(['NAN', 'NONE', '', ' '], 'NÃO INFORMADO')
            
        return df
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
        return None

df_base = load_and_clean_data()

if df_base is not None:
    # DEFINIÇÃO DAS COLUNAS (Baseado no seu arquivo CSV)
    COL_PARTICIPANTE = "NOME DO PARTICIPANTE (ATIVIDADES)" # Coluna A
    COL_RESPONSAVEL = "NOME DO RESPONSÁVEL"               # Coluna Q
    
    # Índices exatos das 22 colunas solicitadas para os gráficos (Ajustados conforme o arquivo)
    idx_graficos = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]

    # --- 4. CONTADORES DO TOPO (BASEADOS NA COLUNA Q) ---
    # Família: Linhas onde o Nome do Responsável existe
    df_familias_validas = df_base[df_base[COL_RESPONSAVEL] != "NÃO INFORMADO"]
    total_familias = len(df_familias_validas) # Isso retornará os seus 292
    
    # Participantes: Todos os registros na coluna A
    total_participantes = len(df_base[df_base[COL_PARTICIPANTE] != "NÃO INFORMADO"])

    st.markdown('<div class="main-header"><h1>Painel CAS | Diagnóstico Familiar Unificado</h1></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Total de Famílias (Linhas Col. Q)</div><div class="kpi-value">{total_familias}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Total de Participantes</div><div class="kpi-value">{total_participantes}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Triagem p/ Exportação</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS E BUSCA ---
    st.write("---")
    f_col1, f_col2, f_col3 = st.columns([1, 1, 2])
    
    with f_col1:
        col_trampo = "EXERCE ATIVIDADE REMUNERADA:"
        op_t = sorted(df_base[col_trampo].unique()) if col_trampo in df_base.columns else []
        sel_t = st.multiselect("Filtro: Trabalho", op_t, default=op_t)
    
    with f_col2:
        col_renda = "RENDA FAMILIAR TOTAL"
        op_r = sorted(df_base[col_renda].unique()) if col_renda in df_base.columns else []
        sel_r = st.multiselect("Filtro: Renda", op_r, default=op_r)

    # Filtra apenas as linhas de família
    df_filtrado = df_familias_validas[(df_familias_validas[col_trampo].isin(sel_t)) & (df_familias_validas[col_renda].isin(sel_r))]
    
    with f_col3:
        nomes_para_selectbox = sorted([str(n) for n in df_filtrado[COL_RESPONSAVEL].unique()])
        selecionado = st.selectbox("🎯 Selecionar Prontuário Familiar:", ["SELECIONE..."] + nomes_para_selectbox)

    # --- 6. EXIBIÇÃO DA FICHA TÉCNICA ---
    if selecionado != "SELECIONE...":
        st.write("---")
        dados_familia = df_filtrado[df_filtrado[COL_RESPONSAVEL] == selecionado].iloc[0]
        
        c_t, c_b = st.columns([3, 1])
        c_t.subheader(f"📂 Prontuário: {selecionado}")
        
        if selecionado not in st.session_state.lista_exportacao:
            if c_b.button("➕ Adicionar à Exportação"):
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()
        else:
            if c_b.button("❌ Remover da Lista"):
                st.session_state.lista_exportacao.remove(selecionado)
                st.rerun()

        with st.expander("👁️ Ver Todos os Dados da Linha desta Família", expanded=True):
            grid = st.columns(4)
            for i, col_nm in enumerate(df_base.columns):
                with grid[i % 4]:
                    st.markdown(f'''<div style="background:white; padding:8px; border-radius:5px; border:1px solid #ddd; margin-bottom:5px;">
                        <small style="color:#64748b; font-weight:bold;">{col_nm}</small><br>
                        <b style="font-size:0.85rem;">{dados_familia[col_nm]}</b>
                    </div>''', unsafe_allow_html=True)

    # --- 7. GRÁFICOS REVISADOS (INDICADORES DAS 292 FAMÍLIAS) ---
    st.write("---")
    st.subheader("📊 Diagnóstico Situacional das Famílias")
    st.info("Os gráficos abaixo contabilizam a realidade das linhas onde o Responsável (Coluna Q) está preenchido.")

    layout_g = st.columns(2)
    colunas_dos_graficos = [df_base.columns[i] for i in idx_graficos if i < len(df_base.columns)]

    for idx, nome_col in enumerate(colunas_dos_graficos):
        with layout_g[idx % 2]:
            # Contagem real e limpa
            contagem = df_filtrado[nome_col].value_counts().reset_index()
            contagem.columns = [nome_col, 'QTD']
            contagem = contagem.sort_values(by='QTD', ascending=True)

            fig = px.bar(
                contagem, y=nome_col, x='QTD', orientation='h',
                title=f"INDICADOR: {nome_col}",
                color='QTD', color_continuous_scale='icefire', text='QTD'
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
        st.sidebar.download_button("🚀 Baixar Relatório das Selecionadas", buf.getvalue(), "Relatorio_CAS_Unificado.xlsx", use_container_width=True)

else:
    st.error("Arquivo não encontrado. Verifique se o nome é 'Planilha Matriculados'.")
