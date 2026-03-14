import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Diagnóstico de Vulnerabilidade", layout="wide", page_icon="📋")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN SÓBRIO E PROFISSIONAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        padding: 30px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px;
    }
    .kpi-box {
        background: white; padding: 20px; border-radius: 12px; border-top: 5px solid #1e40af;
        text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .kpi-title { color: #64748b; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; }
    .kpi-value { color: #1e293b; font-size: 2.5rem; font-weight: 800; }
    .status-vulneravel { background-color: #fee2e2; color: #991b1b; padding: 5px 10px; border-radius: 5px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LÓGICA DE FAMÍLIAS (292) ---
@st.cache_data
def load_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', ''], 'NÃO INFORMADO')
        
        # Filtro: Apenas linhas com responsável preenchido (As 292 famílias)
        df_familias = df[df["NOME DO RESPONSÁVEL"] != "NÃO INFORMADO"].copy()
        # Remove duplicados para ter 1 linha por família na triagem
        df_unicos = df_familias.drop_duplicates(subset=["NOME DO RESPONSÁVEL"])
        
        return df, df_unicos
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
        return None, None

df_geral, df_unicos = load_data()

if df_geral is not None:
    COL_RESP = "NOME DO RESPONSÁVEL"
    COL_PART = "NOME DO PARTICIPANTE (ATIVIDADES)"
    COL_TRAB = "EXERCE ATIVIDADE REMUNERADA:"

    # --- 4. KPIs ---
    st.markdown('<div class="main-header"><h1>Relatório de Vulnerabilidade CAS 2026</h1></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Unidades Familiares</div><div class="kpi-value">{len(df_unicos)}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Participantes Totais</div><div class="kpi-value">{len(df_geral)}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Exportar Selecionados</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTROS POR TRABALHO E VULNERABILIDADE ---
    st.write("---")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        op_trab = sorted(df_unicos[COL_TRAB].unique())
        # Filtro focado em quem "NÃO" trabalha (mais vulneráveis)
        sel_trab = st.multiselect("Filtrar por Trabalho:", op_trab, default=[x for x in op_trab if "NÃO" in x])

    # Filtrar e Ordenar: Quem não trabalha aparece primeiro na lista
    df_filtrado = df_unicos[df_unicos[COL_TRAB].isin(sel_trab)]
    df_filtrado = df_filtrado.sort_values(by=COL_TRAB, ascending=True)

    with c2:
        lista_busca = sorted([str(n) for n in df_filtrado[COL_RESP].unique()])
        selecionado = st.selectbox("🎯 Selecione a Família pelo Responsável:", ["SELECIONE..."] + lista_busca)

    # --- 6. ANÁLISE SOCIOECONÔMICA DETALHADA ---
    if selecionado != "SELECIONE...":
        st.write("---")
        # Puxa todos os membros daquela família na base geral
        familia_completa = df_geral[df_geral[COL_RESP] == selecionado]
        dados_sociais = familia_completa.iloc[0]

        col_text, col_btn = st.columns([3, 1])
        
        with col_text:
            st.subheader(f"👤 Responsável: {selecionado}")
            if "NÃO" in str(dados_sociais[COL_TRAB]):
                st.markdown('<span class="status-vulneravel">⚠️ ALTA VULNERABILIDADE: SEM RENDA REMUNERADA</span>', unsafe_allow_html=True)
        
        with col_btn:
            if selecionado not in st.session_state.lista_exportacao:
                if st.button("➕ Adicionar à Exportação"):
                    st.session_state.lista_exportacao.append(selecionado)
                    st.rerun()
            else:
                if st.button("❌ Remover da Lista"):
                    st.session_state.lista_exportacao.remove(selecionado)
                    st.rerun()

        # Detalhes Socioeconômicos em colunas
        st.write("### 📋 Perfil da Família")
        det1, det2, det3, det4 = st.columns(4)
        det1.metric("Trabalha?", dados_sociais[COL_TRAB])
        det2.metric("Renda Familiar", dados_sociais["RENDA FAMILIAR TOTAL"])
        det3.metric("Moradia", dados_sociais["SITUAÇÃO DE MORADIA"])
        det4.metric("Benefício Social", dados_sociais["A FAMÍLIA RECEBE ALGUM TIPO DE BENEFÍCIO"])

        # Tabela de Participantes (Filhos/Dependentes)
        st.write(f"### 👨‍👩‍👧‍👦 Participantes ({len(familia_completa)})")
        st.dataframe(familia_completa[[COL_PART, "IDADE (PARTICIPANTE)", "ATIVIDADE DESEJADA", "TURNO"]], use_container_width=True)

    # --- 7. EXPORTAÇÃO NO SIDEBAR ---
    if st.session_state.lista_exportacao:
        st.sidebar.markdown("### 🚀 Exportar Relatório")
        df_exp = df_geral[df_geral[COL_RESP].isin(st.session_state.lista_exportacao)]
        
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False, sheet_name='Triagem_Social')
        
        st.sidebar.download_button(
            label="📥 BAIXAR EXCEL",
            data=buf.getvalue(),
            file_name="Relatorio_Vulnerabilidade_CAS.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        if st.sidebar.button("🗑️ Limpar Tudo"):
            st.session_state.lista_exportacao = []
            st.rerun()

else:
    st.error("Planilha não encontrada. Verifique o nome do arquivo.")
