import streamlit as st
import random
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(page_title="Módulo de Ofícios", page_icon="📄", layout="centered")

st.title("📄 Solicitação de Ofícios")
st.markdown("---")

# --- 1. BOTÃO DE DOWNLOAD DO MODELO OFICIAL ---
st.markdown("#### 📥 1. Baixe o Modelo Padrão")
try:
    with open("Modelo de ofício - Afya (oficial).docx", "rb") as file:
        st.download_button(
            label="📄 Baixar Modelo de ofício - Afya (oficial).docx",
            data=file,
            file_name="Modelo de ofício - Afya (oficial).docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
except FileNotFoundError:
    st.warning("⚠️ O arquivo do modelo está sendo carregado no servidor. Aguarde alguns instantes.")

st.markdown("---")
st.markdown("#### 📤 2. Envie sua Solicitação")

# --- 2. SIMULAÇÃO DE PERFIL (Para testar as travas) ---
perfil_usuario = st.radio(
    "Simular login como:",
    ["Administrativo", "Professor", "Aluno"],
    horizontal=True
)

st.markdown("### Preencha os dados da solicitação")

# --- 3. O FORMULÁRIO DE SOLICITAÇÃO ---
with st.form("form_oficio"):
    assunto = st.text_input("Assunto do Ofício (Ex: Solicitação de Visita Técnica)")
    destinatario = st.text_input("Nome do Destinatário / Órgão")
    
    # A Trava Inteligente do Anexo baseada no Perfil
    if perfil_usuario == "Administrativo":
        st.info("💡 Como você é do Administrativo, o envio do modelo preenchido é opcional.")
        arquivo_anexo = st.file_uploader("Anexar modelo de ofício preenchido (Opcional)", type=["docx", "pdf"])
        anexo_obrigatorio = False
    else:
        st.warning("⚠️ O envio do modelo de ofício preenchido é OBRIGATÓRIO para a sua solicitação ser analisada.")
        arquivo_anexo = st.file_uploader("Anexar modelo de ofício preenchido (Obrigatório)", type=["docx", "pdf"])
        anexo_obrigatorio = True

    botao_enviar = st.form_submit_button("Enviar Solicitação")

# --- 4. A LÓGICA DE PROCESSAMENTO E SLA (Prazo) ---
if botao_enviar:
    if not assunto or not destinatario:
        st.error("Por favor, preencha o assunto e o destinatário.")
    elif anexo_obrigatorio and arquivo_anexo is None:
        st.error("Você precisa anexar o documento preenchido para prosseguir!")
    else:
        # Se passou pelas travas, gera o Ticket Temporário (REQ) protegendo a numeração oficial
        numero_ticket = f"REQ-{random.randint(1000, 9999)}"
        data_hoje = datetime.now()
        data_limite = data_hoje + timedelta(days=3) # O SLA de 3 dias
        
        st.success("✅ Solicitação enviada com sucesso!")
        st.markdown(f"**Seu número de acompanhamento é:** `{numero_ticket}`")
        
        # Via Expressa Administrativa x Fila de Análise
        if perfil_usuario == "Administrativo":
            st.success("Como você é do Administrativo, o número oficial já pode ser gerado na próxima tela.")
        else:
            st.info(f"O prazo máximo para a devolutiva do setor responsável é até **{data_limite.strftime('%d/%m/%Y')}**.")
