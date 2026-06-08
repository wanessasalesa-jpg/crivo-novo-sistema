import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CRIVO - Gestão Acadêmica", layout="centered")

# --- CONEXÃO DIRETA COM OS LINKS PÚBLICOS (CSV) ---
URL_ESCALACAO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT66dKuSdRkQiZzhsxc2ZwS8Gph7GeKo-OOtLfSkCo9UkhY6CdtzlZQxqE7aI8AQZ-nLwARbT3AYt8f/pub?gid=0&single=true&output=csv"
URL_RESPOSTAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT66dKuSdRkQiZzhsxc2ZwS8Gph7GeKo-OOtLfSkCo9UkhY6CdtzlZQxqE7aI8AQZ-nLwARbT3AYt8f/pub?gid=247901801&single=true&output=csv"

@st.cache_data(ttl=60)
def carregar_dados():
    df_esc = pd.read_csv(URL_ESCALACAO)
    df_res = pd.read_csv(URL_RESPOSTAS)
    return df_esc, df_res

try:
    df_escalacao, df_respostas = carregar_dados()
    st.success("Conexão estável!")
except Exception as e:
    st.error(f"Erro ao conectar: {e}")
    st.stop()

# --- CSS E IDENTIDADE VISUAL (AQUI ESTÁ O QUE TINHA SUMIDO) ---
st.markdown("""
    <style>
    header {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden;}
    .stButton button {
        width: 100% !important;
        border-radius: 10px !important;
        height: 3.5em !important;
        background-color: #002147 !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
    }
    .bloco-cabecalho {
        background-color: #002147 !important;
        padding: 25px !important;
        border-radius: 12px !important;
        color: white !important;
        margin-bottom: 25px !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO ---
st.markdown("""
    <div class="bloco-cabecalho">
        <h1>🎓 CRIVO</h1>
        <h3>Sistema de Gestão de Bancas Acadêmicas</h3>
        <p style="font-size: 0.85em; opacity: 0.8;">© 2026 Desenvolvido por Wanessa Sales de Almeida</p>
    </div>
    """, unsafe_allow_html=True)

# --- RESTANTE DA SUA LÓGICA ---
st.write("### Identificação do Docente")
email_raw = st.text_input("Digite seu e-mail cadastrado:").strip()
if st.button("Acessar Sistema"):
    st.write("Processando acesso...")
    # (A sua lógica de validação de e-mail e carregamento das telas continua daqui)
