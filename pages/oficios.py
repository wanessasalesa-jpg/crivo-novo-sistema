import streamlit as st
import random
import time
from datetime import datetime, timedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Módulo de Ofícios - CRIVO", page_icon="📄", layout="wide")

# 2. DESIGN CUSTOMIZADO (CSS)
st.markdown("""
    <style>
    .titulo-principal { color: #002147; font-family: 'Arial'; font-weight: bold; margin-bottom: 5px; }
    .cartao-ticket { background-color: #ffffff; padding: 20px; border-radius: 8px; border-left: 6px solid #002147; margin-bottom: 15px; box-shadow: 0px 2px 8px rgba(0,0,0,0.08); }
    .status-pendente { background-color: #ffc107; color: #212529; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .status-aprovado { background-color: #28a745; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .status-recusado { background-color: #dc3545; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .bloco-alerta { background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; border-left: 5px solid #ffeeba; margin-top: 10px;}
    </style>
""", unsafe_allow_html=True)

# 3. BANCO DE DADOS TEMPORÁRIO E CONTROLE DE SESSÃO
if "banco_solicitacoes" not in st.session_state:
    st.session_state.banco_solicitacoes = []
if "contador_oficio_oficial" not in st.session_state:
    st.session_state.contador_oficio_oficial = 0

# --- LÓGICA DE LOGIN ---
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = False
    st.session_state.perfil_usuario = ""

def fazer_login(usuario, senha):
    # Simulação de base de dados de usuários
    if usuario == "admin" and senha == "senha123":
        st.session_state.usuario_logado = True
        st.session_state.perfil_usuario = "Administrativo"
    elif usuario == "prof" and senha == "senha123":
        st.session_state.usuario_logado = True
        st.session_state.perfil_usuario = "Professor"
    elif usuario == "aluno" and senha == "senha123":
        st.session_state.usuario_logado = True
        st.session_state.perfil_usuario = "Aluno"
    else:
        st.error("Credenciais inválidas. Tente novamente.")

def fazer_logout():
    st.session_state.usuario_logado = False
    st.session_state.perfil_usuario = ""

# ==========================================
# TELA DE LOGIN (Mostrada apenas se não estiver logado)
# ==========================================
if not st.session_state.usuario_logado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; color: #002147;'>CRIVO Autenticação</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Módulo de Emissão de Ofícios</p>", unsafe_allow_html=True)
        
        with st.form("form_login"):
            usuario_input = st.text_input("Usuário (Teste com: admin, prof ou aluno)")
            senha_input = st.text_input("Senha (Teste com: senha123)", type="password")
            submit_login = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if submit_login:
                fazer_login(usuario_input, senha_input)
                st.rerun()

