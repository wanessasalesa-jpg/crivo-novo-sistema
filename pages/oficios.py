import streamlit as st
import random
import time
from datetime import datetime, timedelta

# 1. CONFIGURAÇÃO DA PÁGINA (Modo Amplo para caber tabelas e painéis)
st.set_page_config(page_title="Módulo de Ofícios - CRIVO", page_icon="📄", layout="wide")

# 2. DESIGN CUSTOMIZADO (CSS) PARA DEIXAR A INTERFACE ELEGANTE
st.markdown("""
    <style>
    header {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden;}
    
    /* Títulos e Identidade */
    .titulo-principal { color: #002147; font-family: 'Arial'; font-weight: bold; margin-bottom: 5px; }
    .sub-central { color: #555555; margin-bottom: 25px; }
    
    /* Cartões de Solicitação */
    .cartao-ticket { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 8px; 
        border-left: 6px solid #002147; 
        margin-bottom: 15px; 
        box-shadow: 0px 2px 8px rgba(0,0,0,0.08); 
    }
    
    /* Badges de Status */
    .status-pendente { 
        background-color: #ffc107; 
        color: #212529; 
        padding: 4px 10px; 
        border-radius: 4px; 
        font-weight: bold; 
        font-size: 13px;
    }
    .status-aprovado { 
        background-color: #28a745; 
        color: white; 
        padding: 4px 10px; 
        border-radius: 4px; 
        font-weight: bold; 
        font-size: 13px;
    }
    .status-recusado { 
        background-color: #dc3545; 
        color: white; 
        padding: 4px 10px; 
        border-radius: 4px; 
        font-weight: bold; 
        font-size: 13px;
    }
    
    /* Blocos de Informação Lateral */
    .bloco-info {
        background-color: #f1f3f5;
        padding: 15px;
        border-radius: 8px;
        font-size: 14px;
        line-height: 1.5;
    }
    </style>
""", unsafe_allow_html=True)

