import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CAS | Gestão de Vulnerabilidade", layout="wide")

# CSS PARA DESIGN DE ALTO NÍVEL
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; background-color: #f8fafc; }
    
    /* Cabeçalho */
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 40px;
        border-radius: 24px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    }

    /* Grid de Expansão (4 Colunas) */
    .data-grid-item {
        background: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 10px;
    }
    .label-grid { color: #64748b; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }
    .value-grid { color: #1e293b; font-size: 13px; font-weight: 600; }

    /* Cards Principais */
    .glass-card {
        background: white;
        padding: 24px;
        border-radius: 20px;
        border: 1px solid #f1f5f9;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    .badge-vulnerabilidade {
        background-color: #fef2f2;
        color: #dc2626;
        padding: 6px 16px;
        border-radius: 50px;
        font-weight: 800;
        font-size: 14px;
        border: 1px solid #fee2e2;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CARREGAMENTO DE DADOS
@st.cache_data
def load_cas_data():
    # Busca automática pelo arquivo no repositório
    arquivos = [f for f in os.listdir('.') if "Planilha Matriculados" in f]
    if not arquivos: return None
    
    path = arquivos[0]
    df = pd.read_csv(path, dtype=str) if path.endswith('.csv') else pd.read_excel(path, dtype=str)
    df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    return df

df_base = load_cas_data()

if df_base is not None:
    # Colunas de referência
    col_resp = "NOME DO RESPONSÁVEL:"
    col_renda = "RENDA FAMILIAR MENSAL TOTAL:"
    col_trampo = "EXERCE ATIVIDADE REMUNERADA:"

    # Ranking de Vulnerabilidade
    rank_map = {
        "SEM RENDA": 0,
        "ATÉ R$ 405,26": 1,
        "DE R$ 405,26 A R$ 810,50": 2,
        "DE R$ 810,50 A R$ 1.215,76": 3,
        "DE R$ 1.215,76 A R$ 1.621,00 (TRÊS QUARTOS A UM SALÁRIO MÍNIMO)": 4
    }

    # Sidebar: Filtros de Triagem
    st.sidebar.markdown("## 🛡️ Filtros Estratégicos")
    
    f_renda = st.sidebar.multiselect("Nível de Renda:", options=list(rank_map.keys()), default=list(rank_map.keys()))
    
    # NOVO FILTRO: Atividade Remunerada (Sim, Não, Meio Período, etc)
    opcoes_trampo = sorted(df_base[col_trampo].dropna().unique().tolist())
    f_trampo = st.sidebar.multiselect("Ocupação / Trabalho:", options=opcoes_trampo, default=opcoes_trampo)

    # Filtragem e Ordenação (Vulneráveis Primeiro)
    df_responsaveis = df_base[df_base[col_resp].notna()].copy()
    df_responsaveis['v_rank'] = df_responsaveis[col_renda].map(lambda x: rank_map.get(str(x).strip(), 99))
    
    mask = (df_responsaveis[col_renda].isin(f_renda)) & (df_responsaveis[col_trampo].isin(f_trampo))
    df_filtrado = df_responsaveis[mask].sort_values(by=['v_rank', col_resp])
    
    lista_final = df_filtrado[col_resp].unique().tolist()
    selecionado = st.sidebar.selectbox("🎯 Selecionar Responsável:", ["Selecione..."] + lista_final)

    # Painel Principal
    st.markdown('<div class="main-header"><h1>Dossiê Socioeconômico de Vulnerabilidade</h1><p>Monitoramento Analítico das Famílias Matriculadas</p></div>', unsafe_allow_html=True)

    if selecionado != "Selecione...":
        chefe = df_responsaveis[df_responsaveis[col_resp] == selecionado].iloc[0]
        membros = df_base[df_base[col_resp] == selecionado]

        # Cabeçalho do Dossiê
        c_head1, c_head2 = st.columns([2, 1])
        with c_head1:
            st.markdown(f"<h2 style='color:#1e293b; margin-bottom:0;'>{selecionado}</h2>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:#64748b;'>Família composta por {chefe.get('NÚMERO DE PESSOAS NO GRUPO FAMILIAR:', 'N/A')}</p>", unsafe_allow_html=True)
        with c_head2:
            st.markdown(f"<div style='text-align:right'><span class='badge-vulnerabilidade'>{chefe.get(col_renda, 'N/A')}</span></div>", unsafe_allow_html=True)

        st.write(" ")

        # CARDS DE RESUMO
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""<div class="glass-card">
                <div class="label-grid">📍 Localização</div>
                <div class="value-grid"><b>Bairro:</b> {chefe.get('BAIRRO:', 'N/A')}</div>
                <div class="value-grid"><b>Endereço:</b> {chefe.get('ENDEREÇO COMPLETO:', 'N/A')}</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="glass-card">
                <div class="label-grid">💰 Status Econômico</div>
                <div class="value-grid"><b>Trabalha:</b> {chefe.get(col_trampo, 'N/A')}</div>
                <div class="value-grid"><b>Moradia:</b> {chefe.get('SITUAÇÃO DA MORADIA:', 'N/A')}</div>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="glass-card">
                <div class="label-grid">🛡️ Assistência Social</div>
                <div class="value-grid"><b>Benefício:</b> {chefe.get('A FAMÍLIA É BENEFICIÁRIA DE ALGUM PROGRAMA SOCIAL GOVERNAMENTAL:', 'N/A')}</div>
                <div class="value-grid"><b>Programas:</b> {chefe.get('INFORMA O(S) PROGRAMA(S):', 'Nenhum')}</div>
            </div>""", unsafe_allow_html=True)

        # --- EXPANSÃO EM 4 COLUNAS ---
        st.write("---")
        with st.expander("🔍 EXPANDIR FICHA TÉCNICA COMPLETA (4 COLUNAS)", expanded=False):
            st.markdown("### Todos os Dados Correlacionados")
            
            # Pegamos todas as colunas da planilha (56 colunas)
            todas_colunas = df_base.columns.tolist()
            
            # Criamos o layout de 4 colunas para exibir os dados do responsável
            cols = st.columns(4)
            for i, coluna in enumerate(todas_colunas):
                with cols[i % 4]:
                    val = chefe.get(coluna, "---")
                    st.markdown(f"""
                        <div class="data-grid-item">
                            <div class="label-grid">{coluna}</div>
                            <div class="value-grid">{val}</div>
                        </div>
                    """, unsafe_allow_html=True)

            st.write("#### Grupo Familiar (Dependentes)")
            st.dataframe(membros, use_container_width=True)
            
            # Exportação
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                membros.to_excel(writer, index=False)
            st.download_button(f"📥 Baixar Ficha Completa", output.getvalue(), f"{selecionado}.xlsx")

    else:
        st.markdown("<div style='text-align:center; padding:50px; color:#94a3b8;'>Selecione uma família na barra lateral para iniciar a análise.</div>", unsafe_allow_html=True)
else:
    st.error("Planilha não encontrada. Verifique se o arquivo está no repositório.")
