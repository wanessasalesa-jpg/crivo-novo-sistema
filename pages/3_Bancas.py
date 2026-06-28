import streamlit as st
import uuid
import pandas as pd
import io
from datetime import datetime, time, timedelta

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="Portal de Bancas - CRIVO", page_icon="🎓", layout="wide")

# 2. DESIGN (CSS)
st.markdown("""
    <style>
    .titulo-principal { color: #800040; font-family: 'Arial'; font-weight: bold; margin-bottom: 5px; }
    .badge-tcci { background-color: #3498db; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-tccii { background-color: #2980b9; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-mcmiv { background-color: #2ecc71; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-mcmv { background-color: #27ae60; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-piepe { background-color: #e67e22; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .status-orientacao { background-color: #f39c12; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .status-agendado { background-color: #800040; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .ata-ok { color: #27ae60; font-weight: bold; }
    .ata-pendente { color: #e74c3c; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 3. FUNÇÕES UTILITÁRIAS
def forçar_recarregamento_tela():
    try: st.rerun()
    except AttributeError: st.experimental_rerun()

def recarregar_com_sucesso(mensagem):
    st.session_state.msg_sucesso_pendente = mensagem
    forçar_recarregamento_tela()

def exibir_sucesso_pendente():
    if st.session_state.get("msg_sucesso_pendente"):
        st.success(st.session_state.msg_sucesso_pendente)
        st.session_state.msg_sucesso_pendente = ""

def obter_classe_cor(modulo):
    cores = {"TCC I": "badge-tcci", "TCC II": "badge-tccii", "MCM IV": "badge-mcmiv", "MCM V": "badge-mcmv", "PIEPE": "badge-piepe"}
    return cores.get(modulo, "badge-piepe")

def formatar_nome_email(email):
    try: return " ".join([p.capitalize() for p in email.split('@')[0].split('.')])
    except: return email

def liberar_acesso_professor(email_prof, perfil_prof):
    if email_prof and email_prof not in st.session_state.permissoes_acesso:
        st.session_state.permissoes_acesso[email_prof] = {"perfil": perfil_prof, "modulos": []}

def verificar_conflito_horario(data, horario, lista_emails, id_ignorar=None):
    if horario == "N/A" or data == "A definir" or not horario: return False, ""
    emails_validos = set([e for e in lista_emails if e])
    for b in st.session_state.bancos_avaliacoes:
        if b['id'] == id_ignorar: continue
        if b['data'] == data and b['horario'] == horario:
            emails_da_banca = set(filter(None, [b.get('orientador_email'), b.get('coorientador_email'), b.get('avaliador_1_email'), b.get('avaliador_2_email'), b.get('avaliador_sup_email')]))
            conflitos = emails_validos.intersection(emails_da_banca)
            if conflitos: return True, ", ".join(conflitos)
    return False, ""

ADMIN_EMAILS = ["wanessa.almeida@afya.com.br", "wanessa.salmeida@yahoo.com.br"]
lista_horarios_base = [time(h, 0) for h in range(8, 22)]
lista_salas_base = [f"APG {i:02d}" for i in range(1, 13)]
lista_semestres = ["2026.1", "2026.2", "2027.1", "2027.2"]

# 4. ESTADO DA MEMÓRIA
if "bancos_avaliacoes" not in st.session_state: st.session_state.bancos_avaliacoes = []
if "permissoes_acesso" not in st.session_state: st.session_state.permissoes_acesso = {}
if "configuracoes" not in st.session_state: st.session_state.configuracoes = {}
for mod in ["TCC I", "TCC II", "MCM IV", "MCM V", "PIEPE"]:
    if mod not in st.session_state.configuracoes:
        st.session_state.configuracoes[mod] = {
            "salas": lista_salas_base.copy(), "horarios": [t.strftime('%H:%M') for t in lista_horarios_base],
            "agend_ini": datetime.now().date(), "agend_fim": datetime.now().date() + timedelta(days=7),
            "notas_ini": datetime.now().date(), "notas_fim": datetime.now().date() + timedelta(days=30)
        }

if "data_fixada_modulo" not in st.session_state: st.session_state.data_fixada_modulo = {}
if "usar_data_fixada_modulo" not in st.session_state: st.session_state.usar_data_fixada_modulo = {}
if "versao_formulario" not in st.session_state: st.session_state.versao_formulario = 0
if "usuario_bancas" not in st.session_state: st.session_state.usuario_bancas = None 

# ==========================================
# LOGIN E ROTEAMENTO
# ==========================================
def tela_login():
    exibir_sucesso_pendente()
    st.markdown("<h2 class='titulo-principal'>🎓 Portal de Bancas e Avaliações</h2>", unsafe_allow_html=True)
    with st.form("form_login"):
        tipo = st.radio("Perfil:", ["👑 Administrador", "⚙️ Coordenador", "📚 Professor"])
        email = st.text_input("E-mail:").lower().strip()
        senha = st.text_input("Senha:", type="password")
        if st.form_submit_button("Entrar"):
            if senha == "afya2026":
                if "Administrador" in tipo and email in ADMIN_EMAILS: st.session_state.usuario_bancas = {"perfil": "Administrador", "email": email, "nome": formatar_nome_email(email)}; forçar_recarregamento_tela()
                elif "Coordenador" in tipo: st.session_state.usuario_bancas = {"perfil": "Coordenação", "email": email, "nome": formatar_nome_email(email), "modulos": st.session_state.permissoes_acesso.get(email, {}).get("modulos", [])}; forçar_recarregamento_tela()
                elif "Professor" in tipo: st.session_state.usuario_bancas = {"perfil": "Professor", "email": email, "nome": formatar_nome_email(email)}; forçar_recarregamento_tela()

# (Continuarei o restante da lógica de telas abaixo...)
