import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS 2026 | Diagnóstico Social", layout="wide", page_icon="📋")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN PROFISSIONAL E SÓBRIO ---
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
    .vulnerabilidade-alta { color: #dc2626; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LIMPEZA ---
@st.cache_data
def load_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Padronização de dados
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', ''], 'NÃO INFORMADO')
        
        # Filtro de Famílias Reais (Onde há responsável)
        df_familias = df[df["NOME DO RESPONSÁVEL"] != "NÃO INFORMADO"].copy()
        return df, df_familias
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        return None, None

df_geral, df_familias = load_data()

if df_geral is not None:
    COL_RESP = "NOME DO RESPONSÁVEL"
    COL_PART = "NOME DO PARTICIPANTE (ATIVIDADES)"
    COL_TRAB = "EXERCE ATIVIDADE REMUNERADA:"

    # --- 4. CABEÇALHO E KPIs ---
    st.markdown('<div class="main-header"><h1>Relatório de Vulnerabilidade CAS 2026</h1><p>Análise Socioeconômica baseada em Unidades Familiares</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">🏠 Unidades Familiares</div><div class="kpi-value">{len(df_familias)}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">👥 Participantes Atendidos</div><div class="kpi-value">{len(df_geral)}</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">📋 Exportações na Fila</div><div class="kpi-value">{len(st.session_state.lista_exportacao)}</div></div>', unsafe_allow_html=True)

    # --- 5. FILTRO DE VULNERABILIDADE (TRABALHO) ---
    st.write("---")
    st.subheader("🔍 Filtro de Prioridade Social")
    
    col_f1, col_f2 = st.columns([1, 2])
    
    with col_f1:
        op_trab = sorted(df_familias[COL_TRAB].unique())
        # Prioriza o "NÃO" no filtro para destacar vulneráveis
        sel_trab = st.multiselect("Filtrar por Atividade Remunerada:", op_trab, default=[x for x in op_trab if "NÃO" in x])

    # Aplicar Filtro e Ordenar (Quem não trabalha aparece primeiro)
    df_filtrado = df_familias[df_familias[COL_TRAB].isin(sel_trab)]
    df_filtrado = df_filtrado.sort_values(by=COL_TRAB, ascending=True)

    with col_f2:
        # Criar lista de busca tratada
        lista_busca = sorted([str(n) for n in df_filtrado[COL_RESP].unique()])
        selecionado = st.selectbox("Selecione um Responsável para ver o Prontuário:", ["SELECIONE..."] + lista_busca)

    # --- 6. EXIBIÇÃO DO PRONTUÁRIO (SEM GRÁFICOS) ---
    if selecionado != "SELECIONE...":
        st.write("---")
        # Busca todos os dados e participantes dessa família
        familia_dados = df_geral[df_geral[COL_RESP] == selecionado]
        dados_base = familia_dados.iloc[0]

        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader(f"📄 Dados da Família: {selecionado}")
            # Alerta de Vulnerabilidade
            if "NÃO" in str(dados_base[COL_TRAB]):
                st.error("⚠️ ESTA FAMÍLIA ENCONTRA-SE EM ESTADO DE VULNERABILIDADE (SEM RENDA ATIVA)")
            
            st.markdown(f"**Situação de Trabalho:** {dados_base[COL_TRAB]}")
            st.markdown(f"**Renda Familiar:** {dados_base['RENDA FAMILIAR TOTAL']}")
            st.markdown(f"**Situação de Moradia:** {dados_base['SITUAÇÃO DE MORADIA']}")
            st.markdown(f"**Recebe Benefício?** {dados_base['A FAMÍLIA RECEBE ALGUM TIPO DE BENEFÍCIO']}")

        with c2:
            st.subheader("⚙️ Ações")
            if st.button("➕ Adicionar à Lista de Exportação"):
                if selecionado not in st.session_state.lista_exportacao:
                    st.session_state.lista_exportacao.append(selecionado)
                    st.success("Adicionado!")
                    st.rerun()
            
            if st.button("🗑️ Limpar Lista"):
                st.session_state.lista_exportacao = []
                st.rerun()

        st.write("### 👥 Participantes vinculados a este Responsável")
        st.table(familia_dados[[COL_PART, "IDADE (PARTICIPANTE)", "ATIVIDADE DESEJADA", "TURNO"]])

    # --- 7. BARRA LATERAL DE EXPORTAÇÃO ---
    if st.session_state.lista_exportacao:
        st.sidebar.header("🚀 Exportar Relatório")
        st.sidebar.write(f"{len(st.session_state.lista_exportacao)} famílias selecionadas.")
        
        df_exp = df_geral[df_geral[COL_RESP].isin(st.session_state.lista_exportacao)]
        
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False, sheet_name='Relatorio_Social')
        
        st.sidebar.download_button(
            label="📥 Baixar Excel",
            data=buf.getvalue(),
            file_name="Relatorio_Vulnerabilidade_CAS2026.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

else:
    st.error("Arquivo 'Planilha Matriculados' não encontrado. Por favor, faça o upload no repositório.")
