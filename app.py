import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO E VISUAL
st.set_page_config(page_title="CRIVO - Gestão Acadêmica", layout="centered")

# --- CSS (IDENTIDADE VISUAL) ---
st.markdown("""
    <style>
    header {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden;}
    .stButton button { width: 100% !important; border-radius: 10px !important; height: 3.5em !important; background-color: #002147 !important; color: white !important; font-weight: bold !important; border: none !important; }
    .bloco-cabecalho { background-color: #002147 !important; padding: 25px !important; border-radius: 12px !important; color: white !important; margin-bottom: 25px !important; box-shadow: 0px 4px 10px rgba(0,0,0,0.1) !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO (LINK PÚBLICO CSV)
URL_ESCALACAO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT66dKuSdRkQiZzhsxc2ZwS8Gph7GeKo-OOtLfSkCo9UkhY6CdtzlZQxqE7aI8AQZ-nLwARbT3AYt8f/pub?gid=0&single=true&output=csv"
URL_RESPOSTAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT66dKuSdRkQiZzhsxc2ZwS8Gph7GeKo-OOtLfSkCo9UkhY6CdtzlZQxqE7aI8AQZ-nLwARbT3AYt8f/pub?gid=247901801&single=true&output=csv"

@st.cache_data(ttl=60)
def carregar_dados():
    return pd.read_csv(URL_ESCALACAO), pd.read_csv(URL_RESPOSTAS)

try:
    df_escalacao, df_respostas = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar: {e}")
    st.stop()

# 3. CABEÇALHO
st.markdown("""
    <div class="bloco-cabecalho">
        <h1>🎓 CRIVO</h1>
        <h3>Sistema de Gestão de Bancas Acadêmicas</h3>
    </div>
    """, unsafe_allow_html=True)

# 4. VALIDAÇÃO DE ACESSO (LOGÍN SIMPLIFICADO)
if 'email' not in st.session_state:
    st.write("### Identificação do Docente")
    email_input = st.text_input("Digite seu e-mail:").strip().lower()
    
    if st.button("Acessar"):
        # Verifica em TODAS as colunas que podem conter e-mail
        encontrou = False
        for col in df_escalacao.columns:
            if 'email' in col.lower():
                if email_input in df_escalacao[col].astype(str).str.lower().values:
                    encontrou = True
                    break
        
        if encontrou:
            st.session_state.email = email_input
            st.rerun()
        else:
            st.error("E-mail não encontrado na planilha.")
    st.stop()

# 5. O SISTEMA (SE LOGADO)
st.success(f"Bem-vindo, {st.session_state.email}")
st.write("Dados carregados com sucesso. Agora você pode prosseguir com a lógica de avaliação.")
# (Cole o restante da sua lógica de rubricas aqui abaixo)
