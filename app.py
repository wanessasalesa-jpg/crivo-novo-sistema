import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import time
import pytz 

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="CRIVO - Gestão Acadêmica", layout="centered")

# 2. FUSO HORÁRIO E FUNÇÕES
fuso_bruta = pytz.timezone('America/Sao_Paulo')
def obter_agora(): return datetime.now(fuso_bruta)

def tratar_nome_curto(nome_completo):
    if not nome_completo or pd.isna(nome_completo): return ""
    partes = str(nome_completo).strip().split()
    return f"{partes[0]} {partes[1]}" if len(partes) > 1 else partes[0]

# 3. CONEXÃO E ESTILO VISUAL
conn = st.connection("gsheets", type=GSheetsConnection)

# Estilo visual para organizar em Cartões (Cards)
st.markdown("""
    <style>
    .card { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #e1e4e8; margin-bottom: 15px; }
    .stButton button { border-radius: 10px !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

def get_data(aba, ttl_sec=2): return conn.read(worksheet=aba, ttl=ttl_sec)

try:
    df_escalacao = get_data("Escalacao", ttl_sec=300)
except:
    st.error("Conectando ao banco de dados..."); time.sleep(1); st.rerun()

colunas_reais = {str(col).strip().lower(): col for col in df_escalacao.columns}
c_av1_email, c_av1_nome = colunas_reais.get('email_avaliador_1'), colunas_reais.get('avaliador_1')
c_av2_email, c_av2_nome = colunas_reais.get('email_avaliador_2'), colunas_reais.get('avaliador_2')
c_sup_email, c_sup_nome = colunas_reais.get('email_suplente'), colunas_reais.get('avaliador_suplente')
c_ori_email, c_ori_nome = colunas_reais.get('email_orientador'), colunas_reais.get('orientador')
c_turma, c_titulo, c_data, c_horario = colunas_reais.get('turma'), colunas_reais.get('titulo'), colunas_reais.get('data'), colunas_reais.get('horario')
c_aptidao_col, c_assinatura_col = colunas_reais.get('aptidão defesa'), colunas_reais.get('assinatura orientador')
c_aluno1, c_aluno2, c_aluno3, c_aluno4, c_aluno5 = colunas_reais.get('aluno_1'), colunas_reais.get('aluno_2'), colunas_reais.get('aluno_3'), colunas_reais.get('aluno_4'), colunas_reais.get('aluno_5')

def verificar_presenca_email(email, coluna_real):
    if not coluna_real: return False
    return email in df_escalacao[coluna_real].astype(str).str.strip().str.lower().unique()

colunas_respostas_obrigatorias = ["Avaliador", "Email_Avaliador", "Alunos", "Nota_Final", "Papel", "Data_Hora"]
try:
    df_respostas = get_data("Respostas", ttl_sec=0)
    if df_respostas.empty or not all(col in df_respostas.columns for col in colunas_respostas_obrigatorias):
        df_respostas = pd.DataFrame(columns=colunas_respostas_obrigatorias)
except:
    df_respostas = pd.DataFrame(columns=colunas_respostas_obrigatorias)

if 'email' not in st.session_state:
    if "user" in st.query_params: st.session_state.email = st.query_params["user"]

if 'email' not in st.session_state:
    st.title("🎓 CRIVO"); st.subheader("Sistema de Gestão de Bancas"); st.divider()
    email_raw = st.text_input("Digite seu e-mail:").strip()
    if st.button("Acessar"):
        if email_raw:
            if any([verificar_presenca_email(email_raw.lower(), col) for col in [c_av1_email, c_av2_email, c_sup_email, c_ori_email]]):
                st.session_state.email = email_raw.lower(); st.rerun()
            else: st.error("E-mail não autorizado.")
    st.stop()

email_user = st.session_state.email
# (Sua lógica original de definição de papel e exibição continua aqui...)
# Para evitar erros de corte, certifique-se de que o resto da sua lógica original 
# seja colada exatamente abaixo desta linha.
