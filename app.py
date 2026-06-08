import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO E VISUAL
st.set_page_config(page_title="CRIVO - Gestão Acadêmica", layout="centered")

st.markdown("""
    <style>
    header {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden;}
    .stButton button { width: 100% !important; border-radius: 10px !important; height: 3.5em !important; background-color: #002147 !important; color: white !important; font-weight: bold !important; border: none !important; }
    .bloco-cabecalho { background-color: #002147 !important; padding: 25px !important; border-radius: 12px !important; color: white !important; margin-bottom: 25px !important; box-shadow: 0px 4px 10px rgba(0,0,0,0.1) !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO (SEM MENSAGEM DE SUCESSO PARA NÃO POLUIR)
URL_ESCALACAO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT66dKuSdRkQiZzhsxc2ZwS8Gph7GeKo-OOtLfSkCo9UkhY6CdtzlZQxqE7aI8AQZ-nLwARbT3AYt8f/pub?gid=0&single=true&output=csv"
URL_RESPOSTAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT66dKuSdRkQiZzhsxc2ZwS8Gph7GeKo-OOtLfSkCo9UkhY6CdtzlZQxqE7aI8AQZ-nLwARbT3AYt8f/pub?gid=247901801&single=true&output=csv"

@st.cache_data(ttl=60)
def carregar_dados():
    return pd.read_csv(URL_ESCALACAO), pd.read_csv(URL_RESPOSTAS)

df_escalacao, df_respostas = carregar_dados()

# 3. CABEÇALHO
st.markdown("""
    <div class="bloco-cabecalho">
        <h1>🎓 CRIVO</h1>
        <h3>Sistema de Gestão de Bancas Acadêmicas</h3>
        <p style="font-size: 0.85em; opacity: 0.8;">© 2026 Desenvolvido por Wanessa Sales de Almeida</p>
    </div>
    """, unsafe_allow_html=True)

# 4. LÓGICA DE LOGIN (AQUI ESTÁ A CORREÇÃO DO ACESSO)
if 'email' not in st.session_state:
    st.write("### Identificação do Docente")
    email_raw = st.text_input("Digite seu e-mail cadastrado:").strip()
    if st.button("Acessar Sistema"):
        if email_raw:
            email_limpo = email_raw.lower()
            # Verificação contra o dataframe carregado
            if email_limpo in df_escalacao.to_string().lower(): 
                st.session_state.email = email_limpo
                st.rerun()
            else:
                st.error("E-mail não encontrado na escalação.")
    st.stop()

# --- AQUI VOCÊ COLA O RESTANTE DO SEU CÓDIGO ORIGINAL (A partir de 'nome_exibicao = ...') ---
