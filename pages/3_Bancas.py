import streamlit as st
import uuid
import pandas as pd
import io
from datetime import datetime, time

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Portal de Bancas - CRIVO", page_icon="🎓", layout="wide")

# 2. DESIGN CUSTOMIZADO (CSS)
st.markdown("""
    <style>
    .titulo-principal { color: #800040; font-family: 'Arial'; font-weight: bold; margin-bottom: 5px; }
    .cartao-banca { background-color: #ffffff; padding: 20px; border-radius: 8px; border-left: 6px solid #800040; margin-bottom: 5px; box-shadow: 0px 2px 8px rgba(0,0,0,0.08); }
    .badge-tcci { background-color: #3498db; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-tccii { background-color: #2980b9; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-mcmiv { background-color: #2ecc71; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-mcmv { background-color: #27ae60; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-piepe { background-color: #e67e22; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# 3. FUNÇÕES UTILITÁRIAS
def forçar_recarregamento_tela():
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

def formatar_nome_email(email):
    try:
        nome_parte = email.split('@')[0]
        return " ".join([p.capitalize() for p in nome_parte.split('.')])
    except:
        return email

def obter_classe_cor(modulo):
    cores = {
        "TCC I": "badge-tcci", "TCC II": "badge-tccii",
        "MCM IV": "badge-mcmiv", "MCM V": "badge-mcmv", "PIEPE": "badge-piepe"
    }
    return cores.get(modulo, "badge-piepe")

def liberar_acesso_professor(email_prof, perfil_prof):
    if email_prof and email_prof not in st.session_state.permissoes_acesso:
        st.session_state.permissoes_acesso[email_prof] = {"perfil": perfil_prof, "modulos": []}

# 4. BANCO DE DADOS TEMPORÁRIO
if "bancos_avaliacoes" not in st.session_state:
    st.session_state.bancos_avaliacoes = [] 

if "permissoes_acesso" not in st.session_state or isinstance(st.session_state.permissoes_acesso.get("wanessa.almeida@afya.com.br"), str):
    st.session_state.permissoes_acesso = {
        "wanessa.almeida@afya.com.br": {"perfil": "Administrador", "modulos": ["Todos"]}
    }

if "usuario_bancas" not in st.session_state:
    st.session_state.usuario_bancas = None 

# ==========================================
# MÓDULO DE LOGIN
# ==========================================
def tela_login():
    st.markdown("<h2 class='titulo-principal'>🎓 Portal de Bancas e Avaliações</h2>", unsafe_allow_html=True)
    st.write("Insira suas credenciais para acessar a sua área.")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_login"):
            email = st.text_input("E-mail de Acesso:").lower().strip()
            senha = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if submit:
                if email not in st.session_state.permissoes_acesso:
                    st.error("Email não cadastrado. Procure a coordenação do módulo.")
                elif senha != "afya2026": 
                    st.error("Senha incorreta.")
                else:
                    dados_acesso = st.session_state.permissoes_acesso[email]
                    st.session_state.usuario_bancas = {
                        "perfil": dados_acesso["perfil"], 
                        "email": email, 
                        "nome": formatar_nome_email(email),
                        "modulos": dados_acesso.get("modulos", [])
                    }
                    forçar_recarregamento_tela()

# ==========================================
# PAINEL 0: ADMINISTRAÇÃO
# ==========================================
def tela_administracao():
    col_titulo, col_logout = st.columns([4, 1])
    with col_titulo:
        st.markdown(f"### 👑 Painel de Administração Master | Olá, {st.session_state.usuario_bancas['nome']}")
    with col_logout:
        if st.button("Sair (Logout)"):
            st.session_state.usuario_bancas = None
            forçar_recarregamento_tela()
            
    with st.expander("➕ Adicionar Novo Coordenador", expanded=True):
        with st.form("form_add_coord", clear_on_submit=True):
            novo_email_coord = st.text_input("E-mail do Coordenador (@afya.com.br):").lower().strip()
            modulos_delegados = st.multiselect(
                "Selecione os módulos sob responsabilidade:", 
                ["TCC I", "TCC II", "MCM IV", "MCM V", "PIEPE"]
            )
            
            if st.form_submit_button("Conceder Acesso"):
                if not novo_email_coord.endswith("@afya.com.br"):
                    st.error("E-mail inválido.")
                else:
                    st.session_state.permissoes_acesso[novo_email_coord] = {"perfil": "Coordenação", "modulos": modulos_delegados}
                    forçar_recarregamento_tela()
                
    for email, dados in st.session_state.permissoes_acesso.items():
        if isinstance(dados, dict) and dados.get("perfil") == "Coordenação":
            with st.container(border=True):
                st.write(f"**{formatar_nome_email(email)}** ({email}) ➔ Módulos: {', '.join(dados.get('modulos', []))}")
                if st.button("🗑️ Revogar Acesso", key=f"rev_{email}"):
                    del st.session_state.permissoes_acesso[email]
                    forçar_recarregamento_tela()

# ==========================================
# PAINEL 1: COORDENAÇÃO
# ==========================================
def tela_coordenacao():
    col_titulo, col_logout = st.columns([4, 1])
    with col_titulo:
        st.markdown(f"### ⚙️ Painel da Coordenação | Olá, {st.session_state.usuario_bancas['nome']}")
    with col_logout:
        if st.button("Sair (Logout)"):
            st.session_state.usuario_bancas = None
            forçar_recarregamento_tela()
            
    aba_criar, aba_gerenciar = st.tabs(["➕ Criar Novo Grupo/Banca", "📋 Controle e Edição"])
    
    with aba_criar:
        modulos_permitidos = st.session_state.usuario_bancas["modulos"]
        modulo_selecionado = st.selectbox("Selecione o Módulo:", modulos_permitidos, index=None)
        
        if modulo_selecionado:
            formato_piepe = st.radio("Formato:", ["Slide", "Banner"]) if modulo_selecionado == "PIEPE" else None
            with st.form("form_nova_banca", clear_on_submit=True):
                data_banca = st.date_input("Data:", format="DD/MM/YYYY")
                horario = st.time_input("Horário:") if modulo_selecionado != "PIEPE" else None
                titulo = st.text_input("Título:")
                o_email = st.text_input("E-mail Orientador:").lower().strip()
                b1 = st.text_input("E-mail Titular 1:")
                b2 = st.text_input("E-mail Titular 2:")
                bs = st.text_input("E-mail Suplente (opcional):")
                alunos = st.text_area("Nomes dos Alunos:")
                
                if st.form_submit_button("Salvar"):
                    banca = {
                        "id": str(uuid.uuid4())[:8], "modulo": modulo_selecionado, "titulo": titulo,
                        "data": data_banca.strftime("%d/%m/%Y"), "alunos": alunos.split('\n'),
                        "orientador_email": o_email, "avaliador_1_email": b1, "avaliador_2_email": b2, "avaliador_sup_email": bs,
                        "status": "Aguardando"
                    }
                    st.session_state.bancos_avaliacoes.append(banca)
                    st.toast("Banca criada!")

    with aba_gerenciar:
        if st.session_state.bancos_avaliacoes:
            # TRAVA DE SEGURANÇA PARA O EXCEL NÃO QUEBRAR
            df_export = pd.DataFrame(st.session_state.bancos_avaliacoes)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False)
            st.download_button("📥 Baixar Excel", data=buffer.getvalue(), file_name="Bancas.xlsx")
            
            for i, banca in enumerate(reversed(st.session_state.bancos_avaliacoes)):
                with st.container(border=True):
                    st.markdown(f"**{banca['titulo']}**")
                    if st.button("🗑️ Excluir", key=f"del_{banca['id']}"):
                        st.session_state.bancos_avaliacoes.pop(len(st.session_state.bancos_avaliacoes) - 1 - i)
                        st.rerun()

if st.session_state.usuario_bancas is None: tela_login()
elif st.session_state.usuario_bancas["perfil"] == "Administrador": tela_administracao()
elif st.session_state.usuario_bancas["perfil"] == "Coordenação": tela_coordenacao()
