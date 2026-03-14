import streamlit as st
import pandas as pd
import plotly.express as px
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Inteligência Social", layout="wide", page_icon="🧠")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN PREMIUM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #020617 0%, #1e3a8a 100%);
        padding: 35px; border-radius: 20px; color: white; text-align: center; margin-bottom: 25px;
    }
    .kpi-card {
        background: white; padding: 20px; border-radius: 15px; border-top: 5px solid #1e3a8a;
        text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .data-card { background: white; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 8px; }
    .label-card { color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; }
    .value-card { color: #0f172a; font-size: 0.8rem; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E NORMALIZAÇÃO ---
@st.cache_data
def load_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ').upper() for c in df.columns]
        
        # Limpeza rigorosa para evitar duplicados por erro de digitação
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
        
        df = df.replace(["NAN", "NONE", ""], "NÃO INFORMADO")
        
        # Filtro de segurança: remove linhas onde nem responsável nem participante existem
        df = df[~((df["NOME DO RESPONSÁVEL"] == "NÃO INFORMADO") & (df["NOME DO PARTICIPANTE (ATIVIDADES)"] == "NÃO INFORMADO"))]
        
        return df
    except Exception as e:
        st.error(f"Erro Crítico: {e}")
        return None

df_base = load_data()

if df_base is not None:
    # Definição de Colunas Mestras
    COL_RESPONSAVEL = "NOME DO RESPONSÁVEL"
    COL_TRAMPO = "EXERCE ATIVIDADE REMUNERADA:"
    COL_RENDA = "RENDA FAMILIAR TOTAL"
    
    # Criamos uma base ÚNICA por família para análise socioeconômica real
    # Isso impede que uma família com 4 filhos conte como 4 rendas nos gráficos
    df_familias_unicas = df_base.drop_duplicates(subset=[COL_RESPONSAVEL])
    df_familias_unicas = df_familias_unicas[df_familias_unicas[COL_RESPONSAVEL] != "NÃO INFORMADO"]

    # --- 4. KPIs NO TOPO ---
    st.markdown('<div class="main-header"><h1>Gestão de Vulnerabilidade Familiar | CAS</h1></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-card"><div class="label-card">Famílias (Responsáveis)</div><div style="font-size:2rem; font-weight:800;">{len(df_familias_unicas)}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><div class="label-card">Total de Participantes</div><div style="font-size:2rem; font-weight:800;">{len(df_base)}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card"><div class="label-card">Lista de Exportação</div><div style="font-size:2rem; font-weight:800;">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS ---
    st.write("---")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        op_trampo = sorted(df_familias_unicas[COL_TRAMPO].unique())
        f_trampo = st.multiselect("🛠️ Trabalha?", op_trampo, default=op_trampo)
    with c2:
        op_renda = sorted(df_familias_unicas[COL_RENDA].unique())
        f_renda = st.multiselect("💰 Renda Familiar:", op_renda, default=op_renda)
    
    # Aplicando filtros na base de famílias
    df_f_filtrado = df_familias_unicas[df_familias_unicas[COL_TRAMPO].isin(f_trampo) & df_familias_unicas[COL_RENDA].isin(f_renda)]
    
    with c3:
        lista_nomes = sorted(df_f_filtrado[COL_RESPONSAVEL].unique())
        selecionado = st.selectbox("🎯 Selecionar Responsável Familiar:", ["SELECIONE UM NOME..."] + lista_nomes)

    # --- 6. EXIBIÇÃO E PRONTUÁRIO ---
    if selecionado != "SELECIONE UM NOME...":
        st.write("---")
        # Dados do responsável e lista de filhos/participantes
        dados_familia = df_base[df_base[COL_RESPONSAVEL] == selecionado]
        chefe = dados_familia.iloc[0]
        
        col_info, col_sel = st.columns([3, 1])
        with col_info:
            st.subheader(f"👤 {selecionado}")
            st.caption(f"Esta família possui {len(dados_familia)} participante(s) matriculado(s).")
        
        with col_sel:
            if selecionado not in st.session_state.lista_exportacao:
                if st.button("➕ Adicionar para Relatório"):
                    st.session_state.lista_exportacao.append(selecionado)
                    st.rerun()
            else:
                st.success("✅ Na Lista")
                if st.button("❌ Remover"):
                    st.session_state.lista_exportacao.remove(selecionado)
                    st.rerun()

        with st.expander("🔍 VER FICHA SOCIOECONÔMICA", expanded=True):
            # Tabela de participantes daquela família específica
            st.markdown("**Participantes desta Unidade Familiar:**")
            st.table(dados_familia[["NOME DO PARTICIPANTE (ATIVIDADES)", "ATIVIDADE DESEJADA", "TURNO"]])
            
            st.markdown("---")
            cols = st.columns(4)
            # Exibe os 22 indicadores principais na ficha
            indicadores_ficha = [1, 2, 4, 6, 7, 9, 10, 11, 13, 17, 18, 19, 20, 21, 23, 24, 27, 28, 29, 31, 33, 37]
            for i, idx in enumerate(indicadores_ficha):
                if idx < len(df_base.columns):
                    col_name = df_base.columns[idx]
                    with cols[i % 4]:
                        st.markdown(f'''<div class="data-card">
                            <div class="label-card">{col_name}</div>
                            <div class="value-card">{chefe[col_name]}</div>
                        </div>''', unsafe_allow_html=True)

    # --- 7. GRÁFICOS (BASEADOS EM FAMÍLIAS ÚNICAS) ---
    st.write("---")
    st.subheader("📊 Diagnóstico Social (Censo Familiar)")
    st.caption("Gráficos baseados em unidades familiares únicas para evitar distorção de dados.")
    
    

    g_cols = st.columns(2)
    indices_graficos = [1, 4, 6, 9, 13, 17, 18, 21, 23, 25, 27, 28] # Seleção dos mais relevantes para não poluir

    for idx, i_graf em enumerate(indices_graficos):
        if i_graf < len(df_base.columns):
            col_nome = df_base.columns[i_graf]
            with g_cols[idx % 2]:
                # Aqui usamos df_f_filtrado para garantir que a estatística seja por FAMÍLIA
                dados = df_f_filtrado[col_nome].value_counts().reset_index()
                dados.columns = [col_nome, 'CONT']
                
                fig = px.bar(
                    dados, y=col_nome, x='CONT', orientation='h',
                    title=f"{col_nome}",
                    color='CONT', color_continuous_scale='Sunsetdark', text='CONT'
                )
                fig.update_layout(height=300, showlegend=False, coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)

    # --- 8. SIDEBAR EXPORT ---
    if st.session_state.lista_exportacao:
        st.sidebar.markdown("---")
        df_export = df_base[df_base[COL_RESPONSAVEL].isin(st.session_state.lista_exportacao)]
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Triagem_CAS')
        st.sidebar.download_button("📥 BAIXAR RELATÓRIO", data=output.getvalue(), file_name="Relatorio_CAS.xlsx")

else:
    st.info("Aguardando carregamento da Planilha Matriculados...")
