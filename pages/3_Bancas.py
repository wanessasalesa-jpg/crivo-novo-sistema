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
    else:
        if notas_banca:
            return media_banca
        return None

ADMIN_EMAILS = ["wanessa.almeida@afya.com.br", "wanessa.salmeida@yahoo.com.br"]
lista_horarios_base = [time(h, 0) for h in range(8, 22)]
lista_salas_base = [f"APG {i:02d}" for i in range(1, 13)]
lista_semestres = ["2025.2", "2026.1", "2026.2", "2027.1", "2027.2", "2028.1", "2028.2"]

# 4. INICIALIZAÇÃO DA MEMÓRIA
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
            "avaliadores_concluidos": [], "notas_detalhadas": {}
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
# PAINEL 0: LOGIN E ADMINISTRAÇÃO 
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
# PAINEL 1: COORDENAÇÃO 
# ==========================================
def tela_coordenacao():
    exibir_sucesso_pendente()
    col_titulo, col_logout = st.columns([4, 1])
    with col_titulo: st.markdown(f"### ⚙️ Painel da Coordenação | Olá, {st.session_state.usuario_bancas['nome']}")
    with col_logout:
        if st.button("Sair (Logout)", use_container_width=True): st.session_state.usuario_bancas = None; forçar_recarregamento_tela()
            
    aba_ativa = st.radio("Navegação:", ["➕ Cadastrar Grupos", "📋 Gestão e Edição", "📊 Monitoramento", "📈 Diário de Notas"], horizontal=True, label_visibility="collapsed")
    st.markdown("---")
    
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
                
                with st.form(key=f"form_cadastro_v_{st.session_state.versao_formulario}", clear_on_submit=False):
                    data_banca, formato_piepe, horario_banca, sala_banca = None, None, "N/A", "A definir"
                    titulo, b1_nome, b1_email, b2_nome, b2_email, bs_nome, bs_email = "", "", "", "", "", "", ""
                    
                    if is_completo:
                        data_banca = st.date_input("Data da Defesa:", format="DD/MM/YYYY")
                        titulo = st.text_input("Título do Trabalho:")
                    
                    st.write("**Orientação**")
                    col_o1, col_o2 = st.columns(2)
                    with col_o1: o_nome = st.text_input("Nome Completo do Orientador:")
                    with col_o2: o_email = st.text_input("E-mail do Orientador (@afya):").lower().strip()
                    
                    if is_completo:
                        col_line1_l, col_line1_r = st.columns(2)
                        with col_line1_l: b1_nome = st.text_input("Nome Completo Titular 1:")
                        with col_line1_r: b1_email = st.text_input("E-mail Titular 1:").lower().strip()
                        
                        col_line2_l, col_line2_r = st.columns(2)
                        with col_line2_l: b2_nome = st.text_input("Nome Completo Titular 2:")
                        with col_line2_r: b2_email = st.text_input("E-mail Titular 2:").lower().strip()
                        
                    lista_alunos = st.text_area("Integrantes do Grupo (um por linha):")
                    
                    if st.form_submit_button("Salvar Registro Oficial"):
                        if not o_nome or not o_email or not lista_alunos: st.error("Orientador e Alunos são obrigatórios.")
                        else:
                            status_banca = "Aguardando Avaliação" if is_completo else "Em Orientação"
                            nova_banca = {
                                "id": str(uuid.uuid4())[:8], "modulo": modulo_selecionado, "semestre": semestre_selecionado, "formato_piepe": formato_piepe,
                                "data": formatar_data_br(data_banca) if data_banca else "A definir", "horario": "N/A", "sala": "A definir", "titulo": titulo,
                                "orientador_email": o_email, "orientador_nome": o_nome, "coorientador_email": "", "coorientador_nome": "",
                                "avaliador_1_email": b1_email, "avaliador_1_nome": b1_nome, "avaliador_2_email": b2_email, "avaliador_2_nome": b2_nome, "avaliador_sup_email": "", "avaliador_sup_nome": "",
                                "alunos": [n.strip() for n in lista_alunos.split('\n') if n.strip()], "status": status_banca, 
                                "atas_mensais": {"Mês 1": False, "Mês 2": False, "Mês 3": False, "Mês 4": False},
                                "notas_lancadas": {"Orientador": None, "Avaliador 1": None, "Avaliador 2": None, "Suplente": None},
                                "ata_assinada": False, "avaliadores_concluidos": [], "notas_detalhadas": {}
                            }
                            st.session_state.bancos_avaliacoes.append(nova_banca)
                            liberar_acesso_professor(o_email, "Professor")
                            if b1_email: liberar_acesso_professor(b1_email, "Professor")
                            st.session_state.versao_formulario += 1
                            recarregar_com_sucesso("✅ Grupo cadastrado com sucesso!")

    elif aba_ativa == "📋 Gestão e Edição":
        col_f1, col_f2 = st.columns(2)
        with col_f1: filtro_gestao_mod = st.selectbox("🔍 Módulo:", ["Todos"] + st.session_state.usuario_bancas["modulos"], key="gestao_mod")
        with col_f2: filtro_gestao_sem = st.selectbox("📅 Semestre:", ["Todos"] + lista_semestres, key="gestao_sem")
        
        bancas_filtradas_gestao = [b for b in st.session_state.bancos_avaliacoes if (filtro_gestao_mod == "Todos" or b['modulo'] == filtro_gestao_mod) and (filtro_gestao_sem == "Todos" or b.get('semestre') == filtro_gestao_sem)]
        
        for banca in reversed(bancas_filtradas_gestao):
            with st.container(border=True):
                st.write(f"**{banca['modulo']}** ({banca.get('semestre')}) - {banca['data']} | Status: {banca['status']}")
                st.markdown(f"**Título:** {banca.get('titulo') if banca.get('titulo') else 'Projeto Sem Título'}")
                st.write(f"Orientador: {banca['orientador_nome']} | Alunos: {', '.join(banca['alunos'])}")

    elif aba_ativa == "📊 Monitoramento":
        col_m1, col_m2 = st.columns(2)
        with col_m1: filtro_mod_mon = st.selectbox("🔍 Módulo:", ["Todos"] + st.session_state.usuario_bancas["modulos"], key="mon_mod")
        with col_m2: filtro_sem_mon = st.selectbox("📅 Semestre:", ["Todos"] + lista_semestres, key="mon_sem")
        bancas_monitoramento = [b for b in st.session_state.bancos_avaliacoes if (filtro_mod_mon == "Todos" or b['modulo'] == filtro_mod_mon) and (filtro_sem_mon == "Todos" or b.get('semestre') == filtro_sem_mon)]
        
        for banca in bancas_monitoramento:
            media = calcular_media_final(banca)
            atas = banca.get("atas_mensais", {})
            with st.container(border=True):
                st.markdown(f"#### 👤 Orientador(a): {banca.get('orientador_nome', 'N/A')}")
                st.markdown(f"**Projeto:** {banca.get('titulo') if banca.get('titulo') else 'Trabalho Sem Título'} | **Módulo:** {banca['modulo']} ({banca.get('semestre')})")
                st.markdown(f"**Alunos:** {', '.join(banca.get('alunos', []))}")
                
                if banca['modulo'] != "PIEPE":
                    st.markdown("---")
                    st.write("**Atas de Reunião Mensal:**")
                    col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                    with col_a1: st.markdown(f"M1: {'✅' if atas.get('Mês 1') else '❌'}"); st.download_button("📥 PDF M1", "Mock PDF", key=f"dm1_{banca['id']}", use_container_width=True)
                    with col_a2: st.markdown(f"M2: {'✅' if atas.get('Mês 2') else '❌'}"); st.download_button("📥 PDF M2", "Mock PDF", key=f"dm2_{banca['id']}", use_container_width=True)
                    with col_a3: st.markdown(f"M3: {'✅' if atas.get('Mês 3') else '❌'}"); st.download_button("📥 PDF M3", "Mock PDF", key=f"dm3_{banca['id']}", use_container_width=True)
                    with col_a4: st.markdown(f"M4: {'✅' if atas.get('Mês 4') else '❌'}"); st.download_button("📥 PDF M4", "Mock PDF", key=f"dm4_{banca['id']}", use_container_width=True)
                
                st.markdown("---")
                st.write(f"**Média Final Consolidada:** {f'{media:.1f}' if media is not None else 'Pendente'}")
                st.download_button("📥 Baixar Ata de Defesa (PDF)", "Mock Ata Defesa", key=f"d_def_{banca['id']}")

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
                lista_alunos_notas.append({"Aluno (Ordem Alfabética)": aluno, "Média Final": media_str, "Módulo": b["modulo"], "Semestre": b.get("semestre", "N/A")})
        
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
# PAINEL DO PROFESSOR (CONCERTADO: BOTÕES DE ATA + HISTÓRICO DE RUBRICA)
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
    if eh_banca: abas_nomes.append("🎓 Bancas Pendentes")
    abas_nomes.append("🗂️ Histórico de Avaliações")
    
    aba_prof = st.radio("Navegação Prof:", abas_nomes, horizontal=True, label_visibility="collapsed")
    st.markdown("---")
    
    if aba_prof == "🎓 Meus Grupos (Orientação)":
        orientacoes = [b for b in st.session_state.bancos_avaliacoes if meu_email in [b.get('orientador_email'), b.get('coorientador_email')]]
        for banca in orientacoes:
            indice_real = next((i for i, d in enumerate(st.session_state.bancos_avaliacoes) if d["id"] == banca["id"]), None)
            with st.container(border=True):
                st.markdown(f"#### {banca['modulo']} - {banca.get('titulo', 'Projeto sem título')}")
                st.markdown(f"<span style='color: #666;'><b>Status:</b> {banca['status']} | <b>Alunos:</b> {', '.join(banca.get('alunos', []))}</span>", unsafe_allow_html=True)
                
                with st.expander("📅 Ver Controle de Atas Mensais de Orientação"):
                    atas = banca.get("atas_mensais", {"Mês 1": False, "Mês 2": False, "Mês 3": False, "Mês 4": False})
                    
                    for mes in ["Mês 1", "Mês 2", "Mês 3", "Mês 4"]:
                        c1, c2 = st.columns([1, 2])
                        with c1:
                            novo_status = st.checkbox(f"{mes} Concluído", value=atas.get(mes, False), key=f"chk_{mes}_{banca['id']}")
                            if novo_status != atas.get(mes, False):
                                st.session_state.bancos_avaliacoes[indice_real]['atas_mensais'][mes] = novo_status
                        with c2:
                            if st.button(f"📝 Preencher Ata {mes}", key=f"btn_ata_{mes}_{banca['id']}"):
                                st.warning(f"O formulário da Ata do {mes} abrirá aqui (Em desenvolvimento).")

                if banca['modulo'] not in ["MCM V", "PIEPE"]:
                    max_nota = 40.0 if banca['modulo'] in ["TCC I", "TCC II"] else 70.0
                    nota_ori = st.number_input(f"Sua Nota de Orientação (0.0 a {max_nota}):", 0.0, float(max_nota), value=float(banca['notas_lancadas'].get('Orientador', 0) or 0), key=f"n_ori_{banca['id']}")
                    if st.button("Salvar Nota", key=f"s_no_{banca['id']}"):
                        st.session_state.bancos_avaliacoes[indice_real]['notas_lancadas']['Orientador'] = nota_ori
                        recarregar_com_sucesso("Nota salva!")
        
    elif aba_prof == "🎓 Bancas Pendentes":
        bancas_pendentes = [b for b in st.session_state.bancos_avaliacoes if meu_email in [b.get('avaliador_1_email'), b.get('avaliador_2_email'), b.get('avaliador_sup_email')] and meu_email not in b.get('avaliadores_concluidos', [])]
        
        for banca in bancas_pendentes:
            indice_real = next((i for i, d in enumerate(st.session_state.bancos_avaliacoes) if d["id"] == banca["id"]), None)
            with st.container(border=True):
                st.markdown(f"#### {banca['modulo']} - {banca.get('titulo', 'Sem Título')}")
                st.write(f"**Alunos:** {', '.join(banca.get('alunos', []))}")
                
                with st.container(height=420, border=True):
                    st.markdown("<div class='zona-segura'>", unsafe_allow_html=True)
                    nota_final_calc = 0.0
                    
                    if banca['modulo'] in ["TCC I", "TCC II"]:
                        st.markdown("##### 📝 Rubricas Detalhadas da Banca (Máx 60 pontos)")
                        c1 = st.slider("1. Introdução, Referencial e Fundamentação (0 a 15):", 0.0, 15.0, 0.0, step=0.5, key=f"c1_{banca['id']}")
                        c2 = st.slider("2. Metodologia, Resultados e Discussão (0 a 15):", 0.0, 15.0, 0.0, step=0.5, key=f"c2_{banca['id']}")
                        c3 = st.slider("3. Domínio Temático, Clareza e Arguição Oral (0 a 15):", 0.0, 15.0, 0.0, step=0.5, key=f"c3_{banca['id']}")
                        c4 = st.slider("4. Recursos Visuais, Postura e Uso do Tempo (0 a 15):", 0.0, 15.0, 0.0, step=0.5, key=f"c4_{banca['id']}")
                        nota_final_calc = c1 + c2 + c3 + c4
                        notas_dit = {"Fundamentação": c1, "Metodologia": c2, "Arguição Oral": c3, "Tempo/Visual": c4, "Total da Banca": nota_final_calc}
                        
                    elif banca['modulo'] == "MCM IV":
                        st.markdown("##### 📝 Rubricas Detalhadas da Banca (Máx 30 pontos)")
                        c1 = st.slider("1. Conteúdo Escrito e Estruturação Estrutural (0 a 15):", 0.0, 15.0, 0.0, step=0.5, key=f"c1_{banca['id']}")
                        c2 = st.slider("2. Desempenho Oral, Síntese e Arguição Clínica (0 a 15):", 0.0, 15.0, 0.0, step=0.5, key=f"c2_{banca['id']}")
                        nota_final_calc = c1 + c2
                        notas_dit = {"Conteúdo Escrito": c1, "Defesa Oral": c2, "Total da Banca": nota_final_calc}
                        
                    else: # MCM V e PIEPE
                        st.markdown("##### 📝 Rubrica Completa de Avaliação (Máx 100 pontos)")
                        n_un = st.slider("Nota Global Avaliação Clínica:", 0.0, 100.0, 0.0, step=0.5, key=f"cun_{banca['id']}")
                        nota_final_calc = n_un
                        notas_dit = {"Nota Global": n_un, "Total da Banca": nota_final_calc}
                    
                    st.markdown(f"### 🧮 Total Somado: <span style='color:#800040;'>{nota_final_calc:.1f}</span>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                key_modal = f"modal_conf_{banca['id']}"
                if st.button("Finalizar Avaliação Oficial", key=f"btn_fin_{banca['id']}", use_container_width=True):
                    st.session_state[key_modal] = True; st.rerun()
                    
                if st.session_state.get(key_modal):
                    st.warning(f"Confirma o envio da nota oficial **{nota_final_calc:.1f}**?")
                    col_y, col_n = st.columns(2)
                    with col_y:
                        if st.button("✅ Sim, Enviar", key=f"yes_{banca['id']}", use_container_width=True):
                            role = "Avaliador 1" if meu_email == banca.get('avaliador_1_email') else ("Avaliador 2" if meu_email == banca.get('avaliador_2_email') else "Suplente")
                            st.session_state.bancos_avaliacoes[indice_real]['notas_lancadas'][role] = nota_final_calc
                            st.session_state.bancos_avaliacoes[indice_real]['notas_detalhadas'][meu_email] = notas_dit
                            st.session_state.bancos_avaliacoes[indice_real]['avaliadores_concluidos'].append(meu_email)
                            st.session_state[key_modal] = False
                            recarregar_com_sucesso("Avaliação computada com sucesso!")
                    with col_n:
                        if st.button("❌ Cancelar", key=f"no_{banca['id']}", use_container_width=True): st.session_state[key_modal] = False; st.rerun()

    elif aba_prof == "🗂️ Histórico de Avaliações":
        bancas_avaliadas = [b for b in st.session_state.bancos_avaliacoes if meu_email in b.get('avaliadores_concluidos', [])]
        if not bancas_avaliadas:
            st.info("Seu histórico de avaliações finalizadas aparecerá aqui.")
        for banca in bancas_avaliadas:
            with st.container(border=True):
                st.write(f"✅ **{banca['modulo']}** - {banca.get('titulo')} | Alunos: {', '.join(banca['alunos'])}")
                with st.expander("Ver Resumo da Rubrica Atribuída (Detalhado)"):
                    minhas_notas = banca.get('notas_detalhadas', {}).get(meu_email, {})
                    if not minhas_notas:
                        st.write("Detalhes não encontrados.")
                    for criterio, valor in minhas_notas.items():
                        if "Total" in criterio: st.markdown(f"<br><b>{criterio}: {valor:.1f}</b>", unsafe_allow_html=True)
                        else: st.write(f"🔹 {criterio}: {valor:.1f} pontos")

# ==========================================
# ROTEADOR DE TELAS
# ==========================================
if st.session_state.usuario_bancas is None: tela_login()
elif st.session_state.usuario_bancas["perfil"] == "Administrador": tela_administracao()
elif st.session_state.usuario_bancas["perfil"] == "Coordenação": tela_coordenacao()
elif st.session_state.usuario_bancas["perfil"] == "Professor": tela_professor()
