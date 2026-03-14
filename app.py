import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Socioeconômico Famílias CAS", layout="wide", page_icon="🏠")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS CUSTOMIZADO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f1f5f9; }
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e40af 100%);
        padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;
    }
    .info-card {
        background: white; padding: 10px; border-radius: 8px; border-bottom: 3px solid #cbd5e1;
        margin-bottom: 8px; min-height: 65px;
    }
    .label-title { color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; }
    .value-text { color: #0f172a; font-size: 0.85rem; font-weight: 600; margin-top: 2px; }
    .status-alerta {
        background-color: #fef2f2; border: 1px solid #f87171; color: #991b1b;
        padding: 15px; border-radius: 10px; font-weight: bold; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO E LIMPEZA (SUBSTITUINDO NAN POR TRAÇO) ---
@st.cache_data
def load_data():
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    path = arquivos[0]
    try:
        df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
        
        # Limpar nomes das colunas
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Limpeza de dados: remove espaços e substitui vazios/nan por "-"
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            df[col] = df[col].replace(['NAN', 'NONE', '', ' ', 'NULL'], '-')
        
        # Base de Responsáveis Únicos (FAMÍLIAS)
        # Filtramos para ignorar linhas onde o responsável é apenas um traço
        df_unicos = df[df["NOME DO RESPONSÁVEL"] != "-"].drop_duplicates(subset=["NOME DO RESPONSÁVEL"])
        
        return df, df_unicos
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return None, None

df_geral, df_unicos = load_data()

if df_geral is not None:
    # --- 4. FILTROS LATERAIS ---
    st.sidebar.header("🔍 Filtros de Vulnerabilidade")
    
    col_trab = "EXERCE ATIVIDADE REMUNERADA:"
    col_renda = "RENDA FAMILIAR TOTAL"
    col_benef = "A FAMÍLIA RECEBE ALGUM TIPO DE BENEFÍCIO"

    f_trab = st.sidebar.multiselect("Trabalha?", sorted(list(df_unicos[col_trab].unique())), default=list(df_unicos[col_trab].unique()))
    f_renda = st.sidebar.multiselect("Renda:", sorted(list(df_unicos[col_renda].unique())), default=list(df_unicos[col_renda].unique()))
    
    # Busca pela coluna de benefício (ajustando para possíveis espaços no nome da coluna)
    col_benef_real = [c for c in df_geral.columns if "A FAMÍLIA RECEBE ALGUM TIPO DE BENEFÍCIO" in c][0]
    f_benef = st.sidebar.multiselect("Benefício?", sorted(list(df_unicos[col_benef_real].unique())), default=list(df_unicos[col_benef_real].unique()))

    # Aplicação dos filtros na base de famílias
    df_filtrado = df_unicos[
        (df_unicos[col_trab].isin(f_trab)) & 
        (df_unicos[col_renda].isin(f_renda)) &
        (df_unicos[col_benef_real].isin(f_benef))
    ].copy()

    # Ordenação: Quem não trabalha e não tem benefício fica no topo
    df_filtrado['VULN'] = df_filtrado.apply(lambda r: 0 if "NÃO" in r[col_trab] and "NÃO" in r[col_benef_real] else 1, axis=1)
    df_filtrado = df_filtrado.sort_values('VULN')

    # --- 5. INTERFACE PRINCIPAL ---
    st.markdown('<div class="main-header"><h1>Socioeconômico Famílias CAS</h1></div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    # Exibe o número de famílias filtradas (ex: 222)
    c1.metric("Unidades Familiares", len(df_filtrado))
    c2.metric("Matrículas Totais no Grupo", len(df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(df_filtrado["NOME DO RESPONSÁVEL"])]))

    lista_nomes = [n for n in df_filtrado["NOME DO RESPONSÁVEL"].tolist() if n != "-"]
    selecionado = st.selectbox("🎯 Escolha um Responsável para Ver a Ficha Completa:", ["SELECIONE..."] + lista_nomes)

    # --- 6. PRONTUÁRIO DETALHADO ---
    if selecionado != "SELECIONE...":
        st.write("---")
        familia_data = df_geral[df_geral["NOME DO RESPONSÁVEL"] == selecionado]
        dados_base = familia_data.iloc[0]

        # Alerta de Vulnerabilidade
        if "NÃO" in dados_base[col_trab] and "NÃO" in dados_base[col_benef_real]:
            st.markdown(f'<div class="status-alerta">⚠️ ALERTA: Responsável sem ocupação remunerada e sem benefícios sociais registrados.</div>', unsafe_allow_html=True)

        ctit, cbtn = st.columns([3, 1])
        ctit.subheader(f"🏠 Prontuário Social: {selecionado}")
        
        if cbtn.button("➕ Adicionar para Exportação"):
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

        st.write("### 📄 Dados de Cadastro (Raio-X)")
        grid = st.columns(4)
        for i, coluna in enumerate(df_geral.columns.tolist()):
            with grid[i % 4]:
                st.markdown(f'''<div class="info-card">
                    <div class="label-title">{coluna}</div>
                    <div class="value-text">{dados_base[coluna]}</div>
                </div>''', unsafe_allow_html=True)

        st.write("---")
        st.write(f"### 👨‍👩‍👧‍👦 Membros Matriculados ({len(familia_data)})")
        st.table(familia_data[["NOME DO PARTICIPANTE (ATIVIDADES)", "IDADE (PARTICIPANTE)", "ATIVIDADE DESEJADA", "TURNO"]])

    # --- 7. EXPORTAÇÃO ---
    if st.session_state.lista_exportacao:
        st.sidebar.write("---")
        st.sidebar.subheader("📦 Exportar Selecionados")
        df_exp = df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(st.session_state.lista_exportacao)]
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        st.sidebar.download_button("📥 Baixar Excel", buf.getvalue(), "Relatorio_Familias_Selecionadas.xlsx", use_container_width=True)
        if st.sidebar.button("🗑️ Limpar Lista"):
            st.session_state.lista_exportacao = []
            st.rerun()
else:
    st.info("Aguardando carregamento da planilha...")