# 3. CRIAÇÃO DO BANCO DE DADOS TEMPORÁRIO NA MEMÓRIA DO APP
if "banco_solicitacoes" not in st.session_state:
    st.session_state.banco_solicitacoes = [
        {
            "id": "REQ-8412",
            "data_solicitacao": (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y %H:%M"),
            "prazo_limite": (datetime.now() + timedelta(days=2)).strftime("%d/%m/%Y"),
            "perfil": "Professor",
            "assunto": "Solicitação de Visita Técnica ao Hospital Regional de Marabá",
            "destinatario": "Diretoria de Ensino Clínico",
            "status": "Pendente",
            "numero_oficio": "-"
        }
    ]

if "contador_oficio_oficial" not in st.session_state:
    st.session_state.contador_oficio_oficial = 0

# Cabeçalho Principal
st.markdown("<h1 class='titulo-principal'>📄 Central Unificada de Ofícios</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-central'>Gerenciamento de fluxos, análise de conformidade e emissão de numeração sequencial institucional.</p>", unsafe_allow_html=True)

# 4. ORGANIZAÇÃO DAS TELAS EM ABAS (Interface Limpa e Intuitiva)
aba_solicitante, aba_administrativo = st.tabs(["📥 INTERFACE DO SOLICITANTE", "⚙️ PAINEL ADMINISTRATIVO (SECRETARIA)"])

# ==========================================
# ABA 1: TELA DE QUEM VAI SOLICITAR
# ==========================================
with aba_solicitante:
    st.markdown("### Nova Solicitação de Ofício")
    
    col_form, col_ajuda = st.columns([2, 1])
    
    with col_ajuda:
        st.markdown("""
        <div class='bloco-info'>
            <strong>📋 Diretrizes de Emissão:</strong><br>
            1. Baixe o documento modelo oficial abaixo.<br>
            2. Realize o preenchimento dos campos demarcados.<br>
            3. Insira as informações textuais ao lado.<br>
            4. Faça o upload do arquivo para validação da secretaria.
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        
        # Download do arquivo Word
        try:
            with open("Modelo de ofício - Afya (oficial).docx", "rb") as file:
                st.download_button(
                    label="📄 Baixar Modelo Oficial (.DOCX)",
                    data=file,
                    file_name="Modelo de ofício - Afya (oficial).docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
        except FileNotFoundError:
            st.warning("⚠️ Arquivo base 'Modelo de ofício - Afya (oficial).docx' pendente de upload na raiz do repositório.")

    with col_form:
        perfil_simulado = st.radio(
            "Selecione sua categoria atual para teste:",
            ["Aluno", "Professor", "Administrativo"],
            horizontal=True,
            key="perfil_teste"
        )
        
        with st.form("solicitar_oficio_form"):
            assunto_input = st.text_input("Objetivo / Assunto Principal do Documento:")
            destinatario_input = st.text_input("Nome da Pessoa ou Órgão de Destino:")
            
            if perfil_simulado == "Administrativo":
                st.info("💡 Autenticação: Conta administrativa ativa. O upload de arquivo de revisão é opcional.")
                arquivo = st.file_uploader("Carregar arquivo preenchido (Opcional):", type=["docx", "pdf"])
                trava_arquivo = False
            else:
                st.warning("⚠️ Atenção: Para prosseguir é obrigatório anexar o modelo preenchido.")
                arquivo = st.file_uploader("Carregar modelo estruturado preenchido (Obrigatório):", type=["docx", "pdf"])
                trava_arquivo = True
                
            enviar_requisicao = st.form_submit_button("🚀 Protocolar Pedido")
            
        if enviar_requisicao:
            if not assunto_input or not destinatario_input:
                st.error("❌ Preenchimento obrigatório dos campos de Assunto e Destinatário.")
            elif trava_arquivo and arquivo is None:
                st.error("❌ Operação Recusada: O anexo do modelo preenchido é obrigatório para o seu perfil.")
            else:
                id_gerado = f"REQ-{random.randint(1000, 9999)}"
                hoje = datetime.now()
                vencimento_sla = hoje + timedelta(days=3)
                
                novo_registro = {
                    "id": id_gerado,
                    "data_solicitacao": hoje.strftime("%d/%m/%Y %H:%M"),
                    "prazo_limite": vencimento_sla.strftime("%d/%m/%Y"),
                    "perfil": perfil_simulado,
                    "assunto": assunto_input,
                    "destinatario": destinatario_input,
                    "status": "Pendente",
                    "numero_oficio": "-"
                }
                
                # Salva na memória global do sistema
                st.session_state.banco_solicitacoes.append(novo_registro)
                st.success(f"✅ Pedido catalogado com sucesso sob o protocolo: {id_gerado}")
                st.info(f"⏳ Cronograma: Análise técnica programada até no máximo {vencimento_sla.strftime('%d/%m/%Y')}.")

# ==========================================
# ABA 2: TELA DA ADMINISTRADORA (A FILA DE GESTÃO)
# ==========================================
with aba_administrativo:
    st.markdown("### Fila de Triagem e Liberação Docente/Discente")
    st.write("Central de controle exclusiva para recebimento, conferência de prazos (SLA) e carimbo de numeração oficial sequencial.")
    
    fila_dados = st.session_state.banco_solicitacoes
    
    if not fila_dados:
        st.info("Varredura concluída: Nenhuma requisição aguardando processamento na fila.")
    else:
        # Percorre a lista de trás para frente para mostrar o mais novo no topo
        for posicao, item in enumerate(reversed(fila_dados)):
            # Cálculo do índice real na lista original
            indice_real = len(fila_dados) - 1 - posicao
            
            # Define o estilo visual da tag de status
            if item["status"] == "Pendente":
                tag_html = f"<span class='status-pendente'>{item['status']}</span>"
            elif item["status"] == "Aprovado":
                tag_html = f"<span class='status-aprovado'>{item['status']}</span>"
            else:
                tag_html = f"<span class='status-recusado'>{item['status']}</span>"
                
            # Montagem estruturada do cartão visual do pedido
            st.markdown(f"""
            <div class='cartao-ticket'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>{tag_html} &nbsp;&nbsp; <strong>Código: {item['id']}</strong></div>
                    <div style='font-size: 13px; color: #666666;'>Entrada em: {item['data_solicitacao']}</div>
                </div>
                <hr style='margin: 10px 0; border: 0; border-top: 1px solid #e9ecef;'>
                <strong>Requerente:</strong> {item['perfil']}<br>
                <strong>Destinatário Final:</strong> {item['destinatario']}<br>
                <strong>Teor do Objeto:</strong> {item['assunto']}<br>
                <div style='margin-top: 10px; font-size: 14px;'>
                    ⏱️ <strong>Prazo limite para resposta:</strong> <span style='color: #dc3545; font-weight: bold;'>{item['prazo_limite']}</span> 
                    &nbsp;&nbsp;|&nbsp;&nbsp; 
                    🆔 <strong>Número de Ofício Gerado:</strong> <span style='color: #002147; font-weight: bold; font-size: 15px;'>{item['numero_oficio']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Painel de ações (Apenas disponível se o status for Pendente)
            if item["status"] == "Pendente":
                col_btn_aprova, col_btn_rejeita, _ = st.columns([1.2, 1.2, 5])
                
                with col_btn_aprova:
                    if st.button("✅ Validar e Emitir Número", key=f"btn_aprov_{item['id']}_{indice_real}"):
                        # Executa a numeração incremental e ininterrupta oficial
                        st.session_state.contador_oficio_oficial += 1
                        ano_vigente = datetime.now().year
                        oficio_formatado = f"Ofício nº {st.session_state.contador_oficio_oficial:03d}/{ano_vigente} AFYAMARABÁ/AFYA/COORD. DE CURSO"
                        
                        # Altera os dados no banco de dados temporário
                        st.session_state.banco_solicitacoes[indice_real]["status"] = "Aprovado"
                        st.session_state.banco_solicitacoes[indice_real]["numero_oficio"] = oficio_formatado
                        
                        st.success(f"Emitido com sucesso: {oficio_formatado}")
                        time.sleep(1)
                        st.rerun()
                        
                with col_btn_rejeita:
                    if st.button("❌ Indeferir / Corrigir", key=f"btn_rejeit_{item['id']}_{indice_real}"):
                        st.session_state.banco_solicitacoes[indice_real]["status"] = "Recusado"
                        st.warning("Status alterado para Recusado. Usuário notificado para correção.")
                        time.sleep(1)
                        st.rerun()
            
            st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
