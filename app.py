import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Prontuário Social", layout="wide", page_icon="🗂️")

if 'lista_exportacao' not in st.session_state:
    st.session_state.lista_exportacao = []

# --- 2. CSS PARA DESIGN DE PRONTUÁRIO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    .main-header {
        background: linear-gradient(135deg, #020617 0%, #1e3a8a 100%);
        padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;
    }
    .info-card {
        background: white; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0;
        margin-bottom: 8px; min-height: 70px;
    }
    .label-title { color: #64748b; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; line-height: 1.2; }
    .value-text { color: #0f172a; font-size: 0.85rem; font-weight: 600; margin-top: 4px; }
    .alert-box {
        padding: 15px; border-radius: 10px; font-weight: bold; border: 1px solid #f87171;
        background-color: #fef2f2; color: #991b1b; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARREGAMENTO DOS DADOS ---
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
        
        # Base de Famílias Únicas (292)
        df_unicos = df[df["NOME DO RESPONSÁVEL"] != "NÃO INFORMADO"].drop_duplicates(subset=["NOME DO RESPONSÁVEL"])
        return df, df_unicos
    except Exception as e:
        st.error(f"Erro no arquivo: {e}")
        return None, None

df_geral, df_unicos = load_data()

if df_geral is not None:
    # --- 4. SIDEBAR (FILTROS LATERAIS) ---
    st.sidebar.header("🎯 Filtros de Vulnerabilidade")
    
    # Filtro: Trabalho
    op_trab = sorted(list(df_unicos["EXERCE ATIVIDADE REMUNERADA:"].unique()))
    f_trab = st.sidebar.multiselect("Exerce Atividade Remunerada?", op_trab, default=op_trab)
    
    # Filtro: Renda
    op_renda = sorted(list(df_unicos["RENDA FAMILIAR TOTAL"].unique()))
    f_renda = st.sidebar.multiselect("Renda Familiar:", op_renda, default=op_renda)
    
    # Filtro: Benefício
    col_benef = "A FAMÍLIA RECEBE ALGUM TIPO DE BENEFÍCIO"
    op_benef = sorted(list(df_unicos[col_benef].unique()))
    f_benef = st.sidebar.multiselect("Recebe Benefício Social?", op_benef, default=op_benef)

    # Aplicação dos Filtros
    df_f = df_unicos[
        (df_unicos["EXERCE ATIVIDADE REMUNERADA:"].isin(f_trab)) & 
        (df_unicos["RENDA FAMILIAR TOTAL"].isin(f_renda)) &
        (df_unicos[col_benef].isin(f_benef))
    ].copy()

    # Ordenação por Vulnerabilidade (Não trabalha + Sem Benefício no topo)
    df_f['RANK'] = df_f.apply(lambda row: 0 if "NÃO" in row["EXERCE ATIVIDADE REMUNERADA:"] and "NÃO" in row[col_benef] else 1, axis=1)
    df_f = df_f.sort_values('RANK')

    # --- 5. BUSCA CENTRAL ---
    st.markdown('<div class="main-header"><h1>Gestão de Vulnerabilidade e Prontuário Social</h1></div>', unsafe_allow_html=True)
    
    # Tratamento seguro para a lista de nomes (evita o erro sorted/TypeError)
    lista_nomes = [n for n in df_f["NOME DO RESPONSÁVEL"].unique() if n != "NÃO INFORMADO"]
    # Manter a ordem de vulnerabilidade definida no RANK
    opcoes_finais = ["SELECIONE UM RESPONSÁVEL..."] + lista_nomes

    selecionado = st.selectbox(f"🔍 Selecionar Família ({len(lista_nomes)} encontradas):", opcoes_finais)

    # --- 6. EXIBIÇÃO TOTAL (DADOS DA TABELA) ---
    if selecionado != "SELECIONE UM RESPONSÁVEL...":
        st.write("---")
        
        # Dados completos da família
        familia = df_geral[df_geral["NOME DO RESPONSÁVEL"] == selecionado]
        dados_base = familia.iloc[0]
        
        # Alerta de Vulnerabilidade Crítica
        if "NÃO" in dados_base["EXERCE ATIVIDADE REMUNERADA:"] and "NÃO" in dados_base[col_benef]:
            st.markdown(f'<div class="alert-box">🚨 ATENÇÃO: {selecionado} está em Vulnerabilidade Crítica (Sem Trabalho e Sem Benefício).</div>', unsafe_allow_html=True)

        c_nome, c_btn = st.columns([3, 1])
        c_nome.subheader(f"🗂️ Prontuário: {selecionado}")
        
        if c_btn.button("🚀 Adicionar à Exportação"):
            if selecionado not in st.session_state.lista_exportacao:
                st.session_state.lista_exportacao.append(selecionado)
                st.rerun()

        # EXIBIR TUDO: O sistema percorre todas as colunas existentes na planilha
        st.write("### 📝 Informações Detalhadas (Cadastro Completo)")
        todas_colunas = df_geral.columns.tolist()
        
        # Grid de 4 colunas para exibir todos os campos
        cols = st.columns(4)
        for i, campo in enumerate(todas_colunas):
            with cols[i % 4]:
                st.markdown(f'''<div class="info-card">
                    <div class="label-title">{campo}</div>
                    <div class="value-text">{dados_base[campo]}</div>
                </div>''', unsafe_allow_html=True)

        st.write("---")
        st.write(f"### 👨‍👩‍👧‍👦 Participantes da Família ({len(familia)})")
        st.dataframe(familia[["NOME DO PARTICIPANTE (ATIVIDADES)", "IDADE (PARTICIPANTE)", "ATIVIDADE DESEJADA", "TURNO"]], use_container_width=True)

    # --- 7. SIDEBAR EXPORTAÇÃO ---
    if st.session_state.lista_exportacao:
        st.sidebar.write("---")
        st.sidebar.subheader("📦 Exportar Selecionados")
        st.sidebar.info(f"{len(st.session_state.lista_exportacao)} famílias na lista.")
        
        df_exp = df_geral[df_geral["NOME DO RESPONSÁVEL"].isin(st.session_state.lista_exportacao)]
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            df_exp.to_excel(writer, index=False)
        
        st.sidebar.download_button("📥 Baixar Excel", buf.getvalue(), "Relatorio_Vulnerabilidade.xlsx", use_container_width=True)
        
        if st.sidebar.button("🗑️ Limpar Lista"):
            st.session_state.lista_exportacao = []
            st.rerun()

else:
    st.error("Planilha não detectada. Por favor, verifique o arquivo no repositório.")
