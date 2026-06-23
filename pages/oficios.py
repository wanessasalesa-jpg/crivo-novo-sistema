import streamlit as st
import random
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(page_title="Módulo de Ofícios", page_icon="📄", layout="centered")

st.title("📄 Solicitação de Ofícios")
st.markdown("---")

# 1. Simulação de Login (Apenas para testarmos a sua lógica de perfis)
perfil_usuario = st.radio(
    "Simular login como:",
    ["Administrativo", "Professor", "Aluno"],
    horizontal=True
)

st.markdown("### Preencha os dados da solicitação")

# 2. O Formulário de Solicitação
with st.form("form_oficio"):
    assunto = st.text_input("Assunto do Ofício (Ex: Solicitação de Visita Técnica)")
    destinatario = st.text_input("Nome do Destinatário / Órgão")
    
    # 3. A Trava Inteligente do Anexo
    if perfil_usuario == "Administrativo":
        st.info("💡 Como você é do Administrativo, o envio do modelo preenchido é opcional.")
        arquivo_anexo = st.file_uploader("Anexar modelo de ofício preenchido (Opcional)", type=["docx", "pdf"])
        anexo_obrigatorio = False
    else:
        st.warning("⚠️ O envio do modelo de ofício preenchido é OBRIGATÓRIO para a sua solicitação ser analisada.")
        arquivo_anexo = st.file_uploader("Anexar modelo de ofício preenchido (Obrigatório)", type=["docx", "pdf"])
        anexo_obrigatorio = True

    botao_enviar = st.form_submit_button("Enviar Solicitação")

# 4. A Lógica de Processamento e SLA
if botao_enviar:
    if not assunto or not destinatario:
        st.error("Por favor, preencha o assunto e o destinatário.")
    elif anexo_obrigatorio and arquivo_anexo is None:
        st.error("Você precisa anexar o documento preenchido para prosseguir!")
    else:
        # Se passou pelas travas, gera o Ticket Temporário (REQ)
        numero_ticket = f"REQ-{random.randint(1000, 9999)}"
        data_hoje = datetime.now()
        data_limite = data_hoje + timedelta(days=3) # O SLA de 3 dias que você pediu!
        
        st.success("✅ Solicitação enviada com sucesso!")
        st.markdown(f"**Seu número de acompanhamento é:** `{numero_ticket}`")
        
        # Via Expressa Administrativa x Fila de Análise
        if perfil_usuario == "Administrativo":
            st.success(f"Como você é do Administrativo, o número oficial já pode ser gerado na próxima tela.")
        else:
            st.info(f"O prazo máximo para a devolutiva do setor responsável é até **{data_limite.strftime('%d/%m/%Y')}**.")
