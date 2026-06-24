import streamlit as st
import uuid
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Portal de Bancas - CRIVO", page_icon="🎓", layout="wide")

# 2. DESIGN CUSTOMIZADO (CSS)
st.markdown("""
    <style>
    .titulo-principal { color: #800040; font-family: 'Arial'; font-weight: bold; margin-bottom: 5px; }
    .cartao-banca { background-color: #ffffff; padding: 20px; border-radius: 8px; border-left: 6px solid #800040; margin-bottom: 15px; box-shadow: 0px 2px 8px rgba(0,0,0,0.08); }
    .badge-modulo { background-color: #002147; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-piepe { background-color: #e67e22; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# 3. FUNÇÃO ANTI-TRAVAMENTO
def forçar_recarregamento_tela():
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

# 4. BANCO DE DADOS TEMPORÁRIO (SESSÃO)
if "bancos_avaliacoes" not in st.session_state:
    st.session_state.bancos_avaliacoes = [] # Guarda todos os grupos criados
if "usuario_bancas" not in st.session_state:
    st.session_state.usuario_bancas = None # Guarda quem está logado

# ==========================================
# MÓDULO DE LOGIN INTELIGENTE
# ==========================================
def tela_login():
    st.markdown("<h2 class='titulo-principal'>🎓 Portal de Bancas e Avaliações</h2>", unsafe_allow_html=True)
    st.write("Selecione o seu perfil para aceder ao sistema.")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_login"):
            perfil = st.selectbox("Eu sou:", ["Selecione...", "Coordenação", "Orientador", "Avaliador"])
            email = st.text_input("E-mail Institucional (@afya.com.br)")
            senha = st.text_input("Senha", type="password")
            
            submit = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if submit:
                if perfil == "Selecione...":
                    st.warning("Por favor, selecione um perfil de acesso.")
                elif not email.endswith("@afya.com.br"):
                    st.error("Acesso restrito a e-mails institucionais da Afya.")
                elif senha != "afya2026": # Senha padrão provisória para testes
                    st.error("Senha incorreta.")
                else:
                    # Login com sucesso
                    st.session_state.usuario_bancas = {"perfil": perfil, "email": email}
                    forçar_recarregamento_tela()

# ==========================================
# PAINEL 1: COORDENAÇÃO (Criador de Grupos)
# ==========================================
def tela_coordenacao():
    col_titulo, col_logout = st.columns([4, 1])
    with col_titulo:
        st.markdown(f"### ⚙️ Painel da Coordenação | Logado como: {st.session_state.usuario_bancas['email']}")
    with col_logout:
        if st.button("Sair (Logout)"):
            st.session_state.usuario_bancas = None
            forçar_recarregamento_tela()
            
    aba_criar, aba_gerenciar = st.tabs(["➕ Criar Novo Grupo/Banca", "📋 Bancas Cadastradas"])
    
    # --- ABA DE CRIAÇÃO ---
    with aba_criar:
        st.info("Preencha os dados abaixo para formar o grupo, designar o orientador e a banca avaliadora.")
        
        with st.form("form_nova_banca", clear_on_submit=True):
            col_mod, col_data = st.columns(2)
            with col_mod:
                modulo = st.selectbox("Módulo da Avaliação:", ["TCC I", "TCC II", "MCM IV", "MCM V", "PIEPE"])
            with col_data:
                data_banca = st.date_input("Data Prevista da Defesa/Apresentação:")
            
            # Trava Mágica do PIEPE (Só aparece se o módulo for PIEPE)
            formato_piepe = None
            if modulo == "PIEPE":
                st.warning("⚠️ Módulo PIEPE selecionado. Defina o formato da avaliação para bloquear a rubrica correta para o professor.")
                formato_piepe = st.radio("Formato da Apresentação do Grupo:", ["Slide", "Banner"], horizontal=True)
            
            st.markdown("---")
            titulo = st.text_input("Título do Projeto/Trabalho:")
            orientador = st.text_input("Nome do Orientador:")
            
            st.markdown("---")
            st.write("**Composição da Banca Avaliadora**")
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                avaliador_1 = st.text_input("Avaliador Titular 1:")
            with col_b2:
                avaliador_2 = st.text_input("Avaliador Titular 2 (Opcional):")
            with col_b3:
                avaliador_suplente = st.text_input("Avaliador Suplente:")
                
            st.markdown("---")
            st.write("**Integrantes do Grupo**")
            st.info("💡 Dica: Pode copiar e colar a lista de nomes do Excel ou Word. Coloque um nome por linha.")
            lista_alunos = st.text_area("Nomes dos Alunos:", height=150, placeholder="Luana Santos de Sousa\nMarcia Izabella Alves\nLara Sophie Pereira...")
            
            btn_salvar = st.form_submit_button("Salvar e Gerar Banca")
            
            if btn_salvar:
                if not modulo or not titulo or not orientador or not avaliador_1 or not lista_alunos:
                    st.error("Preencha todos os campos obrigatórios (Módulo, Título, Orientador, Avaliador 1 e Alunos).")
                else:
                    # Transforma o texto numa lista real de alunos, removendo linhas vazias
                    alunos_processados = [nome.strip() for nome in lista_alunos.split('\n') if nome.strip()]
                    
                    nova_banca = {
                        "id": str(uuid.uuid4())[:8], # Gera um código único para a banca
                        "modulo": modulo,
                        "formato_piepe": formato_piepe,
                        "data": data_banca.strftime("%d/%m/%Y"),
                        "titulo": titulo,
                        "orientador": orientador,
                        "avaliador_1": avaliador_1,
                        "avaliador_2": avaliador_2,
                        "avaliador_suplente": avaliador_suplente,
                        "alunos": alunos_processados,
                        "status": "Aguardando Avaliação",
                        "notas_banca": [],
                        "nota_orientador": None
                    }
                    st.session_state.bancos_avaliacoes.append(nova_banca)
                    st.success(f"✅ Banca de {modulo} criada com sucesso! Foram registados {len(alunos_processados)} alunos neste grupo.")

    # --- ABA DE GERENCIAMENTO ---
    with aba_gerenciar:
        if not st.session_state.bancos_avaliacoes:
            st.info("Nenhuma banca foi cadastrada até ao momento.")
        else:
            for banca in reversed(st.session_state.bancos_avaliacoes):
                classe_badge = "badge-piepe" if banca['modulo'] == "PIEPE" else "badge-modulo"
                info_piepe = f" | Formato: {banca['formato_piepe']}" if banca['modulo'] == "PIEPE" else ""
                
                st.markdown(f"""
                <div class='cartao-banca'>
                    <span class='{classe_badge}'>{banca['modulo']}</span> <span style='color: #666; font-size: 14px;'>{info_piepe} | Data: {banca['data']}</span>
                    <h4 style='margin-top: 10px; margin-bottom: 5px; color: #333;'>{banca['titulo']}</h4>
                    <strong>Orientador:</strong> {banca['orientador']}<br>
                    <strong>Banca:</strong> {banca['avaliador_1']} | {banca['avaliador_2']} | {banca['avaliador_suplente']} (Suplente)<br>
                    <hr style='margin: 10px 0;'>
                    <strong>Alunos ({len(banca['alunos'])}):</strong> {', '.join(banca['alunos'])}
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# PAINEL 2: AVALIADOR (Em construção)
# ==========================================
def tela_avaliador():
    col_titulo, col_logout = st.columns([4, 1])
    with col_titulo:
        st.markdown(f"### 📱 Painel do Avaliador | Logado como: {st.session_state.usuario_bancas['email']}")
    with col_logout:
        if st.button("Sair (Logout)"):
            st.session_state.usuario_bancas = None
            forçar_recarregamento_tela()
    
    st.info("🚧 Módulo de preenchimento de notas (com caixas de seleção à prova de erros) será construído aqui na próxima etapa!")

# ==========================================
# PAINEL 3: ORIENTADOR (Em construção)
# ==========================================
def tela_orientador():
    col_titulo, col_logout = st.columns([4, 1])
    with col_titulo:
        st.markdown(f"### 📚 Painel do Orientador | Logado como: {st.session_state.usuario_bancas['email']}")
    with col_logout:
        if st.button("Sair (Logout)"):
            st.session_state.usuario_bancas = None
            forçar_recarregamento_tela()
            
    st.info("🚧 Módulo do Diário de Bordo (Atas Mensais) e Fechamento de Notas será construído aqui!")

# ==========================================
# ROTEADOR DE TELAS
# ==========================================
if st.session_state.usuario_bancas is None:
    tela_login()
else:
    perfil_atual = st.session_state.usuario_bancas["perfil"]
    if perfil_atual == "Coordenação":
        tela_coordenacao()
    elif perfil_atual == "Avaliador":
        tela_avaliador()
    elif perfil_atual == "Orientador":
        tela_orientador()
