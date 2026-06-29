import streamlit as st
import uuid
import pandas as pd
import io
from datetime import datetime, time, timedelta

# 1. CONFIGURAÇÃO DA PÁGINA E CSS
st.set_page_config(page_title="Portal de Bancas - CRIVO", page_icon="🎓", layout="wide")

st.markdown("""
    <style>
    .titulo-principal { color: #800040; font-family: 'Arial'; font-weight: bold; margin-bottom: 5px; }
    .cartao-banca { background-color: #ffffff; padding: 20px; border-radius: 8px; border-left: 6px solid #800040; margin-bottom: 15px; box-shadow: 0px 2px 8px rgba(0,0,0,0.08); }
    .badge-tcci { background-color: #3498db; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-tccii { background-color: #2980b9; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-mcmiv { background-color: #2ecc71; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-mcmv { background-color: #27ae60; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-piepe { background-color: #e67e22; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .status-orientacao { background-color: #f39c12; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .status-agendado { background-color: #800040; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .ata-ok { color: #27ae60; font-weight: bold; font-size: 13px; }
    .ata-pendente { color: #e74c3c; font-weight: bold; font-size: 13px; }
    .media-final { font-size: 15px; font-weight: bold; color: #800040; background-color: #f1f1f1; padding: 4px 8px; border-radius: 4px; }
    .zona-segura { background-color: #fafafa; border: 2px dashed #ddd; border-radius: 8px; padding: 15px; margin-bottom: 10px; }
    .rubrica-desc { font-size: 13px; color: #555; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# 3. FUNÇÕES E LISTAS
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

def formatar_data_br(data_obj):
    return data_obj.strftime("%d/%m/%Y") if isinstance(data_obj, datetime) or isinstance(data_obj, type(datetime.now().date())) else data_obj

def calcular_media_final(banca):
    notas = banca.get("notas_lancadas", {})
    nota_ori = notas.get("Orientador")
    
    notas_banca = [v for k, v in notas.items() if k != "Orientador" and isinstance(v, (int, float))]
    media_banca = sum(notas_banca)/len(notas_banca) if notas_banca else 0
    
    if banca['modulo'] in ["TCC I", "TCC II", "MCM IV"]:
        if nota_ori is not None and notas_banca:
            return nota_ori + media_banca
        return None
    else: # MCM V e PIEPE
        if notas_banca:
            return media_banca
        return None

ADMIN_EMAILS = ["wanessa.almeida@afya.com.br", "wanessa.salmeida@yahoo.com.br"]
lista_horarios_base = [time(h, 0) for h in range(8, 22)]
lista_salas_base = [f"APG {i:02d}" for i in range(1, 13)]
lista_semestres = ["2025.2", "2026.1", "2026.2", "2027.1", "2027.2", "2028.1", "2028.2"]

# 4. INICIALIZAÇÃO DA MEMÓRIA BLINDADA
if "bancos_avaliacoes" not in st.session_state:
    st.session_state.bancos_avaliacoes = [
        {
            "id": "tcc2-demo", "modulo": "TCC II", "semestre": "2026.1", "formato_piepe": None,
            "data": "19/06/2026", "horario": "14:00", "sala": "APG 02", "titulo": "Fatores Preditivos para Indicação de Cesárea Emergencial",
            "orientador_email": "brunna.costa@afya.com.br", "orientador_nome": "Bruna Patrícia Dutra da Costa",
            "coorientador_email": "", "coorientador_nome": "",
            "avaliador_1_email": "carlos.silva@afya.com.br", "avaliador_1_nome": "Carlos Silva",
            "avaliador_2_email": "maria.oliveira@afya.com.br", "avaliador_2_nome": "Maria Oliveira",
            "avaliador_sup_email": "jose.santos@afya.com.br", "avaliador_sup_nome": "José Santos",
            "alunos": ["Kamila Sousa Saraiva Fernandes", "Jorge Kalil de Miranda Dias"], "status": "Aguardando Avaliação",
            "atas_mensais": {"Mês 1": True, "Mês 2": True, "Mês 3": True, "Mês 4": False},
            "notas_lancadas": {"Orientador": 35.0, "Avaliador 1": None, "Avaliador 2": 50.0, "Suplente": 55.0},
            "ata_assinada": False,
            "avaliadores_concluidos": [],
            "notas_detalhadas": {}
        }
    ]

for b in st.session_state.bancos_avaliacoes:
    if "avaliadores_concluidos" not in b: b["avaliadores_concluidos"] = []
    if "notas_detalhadas" not in b: b["notas_detalhadas"] = {}

if "permissoes_acesso" not in st.session_state:
    st.session_state.permissoes_acesso = {
        "brunna.costa@afya.com.br": {"perfil": "Professor", "modulos": []},
        "carlos.silva@afya.com.br": {"perfil": "Professor", "modulos": []}
    }

if "configuracoes" not in st.session_state or not isinstance(st.session_state.configuracoes, dict): 
    st.session_state.configuracoes = {}
if "agendamento_aberto" not in st.session_state.configuracoes: 
    st.session_state.configuracoes["agendamento_aberto"] = False
if "disponibilidade_por_modulo" not in st.session_state.configuracoes: 
    st.session_state.configuracoes["disponibilidade_por_modulo"] = {}

for mod in ["TCC I", "TCC II", "MCM IV", "MCM V", "PIEPE"]:
    if mod not in st.session_state.configuracoes["disponibilidade_por_modulo"]:
        st.session_state.configuracoes["disponibilidade_por_modulo"][mod] = {}
    cfg = st.session_state.configuracoes["disponibilidade_por_modulo"][mod]
    if "salas" not in cfg: cfg["salas"] = lista_salas_base.copy()
    if "horarios" not in cfg: cfg["horarios"] = [t.strftime('%H:%M') for t in lista_horarios_base]
    if "agend_ini" not in cfg: cfg["agend_ini"] = datetime.now().date()
    if "agend_fim" not in cfg: cfg["agend_fim"] = datetime.now().date() + timedelta(days=7)
    if "notas_ini" not in cfg: cfg["notas_ini"] = datetime.now().date()
    if "notas_fim" not in cfg: cfg["notas_fim"] = datetime.now().date() + timedelta(days=30)

if "data_fixada_modulo" not in st.session_state: st.session_state.data_fixada_modulo = {}
if "usar_data_fixada_modulo" not in st.session_state: st.session_state.usar_data_fixada_modulo = {}
if "versao_formulario" not in st.session_state: st.session_state.versao_formulario = 0
if "usuario_bancas" not in st.session_state: st.session_state.usuario_bancas = None 

# ==========================================
# MÓDULO DE LOGIN
# ==========================================
def tela_login():
    exibir_sucesso_pendente()
    st.markdown("<h2 class='titulo-principal'>🎓 Portal de Bancas e Avaliações</h2>", unsafe_allow_html=True)
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_login", clear_on_submit=False):
            st.write("**1. Escolha o seu Perfil de Acesso:**")
            tipo_acesso = st.radio("Perfil:", ["👑 Administrador (Gestão)", "⚙️ Coordenação (Gestão de Bancas)", "📚 Professor (Avaliador/Orientador)"], label_visibility="collapsed")
            st.write("**2. Insira suas credenciais:**")
            email = st.text_input("E-mail Institucional:").lower().strip()
            senha = st.text_input("Senha:", type="password")
            submit = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if submit:
                if senha != "afya2026": st.error("Senha incorreta.")
                else:
                    if "Administrador" in tipo_acesso:
                        if email in ADMIN_EMAILS:
                            st.session_state.usuario_bancas = {"perfil": "Administrador", "email": email, "nome": formatar_nome_email(email), "modulos": []}
                            forçar_recarregamento_tela()
                        else: st.error("E-mail não possui privilégios de Administrador.")
                    elif "Coordenação" in tipo_acesso:
                        dados = st.session_state.permissoes_acesso.get(email)
                        if dados and dados.get("perfil") == "Coordenação":
                            st.session_state.usuario_bancas = {"perfil": "Coordenação", "email": email, "nome": formatar_nome_email(email), "modulos": dados.get("modulos", [])}
                            forçar_recarregamento_tela()
                        else: st.error("E-mail não cadastrado como Coordenação.")
                    elif "Professor" in tipo_acesso:
                        is_prof = False; nome_encontrado = formatar_nome_email(email)
                        for b in st.session_state.bancos_avaliacoes:
                            emails = [b.get("orientador_email"), b.get("coorientador_email"), b.get("avaliador_1_email"), b.get("avaliador_2_email"), b.get("avaliador_sup_email")]
                            if email in emails:
                                is_prof = True
                                if email == b.get("orientador_email"): nome_encontrado = b.get("orientador_nome")
                                elif email == b.get("coorientador_email"): nome_encontrado = b.get("coorientador_nome")
                                elif email == b.get("avaliador_1_email"): nome_encontrado = b.get("avaliador_1_nome")
                                elif email == b.get("avaliador_2_email"): nome_encontrado = b.get("avaliador_2_nome")
                                elif email == b.get("avaliador_sup_email"): nome_encontrado = b.get("avaliador_sup_nome")
                                break
                        if is_prof or email in st.session_state.permissoes_acesso:
                            st.session_state.usuario_bancas = {"perfil": "Professor", "email": email, "nome": nome_encontrado}
                            forçar_recarregamento_tela()
                        else: st.error("E-mail não cadastrado na base ou sem grupos ativos.")

# ==========================================
# PAINEL 0: ADMINISTRAÇÃO 
# ==========================================
def tela_administracao():
    exibir_sucesso_pendente()
    col_titulo, col_logout = st.columns([4, 1])
    with col_titulo: st.markdown(f"### 👑 Painel de Administração Master | Olá, {st.session_state.usuario_bancas['nome']}")
    with col_logout:
        if st.button("Sair (Logout)"): st.session_state.usuario_bancas = None; forçar_recarregamento_tela()
            
    with st.expander("➕ Adicionar Novo Coordenador", expanded=True):
        with st.form("form_add_coord", clear_on_submit=False):
            novo_email_coord = st.text_input("E-mail da Coordenação (@afya.com.br):").lower().strip()
            modulos_delegados = st.multiselect("Módulos sob responsabilidade:", ["TCC I", "TCC II", "MCM IV", "MCM V", "PIEPE"])
            if st.form_submit_button("Conceder Acesso"):
                if not novo_email_coord.endswith("@afya.com.br") and not novo_email_coord.endswith("@yahoo.com.br"): st.error("E-mail inválido.")
                elif not modulos_delegados: st.error("Selecione um módulo.")
                else:
                    st.session_state.permissoes_acesso[novo_email_coord] = {"perfil": "Coordenação", "modulos": modulos_delegados}
                    recarregar_com_sucesso(f"Acesso concedido para {novo_email_coord}!")
                
    st.markdown("#### Coordenações Cadastradas")
    for email, dados in list(st.session_state.permissoes_acesso.items()):
        if isinstance(dados, dict) and dados.get("perfil") == "Coordenação":
            with st.container(border=True):
                st.markdown(f"**👤 {formatar_nome_email(email)}** ({email})")
                novos_mods = st.multiselect(f"Módulos autorizados:", ["TCC I", "TCC II", "MCM IV", "MCM V", "PIEPE"], default=dados.get("modulos", []), key=f"mod_{email}")
                col1, col2, col3 = st.columns([2, 2, 6])
                with col1:
                    if st.button("💾 Salvar Módulos", key=f"save_{email}", use_container_width=True):
                        st.session_state.permissoes_acesso[email]["modulos"] = novos_mods; recarregar_com_sucesso("Módulos atualizados!")
                with col2:
                    if st.button("🗑️ Revogar", key=f"del_{email}", use_container_width=True):
                        del st.session_state.permissoes_acesso[email]; recarregar_com_sucesso("Acesso revogado!")

# ==========================================
# PAINEL 1: COORDENAÇÃO (MENU INTELIGENTE)
# ==========================================
def tela_coordenacao():
    exibir_sucesso_pendente()
    col_titulo, col_logout = st.columns([4, 1])
    with col_titulo: st.markdown(f"### ⚙️ Painel da Coordenação | Olá, {st.session_state.usuario_bancas['nome']}")
    with col_logout:
        if st.button("Sair (Logout)", use_container_width=True): st.session_state.usuario_bancas = None; forçar_recarregamento_tela()
            
    # MENU DE NAVEGAÇÃO COM MEMÓRIA (Substitui st.tabs para não redirecionar ao editar)
    if "menu_coordenacao" not in st.session_state: st.session_state.menu_coordenacao = "📋 Gestão e Edição"
    aba_ativa = st.radio("Navegação:", ["➕ Cadastrar Grupos", "📋 Gestão e Edição", "📊 Monitoramento", "📈 Diário de Notas"], horizontal=True, label_visibility="collapsed")
    st.markdown("---")
    
    # ------------------ ABA 1: CADASTRAR ------------------
    if aba_ativa == "➕ Cadastrar Grupos":
        modulos_permitidos = st.session_state.usuario_bancas["modulos"]
        if not modulos_permitidos: st.warning("Sem módulos atribuídos.")
        else:
            col_mod1, col_mod2 = st.columns(2)
            with col_mod1: modulo_selecionado = st.selectbox("1. Selecione o Módulo:", modulos_permitidos, index=None)
            with col_mod2: semestre_selecionado = st.selectbox("2. Semestre Vigente:", lista_semestres, index=lista_semestres.index("2026.1"))
            
            if modulo_selecionado:
                fase_cadastro = st.radio("3. Em qual fase do semestre estamos?", ["📍 Início do Semestre (Apenas Grupo e Orientador)", "🎓 Final do Semestre (Agendamento Completo)"], horizontal=True)
                is_completo = "Final" in fase_cadastro
                
                if modulo_selecionado not in st.session_state.usar_data_fixada_modulo: st.session_state.usar_data_fixada_modulo[modulo_selecionado] = False
                if modulo_selecionado not in st.session_state.data_fixada_modulo: st.session_state.data_fixada_modulo[modulo_selecionado] = datetime.now().date()
                
                if is_completo:
                    col_fix1, col_fix2 = st.columns([1, 3])
                    with col_fix1:
                        fixar_data = st.checkbox(f"Fixar Data p/ {modulo_selecionado}?", value=st.session_state.usar_data_fixada_modulo[modulo_selecionado])
                        st.session_state.usar_data_fixada_modulo[modulo_selecionado] = fixar_data
                    with col_fix2:
                        if fixar_data:
                            data_escolhida = st.date_input("Data Padrão para Fixar:", value=st.session_state.data_fixada_modulo[modulo_selecionado], format="DD/MM/YYYY")
                            st.session_state.data_fixada_modulo[modulo_selecionado] = data_escolhida
                else: fixar_data = False

                with st.form(key=f"form_cadastro_v_{st.session_state.versao_formulario}", clear_on_submit=False):
                    if is_completo:
                        if fixar_data: data_banca = st.date_input("Data da Defesa:", value=st.session_state.data_fixada_modulo[modulo_selecionado], format="DD/MM/YYYY", disabled=True)
                        else: data_banca = st.date_input("Data da Defesa:", format="DD/MM/YYYY")
                    else: data_banca = None
                    
                    formato_piepe, horario_banca, sala_banca = None, None, "A definir"
                    titulo, b1_nome, b1_email, b2_nome, b2_email, bs_nome, bs_email = "", "", "", "", "", "", ""
                    
                    config_mod = st.session_state.configuracoes["disponibilidade_por_modulo"].get(modulo_selecionado, {})
                    salas_filtradas = ["A definir"] + config_mod.get("salas", lista_salas_base)
                    horarios_filtrados = config_mod.get("horarios", [t.strftime('%H:%M') for t in lista_horarios_base])
                    
                    if is_completo:
                        if modulo_selecionado == "PIEPE":
                            st.info("⚠️ PIEPE: A Coordenação define a Sala, Horário e Formato abaixo.")
                            formato_piepe = st.radio("Formato PIEPE:", ["Slide", "Banner"], horizontal=True)
                            col_ph, col_ps = st.columns(2)
                            with col_ph: horario_banca = st.selectbox("Horário:", lista_horarios_base, format_func=lambda t: t.strftime('%H:%M')) if not horarios_filtrados else st.selectbox("Horário:", [time(int(h.split(':')[0]), 0) for h in horarios_filtrados], format_func=lambda t: t.strftime('%H:%M'))
                            with col_ps: sala_banca = st.selectbox("Sala:", salas_filtradas)
                        else:
                            col_hr, col_sl = st.columns(2)
                            with col_hr: horario_banca = st.selectbox("Horário de Início:", lista_horarios_base, format_func=lambda t: t.strftime('%H:%M')) if not horarios_filtrados else st.selectbox("Horário de Início:", [time(int(h.split(':')[0]), 0) for h in horarios_filtrados], format_func=lambda t: t.strftime('%H:%M'))
                            with col_sl: sala_banca = st.selectbox("Sala:", salas_filtradas)
                        titulo = st.text_input("Título do Trabalho:")

                    st.markdown("---")
                    st.write("**Orientação**")
                    col_o1, col_o2 = st.columns(2)
                    with col_o1: o_nome = st.text_input("Nome Completo do Orientador:")
                    with col_o2: o_email = st.text_input("E-mail do Orientador (@afya ou parceiro):").lower().strip()
                    with st.expander("➕ Adicionar Co-orientador (Opcional)"):
                        col_co1, col_co2 = st.columns(2)
                        with col_co1: co_nome = st.text_input("Nome Co-orientador:")
                        with col_co2: co_email = st.text_input("E-mail Co-orientador:").lower().strip()
                    
                    if is_completo:
                        st.markdown("---")
                        st.write("**Membros da Banca Avaliadora**")
                        lbl_n1 = "Nome Completo Titular 1:"
                        lbl_n2 = "Nome Completo Titular 2:"
                        lbl_e1 = "E-mail Titular 1:"
                        lbl_e2 = "E-mail Titular 2:"
                        
                        col_line1_l, col_line1_r = st.columns(2)
                        with col_line1_l: b1_nome = st.text_input(lbl_n1)
                        with col_line1_r: b1_email = st.text_input(lbl_e1).lower().strip()
                        
                        col_line2_l, col_line2_r = st.columns(2)
                        with col_line2_l: b2_nome = st.text_input(lbl_n2)
                        with col_line2_r: b2_email = st.text_input(lbl_e2).lower().strip()

                        if modulo_selecionado in ["TCC II", "MCM V"]:
                            st.write("**Membro Suplente**")
                            col_sup_l, col_sup_r = st.columns(2)
                            with col_sup_l: bs_nome = st.text_input("Nome Completo Suplente:")
                            with col_sup_r: bs_email = st.text_input("E-mail Suplente:").lower().strip()
                        elif modulo_selecionado == "PIEPE":
                            st.write("**Membro Suplente**")
                            col_sup_l, col_sup_r = st.columns(2)
                            with col_sup_l: bs_nome = st.text_input("Nome Completo Suplente (Opcional):")
                            with col_sup_r: bs_email = st.text_input("E-mail Suplente (Opcional):").lower().strip()
                            
                    st.markdown("---")
                    lista_alunos = st.text_area("Integrantes do Grupo (um por linha):", height=100)
                    
                    if st.form_submit_button("Salvar Registro Oficial"):
                        ori_valido = o_email.endswith("@afya.com.br") or o_email.endswith("@parceiro.afya.com.br")
                        co_valido = co_email.endswith("@afya.com.br") or co_email.endswith("@parceiro.afya.com.br") if co_email else True
                        precisa_sup = modulo_selecionado in ["TCC II", "MCM V"]

                        if not o_nome or not o_email or not lista_alunos: st.error("Orientador e Alunos são obrigatórios.")
                        elif co_email and not co_nome: st.error("Preencha o Nome do Co-orientador.")
                        elif not ori_valido or not co_valido: st.error("Domínio de e-mail da orientação inválido.")
                        else:
                            erro_banca = False
                            hora_str = horario_banca.strftime("%H:%M") if (is_completo and horario_banca) else "N/A"
                            data_str = formatar_data_br(data_banca) if (is_completo and data_banca) else "A definir"
                            
                            if is_completo:
                                if not titulo or not b1_nome or not b1_email or not b2_nome or not b2_email: st.error("Título e Avaliadores Titulares são obrigatórios."); erro_banca = True
                                elif precisa_sup and (not bs_nome or not bs_email): st.error("E-mail do Suplente é obrigatório para TCC II e MCM V."); erro_banca = True
                                teve_conflito, conflitos = verificar_conflito_horario(data_str, hora_str, [o_email, co_email, b1_email, b2_email, bs_email])
                                if teve_conflito: st.error(f"🚨 ALERTA DE CHOQUE! E-mails {conflitos} ocupados nessa hora."); erro_banca = True

                            if not erro_banca:
                                status_banca = "Aguardando Avaliação" if is_completo else "Em Orientação"
                                nova_banca = {
                                    "id": str(uuid.uuid4())[:8], "modulo": modulo_selecionado, "semestre": semestre_selecionado, "formato_piepe": formato_piepe,
                                    "data": data_str, "horario": hora_str, "sala": sala_banca, "titulo": titulo,
                                    "orientador_email": o_email, "orientador_nome": o_nome, "coorientador_email": co_email, "coorientador_nome": co_nome,
                                    "avaliador_1_email": b1_email, "avaliador_1_nome": b1_nome, "avaliador_2_email": b2_email, "avaliador_2_nome": b2_nome,
                                    "avaliador_sup_email": bs_email, "avaliador_sup_nome": bs_nome,
                                    "alunos": [n.strip() for n in lista_alunos.split('\n') if n.strip()], 
                                    "status": status_banca, 
                                    "atas_mensais": {"Mês 1": False, "Mês 2": False, "Mês 3": False, "Mês 4": False},
                                    "notas_lancadas": {"Orientador": None, "Avaliador 1": None, "Avaliador 2": None, "Suplente": None},
                                    "ata_assinada": False,
                                    "avaliadores_concluidos": [], "notas_detalhadas": {}
                                }
                                st.session_state.bancos_avaliacoes.append(nova_banca)
                                liberar_acesso_professor(o_email, "Professor")
                                if co_email: liberar_acesso_professor(co_email, "Professor")
                                if is_completo:
                                    liberar_acesso_professor(b1_email, "Professor"); liberar_acesso_professor(b2_email, "Professor")
                                    if bs_email: liberar_acesso_professor(bs_email, "Professor")
                                
                                st.session_state.versao_formulario += 1
                                recarregar_com_sucesso("✅ Grupo cadastrado com sucesso!")

    # ------------------ ABA 2: GESTÃO E EDIÇÃO ------------------
    elif aba_ativa == "📋 Gestão e Edição":
        col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
        with col_f1: filtro_gestao_mod = st.selectbox("🔍 Módulo:", ["Todos"] + st.session_state.usuario_bancas["modulos"], key="gestao_mod")
        with col_f2: filtro_gestao_sem = st.selectbox("📅 Semestre:", ["Todos"] + lista_semestres, key="gestao_sem")
        with col_f3:
            st.write("⚙️ Autonomia dos Professores")
            agendamento = st.toggle("🔓 Permitir Agendamento de Defesa", value=st.session_state.configuracoes["agendamento_aberto"], key="gestao_tgg")
            st.session_state.configuracoes["agendamento_aberto"] = agendamento

        with st.expander("🗓️ Configurar Janelas (Agendamento e Notas por Turma)", expanded=False):
            mod_alvo = st.selectbox("Selecione a Turma/Módulo:", ["TCC I", "TCC II", "MCM IV", "MCM V", "PIEPE"], key="mod_alvo_config")
            st.markdown(f"**1. Período de AGENDAMENTO ({mod_alvo}):**")
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                dt_ag_ini = st.date_input("Início Agendamento:", value=st.session_state.configuracoes["disponibilidade_por_modulo"][mod_alvo].get("agend_ini", datetime.now().date()), format="DD/MM/YYYY", key=f"d_ag_i_{mod_alvo}")
                st.session_state.configuracoes["disponibilidade_por_modulo"][mod_alvo]["agend_ini"] = dt_ag_ini
            with col_a2:
                dt_ag_fim = st.date_input("Fim Agendamento:", value=st.session_state.configuracoes["disponibilidade_por_modulo"][mod_alvo].get("agend_fim", datetime.now().date()), format="DD/MM/YYYY", key=f"d_ag_f_{mod_alvo}")
                st.session_state.configuracoes["disponibilidade_por_modulo"][mod_alvo]["agend_fim"] = dt_ag_fim
                
            st.markdown(f"**2. Restrições Logísticas ({mod_alvo}):**")
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                salas_sel = st.multiselect("Salas APG:", lista_salas_base, default=st.session_state.configuracoes["disponibilidade_por_modulo"][mod_alvo].get("salas", lista_salas_base), key=f"salas_mult_{mod_alvo}")
                st.session_state.configuracoes["disponibilidade_por_modulo"][mod_alvo]["salas"] = salas_sel
            with col_s2:
                horas_txt = [t.strftime('%H:%M') for t in lista_horarios_base]
                horas_sel = st.multiselect("Horários (Até 21:00):", horas_txt, default=st.session_state.configuracoes["disponibilidade_por_modulo"][mod_alvo].get("horarios", horas_txt), key=f"horas_mult_{mod_alvo}")
                st.session_state.configuracoes["disponibilidade_por_modulo"][mod_alvo]["horarios"] = horas_sel
                
            st.markdown(f"**3. Período de LANÇAMENTO DE NOTAS ({mod_alvo}):**")
            col_n1, col_n2 = st.columns(2)
            with col_n1:
                dt_n_ini = st.date_input("Início das Notas:", value=st.session_state.configuracoes["disponibilidade_por_modulo"][mod_alvo].get("notas_ini", datetime.now().date()), format="DD/MM/YYYY", key=f"d_n_i_{mod_alvo}")
                st.session_state.configuracoes["disponibilidade_por_modulo"][mod_alvo]["notas_ini"] = dt_n_ini
            with col_n2:
                dt_n_fim = st.date_input("Fim das Notas:", value=st.session_state.configuracoes["disponibilidade_por_modulo"][mod_alvo].get("notas_fim", datetime.now().date()), format="DD/MM/YYYY", key=f"d_n_f_{mod_alvo}")
                st.session_state.configuracoes["disponibilidade_por_modulo"][mod_alvo]["notas_fim"] = dt_n_fim

        st.markdown("---")
        bancas_filtradas_gestao = [b for b in st.session_state.bancos_avaliacoes if (filtro_gestao_mod == "Todos" or b['modulo'] == filtro_gestao_mod) and (filtro_gestao_sem == "Todos" or b.get('semestre') == filtro_gestao_sem)]
        if not bancas_filtradas_gestao: st.info("Nenhum grupo localizado para estes filtros.")
        else:
            for banca in reversed(bancas_filtradas_gestao):
                indice_real = next((i for i, d in enumerate(st.session_state.bancos_avaliacoes) if d["id"] == banca["id"]), None)
                classe_cor = obter_classe_cor(banca['modulo'])
                classe_st = "status-agendado" if banca['status'] in ["Aguardando Avaliação", "Avaliada"] else "status-orientacao"
                
                hora_str = f" às {banca.get('horario')}" if banca.get('horario') and banca.get('horario') != "N/A" else ""
                sala_str = f" | Sala: {banca.get('sala', 'A definir')}" if banca.get('sala') else ""
                info_extras = f"{banca.get('semestre', 'N/A')} | {banca['data']}{hora_str}{sala_str}"
                
                ori_str = f"{banca['orientador_nome']}"
                av_str = "<i>A definir</i>" if not banca.get('avaliador_1_nome') else f"{banca['avaliador_1_nome']} | {banca.get('avaliador_2_nome', '')}"
                
                edit_key = f"edit_{banca['id']}"
                if edit_key not in st.session_state: st.session_state[edit_key] = False
                
                with st.container(border=True):
                    st.markdown(f"""
                    <div style='border-left: 5px solid #800040; padding-left: 15px; margin-bottom: 15px;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div><span class='{classe_cor}'>{banca['modulo']}</span> <span style='color: #666; font-size: 14px;'> | {info_extras}</span></div>
                            <div><span class='{classe_st}'>{banca['status']}</span></div>
                        </div>
                        <h4 style='margin-top: 10px; margin-bottom: 5px; color: #333;'>{banca.get('titulo') if banca.get('titulo') else 'Projeto Sem Título'}</h4>
                        <p style='margin: 0; font-size: 14px;'><strong>Orientação:</strong> {ori_str}</p>
                        <p style='margin: 0; font-size: 14px;'><strong>Avaliadores:</strong> {av_str}</p>
                        <p style='margin: 8px 0 0 0; font-size: 14px;'><strong>Alunos:</strong> {', '.join(banca.get('alunos', []))}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_b1, col_b2, col_b3 = st.columns([2, 2, 2])
                    with col_b1:
                        if st.button("✏️ Editar / Agendar", key=f"btn_{edit_key}", use_container_width=True):
                            st.session_state[edit_key] = not st.session_state[edit_key]; st.rerun()
                    with col_b2:
                        if st.button("🗑️ Excluir", key=f"del_{banca['id']}", use_container_width=True):
                            st.session_state.bancos_avaliacoes.pop(indice_real); recarregar_com_sucesso("Banca excluída!")
                    with col_b3:
                        novo_mod = "TCC II" if banca['modulo'] == "TCC I" else "MCM V" if banca['modulo'] == "MCM IV" else banca['modulo']
                        if novo_mod != banca['modulo']:
                            if st.button(f"🔄 Migrar p/ {novo_mod}", key=f"mig_{banca['id']}", use_container_width=True):
                                curr_sem = banca.get('semestre', '2026.1')
                                idx_sem = lista_semestres.index(curr_sem) if curr_sem in lista_semestres else -1
                                novo_sem = lista_semestres[idx_sem + 1] if idx_sem >= 0 and idx_sem + 1 < len(lista_semestres) else curr_sem
                                b_copy = banca.copy()
                                b_copy.update({"id": str(uuid.uuid4())[:8], "modulo": novo_mod, "semestre": novo_sem, "status": "Em Orientação", "avaliadores_concluidos": [], "notas_detalhadas": {}})
                                st.session_state.bancos_avaliacoes.append(b_copy); recarregar_com_sucesso(f"Migrado para {novo_mod}!")
                    
                    if st.session_state[edit_key]:
                        st.markdown("---")
                        with st.form(key=f"form_ed_real_{banca['id']}", clear_on_submit=False):
                            try: data_obj = datetime.strptime(banca['data'], "%d/%m/%Y").date() if banca['data'] != "A definir" else datetime.now().date()
                            except: data_obj = datetime.now().date()
                            
                            col_ed1, col_ed2 = st.columns(2)
                            with col_ed1: edit_semestre = st.selectbox("Semestre:", lista_semestres, index=lista_semestres.index(banca.get('semestre', '2026.1')) if banca.get('semestre') in lista_semestres else 0)
                            with col_ed2: edit_data = st.date_input("Data:", value=data_obj, format="DD/MM/YYYY")
                            
                            edit_titulo = st.text_input("Título do Trabalho:", value=banca.get('titulo', ''))
                            edit_alunos = st.text_area("Alunos (um por linha):", value="\n".join(banca.get('alunos', [])), height=100)
                            
                            col_actions1, col_actions2 = st.columns(2)
                            with col_actions1: salvar_alt = st.form_submit_button("💾 Salvar Alterações", use_container_width=True)
                            with col_actions2: cancelar_alt = st.form_submit_button("❌ Cancelar", use_container_width=True)
                            if cancelar_alt: st.session_state[edit_key] = False; st.rerun()
                            if salvar_alt:
                                st.session_state.bancos_avaliacoes[indice_real].update({"semestre": edit_semestre, "data": formatar_data_br(edit_data), "titulo": edit_titulo, "alunos": [n.strip() for n in edit_alunos.split('\n') if n.strip()]})
                                st.session_state[edit_key] = False; recarregar_com_sucesso("Atualizado!")

    # ------------------ ABA 3: MONITORAMENTO ------------------
    elif aba_ativa == "📊 Monitoramento":
        st.info("Painel Gerencial de Atas e Notas. Os dados de orientação e botões de download estão fixos.")
        col_m1, col_m2 = st.columns(2)
        with col_m1: filtro_mod_mon = st.selectbox("🔍 Módulo:", ["Todos"] + st.session_state.usuario_bancas["modulos"], key="mon_mod")
        with col_m2: filtro_sem_mon = st.selectbox("📅 Semestre:", ["Todos"] + lista_semestres, key="mon_sem")
        bancas_monitoramento = [b for b in st.session_state.bancos_avaliacoes if (filtro_mod_mon == "Todos" or b['modulo'] == filtro_mod_mon) and (filtro_sem_mon == "Todos" or b.get('semestre') == filtro_sem_mon)]
        
        if not bancas_monitoramento: st.write("Nenhum grupo ativo.")
        else:
            for banca in bancas_monitoramento:
                notas = banca.get("notas_lancadas", {})
                media = calcular_media_final(banca)
                atas = banca.get("atas_mensais", {})
                
                with st.container(border=True):
                    # INFORMAÇÕES COMPLETAS (Restauradas)
                    st.markdown(f"#### 👤 Orientador(a): {banca.get('orientador_nome', 'N/A')}")
                    st.markdown(f"<span style='color: #666;'><b>Projeto:</b> {banca.get('titulo', 'Trabalho Sem Título')} | <b>Módulo:</b> {banca['modulo']} ({banca.get('semestre')})</span>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color: #666;'><b>Alunos:</b> {', '.join(banca.get('alunos', []))}</span>", unsafe_allow_html=True)
                    
                    if banca['modulo'] != "PIEPE":
                        st.markdown("---")
                        st.write("**Atas de Reunião Mensal (Orientação):**")
                        col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                        def txt_ata(mes): return f"<div class='{'ata-ok' if atas.get(mes) else 'ata-pendente'}'>{mes}: {'✅ Concluída' if atas.get(mes) else '❌ Pendente'}</div>"
                        
                        # BOTÕES DE DOWNLOAD SEMPRE VISÍVEIS
                        with col_a1: 
                            st.markdown(txt_ata("Mês 1"), unsafe_allow_html=True)
                            st.download_button("📥 Baixar PDF", "Mock PDF Ata M1", file_name=f"Ata_M1_{banca['id']}.pdf", key=f"d_a1_{banca['id']}", use_container_width=True)
                        with col_a2: 
                            st.markdown(txt_ata("Mês 2"), unsafe_allow_html=True)
                            st.download_button("📥 Baixar PDF", "Mock PDF Ata M2", file_name=f"Ata_M2_{banca['id']}.pdf", key=f"d_a2_{banca['id']}", use_container_width=True)
                        with col_a3: 
                            st.markdown(txt_ata("Mês 3"), unsafe_allow_html=True)
                            st.download_button("📥 Baixar PDF", "Mock PDF Ata M3", file_name=f"Ata_M3_{banca['id']}.pdf", key=f"d_a3_{banca['id']}", use_container_width=True)
                        with col_a4: 
                            st.markdown(txt_ata("Mês 4"), unsafe_allow_html=True)
                            st.download_button("📥 Baixar PDF", "Mock PDF Ata M4", file_name=f"Ata_M4_{banca['id']}.pdf", key=f"d_a4_{banca['id']}", use_container_width=True)

                    st.markdown("---")
                    st.write("**Lançamento de Notas:**")
                    col_n1, col_n2, col_n3, col_n4 = st.columns(4)
                    def txt_n(k): return f"<div class='{'ata-ok' if notas.get(k) is not None else 'ata-pendente'}'>{k}: {'✅ ('+str(notas.get(k))+')' if notas.get(k) is not None else '❌'}</div>"
                    
                    if banca['modulo'] not in ["MCM V", "PIEPE"]:
                        with col_n1: st.markdown(txt_n("Orientador"), unsafe_allow_html=True)
                    with col_n2: st.markdown(txt_n("Avaliador 1"), unsafe_allow_html=True)
                    with col_n3: st.markdown(txt_n("Avaliador 2"), unsafe_allow_html=True)
                    with col_n4: st.markdown(txt_n("Suplente") if banca.get("avaliador_sup_email") else "", unsafe_allow_html=True)
                    
                    st.markdown(f"<div style='text-align: right;'><span class='media-final'>Média Final: {f'{media:.1f}' if media is not None else 'Pendente'}</span></div>", unsafe_allow_html=True)
                    
                    if banca['modulo'] in ["TCC I", "TCC II", "MCM IV", "MCM V"]:
                        st.markdown("---")
                        status_ata = "✅ Documento Assinado" if banca.get("ata_assinada") else "❌ Aguardando Assinaturas na Ata de Defesa"
                        col_at1, col_at2 = st.columns([3,1])
                        with col_at1: st.markdown(f"<span style='font-size:14px; font-weight:bold;'>Status Oficial: {status_ata}</span>", unsafe_allow_html=True)
                        # BOTÃO DE DOWNLOAD SEMPRE VISÍVEL
                        with col_at2: st.download_button("📥 Baixar Ata de Defesa", "Mock Ata Defesa", file_name=f"Ata_Defesa_{banca['id']}.pdf", use_container_width=True, key=f"d_def_{banca['id']}")

    # ------------------ ABA 4: DIÁRIO DE NOTAS ------------------
    elif aba_ativa == "📈 Diário de Notas":
        col_m1, col_m2 = st.columns(2)
        with col_m1: filtro_mod_dia = st.selectbox("🔍 Módulo:", ["Todos"] + st.session_state.usuario_bancas["modulos"], key="dia_mod")
        with col_m2: filtro_sem_dia = st.selectbox("📅 Semestre:", ["Todos"] + lista_semestres, key="dia_sem")
        st.markdown("---")

        bancas_diario = [b for b in st.session_state.bancos_avaliacoes if (filtro_mod_dia == "Todos" or b['modulo'] == filtro_mod_dia) and (filtro_sem_dia == "Todos" or b.get('semestre') == filtro_sem_dia)]
        
        lista_alunos_notas = []
        for b in bancas_diario:
            media_calc = calcular_media_final(b)
            media_str = f"{media_calc:.1f}" if media_calc is not None else "Pendente"

            for aluno in b.get("alunos", []):
                lista_alunos_notas.append({
                    "Aluno (Ordem Alfabética)": aluno,
                    "Média Final": media_str,
                    "Módulo": b["modulo"],
                    "Semestre": b.get("semestre", "N/A")
                })
        
        if lista_alunos_notas:
            df_notas = pd.DataFrame(lista_alunos_notas)
            df_notas = df_notas.sort_values(by="Aluno (Ordem Alfabética)").reset_index(drop=True)
            df_notas.index = range(1, len(df_notas) + 1)
            st.dataframe(df_notas, use_container_width=True)
            
            buffer_notas = io.BytesIO()
            with pd.ExcelWriter(buffer_notas, engine='openpyxl') as writer:
                df_notas.to_excel(writer, index=False, sheet_name='Diario de Notas')
                worksheet = writer.sheets['Diario de Notas']
                for idx, col in enumerate(df_notas.columns):
                    max_len = max([len(str(x)) for x in df_notas[col].values] + [len(str(col))]) + 2
                    col_letter = chr(65 + idx)
                    worksheet.column_dimensions[col_letter].width = min(max_len, 45)
            st.download_button("📥 Baixar Diário de Notas (.xlsx)", data=buffer_notas.getvalue(), file_name=f"Diario_Notas_{filtro_mod_dia}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("Nenhum aluno cadastrado nos filtros atuais.")

# ==========================================
# PAINEL DO PROFESSOR (NOVO E CONTEXTUAL)
# ==========================================
def tela_professor():
    exibir_sucesso_pendente()
    col_titulo, col_logout = st.columns([4, 1])
    with col_titulo: st.markdown(f"### 📚 Portal do Docente | Olá, {st.session_state.usuario_bancas['nome']}")
    with col_logout:
        if st.button("Sair (Logout)"): st.session_state.usuario_bancas = None; forçar_recarregamento_tela()
            
    meu_email = st.session_state.usuario_bancas['email']
    hoje = datetime.now().date()
    
    eh_orientador = any(meu_email in [b.get('orientador_email'), b.get('coorientador_email')] for b in st.session_state.bancos_avaliacoes)
    eh_banca = any(meu_email in [b.get('avaliador_1_email'), b.get('avaliador_2_email'), b.get('avaliador_sup_email')] for b in st.session_state.bancos_avaliacoes)
    
    abas_nomes = []
    if eh_orientador: abas_nomes.append("🎓 Meus Grupos (Orientação)")
    if eh_banca: abas_nomes.append("⚖️ Bancas Pendentes")
    abas_nomes.append("🗂️ Histórico de Avaliações")
    
    # Usando st.radio estilizado para o professor também não perder o estado
    aba_prof = st.radio("Navegação Prof:", abas_nomes, horizontal=True, label_visibility="collapsed")
    st.markdown("---")
    
    # --- ABA: ORIENTAÇÃO ---
    if aba_prof == "🎓 Meus Grupos (Orientação)":
        st.info("Aqui você gerencia Atas Mensais e a sua Nota de Orientação.")
        orientacoes = [b for b in st.session_state.bancos_avaliacoes if meu_email in [b.get('orientador_email'), b.get('coorientador_email')]]
        for banca in orientacoes:
            with st.container(border=True):
                st.markdown(f"#### {banca['modulo']} - {banca.get('titulo', 'Projeto sem título')}")
                st.markdown(f"<span style='color: #666;'><b>Status:</b> {banca['status']} | <b>Alunos:</b> {', '.join(banca.get('alunos', []))}</span>", unsafe_allow_html=True)
                st.markdown("---")
                
                # BOTÕES DETALHADOS DE ATA
                st.write("**📝 Controle de Atas Mensais de Orientação**")
                atas = banca.get("atas_mensais", {"Mês 1": False, "Mês 2": False, "Mês 3": False, "Mês 4": False})
                
                for mes in ["Mês 1", "Mês 2", "Mês 3", "Mês 4"]:
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown(f"**{mes}**: {'✅ Concluída' if atas.get(mes) else '❌ Pendente'}")
                    with c2:
                        if st.button(f"📝 Preencher Ata {mes}", key=f"fill_{mes}_{banca['id']}"):
                            st.warning(f"Aqui abrirá o formulário da Ata de Acompanhamento do {mes} (Em desenvolvimento).")
                
                if banca['modulo'] not in ["MCM V", "PIEPE"]:
                    st.markdown("---")
                    st.write("**Lançamento de Nota do Orientador**")
                    max_nota = 40.0 if banca['modulo'] in ["TCC I", "TCC II"] else 70.0
                    st.info(f"O módulo {banca['modulo']} permite nota máxima de **{max_nota} pontos** para o Orientador.")
                    
                    nota_ori = st.number_input(f"Sua Nota (0.0 a {max_nota}):", 0.0, float(max_nota), value=float(banca['notas_lancadas'].get('Orientador', 0) or 0), step=0.5, key=f"n_ori_{banca['id']}")
                    if st.button("Salvar Nota de Orientador", key=f"save_n_{banca['id']}"):
                        indice_real = next((i for i, d in enumerate(st.session_state.bancos_avaliacoes) if d["id"] == banca["id"]), None)
                        st.session_state.bancos_avaliacoes[indice_real]['notas_lancadas']['Orientador'] = nota_ori
                        recarregar_com_sucesso("Nota de orientação salva com sucesso!")
        
    # --- ABA: BANCAS PENDENTES (RUBRICAS DESCRITIVAS) ---
    elif aba_prof == "⚖️ Bancas Pendentes":
        bancas_pendentes = [b for b in st.session_state.bancos_avaliacoes if meu_email in [b.get('avaliador_1_email'), b.get('avaliador_2_email'), b.get('avaliador_sup_email')] and meu_email not in b.get('avaliadores_concluidos', [])]
        
        if not bancas_pendentes: 
            st.success("🎉 Você não tem bancas pendentes de avaliação no momento.")
        else:
            st.warning("⚠️ **Atenção:** Grupos avaliados sumirão desta tela e irão para a aba 'Histórico'.")
            for banca in bancas_pendentes:
                indice_real = next((i for i, d in enumerate(st.session_state.bancos_avaliacoes) if d["id"] == banca["id"]), None)
                cfg = st.session_state.configuracoes["disponibilidade_por_modulo"].get(banca['modulo'], {})
                janela_notas = cfg.get("notas_ini", hoje) <= hoje <= cfg.get("notas_fim", hoje)
                
                with st.container(border=True):
                    st.markdown(f"#### {banca['modulo']} - {banca.get('titulo', 'Sem Título')}")
                    st.write(f"**Alunos:** {', '.join(banca.get('alunos', []))}")
                    
                    if not janela_notas:
                        st.error(f"⏳ O sistema de notas para {banca['modulo']} está fechado pela coordenação.")
                    else:
                        with st.container(height=420, border=True):
                            st.markdown("<div class='zona-segura'>", unsafe_allow_html=True)
                            
                            key_e = f"n_escrita_{banca['id']}"
                            key_o = f"n_oral_{banca['id']}"
                            key_u = f"n_unica_{banca['id']}"
                            nota_final_calc = 0.0
                            
                            if banca['modulo'] in ["TCC I", "TCC II"]:
                                st.markdown("##### 📝 Rubrica: Parte Escrita (Máx 30 pts)")
                                st.markdown("""<div class='rubrica-desc'><b>Itens avaliados:</b> Fundamentação Teórica, Clareza Metodológica, Desenvolvimento dos Resultados e Formatação (ABNT/Vancouver).</div>""", unsafe_allow_html=True)
                                n_escrita = st.slider("Nota da Parte Escrita:", 0.0, 30.0, 0.0, step=0.5, key=key_e)
                                
                                st.markdown("##### 🗣️ Rubrica: Apresentação Oral (Máx 30 pts)")
                                st.markdown("""<div class='rubrica-desc'><b>Itens avaliados:</b> Domínio do tema, Clareza na exposição, Uso adequado do tempo e Capacidade de síntese na arguição.</div>""", unsafe_allow_html=True)
                                n_oral = st.slider("Nota da Apresentação Oral:", 0.0, 30.0, 0.0, step=0.5, key=key_o)
                                
                                nota_final_calc = n_escrita + n_oral
                                notas_dit = {"Escrita": n_escrita, "Oral": n_oral, "Final da Banca": nota_final_calc}
                                
                            elif banca['modulo'] == "MCM IV":
                                st.markdown("##### 📝 Rubrica Global da Banca (Máx 30 pts)")
                                st.markdown("""<div class='rubrica-desc'><b>Critérios:</b> Avaliação consolidada abordando tanto o conteúdo científico do material escrito quanto a clareza da defesa oral do projeto.</div>""", unsafe_allow_html=True)
                                n_unica = st.slider("Nota da Banca Avaliadora:", 0.0, 30.0, 0.0, step=0.5, key=key_u)
                                nota_final_calc = n_unica
                                notas_dit = {"Final da Banca": nota_final_calc}
                                
                            else: # MCM V e PIEPE
                                st.markdown("##### 📝 Rubrica Global (Máx 100 pts)")
                                st.markdown("""<div class='rubrica-desc'><b>Critérios:</b> Domínio teórico avançado, relevância do raciocínio clínico, aplicabilidade prática, postura profissional e qualidade da exposição na defesa.</div>""", unsafe_allow_html=True)
                                n_unica = st.slider("Nota Global da Avaliação:", 0.0, 100.0, 0.0, step=0.5, key=key_u)
                                nota_final_calc = n_unica
                                notas_dit = {"Final da Banca": nota_final_calc}
                            
                            st.markdown("---")
                            st.markdown(f"### 🧮 Total Ponderado da Banca: <span style='color:#800040;'>{nota_final_calc:.1f}</span>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                        key_modal = f"modal_conf_{banca['id']}"
                        if st.button("Finalizar Avaliação Oficial", key=f"btn_fin_{banca['id']}", use_container_width=True):
                            st.session_state[key_modal] = True
                            st.rerun()
                            
                        if st.session_state.get(key_modal):
                            st.warning(f"Você está prestes a atribuir a nota **{nota_final_calc:.1f}** a este grupo. Esta ação não poderá ser desfeita.")
                            if nota_final_calc == 0: st.error("🚨 ALERTA: A nota atribuída é ZERO. Confirma?")
                            
                            col_y, col_n = st.columns(2)
                            with col_y:
                                if st.button("✅ Sim, Confirmar e Enviar", key=f"yes_{banca['id']}", use_container_width=True):
                                    role = "Avaliador 1" if meu_email == banca.get('avaliador_1_email') else ("Avaliador 2" if meu_email == banca.get('avaliador_2_email') else "Suplente")
                                    st.session_state.bancos_avaliacoes[indice_real]['notas_lancadas'][role] = nota_final_calc
                                    st.session_state.bancos_avaliacoes[indice_real]['notas_detalhadas'][meu_email] = notas_dit
                                    st.session_state.bancos_avaliacoes[indice_real]['avaliadores_concluidos'].append(meu_email)
                                    st.session_state[key_modal] = False
                                    recarregar_com_sucesso(f"Avaliação de {banca['modulo']} enviada com sucesso!")
                            with col_n:
                                if st.button("❌ Não, Cancelar e Revisar", key=f"no_{banca['id']}", use_container_width=True):
                                    st.session_state[key_modal] = False
                                    st.rerun()
        
    # --- ABA: HISTÓRICO DE AVALIAÇÕES ---
    elif aba_prof == "🗂️ Histórico de Avaliações":
        bancas_avaliadas = [b for b in st.session_state.bancos_avaliacoes if meu_email in b.get('avaliadores_concluidos', [])]
        if not bancas_avaliadas:
            st.info("O seu histórico de avaliações concluídas aparecerá aqui.")
        else:
            for banca in bancas_avaliadas:
                with st.container(border=True):
                    minhas_notas = banca['notas_detalhadas'].get(meu_email, {})
                    st.write(f"✅ **{banca['modulo']}** - {banca.get('titulo', 'Sem Título')} | Alunos: {', '.join(banca.get('alunos', []))}")
                    with st.expander("Ver minha Rubrica e Notas (Cópia de Segurança)"):
                        for criterio, valor in minhas_notas.items():
                            if "Final" in criterio: st.markdown(f"**Nota {criterio}:** {valor:.1f}")
                            else: st.write(f"- {criterio}: {valor:.1f}")

# ==========================================
# ROTEADOR DE TELAS
# ==========================================
if st.session_state.usuario_bancas is None: tela_login()
elif st.session_state.usuario_bancas["perfil"] == "Administrador": tela_administracao()
elif st.session_state.usuario_bancas["perfil"] == "Coordenação": tela_coordenacao()
elif st.session_state.usuario_bancas["perfil"] == "Professor": tela_professor()
