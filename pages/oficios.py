import streamlit as st
import random
import io
import pandas as pd
from datetime import datetime, timedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Módulo de Ofícios - CRIVO", page_icon="📄", layout="wide")

# 2. DESIGN CUSTOMIZADO (CSS)
st.markdown("""
    <style>
    .titulo-principal { color: #002147; font-family: 'Arial'; font-weight: bold; margin-bottom: 5px; }
    .cartao-ticket { background-color: #ffffff; padding: 20px; border-radius: 8px; border-left: 6px solid #002147; margin-bottom: 15px; box-shadow: 0px 2px 8px rgba(0,0,0,0.08); }
    
    /* Cores de Status */
    .status-pendente { background-color: #ffc107; color: #212529; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .status-aprovado { background-color: #28a745; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .status-recusado { background-color: #dc3545; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    
    /* Cores de Perfil */
    .perfil-aluno { background-color: #17a2b8; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .perfil-professor { background-color: #6f42c1; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .perfil-admin { background-color: #343a40; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    
    .bloco-alerta { background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; border-left: 5px solid #ffeeba; margin-top: 10px; margin-bottom: 15px;}
    </style>
""", unsafe_allow_html=True)

# 3. SIMULADOR DE MOTOR DE E-MAILS
def enviar_email_notificacao(destinatario, assunto, mensagem_html):
    print(f"[LOG SISTEMA] E-mail simulado para {destinatario} | Assunto: {assunto}")
    return True

# 4. BANCO DE DADOS TEMPORÁRIO E CONTROLE DE SESSÃO
if "banco_solicitacoes" not in st.session_state:
    st.session_state.banco_solicitacoes = []
if "contador_oficio_oficial" not in st.session_state:
    st.session_state.contador_oficio_oficial = 0
if "gestor_logado" not in st.session_state:
    st.session_state.gestor_logado = False
if "protocolo_buscado" not in st.session_state:
    st.session_state.protocolo_buscado = ""

# CABEÇALHO PÚBLICO
st.markdown("<h2 class='titulo-principal'>📄 Central de Ofícios Institucionais</h2>", unsafe_allow_html=True)
st.write("Sistema automatizado de requisição e emissão de numeração sequencial.")
st.markdown("---")

# 5. SISTEMA DE ABAS (Nome fixo para evitar que a tela pule!)
aba_solicitar, aba_acompanhar, aba_gestao = st.tabs(["📤 Nova Solicitação", "🔍 Acompanhar Pedido", "⚙️ Área da Gestão (Restrito)"])

# ==========================================
# ABA 1: SOLICITAÇÃO
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
        
        with st.form("form_pedido", clear_on_submit=True):
            nome_solicitante = st.text_input("Nome Completo do Solicitante:")
            email_solicitante = st.text_input("E-mail para contato:")
            
            if perfil_solicitante in ["Professor", "Administrativo"]:
                setor_solicitante = st.text_input("Setor Solicitante (Ex: Coordenação de Medicina, Diretoria):")
            else:
                setor_solicitante = "Não se aplica (Aluno)"
                
            st.markdown("---")
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
            if not nome_solicitante or not email_solicitante or not assunto or not destinatario:
                st.error("❌ Por favor, preencha todos os campos de texto obrigatórios (Nome, E-mail, Assunto e Destinatário).")
            elif perfil_solicitante in ["Professor", "Administrativo"] and not setor_solicitante:
                st.error("❌ Por favor, preencha o campo 'Setor Solicitante'.")
            elif perfil_solicitante in ["Professor", "Administrativo"] and not email_solicitante.lower().endswith("@afya.com.br"):
                st.error("❌ Acesso Bloqueado: Para perfis de Professor ou Administrativo, é obrigatório o uso do e-mail institucional (@afya.com.br).")
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
                    "data_emissao": "-", # Nova coluna criada e vazia inicialmente
                    "prazo_limite": vencimento.strftime("%d/%m/%Y"),
                    "perfil": perfil_solicitante,
                    "nome": nome_solicitante,
                    "email": email_solicitante,
                    "setor": setor_solicitante,
                    "assunto": assunto,
                    "destinatario": destinatario,
                    "status": "Pendente",
                    "numero_oficio": "-",
                    "nome_arquivo": arquivo_nome,
                    "bytes_arquivo": arquivo_bytes,
                    "feedback_admin": "",
                    "reenviado": False
                })
                
                enviar_email_notificacao(email_solicitante, f"Protocolo Recebido: {id_gerado}", f"Protocolo {id_gerado}")
                st.success(f"✅ Pedido enviado com sucesso! Seu protocolo é: **{id_gerado}**")

