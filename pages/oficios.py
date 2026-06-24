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
    .bloco-alerta { background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; border-left: 5px solid #ffeeba; margin-top: 10px; margin-bottom: 15px;}
    </style>
""", unsafe_allow_html=True)

# 3. BANCO DE DADOS TEMPORÁRIO E CONTROLE DE SESSÃO
if "banco_solicitacoes" not in st.session_state:
    st.session_state.banco_solicitacoes = []
if "contador_oficio_oficial" not in st.session_state:
    st.session_state.contador_oficio_oficial = 0
if "gestor_logado" not in st.session_state:
    st.session_state.gestor_logado = False

# CABEÇALHO PÚBLICO
st.markdown("<h2 class='titulo-principal'>📄 Central de Ofícios Institucionais</h2>", unsafe_allow_html=True)
st.write("Sistema automatizado de requisição e emissão de numeração sequencial.")
st.markdown("---")

# 4. SISTEMA DE ABAS
aba_solicitar, aba_acompanhar, aba_gestao = st.tabs(["📤 Nova Solicitação", "🔍 Acompanhar Pedido", "⚙️ Área da Gestão (Restrito)"])

# ==========================================
# ABA 1: SOLICITAÇÃO (Aberta a todos)
# ==========================================
with aba_solicitar:
    col_form, col_ajuda = st.columns([2, 1])
    
    with col_ajuda:
        st.info("Baixe o modelo oficial, preencha seus dados e anexe ao lado para avaliação. O prazo de devolutiva é de 3 dias.")
        try:
            with open("Modelo de ofício - Afya (oficial).docx", "rb") as file:
                st.download_button(label="📄 Baixar Modelo Oficial (.DOCX)", data=file, file_name="Modelo de ofício - Afya (oficial).docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        except FileNotFoundError:
            st.warning("⚠️ Arquivo modelo não encontrado no servidor.")

    with col_form:
        perfil_solicitante = st.radio("Eu sou:", ["Aluno", "Professor", "Administrativo"], horizontal=True)
        
        with st.form("form_pedido"):
            assunto = st.text_input("Objetivo / Assunto do Documento:")
            destinatario = st.text_input("Destinatário Final:")
            
            if perfil_solicitante == "Administrativo":
                st.info("💡 Como você é da equipe administrativa, o envio de anexo para revisão é opcional.")
                arquivo_upload = st.file_uploader("Anexar ofício (Opcional):", type=["docx", "pdf"])
                obrigatorio = False
            else:
                st.warning("⚠️ Atenção: Para Alunos e Professores, o anexo do modelo preenchido é obrigatório.")
                arquivo_upload = st.file_uploader("Anexar seu ofício preenchido (Obrigatório):", type=["docx", "pdf"])
                obrigatorio = True
            
            enviar = st.form_submit_button("Protocolar Pedido")
            
        if enviar:
            if not assunto or not destinatario:
                st.error("Preencha o assunto e o destinatário.")
            elif obrigatorio and arquivo_upload is None:
                st.error("❌ Operação Recusada: O anexo é obrigatório para o seu perfil.")
            else:
                id_gerado = f"REQ-{random.randint(1000, 9999)}"
                vencimento = datetime.now() + timedelta(days=3)
                
                arquivo_bytes = arquivo_upload.getvalue() if arquivo_upload else None
                arquivo_nome = arquivo_upload.name if arquivo_upload else "Sem anexo"
                
                st.session_state.banco_solicitacoes.append({
                    "id": id_gerado,
                    "data_solicitacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "prazo_limite": vencimento.strftime("%d/%m/%Y"),
                    "perfil": perfil_solicitante,
                    "assunto": assunto,
                    "destinatario": destinatario,
                    "status": "Pendente",
                    "numero_oficio": "-",
                    "nome_arquivo": arquivo_nome,
                    "bytes_arquivo": arquivo_bytes,
                    "feedback_admin": "",
                    "reenviado": False # Etiqueta inicial de controle
                })
                st.success(f"✅ Pedido enviado com sucesso! Seu protocolo é: **{id_gerado}**")

# ==========================================
# ABA 2: ACOMPANHAMENTO E REENVIO CORRIGIDO
# ==========================================
with aba_acompanhar:
    st.markdown("### Consultar andamento do Ofício")
    codigo_busca = st.text_input("Digite o número do seu Protocolo (Ex: REQ-1234):")
    
    if st.button("Buscar Protocolo"):
        encontrado = next((item for item in st.session_state.banco_solicitacoes if item["id"] == codigo_busca), None)
        
        if encontrado:
            st.markdown(f"**Status atual:** {encontrado['status']}")
            st.markdown(f"**Número Oficial Emitido:** {encontrado['numero_oficio']}")
            st.markdown(f"**Prazo Limite para Análise:** {encontrado['prazo_limite']}")
            
            # CONFIRMAÇÃO FIXA DE REENVIO (Aparece mesmo após o reboot da tela)
            if encontrado.get("reenviado") and encontrado['status'] == "Pendente":
                st.success("✅ Nova versão enviada com sucesso! O documento retornou para a fila de análise da secretaria.")
            
            # --- SE ESTIVER EM EXIGÊNCIA ---
            if encontrado['status'] == "Correção Solicitada" and encontrado['feedback_admin']:
                st.markdown(f"""
                <div class='bloco-alerta'>
                    <strong>⚠️ A Secretaria solicitou ajustes no seu documento:</strong><br>
                    {encontrado['feedback_admin']}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("#### 🔄 Enviar Nova Versão")
                st.write("Faça as correções apontadas no seu arquivo e envie a nova versão abaixo para reanálise.")
                novo_arquivo = st.file_uploader("Anexar arquivo corrigido:", type=["docx", "pdf"], key=f"reup_{encontrado['id']}")
                
                if st.button("Reenviar para a Secretaria"):
                    if novo_arquivo is None:
                        st.error("Por favor, anexe o arquivo corrigido antes de clicar em reenviar.")
                    else:
                        indice = st.session_state.banco_solicitacoes.index(encontrado)
                        novo_prazo = datetime.now() + timedelta(days=3)
                        
                        # Atualização dos dados na memória central do sistema
                        st.session_state.banco_solicitacoes[indice]["status"] = "Pendente"
                        st.session_state.banco_solicitacoes[indice]["nome_arquivo"] = novo_arquivo.name
                        st.session_state.banco_solicitacoes[indice]["bytes_arquivo"] = novo_arquivo.getvalue()
                        st.session_state.banco_solicitacoes[indice]["feedback_admin"] = ""
                        st.session_state.banco_solicitacoes[indice]["prazo_limite"] = novo_prazo.strftime("%d/%m/%Y")
                        st.session_state.banco_solicitacoes[indice]["reenviado"] = True # Ativa o aviso fixo
                        
                        st.rerun()
        else:
            st.error("Protocolo não encontrado. Verifique se digitou corretamente.")

# ==========================================
# ABA 3: ÁREA DA GESTÃO (Protegida por Login)
# ==========================================
with aba_gestao:
    if not st.session_state.gestor_logado:
        st.markdown("### Acesso Restrito - Equipe Administrativa")
        
        col_login, col_vazia = st.columns([1, 1])
        with col_login:
            with st.form("login_gestao"):
                email = st.text_input("E-mail Institucional (@afya.com.br)")
                senha = st.text_input("Senha de Acesso", type="password")
                btn_login = st.form_submit_button("Acessar Painel")
                
                if btn_login:
                    if email == "gestao@afya.com.br" and senha == "afya2026":
                        st.session_state.gestor_logado = True
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")
    else:
        col_tit, col_sair = st.columns([4, 1])
        with col_tit:
            st.markdown("### ⚙️ Painel de Aprovação e Numeração")
        with col_sair:
            if st.button("Sair (Logout)"):
                st.session_state.gestor_logado = False
                st.rerun()
                
        filtro = st.radio("Filtrar visualização:", ["Apenas Pendentes", "Todos os Protocolos"], horizontal=True)
        
        lista_exibicao = st.session_state.banco_solicitacoes
        if filtro == "Apenas Pendentes":
            lista_exibicao = [item for item in lista_exibicao if item["status"] == "Pendente"]
            
        if not lista_exibicao:
            st.info("Nenhuma requisição aguardando análise no momento.")
        else:
            for item in reversed(lista_exibicao):
                indice = st.session_state.banco_solicitacoes.index(item)
                
                st.markdown(f"""
                <div class='cartao-ticket'>
                    <strong>Protocolo: {item['id']}</strong> | Requerente: {item['perfil']}<br>
                    <strong>Assunto:</strong> {item['assunto']}<br>
                    <strong>Status:</strong> {item['status']} | <strong>Ofício Gerado:</strong> <span style='color: #002147; font-weight: bold;'>{item['numero_oficio']}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # CHAVE DINÂMICA (Garante a quebra de cache ao reajustar o arquivo)
                if item.get("bytes_arquivo"):
                    st.download_button(
                        label=f"📥 Baixar Documento Enviado ({item['nome_arquivo']})", 
                        data=item["bytes_arquivo"], 
                        file_name=item["nome_arquivo"], 
                        key=f"dl_{item['id']}_{item['nome_arquivo']}"
                    )
                
                if item["status"] == "Pendente":
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Aprovar e Gerar Número Oficial", key=f"aprova_{item['id']}"):
                            st.session_state.contador_oficio_oficial += 1
                            oficio_gerado = f"Ofício nº {st.session_state.contador_oficio_oficial:03d}/{datetime.now().year} AFYAMARABÁ/AFYA/COORD. DE CURSO"
                            st.session_state.banco_solicitacoes[indice]["status"] = "Aprovado"
                            st.session_state.banco_solicitacoes[indice]["numero_oficio"] = oficio_gerado
                            st.session_state.banco_solicitacoes[indice]["reenviado"] = False
                            st.rerun()
                            
                    with col2:
                        with st.expander("❌ Solicitar Correção ao Usuário"):
                            feedback = st.text_area("Aponte os erros para correção:", key=f"fb_{item['id']}")
                            if st.button("Devolver Documento", key=f"dev_{item['id']}"):
                                if not feedback:
                                    st.warning("Escreva o motivo antes de devolver.")
                                else:
                                    st.session_state.banco_solicitacoes[indice]["status"] = "Correção Solicitada"
                                    st.session_state.banco_solicitacoes[indice]["feedback_admin"] = feedback
                                    st.session_state.banco_solicitacoes[indice]["reenviado"] = False
                                    st.rerun()
                st.markdown("---")
