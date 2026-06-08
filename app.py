import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import pytz 

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CRIVO - Gestão Acadêmica", layout="centered")

# 2. FUSO HORÁRIO
fuso_bruta = pytz.timezone('America/Sao_Paulo')

def obter_agora():
    return datetime.now(fuso_bruta)

def tratar_nome_curto(nome_completo):
    if not nome_completo or pd.isna(nome_completo): return ""
    partes = str(nome_completo).strip().split()
    return f"{partes[0]} {partes[1]}" if len(partes) > 1 else partes[0]

# 3. CONEXÃO DIRETA VIA LINK PÚBLICO (PUBLICAR NA WEB - CSV)
# COLOQUE AQUI O SEU LINK GERADO EM "PUBLICAR NA WEB" -> FORMATO .CSV
URL_ESCALACAO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT66dKuSdRkQiZzhsxc2ZwS8Gph7GeKo-OOtLfSkCo9UkhY6CdtzlZQxqE7aI8AQZ-nLwARbT3AYt8f/pub?gid=0&single=true&output=csv"
URL_RESPOSTAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT66dKuSdRkQiZzhsxc2ZwS8Gph7GeKo-OOtLfSkCo9UkhY6CdtzlZQxqE7aI8AQZ-nLwARbT3AYt8f/pub?gid=247901801&single=true&output=csv"

@st.cache_data(ttl=60)
def carregar_dados():
    df_esc = pd.read_csv(URL_ESCALACAO)
    df_res = pd.read_csv(URL_RESPOSTAS)
    return df_esc, df_res

try:
    df_escalacao, df_respostas = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# --- MAPEAMENTO DAS COLUNAS (O SEU CÓDIGO CONTINUA DAQUI...) ---
colunas_reais = {str(col).strip().lower(): col for col in df_escalacao.columns}

c_av1_email = colunas_reais.get('email_avaliador_1')
c_av1_nome = colunas_reais.get('avaliador_1')
# ... (Mantenha o restante das suas definições de colunas aqui)

# --- A PARTIR DAQUI, PODE COLAR O RESTANTE DO SEU CÓDIGO ORIGINAL ---
# (Lógica de autenticação, formulários, rubricas, etc.)