# ==========================================
# ABA 2: ACOMPANHAMENTO E REENVIO
# ==========================================
with aba_acompanhar:
    st.markdown("### Consultar andamento do Ofício")
    
    with st.form("form_busca", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            codigo_busca = st.text_input("Digite o número do seu Protocolo (Ex: REQ-1234):")
        with col2:
            st.write("")
            st.write("")
            submit_busca = st.form_submit_button("Buscar Protocolo")
            
        if submit_busca:
            st.session_state.protocolo_buscado = codigo_busca
            
    if st.session_state.protocolo_buscado:
        encontrado = next((item for item in st.session_state.banco_solicitacoes if item["id"] == st.session_state.protocolo_buscado), None)
        
        if encontrado:
            st.markdown("---")
            st.markdown(f"**Status atual:** {encontrado['status']}")
            st.markdown(f"**Número Oficial Emitido:** {encontrado['numero_oficio']}")
            st.markdown(f"**Prazo Limite para Análise:** {encontrado['prazo_limite']}")
            if encontrado['data_emissao'] != "-":
                st.markdown(f"**Data de Emissão (Aprovação):** {encontrado['data_emissao']}")
            
            if encontrado.get("reenviado") and encontrado['status'] == "Pendente":
                st.success("✅ Nova versão enviada com sucesso! O documento retornou para a fila de análise da secretaria.")
            
            if encontrado['status'] == "Correção Solicitada" and encontrado['feedback_admin']:
                st.markdown(f"""
                <div class='bloco-alerta'>
                    <strong>⚠️ A Secretaria solicitou ajustes no seu documento:</strong><br>
                    {encontrado['feedback_admin']}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("#### 🔄 Enviar Nova Versão")
                with st.form(key=f"form_reenvio_{encontrado['id']}", clear_on_submit=True):
                    novo_arquivo = st.file_uploader("Anexar arquivo corrigido:", type=["docx", "pdf"])
                    btn_reenviar = st.form_submit_button("Reenviar para a Secretaria")
                    
                    if btn_reenviar:
                        if novo_arquivo is None:
                            st.error("Por favor, anexe o arquivo corrigido antes de clicar em reenviar.")
                        else:
                            indice = st.session_state.banco_solicitacoes.index(encontrado)
                            novo_prazo = datetime.now() + timedelta(days=3)
                            
                            st.session_state.banco_solicitacoes[indice]["status"] = "Pendente"
                            st.session_state.banco_solicitacoes[indice]["nome_arquivo"] = novo_arquivo.name
                            st.session_state.banco_solicitacoes[indice]["bytes_arquivo"] = novo_arquivo.getvalue()
                            st.session_state.banco_solicitacoes[indice]["feedback_admin"] = ""
                            st.session_state.banco_solicitacoes[indice]["prazo_limite"] = novo_prazo.strftime("%d/%m/%Y")
                            st.session_state.banco_solicitacoes[indice]["reenviado"] = True
                            st.rerun() 
        else:
            st.error(f"Protocolo '{st.session_state.protocolo_buscado}' não encontrado. Verifique se digitou corretamente.")

# ==========================================
# ABA 3: ÁREA DA GESTÃO (COM EXCEL INTELIGENTE)
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
        # AQUI FICA O AVISO DE PENDÊNCIAS (Protegido e invisível para os alunos)
        qtd_pendentes = sum(1 for item in st.session_state.banco_solicitacoes if item["status"] == "Pendente")
        
        col_tit, col_sair = st.columns([4, 1])
        with col_tit:
            st.markdown(f"### ⚙️ Painel de Aprovação ({qtd_pendentes} pendentes)")
        with col_sair:
            if st.button("Sair (Logout)"):
                st.session_state.gestor_logado = False
                st.rerun()
        
        with st.expander("📊 Relatórios e Prestação de Contas (Exportar para Excel)"):
            st.write("Baixe a planilha estruturada com o histórico de todos os ofícios, tempos de resposta e emissões.")
            if not st.session_state.banco_solicitacoes:
                st.info("Ainda não há dados suficientes para gerar um relatório.")
            else:
                # Criando o DataFrame
                df = pd.DataFrame(st.session_state.banco_solicitacoes)
                df_export = df[['id', 'data_solicitacao', 'data_emissao', 'perfil', 'nome', 'setor', 'assunto', 'destinatario', 'status', 'numero_oficio']]
                df_export.columns = ['Protocolo', 'Data Entrada', 'Data Emissão', 'Perfil', 'Nome Solicitante', 'Setor', 'Assunto', 'Destinatário', 'Status Atual', 'Nº Oficial Gerado']
                
                # GERADOR DE ARQUIVO .XLSX (Excel nativo com autoajuste de colunas)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_export.to_excel(writer, index=False, sheet_name='Ofícios Afya')
                    worksheet = writer.sheets['Ofícios Afya']
                    
                    # Lógica matemática para ler o tamanho do texto e abrir a coluna perfeitamente
                    for idx, col in enumerate(df_export.columns):
                        series = df_export[col]
                        max_len = max(series.astype(str).map(len).max(), len(str(col))) + 2
                        col_letter = chr(65 + idx) # Converte 0 para A, 1 para B, etc.
                        worksheet.column_dimensions[col_letter].width = max_len
                
                st.download_button(
                    label="📥 Baixar Relatório Completo (.xlsx)",
                    data=buffer.getvalue(),
                    file_name=f"Relatorio_Oficios_Afya_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        st.markdown("---")
        
        if qtd_pendentes > 0:
            st.warning(f"🚨 **Atenção:** Você tem **{qtd_pendentes} ofício(s)** pendente(s) aguardando sua análise e liberação.")
        else:
            st.success("🎉 **Excelente!** Não há ofícios pendentes na sua fila de análise no momento.")
                
        filtro = st.radio("Filtrar visualização:", ["Apenas Pendentes", "Todos os Protocolos"], horizontal=True)
        
        lista_exibicao = st.session_state.banco_solicitacoes
        if filtro == "Apenas Pendentes":
            lista_exibicao = [item for item in lista_exibicao if item["status"] == "Pendente"]
            
        if not lista_exibicao and filtro == "Apenas Pendentes":
            st.info("Nenhuma requisição aguardando análise no momento.")
        else:
            for item in reversed(lista_exibicao):
                indice = st.session_state.banco_solicitacoes.index(item)
                
                if item['perfil'] == "Aluno":
                    badge = "<span class='perfil-aluno'>🧑‍🎓 Aluno</span>"
                elif item['perfil'] == "Professor":
                    badge = "<span class='perfil-professor'>👨‍🏫 Professor</span>"
                else:
                    badge = "<span class='perfil-admin'>⚙️ Administrativo</span>"
                
                st.markdown(f"""
                <div class='cartao-ticket'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div><strong>Protocolo: {item['id']}</strong></div>
                        <div style='font-size: 13px; color: #666;'>Requerente: {badge}</div>
                    </div>
                    <hr style='margin: 10px 0; border: 0; border-top: 1px solid #e9ecef;'>
                    <strong>Nome:</strong> {item['nome']} ({item['email']})<br>
                    <strong>Setor:</strong> {item.get('setor', 'Não informado')}<br>
                    <strong>Assunto:</strong> {item['assunto']}<br>
                    <strong>Destinatário Final:</strong> {item['destinatario']}<br>
                    <div style='margin-top: 10px;'>
                        <strong>Status:</strong> {item['status']} | <strong>Ofício Gerado:</strong> <span style='color: #002147; font-weight: bold;'>{item['numero_oficio']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
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
                            
                            oficio_gerado = f"Ofício nº {st.session_state.contador_oficio_oficial:03d}/{datetime.now().year}"
                            
                            st.session_state.banco_solicitacoes[indice]["status"] = "Aprovado"
                            st.session_state.banco_solicitacoes[indice]["numero_oficio"] = oficio_gerado
                            st.session_state.banco_solicitacoes[indice]["reenviado"] = False
                            
                            # CARIMBANDO A DATA E HORA EXATA DA EMISSÃO
                            st.session_state.banco_solicitacoes[indice]["data_emissao"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                            
                            enviar_email_notificacao(item['email'], f"Ofício Aprovado: {item['id']}", "Aprovação simulada")
                            st.rerun() # Como o nome da aba agora é fixo, a tela não vai pular!
                            
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
                                    
                                    enviar_email_notificacao(item['email'], f"Correção Solicitada: {item['id']}", "Recusa simulada")
                                    st.rerun()
                                    
                elif item["status"] == "Correção Solicitada":
                    st.info("⏳ Aguardando o usuário realizar as correções e enviar a nova versão do documento.")
                
                st.markdown("---")