# ==========================================
# SISTEMA ROTEADO (Mostrado após o login)
# ==========================================
else:
    # Cabeçalho com botão de sair
    col_titulo, col_sair = st.columns([4, 1])
    with col_titulo:
        st.markdown("<h2 class='titulo-principal'>📄 Central de Ofícios Institucionais</h2>", unsafe_allow_html=True)
    with col_sair:
        st.write(f"Logado como: **{st.session_state.perfil_usuario}**")
        if st.button("Sair (Logout)"):
            fazer_logout()
            st.rerun()
    st.markdown("---")

    # ---------------------------------------------------------
    # VISÃO 1: ÁREA DO SOLICITANTE (ALUNO OU PROFESSOR)
    # ---------------------------------------------------------
    if st.session_state.perfil_usuario in ["Aluno", "Professor"]:
        aba_solicitar, aba_acompanhar = st.tabs(["📤 Nova Solicitação", "🔍 Acompanhar Pedido"])
        
        with aba_solicitar:
            col_form, col_ajuda = st.columns([2, 1])
            
            with col_ajuda:
                st.info("Baixe o modelo oficial, preencha seus dados e anexe ao lado para avaliação.")
                try:
                    with open("Modelo de ofício - Afya (oficial).docx", "rb") as file:
                        st.download_button(label="📄 Baixar Modelo Oficial (.DOCX)", data=file, file_name="Modelo de ofício - Afya (oficial).docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
                except FileNotFoundError:
                    st.warning("⚠️ Arquivo modelo não encontrado no servidor.")

            with col_form:
                with st.form("form_pedido"):
                    st.write(f"Nova solicitação - Perfil: **{st.session_state.perfil_usuario}**")
                    assunto = st.text_input("Objetivo / Assunto do Documento:")
                    destinatario = st.text_input("Destinatário Final:")
                    
                    st.warning("⚠️ Atenção: O anexo do modelo preenchido é obrigatório para análise.")
                    arquivo_upload = st.file_uploader("Anexar seu ofício preenchido:", type=["docx", "pdf"])
                    
                    enviar = st.form_submit_button("Protocolar Pedido")
                    
                if enviar:
                    if not assunto or not destinatario:
                        st.error("Preencha o assunto e o destinatário.")
                    elif arquivo_upload is None:
                        st.error("❌ Operação Recusada: O anexo é obrigatório para professores e alunos.")
                    else:
                        id_gerado = f"REQ-{random.randint(1000, 9999)}"
                        vencimento = datetime.now() + timedelta(days=3)
                        
                        # Salvando todos os dados, incluindo o arquivo lido em bytes
                        st.session_state.banco_solicitacoes.append({
                            "id": id_gerado,
                            "data_solicitacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "prazo_limite": vencimento.strftime("%d/%m/%Y"),
                            "perfil": st.session_state.perfil_usuario,
                            "assunto": assunto,
                            "destinatario": destinatario,
                            "status": "Pendente",
                            "numero_oficio": "-",
                            "nome_arquivo": arquivo_upload.name,
                            "bytes_arquivo": arquivo_upload.getvalue(), # O Cofre do Arquivo
                            "feedback_admin": "" # Onde a secretária vai digitar as correções
                        })
                        st.success(f"✅ Protocolo gerado: {id_gerado}")
                        st.info("Guarde este número para acompanhar o status na aba ao lado.")
                        
        with aba_acompanhar:
            st.markdown("### Digite seu código de protocolo para verificar o andamento")
            codigo_busca = st.text_input("Protocolo (Ex: REQ-1234):")
            
            if st.button("Consultar"):
                encontrado = next((item for item in st.session_state.banco_solicitacoes if item["id"] == codigo_busca), None)
                
                if encontrado:
                    st.markdown(f"**Status atual:** {encontrado['status']}")
                    st.markdown(f"**Número Oficial:** {encontrado['numero_oficio']}")
                    st.markdown(f"**Prazo de Resposta:** {encontrado['prazo_limite']}")
                    
                    if encontrado['status'] == "Correção Solicitada" and encontrado['feedback_admin']:
                        st.markdown(f"""
                        <div class='bloco-alerta'>
                            <strong>⚠️ A Secretaria solicitou ajustes no seu documento:</strong><br>
                            {encontrado['feedback_admin']}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error("Protocolo não encontrado. Verifique se digitou corretamente.")

    # ---------------------------------------------------------
    # VISÃO 2: ÁREA DA SECRETARIA / ADMINISTRATIVA
    # ---------------------------------------------------------
    elif st.session_state.perfil_usuario == "Administrativo":
        st.markdown("### Painel de Gestão e Triagem")
        
        # Filtro para ver apenas os pendentes ou todos
        filtro = st.radio("Filtrar lista:", ["Apenas Pendentes", "Todos os Protocolos"], horizontal=True)
        
        lista_exibicao = st.session_state.banco_solicitacoes
        if filtro == "Apenas Pendentes":
            lista_exibicao = [item for item in lista_exibicao if item["status"] == "Pendente"]
            
        if not lista_exibicao:
            st.info("A fila está limpa! Nenhum ofício aguardando análise.")
        else:
            for item in reversed(lista_exibicao):
                indice = st.session_state.banco_solicitacoes.index(item)
                
                st.markdown(f"""
                <div class='cartao-ticket'>
                    <strong>Protocolo {item['id']}</strong> | Requerente: {item['perfil']}<br>
                    <strong>Assunto:</strong> {item['assunto']}<br>
                    <strong>Status:</strong> {item['status']} | <strong>Ofício Gerado:</strong> {item['numero_oficio']}
                </div>
                """, unsafe_allow_html=True)
                
                # Botão para a Secretária baixar e ler o anexo enviado
                if item.get("bytes_arquivo"):
                    st.download_button(label=f"📥 Baixar Documento Enviado ({item['nome_arquivo']})", data=item["bytes_arquivo"], file_name=item["nome_arquivo"], key=f"dl_{item['id']}")
                
                # Ações de Aprovação ou Recusa
                if item["status"] == "Pendente":
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Aprovar e Gerar Nº Oficial", key=f"aprova_{item['id']}"):
                            st.session_state.contador_oficio_oficial += 1
                            oficio_gerado = f"Ofício nº {st.session_state.contador_oficio_oficial:03d}/{datetime.now().year} AFYAMARABÁ/AFYA/COORD. DE CURSO"
                            st.session_state.banco_solicitacoes[indice]["status"] = "Aprovado"
                            st.session_state.banco_solicitacoes[indice]["numero_oficio"] = oficio_gerado
                            st.rerun()
                            
                    with col2:
                        with st.expander("❌ Solicitar Correção"):
                            feedback = st.text_area("Descreva os erros para o usuário corrigir:", key=f"fb_{item['id']}")
                            if st.button("Devolver Ofício"):
                                if not feedback:
                                    st.warning("Preencha o motivo antes de devolver.")
                                else:
                                    st.session_state.banco_solicitacoes[indice]["status"] = "Correção Solicitada"
                                    st.session_state.banco_solicitacoes[indice]["feedback_admin"] = feedback
                                    st.rerun()
                st.markdown("---")
