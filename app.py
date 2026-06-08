import streamlit as st
import pandas as pd
from datetime import datetime
import time

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CRIVO - Gestão Acadêmica", layout="centered")

# 2. CONEXÃO DIRETA (Links CSV)
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

# 3. FUNÇÕES AUXILIARES
def obter_agora():
    return datetime.now()

def tratar_nome_curto(nome_completo):
    if not nome_completo or pd.isna(nome_completo): return ""
    partes = str(nome_completo).strip().split()
    return f"{partes[0]} {partes[1]}" if len(partes) > 1 else partes[0]

# 4. MAPEAMENTO DE COLUNAS
colunas_reais = {str(col).strip().lower(): col for col in df_escalacao.columns}

c_av1_email = colunas_reais.get('email_avaliador_1')
c_av1_nome = colunas_reais.get('avaliador_1')
c_av2_email = colunas_reais.get('email_avaliador_2')
c_av2_nome = colunas_reais.get('avaliador_2')
c_sup_email = colunas_reais.get('email_suplente')
c_sup_nome = colunas_reais.get('avaliador_suplente')
c_ori_email = colunas_reais.get('email_orientador')
c_ori_nome = colunas_reais.get('orientador')
c_turma = colunas_reais.get('turma')
c_titulo = colunas_reais.get('titulo')
c_data = colunas_reais.get('data')
c_horario = colunas_reais.get('horario')
c_aptidao_col = colunas_reais.get('aptidão defesa')
c_assinatura_col = colunas_reais.get('assinatura orientador')
c_aluno1 = colunas_reais.get('aluno_1')
c_aluno2 = colunas_reais.get('aluno_2')
c_aluno3 = colunas_reais.get('aluno_3')
c_aluno4 = colunas_reais.get('aluno_4')
c_aluno5 = colunas_reais.get('aluno_5')

def verificar_presenca_email(email, coluna_real):
    if not coluna_real: return False
    return email in df_escalacao[coluna_real].astype(str).str.strip().str.lower().unique()

# --- LÓGICA DO SISTEMA ---
if 'email' not in st.session_state:
    if "user" in st.query_params: st.session_state.email = st.query_params["user"]

if 'email' not in st.session_state:
    st.title("🎓 CRIVO")
    email_raw = st.text_input("Digite seu e-mail:").strip()
    if st.button("Acessar"):
        if verificar_presenca_email(email_raw.lower(), c_av1_email) or verificar_presenca_email(email_raw.lower(), c_ori_email):
            st.session_state.email = email_raw.lower()
            st.rerun()
    st.stop()

# (Cole o restante da tua lógica a partir daqui...)
