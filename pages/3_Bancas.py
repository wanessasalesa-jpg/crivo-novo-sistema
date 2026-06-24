import streamlit as st
import uuid
import pandas as pd
import io
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Portal de Bancas - CRIVO", page_icon="🎓", layout="wide")

# 2. DESIGN CUSTOMIZADO (CSS) E CORES DOS MÓDULOS
st.markdown("""
    <style>
    .titulo-principal { color: #800040; font-family: 'Arial'; font-weight: bold; margin-bottom: 5px; }
    .cartao-banca { background-color: #ffffff; padding: 20px; border-radius: 8px; border-left: 6px solid #800040; margin-bottom: 15px; box-shadow: 0px 2px 8px rgba(0,0,0,0.08); }
    
    /* Paleta de Cores dos Módulos */
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
    """Converte 'primeiro.ultimo@afya.com.br' para 'Primeiro Ultimo'"""
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

# 4. BANCO DE DADOS TEMPORÁRIO (SESSÃO) E CONTROLE DE ACESSO
if "bancos_avaliacoes" not in st.session_state:
    st.session_state.bancos_avaliacoes = [] 

if "permissoes_acesso" not in st.session_state:
    # A Administradora Master já nasce configurada no sistema
    st.session_state.permissoes_acesso = {
        "wanessa.almeida@afya.com.br": "Administrador"
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
            email = st.text_input("E-mail Institucional (@afya.com.br)").lower().strip()
            senha = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if submit:
                if not email.endswith("@afya.com.br"):
                    st.error("Acesso restrito a e-mails institucionais da Afya.")
                elif senha != "afya2026": 
                    st.error("Senha incorreta.")
                elif email not in st.session_state.permissoes_acesso:
                    st.error("O seu e-mail não possui permissão de acesso cadastrada. Procure a administração.")
                else:
                    perfil_atribuido = st.session_state.permissoes_acesso[email]
                    nome_formatado = formatar_nome_email(email)
                    st.session_state.usuario_bancas = {"perfil": perfil_atribuido, "email": email, "nome": nome_formatado}
                    forçar_recarregamento_tela()

# ==========================================
# PAINEL 0: ADMINISTRAÇÃO (Master)
# ==========================================
def tela_administracao():
    col_titulo, col_logout = st.columns([4, 1])
    with col_titulo:
        st.markdown(f"### 👑 Painel de Administração Master | Olá, {st.session_state.usuario_bancas['nome']}")
    with col_logout:
        if st.button("Sair (Logout)"):
            st.session_state.usuario_bancas = None
            forçar_recarregamento_tela()
            
    st.info("Nesta área, você delega quais professores terão acesso ao perfil de Coordenação do módulo.")
    
    with st.form("form_add_coord", clear_on_submit=True):
        novo_email_coord = st.text_input("Adicionar E-mail do Coordenador (@afya.com.br):").lower().strip()
        if st.form_submit_button("Conceder Acesso de Coordenação"):
            if novo_email_coord and novo_email_coord.endswith("@afya.com.br"):
                st.session_state.permissoes_acesso[novo_email_coord] = "Coordenação"
                st.toast(f"✅ Acesso concedido para {novo_email_coord}!")
                forçar_recarregamento_tela()
            else:
                st.error("Insira um e-mail válido da Afya.")
                
    st.markdown("#### Coordenadores Cadastrados")
    for email, perfil in st.session_state.permissoes_acesso.items():
        if perfil == "Coordenação":
            st.write(f"- 👤 {formatar_nome_email(email)} ({email})")

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
    
    # --- ABA DE CRIAÇÃO ---
    with aba_criar:
        st.info("O módulo selecionado define automaticamente as regras da banca e da emissão de documentos.")
        
        # Seletor FORA do form para atualizar a tela em tempo real
        modulo_selecionado = st.selectbox("Selecione o Módulo da Avaliação:", ["TCC I", "TCC II", "MCM IV", "MCM V", "PIEPE"])
        
        formato_piepe = None
        if modulo_selecionado == "PIEPE":
            st.warning("⚠️ PIEPE: Defina o formato da apresentação. O avaliador verá apenas a rubrica correspondente.")
            formato_piepe = st.radio("Formato de Avaliação:", ["Slide", "Banner"], horizontal=True)

        with st.form("form_nova_banca", clear_on_submit=True):
            data_banca = st.date_input("Data da Defesa:", format="DD/MM/YYYY")
            titulo = st.text_input("Título do Projeto/Trabalho:")
            
            st.markdown("---")
            st.write("**Orientação**")
            col_o1, col_o2 = st.columns(2)
            with col_o1:
                orientador_email = st.text_input("E-mail do Orientador (@afya.com.br):").lower().strip()
                
            st.markdown("---")
            st.write("**Composição da Banca Avaliadora**")
            
            # Lógica Condicional de Avaliadores
            if modulo_selecionado in ["TCC I", "MCM IV"]:
                st.write("*Regra do Módulo: Dois avaliadores obrigatórios. Sem suplente.*")
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    avaliador_1_email = st.text_input("E-mail Avaliador 1 (@afya.com.br):").lower().strip()
                with col_b2:
                    avaliador_2_email = st.text_input("E-mail Avaliador 2 (@afya.com.br):").lower().strip()
                avaliador_sup_email = ""
            else:
                st.write("*Regra do Módulo: Um avaliador titular e um suplente.*")
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    avaliador_1_email = st.text_input("E-mail Avaliador Titular (@afya.com.br):").lower().strip()
                with col_b2:
                    avaliador_sup_email = st.text_input("E-mail Avaliador Suplente (@afya.com.br):").lower().strip()
                avaliador_2_email = ""
                
            st.markdown("---")
            st.write("**Integrantes do Grupo**")
            st.info("Cole a lista de nomes (um por linha). O sistema ignora linhas vazias.")
            lista_alunos = st.text_area("Nomes dos Alunos:", height=150)
            
            btn_salvar = st.form_submit_button("Salvar e Gerar Banca")
            
            if btn_salvar:
                if not titulo or not orientador_email or not avaliador_1_email or not lista_alunos:
                    st.error("Preencha todos os campos obrigatórios e e-mails.")
                else:
                    alunos_processados = [nome.strip() for nome in lista_alunos.split('\n') if nome.strip()]
                    nova_banca = {
                        "id": str(uuid.uuid4())[:8],
                        "modulo": modulo_selecionado,
                        "formato_piepe": formato_piepe,
                        "data": data_banca.strftime("%d/%m/%Y"),
                        "titulo": titulo,
                        "orientador_email": orientador_email,
                        "orientador_nome": formatar_nome_email(orientador_email),
                        "avaliador_1_email": avaliador_1_email,
                        "avaliador_1_nome": formatar_nome_email(avaliador_1_email),
                        "avaliador_2_email": avaliador_2_email,
                        "avaliador_2_nome": formatar_nome_email(avaliador_2_email) if avaliador_2_email else "",
                        "avaliador_sup_email": avaliador_sup_email,
                        "avaliador_sup_nome": formatar_nome_email(avaliador_sup_email) if avaliador_sup_email else "",
                        "alunos": alunos_processados,
                        "status": "Aguardando Avaliação",
                        "notas_banca": [],
                        "nota_orientador": None,
                        "nota_final": None
                    }
                    st.session_state.bancos_avaliacoes.append(nova_banca)
                    
                    # Concede acesso automático aos e-mails cadastrados
                    st.session_state.permissoes_acesso[orientador_email] = "Orientador"
                    st.session_state.permissoes_acesso[avaliador_1_email] = "Avaliador"
                    if avaliador_2_email: st.session_state.permissoes_acesso[avaliador_2_email] = "Avaliador"
                    if avaliador_sup_email: st.session_state.permissoes_acesso[avaliador_sup_email] = "Avaliador"
                    
                    # Mensagem que desaparece sozinha
                    st.toast("✅ Banca criada com sucesso e acessos liberados!", icon="🎉")

    # --- ABA DE GERENCIAMENTO ---
    with aba_gerenciar:
        if not st.session_state.bancos_avaliacoes:
            st.info("Nenhuma banca cadastrada.")
        else:
            with st.expander("📊 Relatório Consolidado (Exportar Excel)"):
                df_export = pd.DataFrame(st.session_state.bancos_avaliacoes)
                # Formata a lista de alunos para texto limpo na planilha
                df_export['alunos'] = df_export['alunos'].apply(lambda x: ", ".join(x))
                csv_data = df_export.to_csv(index=False, sep=';').encode('utf-8-sig')
                
                st.download_button(
                    label="📥 Baixar Planilha de Notas e Grupos",
                    data=csv_data,
                    file_name=f"Relatorio_Bancas_Afya_{datetime.now().strftime('%d_%m_%Y')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            st.markdown("---")
            for i, banca in enumerate(reversed(st.session_state.bancos_avaliacoes)):
                indice_real = len(st.session_state.bancos_avaliacoes) - 1 - i
                classe_cor = obter_classe_cor(banca['modulo'])
                info_piepe = f" | Formato: {banca['formato_piepe']}" if banca['modulo'] == "PIEPE" else ""
                
                st.markdown(f"""
                <div class='cartao-banca'>
                    <div style='display: flex; justify-content: space-between;'>
                        <div><span class='{classe_cor}'>{banca['modulo']}</span> <span style='color: #666; font-size: 14px;'>{info_piepe} | {banca['data']}</span></div>
                        <div style='font-size: 13px; color: #800040;'><b>Status:</b> {banca['status']}</div>
                    </div>
                    <h4 style='margin-top: 10px; margin-bottom: 5px;'>{banca['titulo']}</h4>
                    <strong>Orientador:</strong> {banca['orientador_nome']}<br>
                    <strong>Avaliadores:</strong> {banca['avaliador_1_nome']} 
                    {f" | {banca['avaliador_2_nome']}" if banca['avaliador_2_nome'] else ""}
                    {f" | {banca['avaliador_sup_nome']} (Suplente)" if banca['avaliador_sup_nome'] else ""}
                    <hr style='margin: 10px 0;'>
                    <strong>Alunos ({len(banca['alunos'])}):</strong> {', '.join(banca['alunos'])}
                </div>
                """, unsafe_allow_html=True)
                
                # Botão de exclusão seguro
                if st.button("🗑️ Excluir Banca", key=f"del_{banca['id']}"):
                    st.session_state.bancos_avaliacoes.pop(indice_real)
                    st.rerun()

# ==========================================
# PAINEL 2: AVALIADOR 
# ==========================================
def tela_avaliador():
    col_titulo, col_logout = st.columns([4, 1])
    with col_titulo:
        st.markdown(f"### 📱 Painel do Avaliador | Olá, {st.session_state.usuario_bancas['nome']}")
    with col_logout:
        if st.button("Sair (Logout)"):
            st.session_state.usuario_bancas = None
            forçar_recarregamento_tela()
    
    st.info("🚧 Módulo de preenchimento de notas (com caixas de seleção à prova de erros) será construído aqui na próxima etapa!")

# ==========================================
# PAINEL 3: ORIENTADOR 
# ==========================================
def tela_orientador():
    col_titulo, col_logout = st.columns([4, 1])
    with col_titulo:
        st.markdown(f"### 📚 Painel do Orientador | Olá, {st.session_state.usuario_bancas['nome']}")
    with col_logout:
        if st.button("Sair (Logout)"):
            st.session_state.usuario_bancas = None
            forçar_recarregamento_tela()
            
    st.info("🚧 Módulo do Diário de Bordo (Atas Mensais) e Fechamento de Notas será construído aqui!")

# ==========================================
# ROTEADOR DE TELAS (O CÉREBRO DA NAVEGAÇÃO)
# ==========================================
if st.session_state.usuario_bancas is None:
    tela_login()
else:
    perfil_atual = st.session_state.usuario_bancas["perfil"]
    if perfil_atual == "Administrador":
        tela_administracao()
    elif perfil_atual == "Coordenação":
        tela_coordenacao()
    elif perfil_atual == "Avaliador":
        tela_avaliador()
    elif perfil_atual == "Orientador":
        tela_orientador()
