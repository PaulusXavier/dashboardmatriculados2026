import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="SINE - Inteligência Social", layout="wide")

# CSS para garantir que as letras sejam SEMPRE pretas e visíveis (Contraste Forçado)
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
    
    /* Forçar cor preta em todos os textos dentro dos cards para evitar conflito com tema escuro */
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

# 2. CAMINHO DO ARQUIVO (Ajustado para mesma pasta do script)
CAMINHO = "Planilha Matriculados.xlsx"

@st.cache_data
def carregar_dados_excel(caminho):
    try:
        if not os.path.exists(caminho):
            # Se não achar na pasta local, tenta o caminho absoluto antigo como backup
            caminho_abs = r"C:\Users\paulo\Downloads\Planilha com Dados para o SINE\Planilha Matriculados.xlsx"
            if os.path.exists(caminho_abs):
                caminho = caminho_abs
            else:
                st.error(f"Arquivo não encontrado.")
                return None
        df = pd.read_excel(caminho, dtype=str)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return None

df = carregar_dados_excel(CAMINHO)

# Função para buscar informação com tratamento de erro
def get_safe_val(dataframe, col_name):
    if col_name in dataframe.columns:
        val = dataframe[col_name].iloc[0]
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

    # --- BARRA LATERAL ---
    st.sidebar.header("📊 Filtros e Estatísticas")
    
    col_t = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_ah = 'EXERCE ATIVIDADE REMUNERADA:'

    # Estatística de Bairros
    if 'BAIRRO:' in df.columns:
        st.sidebar.markdown("### Demanda por Bairro")
        stats_bairro = df['BAIRRO:'].value_counts().reset_index()
        fig = px.pie(stats_bairro, values='count', names='BAIRRO:', hole=0.4)
        fig.update_layout(showlegend=False, height=200, margin=dict(t=0,b=0,l=0,r=0))
        st.sidebar.plotly_chart(fig, use_container_width=True)

    # Filtro de Atividade Remunerada
    df_filtrado = df.copy()
    if col_ah in df.columns:
        opcoes_ah = ["Todos"] + sorted([str(x) for x in df[col_ah].dropna().unique()])
        sel_ah = st.sidebar.selectbox("Filtro Trabalho:", opcoes_ah)
        if sel_ah != "Todos":
            df_filtrado = df[df[col_ah] == sel_ah]

    # Lista de Responsáveis
    if col_t in df_filtrado.columns:
        df_prio = df_filtrado[[col_t, col_renda]].drop_duplicates(subset=[col_t])
        df_prio['rank'] = df_prio[col_renda].apply(get_rank)
        lista_ordenada = df_prio.sort_values(by=['rank', col_t])[col_t].map(str).tolist()
        
        selecionado = st.sidebar.selectbox("Responsável (Ordenado por Renda):", lista_ordenada)
        
        if selecionado:
            dados_resp = df_filtrado[df_filtrado[col_t] == selecionado]
            renda_atual = get_safe_val(dados_resp, col_renda)
            
            st.markdown(f"<h1 style='text-align: center;'>{selecionado}</h1>", unsafe_allow_html=True)
            
            if get_rank(renda_atual) <= 2:
                st.markdown(f'<div class="alerta-baixa-renda">⚠️ ALTA VULNERABILIDADE: {renda_atual}</div>', unsafe_allow_html=True)

            # --- SEÇÃO 1: TERRITÓRIO ---
            st.markdown(f'''
                <div class="section-card bg-endereco">
                    <h3>🏠 1. Território e Localização</h3>
                    <p><b>Endereço:</b> {get_safe_val(dados_resp, 'ENDEREÇO COMPLETO:')}</p>
                    <p><b>Bairro:</b> {get_safe_val(dados_resp, 'BAIRRO:')}</p>
                    <p><b>Município:</b> {get_safe_val(dados_resp, 'MUNICÍPIO:')}</p>
                </div>
            ''', unsafe_allow_html=True)

            # --- SEÇÃO 2: COMPOSIÇÃO FAMILIAR ---
            st.markdown('<div class="section-card bg-pessoal"><h3>👥 2. Composição Familiar</h3>', unsafe_allow_html=True)
            cols_fixas = ['NOME:', 'IDADE:', 'GÊNERO:', 'GRAU DE PARENTESCO:', 'ESCOLARIDADE:', 'PESSOA COM DEFICIÊNCIA:']
            existentes = [c for c in cols_fixas if c in df.columns]
            st.dataframe(dados_resp[existentes], use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # --- SEÇÃO 3: INDICADORES SOCIOECONÔMICOS (TODOS RECUPERADOS) ---
            st.markdown(f'''
                <div class="section-card bg-economico">
                    <h3>💰 3. Indicadores Socioeconômicos</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div>
                            <p><b>Renda Familiar:</b> {renda_atual}</p>
                            <p><b>Trabalha:</b> {get_safe_val(dados_resp, col_ah)}</p>
                            <p><b>Situação da Moradia:</b> {get_safe_val(dados_resp, 'SITUAÇÃO DA MORADIA:')}</p>
                        </div>
                        <div>
                            <p><b>Beneficiário Social:</b> {get_safe_val(dados_resp, 'A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:')}</p>
                            <p><b>Programas:</b> {get_safe_val(dados_resp, 'INFORMA O(S) PROGRAMA(S):')}</p>
                            <p><b>Nº Pessoas na Casa:</b> {get_safe_val(dados_resp, 'NÚMERO DE PESSOAS NO GRUPO FAMILIAR:')}</p>
                        </div>
                    </div>
                </div>
            ''', unsafe_allow_html=True)

            # --- SEÇÃO 4: CONFERÊNCIA TÉCNICA TOTAL ---
            with st.expander("🔍 Visualizar Ficha Técnica Completa (B até BD)"):
                colunas_alvo = df.columns[1:56]
                for idx, row in dados_resp.iterrows():
                    st.markdown(f"### Registro de: {row.get('NOME:', 'Integrante')}")
                    for col in colunas_alvo:
                        val = row[col]
                        if pd.notna(val) and str(val).lower() != 'nan':
                            st.markdown(f"<span class='label-conferencia'>{col}</span>", unsafe_allow_html=True)
                            st.markdown(f"<div class='valor-conferencia'>{val}</div>", unsafe_allow_html=True)
                    st.divider()
