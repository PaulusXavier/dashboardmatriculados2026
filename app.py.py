import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="SINE - Inteligência Social", layout="wide")

# CSS PARA GARANTIR CONTRASTE (Texto sempre preto nos cards para leitura em modo claro/escuro)
st.markdown("""
    <style>
    .section-card { 
        padding: 20px; 
        border-radius: 12px; 
        margin-bottom: 20px; 
        border: 1px solid #e2e8f0; 
    }
    .bg-endereco { background-color: #e0f2fe !important; border-left: 10px solid #0284c7; }
    .bg-pessoal { background-color: #ffe4e6 !important; border-left: 10px solid #be123c; }
    .bg-economico { background-color: #dcfce7 !important; border-left: 10px solid #16a34a; }
    
    /* Forçar cor preta em todos os textos dentro dos cards */
    .section-card h3, .section-card p, .section-card b, .section-card span { 
        color: #1a1a1a !important; 
    }
    
    .alerta-baixa-renda { 
        background-color: #7f1d1d; color: white !important; padding: 15px; 
        border-radius: 8px; text-align: center; font-weight: bold; font-size: 18px; margin-bottom: 20px; 
    }
    .label-conferencia { font-weight: bold; color: #475569; margin-top: 10px; display: block; }
    .valor-conferencia { color: #1e293b; background: #f8fafc; padding: 5px 10px; border-radius: 4px; border: 1px solid #dee2e6; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# 2. CAMINHO AJUSTADO PARA NUVEM/PASTA LOCAL
# O arquivo deve estar na mesma pasta que este código .py
CAMINHO = "Planilha Matriculados.xlsx"

@st.cache_data
def carregar_dados_excel(caminho):
    try:
        if not os.path.exists(caminho):
            st.error(f"Arquivo '{caminho}' não encontrado na pasta do projeto.")
            return None
        # Lê garantindo que tudo seja tratado como texto para evitar erros de tipo
        df = pd.read_excel(caminho, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return None

df = carregar_dados_excel(CAMINHO)

# Função auxiliar para garantir visibilidade do texto nos blocos coloridos
def format_text(dataframe, col_keyword):
    cols = [c for c in dataframe.columns if col_keyword.upper() in c.upper()]
    if cols and not dataframe.empty:
        val = dataframe[cols[0]].iloc[0]
        return str(val) if pd.notna(val) and str(val).lower() != 'nan' else "---"
    return "Não encontrado"

if df is not None:
    # --- MAPEAMENTO DE PRIORIDADE ---
    ordem_renda = {
        "SEM RENDA": 0, "ATÉ R$ 405,26": 1, "DE R$ 405,26 A R$ 810,50": 2,
        "DE R$ 810,50 A R$ 1.215,76": 3, "DE R$ 1.215,76 A R$ 1.621,00": 4, "ACIMA DE R$ 1.621,00": 5
    }

    def get_rank(r):
        r = str(r).upper()
        for k, v in ordem_renda.items():
            if k in r: return v
        return 99

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("📊 Painel de Controle")
    
    col_resp = "NOME DO RESPONSÁVEL:"
    
    if col_resp in df.columns:
        # CORREÇÃO DEFINITIVA: Limpa nomes, remove nulos e ordena sem erro de tipo
        lista_nomes = sorted([str(n).strip() for n in df[col_resp].unique() if pd.notna(n)])
        
        selecionado = st.sidebar.selectbox("Selecione o Responsável:", lista_nomes)
        
        if selecionado:
            dados_resp = df[df[col_resp] == selecionado]
            col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
            renda_val = format_text(dados_resp, 'RENDA')
            
            st.markdown(f"<h1 style='text-align: center;'>{selecionado}</h1>", unsafe_allow_html=True)
            
            if get_rank(renda_val) <= 2:
                st.markdown(f'<div class="alerta-baixa-renda">⚠️ ALTA VULNERABILIDADE: {renda_val}</div>', unsafe_allow_html=True)

            # --- SEÇÃO 1: TERRITÓRIO ---
            st.markdown(f'''
                <div class="section-card bg-endereco">
                    <h3>🏠 1. Território e Localização</h3>
                    <p><b>Endereço:</b> {format_text(dados_resp, 'ENDEREÇO')}</p>
                    <p><b>Bairro:</b> {format_text(dados_resp, 'BAIRRO')}</p>
                    <p><b>Município:</b> {format_text(dados_resp, 'MUNICÍPIO')}</p>
                </div>
            ''', unsafe_allow_html=True)

            # --- SEÇÃO 2: COMPOSIÇÃO FAMILIAR ---
            st.markdown('<div class="section-card bg-pessoal"><h3>👥 2. Composição Familiar</h3>', unsafe_allow_html=True)
            colunas_familia = ['NOME:', 'IDADE:', 'GÊNERO:', 'GRAU DE PARENTESCO:', 'ESCOLARIDADE:']
            cols_exis = [c for c in df.columns if any(f.upper() in c.upper() for f in colunas_familia)]
            st.dataframe(dados_resp[cols_exis], use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # --- SEÇÃO 3: INDICADORES ECONÔMICOS ---
            st.markdown(f'''
                <div class="section-card bg-economico">
                    <h3>💰 3. Indicadores Socioeconômicos</h3>
                    <p><b>Renda Familiar:</b> {renda_val}</p>
                    <p><b>Trabalha:</b> {format_text(dados_resp, 'ATIVIDADE REMUNERADA')}</p>
                    <p><b>Moradia:</b> {format_text(dados_resp, 'MORADIA')}</p>
                    <p><b>Beneficiário Social:</b> {format_text(dados_resp, 'BENEFICIÁRIA')}</p>
                </div>
            ''', unsafe_allow_html=True)

            # --- SEÇÃO 4: CONFERÊNCIA TOTAL (PRONTUÁRIO) ---
            with st.expander("🔍 Visualizar Ficha Técnica Completa (B até BD)"):
                colunas_alvo = df.columns[1:56] # Captura intervalo técnico
                for idx, row in dados_resp.iterrows():
                    st.markdown(f"### Registro de: {row.get('NOME:', 'Integrante')}")
                    for col in colunas_alvo:
                        val = row[col]
                        if pd.notna(val) and str(val).lower() != 'nan':
                            st.markdown(f"<span class='label-conferencia'>{col}</span>", unsafe_allow_html=True)
                            st.markdown(f"<div class='valor-conferencia'>{val}</div>", unsafe_allow_html=True)
                    st.divider()