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
    .badge-tcci { background-color: #3498db; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; display: inline-block; }
    .badge-tccii { background-color: #2980b9; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; display: inline-block; }
    .badge-mcmiv { background-color: #2ecc71; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; display: inline-block; }
    .badge-mcmv { background-color: #27ae60; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; display: inline-block; }
    .badge-piepe { background-color: #e67e22; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; display: inline-block; }
    .status-orientacao { background-color: #f39c12; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .status-agendado { background-color: #800040; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .ata-ok { color: #27ae60; font-weight: bold; font-size: 13px; }
    .ata-pendente { color: #e74c3c; font-weight: bold; font-size: 13px; }
    .media-final { font-size: 15px; font-weight: bold; color: #800040; background-color: #f1f1f1; padding: 4px 8px; border-radius: 4px; }
    .zona-segura { background-color: #fafafa; border: 2px dashed #ddd; border-radius: 8px; padding: 15px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# 3. FUNÇÕES UTILITÁRIAS
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

def calcular_media_final(banca, nome_aluno=None):
    notas = banca.get("notas_lancadas", {})
    notas_banca = [v for k, v in notas.items() if k != "Orientador" and isinstance(v, (int, float))]
    media_banca = sum(notas_banca)/len(notas_banca) if notas_banca else 0
    
    if banca['modulo'] in ["MCM V", "PIEPE"]:
        return media_banca if notas_banca else None
        
    nota_ori = notas.get("Orientador", {})
    nota_aluno_ori = None
    if isinstance(nota_ori, dict) and nome_aluno:
        nota_aluno_ori = nota_ori.get(nome_aluno)
    elif isinstance(nota_ori, (int, float)):
        nota_aluno_ori = nota_ori
        
    if nota_aluno_ori is not None and notas_banca:
        return nota_aluno_ori + media_banca
    return None

ADMIN_EMAILS = ["wanessa.almeida@afya.com.br", "wanessa.salmeida@yahoo.com.br"]
lista_horarios_base = [time(h, 0) for h in range(8, 22)]
lista_salas_base = [f"APG {i:02d}" for i in range(1, 13)]
lista_semestres = ["2025.2", "2026.1", "2026.2", "2027.1", "2027.2", "2028.1", "2028.2"]

# 4. INICIALIZAÇÃO E BLINDAGEM DE MEMÓRIA
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
            "atas_mensais": {"Ata Mês 1": True, "Ata Mês 2": True, "Ata Mês 3": True, "Ata Mês 4": False},
            "conteudo_atas": {},
            "notas_lancadas": {"Orientador": {"Kamila Sousa Saraiva Fernandes": 38.0, "Jorge Kalil de Miranda Dias": 35.0}, "Avaliador 1": None, "Avaliador 2": 50.0, "Suplente": 55.0},
            "ata_assinada": False, "assinaturas_defesa": [],
            "avaliadores_concluidos": [], "notas_detalhadas": {}
        }
    ]

# Vacina contra chaves ausentes
for b in st.session_state.bancos_avaliacoes:
    if "avaliadores_concluidos" not in b: b["avaliadores_concluidos"] = []
    if "notas_detalhadas" not in b: b["notas_detalhadas"] = {}
    if "conteudo_atas" not in b: b["conteudo_atas"] = {}
    if "assinaturas_defesa" not in b: b["assinaturas_defesa"] = []
    novas_atas = {}
    for k, v in b.get("atas_mensais", {}).items():
        novo_k = k.replace("Mês ", "Ata Mês ") if "Ata" not in k else k
        novas_atas[novo_k] = v
    b["atas_mensais"] = novas_atas

if "permissoes_acesso" not in st.session_state:
    st.session_state.permissoes_acesso = {
        "brunna.costa@afya.com.br": {"perfil": "Professor", "modulos": []},
        "carlos.silva@afya.com.br": {"perfil": "Professor", "modulos": []}
    }

if "configuracoes" not in st.session_state: st.session_state.configuracoes = {"agendamento_aberto": False, "disponibilidade_por_modulo": {}}
for mod in ["TCC I", "TCC II", "MCM IV", "MCM V", "PIEPE"]:
    if mod not in st.session_state.configuracoes["disponibilidade_por_modulo"]:
        st.session_state.configuracoes["disponibilidade_por_modulo"][mod] = {
            "salas": lista_salas_base.copy(), "horarios": [t.strftime('%H:%M') for t in lista_horarios_base],
            "agend_ini": datetime.now().date(), "agend_fim": datetime.now().date() + timedelta(days=7),
            "notas_ini": datetime.now().date(), "notas_fim": datetime.now().date() + timedelta(days=30)
        }

if "usar_data_fixada_modulo" not in st.session_state: st.session_state.usar_data_fixada_modulo = {}
if "data_fixada_modulo" not in st.session_state: st.session_state.data_fixada_modulo = {}
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
                    
                    config_mod = st.session_state.configuracoes["disponibilidade_por_modulo"].get(modulo_selecionado, {})
                    salas_filtradas = ["A definir"] + config_mod.get("salas", lista_salas_base)
                    horarios_filtrados = config_mod.get("horarios", [t.strftime('%H:%M') for t in lista_horarios_base])
                    
                    if is_completo:
                        data_banca = st.date_input("Data da Defesa:", format="DD/MM/YYYY")
                        titulo = st.text_input("Título do Trabalho:")
                        if modulo_selecionado == "PIEPE":
                            formato_piepe = st.radio("Formato PIEPE:", ["Slide", "Banner"], horizontal=True)
                            col_ph, col_ps = st.columns(2)
                            with col_ph: horario_banca = st.selectbox("Horário:", lista_horarios_base, format_func=lambda t: t.strftime('%H:%M')) if not horarios_filtrados else st.selectbox("Horário:", [time(int(h.split(':')[0]), 0) for h in horarios_filtrados], format_func=lambda t: t.strftime('%H:%M'))
                            with col_ps: sala_banca = st.selectbox("Sala:", salas_filtradas)
                        else:
                            col_hr, col_sl = st.columns(2)
                            with col_hr: horario_banca = st.selectbox("Horário de Início:", lista_horarios_base, format_func=lambda t: t.strftime('%H:%M')) if not horarios_filtrados else st.selectbox("Horário de Início:", [time(int(h.split(':')[0]), 0) for h in horarios_filtrados], format_func=lambda t: t.strftime('%H:%M'))
                            with col_sl: sala_banca = st.selectbox("Sala:", salas_filtradas)

                    st.write("**Orientação**")
                    col_o1, col_o2 = st.columns(2)
                    with col_o1: o_nome = st.text_input("Nome Completo do Orientador:")
                    with col_o2: o_email = st.text_input("E-mail do Orientador (@afya):").lower().strip()
                    with st.expander("➕ Adicionar Co-orientador (Opcional)"):
                        col_co1, col_co2 = st.columns(2)
                        with col_co1: co_nome = st.text_input("Nome Co-orientador:")
                        with col_co2: co_email = st.text_input("E-mail Co-orientador:").lower().strip()
                    
                    if is_completo:
                        st.markdown("---")
                        st.write("**Membros da Banca Avaliadora**")
                        col_line1_l, col_line1_r = st.columns(2)
                        with col_line1_l: b1_nome = st.text_input("Nome Completo Titular 1:")
                        with col_line1_r: b1_email = st.text_input("E-mail Titular 1:").lower().strip()
                        
                        col_line2_l, col_line2_r = st.columns(2)
                        with col_line2_l: b2_nome = st.text_input("Nome Completo Titular 2:")
                        with col_line2_r: b2_email = st.text_input("E-mail Titular 2:").lower().strip()

                        if modulo_selecionado in ["TCC II", "MCM V"]:
                            st.write("**Membro Suplente (Obrigatório para TCC II e MCM V)**")
                            col_sup_l, col_sup_r = st.columns(2)
                            with col_sup_l: bs_nome = st.text_input("Nome Completo Suplente:")
                            with col_sup_r: bs_email = st.text_input("E-mail Suplente:").lower().strip()
                            
                    lista_alunos = st.text_area("Integrantes do Grupo (um por linha):", height=100)
                    
                    if st.form_submit_button("Salvar Registro Oficial"):
                        if not o_nome or not o_email or not lista_alunos: st.error("Orientador e Alunos são obrigatórios.")
                        else:
                            hora_str = horario_banca.strftime("%H:%M") if (is_completo and horario_banca) else "N/A"
                            status_banca = "Aguardando Avaliação" if is_completo else "Em Orientação"
                            nova_banca = {
                                "id": str(uuid.uuid4())[:8], "modulo": modulo_selecionado, "semestre": semestre_selecionado, "formato_piepe": formato_piepe,
                                "data": formatar_data_br(data_banca) if data_banca else "A definir", "horario": hora_str, "sala": sala_banca, "titulo": titulo,
                                "orientador_email": o_email, "orientador_nome": o_nome, "coorientador_email": co_email, "coorientador_nome": co_nome,
                                "avaliador_1_email": b1_email, "avaliador_1_nome": b1_nome, "avaliador_2_email": b2_email, "avaliador_2_nome": b2_nome,
                                "avaliador_sup_email": bs_email, "avaliador_sup_nome": bs_nome,
                                "alunos": [n.strip() for n in lista_alunos.split('\n') if n.strip()], "status": status_banca, 
                                "atas_mensais": {"Ata Mês 1": False, "Ata Mês 2": False, "Ata Mês 3": False, "Ata Mês 4": False}, "conteudo_atas": {},
                                "notas_lancadas": {"Orientador": {}, "Avaliador 1": None, "Avaliador 2": None, "Suplente": None},
                                "ata_assinada": False, "assinaturas_defesa": [], "avaliadores_concluidos": [], "notas_detalhadas": {}
                            }
                            st.session_state.bancos_avaliacoes.append(nova_banca)
                            liberar_acesso_professor(o_email, "Professor")
                            if b1_email: liberar_acesso_professor(b1_email, "Professor")
                            if b2_email: liberar_acesso_professor(b2_email, "Professor")
                            st.session_state.versao_formulario += 1
                            recarregar_com_sucesso("✅ Grupo cadastrado com sucesso!")

    elif aba_ativa == "📋 Gestão e Edição":
        col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
        with col_f1: filtro_gestao_mod = st.selectbox("🔍 Módulo:", ["Todos"] + st.session_state.usuario_bancas["modulos"], key="gestao_mod")
        with col_f2: filtro_gestao_sem = st.selectbox("📅 Semestre:", ["Todos"] + lista_semestres, key="gestao_sem")
        with col_f3:
            agendamento = st.toggle("🔓 Permitir Agendamento de Defesa (Professores)", value=st.session_state.configuracoes["agendamento_aberto"], key="gestao_tgg")
            st.session_state.configuracoes["agendamento_aberto"] = agendamento

        bancas_filtradas_gestao = [b for b in st.session_state.bancos_avaliacoes if (filtro_gestao_mod == "Todos" or b['modulo'] == filtro_gestao_mod) and (filtro_gestao_sem == "Todos" or b.get('semestre') == filtro_gestao_sem)]
        if not bancas_filtradas_gestao: 
            st.warning("Não existem grupos cadastrados para este semestre/módulo.")
        else:
            for banca in reversed(bancas_filtradas_gestao):
                indice_real = next((i for i, d in enumerate(st.session_state.bancos_avaliacoes) if d["id"] == banca["id"]), None)
                classe_cor = obter_classe_cor(banca['modulo'])
                classe_st = "status-agendado" if banca['status'] in ["Aguardando Avaliação", "Avaliada"] else "status-orientacao"
                
                hora_str = f" às {banca.get('horario')}" if banca.get('horario') and banca.get('horario') != "N/A" else ""
                sala_str = f" | Sala: {banca.get('sala', 'A definir')}" if banca.get('sala') else ""
                info_extras = f"{banca.get('semestre', 'N/A')} | {banca['data']}{hora_str}{sala_str}"
                
                ori_str = f"{banca['orientador_nome']}"
                if banca.get('coorientador_nome'): ori_str += f" | <b>Co:</b> {banca['coorientador_nome']}"
                av_str = "<i>A definir</i>" if not banca.get('avaliador_1_nome') else f"{banca['avaliador_1_nome']} | {banca.get('avaliador_2_nome', '')}"
                if banca.get('avaliador_sup_nome'): av_str += f" | {banca['avaliador_sup_nome']} (Sup)"
                
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
                        if st.button("✏️ Editar/Atribuir Banca", key=f"btn_{edit_key}", use_container_width=True):
                            st.session_state[edit_key] = not st.session_state[edit_key]; st.rerun()
                    with col_b2:
                        if st.button("🗑️ Excluir", key=f"del_{banca['id']}", use_container_width=True):
                            st.session_state.bancos_avaliacoes.pop(indice_real); recarregar_com_sucesso("Banca excluída!")
                    with col_b3:
                        novo_mod = "TCC II" if banca['modulo'] == "TCC I" else ("MCM V" if banca['modulo'] == "MCM IV" else banca['modulo'])
                        if novo_mod != banca['modulo']:
                            if st.button(f"🔄 Migrar p/ {novo_mod}", key=f"mig_{banca['id']}", use_container_width=True):
                                curr_sem = banca.get('semestre', '2026.1')
                                try:
                                    idx_sem = lista_semestres.index(curr_sem)
                                    novo_sem = lista_semestres[idx_sem + 1] if idx_sem + 1 < len(lista_semestres) else curr_sem
                                except: novo_sem = curr_sem
                                
                                b_copy = banca.copy()
                                b_copy.update({"id": str(uuid.uuid4())[:8], "modulo": novo_mod, "semestre": novo_sem, "status": "Em Orientação", "avaliadores_concluidos": [], "notas_detalhadas": {}, "assinaturas_defesa": []})
                                st.session_state.bancos_avaliacoes.append(b_copy); recarregar_com_sucesso(f"Migrado para {novo_mod} ({novo_sem})!")
                    
                    if st.session_state[edit_key]:
                        st.markdown("---")
                        with st.form(key=f"form_ed_real_{banca['id']}", clear_on_submit=False):
                            try: data_obj = datetime.strptime(banca['data'], "%d/%m/%Y").date() if banca['data'] != "A definir" else datetime.now().date()
                            except: data_obj = datetime.now().date()
                            try:
                                h, m = map(int, banca.get('horario', '08:00').split(':'))
                                hora_obj = time(h, m) if time(h,m) in lista_horarios_base else time(8, 0)
                            except: hora_obj = time(8, 0)
                            
                            col_e1, col_e2, col_e3, col_e4 = st.columns(4)
                            with col_e1: edit_semestre = st.selectbox("Semestre:", lista_semestres, index=lista_semestres.index(banca.get('semestre', '2026.1')) if banca.get('semestre') in lista_semestres else 0)
                            with col_e2: edit_data = st.date_input("Data da Defesa:", value=data_obj, format="DD/MM/YYYY")
                            with col_e3: edit_hora = st.selectbox("Horário:", lista_horarios_base, index=lista_horarios_base.index(hora_obj) if hora_obj in lista_horarios_base else 0, format_func=lambda t: t.strftime('%H:%M'))
                            with col_e4: edit_sala = st.selectbox("Sala:", ["A definir"] + lista_salas_base, index=(["A definir"] + lista_salas_base).index(banca.get('sala', 'A definir')) if banca.get('sala') in ["A definir"] + lista_salas_base else 0)
                            
                            edit_titulo = st.text_input("Título do Trabalho:", value=banca.get('titulo', ''))
                            
                            edit_formato = banca.get('formato_piepe')
                            if banca['modulo'] == "PIEPE":
                                edit_formato = st.radio("Formato PIEPE:", ["Slide", "Banner"], index=0 if banca.get('formato_piepe') == 'Slide' else 1, horizontal=True)
                            
                            st.write("**Orientação e Avaliadores (Você pode adicionar ou remover)**")
                            col_eo1, col_eo2 = st.columns(2)
                            with col_eo1: e_on = st.text_input("Nome Orientador:", value=banca.get('orientador_nome',''))
                            with col_eo2: e_oe = st.text_input("Email Orientador:", value=banca.get('orientador_email',''))
                            
                            col_ec1, col_ec2 = st.columns(2)
                            with col_ec1: e_con = st.text_input("Nome Coorientador:", value=banca.get('coorientador_nome',''))
                            with col_ec2: e_coe = st.text_input("Email Coorientador:", value=banca.get('coorientador_email',''))
                            
                            col_eb1, col_eb2 = st.columns(2)
                            with col_eb1: e_b1n = st.text_input("Nome Titular 1:", value=banca.get('avaliador_1_nome',''))
                            with col_eb2: e_b1e = st.text_input("Email Titular 1:", value=banca.get('avaliador_1_email',''))
                            
                            col_eb3, col_eb4 = st.columns(2)
                            with col_eb3: e_b2n = st.text_input("Nome Titular 2:", value=banca.get('avaliador_2_nome',''))
                            with col_eb4: e_b2e = st.text_input("Email Titular 2:", value=banca.get('avaliador_2_email',''))
                            
                            if banca['modulo'] in ["TCC II", "MCM V"]:
                                col_es1, col_es2 = st.columns(2)
                                with col_es1: e_bsn = st.text_input("Nome Suplente:", value=banca.get('avaliador_sup_nome',''))
                                with col_es2: e_bse = st.text_input("Email Suplente:", value=banca.get('avaliador_sup_email',''))
                            else:
                                e_bsn, e_bse = "", ""

                            edit_alunos = st.text_area("Alunos (um por linha):", value="\n".join(banca.get('alunos', [])), height=100)
                            
                            col_actions1, col_actions2 = st.columns(2)
                            with col_actions1: salvar_alt = st.form_submit_button("💾 Salvar Alterações Completas", use_container_width=True)
                            with col_actions2: cancelar_alt = st.form_submit_button("❌ Cancelar", use_container_width=True)
                            if cancelar_alt: st.session_state[edit_key] = False; st.rerun()
                            if salvar_alt:
                                h_str = edit_hora.strftime("%H:%M")
                                novo_status = "Aguardando Avaliação" if (e_b1e and e_b2e) else "Em Orientação"
                                st.session_state.bancos_avaliacoes[indice_real].update({
                                    "semestre": edit_semestre, "data": formatar_data_br(edit_data), "horario": h_str, "sala": edit_sala, "titulo": edit_titulo, "status": novo_status, "formato_piepe": edit_formato,
                                    "orientador_nome": e_on, "orientador_email": e_oe, "coorientador_nome": e_con, "coorientador_email": e_coe,
                                    "avaliador_1_nome": e_b1n, "avaliador_1_email": e_b1e, "avaliador_2_nome": e_b2n, "avaliador_2_email": e_b2e,
                                    "avaliador_sup_nome": e_bsn, "avaliador_sup_email": e_bse,
                                    "alunos": [n.strip() for n in edit_alunos.split('\n') if n.strip()]
                                })
                                if e_oe: liberar_acesso_professor(e_oe, "Professor")
                                if e_b1e: liberar_acesso_professor(e_b1e, "Professor")
                                if e_b2e: liberar_acesso_professor(e_b2e, "Professor")
                                st.session_state[edit_key] = False; recarregar_com_sucesso("Grupo atualizado com membros e horários!")

    elif aba_ativa == "📊 Monitoramento":
        col_m1, col_m2 = st.columns(2)
        with col_m1: filtro_mod_mon = st.selectbox("🔍 Módulo:", ["Todos"] + st.session_state.usuario_bancas["modulos"], key="mon_mod")
        with col_m2: filtro_sem_mon = st.selectbox("📅 Semestre:", ["Todos"] + lista_semestres, key="mon_sem")
        bancas_monitoramento = [b for b in st.session_state.bancos_avaliacoes if (filtro_mod_mon == "Todos" or b['modulo'] == filtro_mod_mon) and (filtro_sem_mon == "Todos" or b.get('semestre') == filtro_sem_mon)]
        
        if not bancas_monitoramento: 
            st.warning("Não existem grupos cadastrados para este semestre/módulo.")
        else:
            for banca in bancas_monitoramento:
                media_geral = calcular_media_final(banca)
                atas = banca.get("atas_mensais", {})
                classe_cor = obter_classe_cor(banca['modulo'])
                
                with st.container(border=True):
                    # Cabeçalho Colorido do Monitoramento
                    st.markdown(f"""
                    <div style='margin-bottom: 10px;'>
                        <span class='{classe_cor}'>{banca['modulo']} ({banca.get('semestre')})</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"#### 👤 Orientador(a): {banca.get('orientador_nome', 'N/A')}")
                    st.markdown(f"**Projeto:** {banca.get('titulo') if banca.get('titulo') else 'Trabalho Sem Título'}")
                    st.markdown(f"**Alunos:** {', '.join(banca.get('alunos', []))}")
                    
                    if banca['modulo'] != "PIEPE":
                        st.markdown("---")
                        st.write("**Atas de Reunião Mensal:**")
                        col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                        with col_a1: st.markdown(f"M1: {'✅' if atas.get('Ata Mês 1') else '❌'}"); st.download_button("📥 PDF M1", "Mock PDF", key=f"dm1_{banca['id']}", use_container_width=True)
                        with col_a2: st.markdown(f"M2: {'✅' if atas.get('Ata Mês 2') else '❌'}"); st.download_button("📥 PDF M2", "Mock PDF", key=f"dm2_{banca['id']}", use_container_width=True)
                        with col_a3: st.markdown(f"M3: {'✅' if atas.get('Ata Mês 3') else '❌'}"); st.download_button("📥 PDF M3", "Mock PDF", key=f"dm3_{banca['id']}", use_container_width=True)
                        with col_a4: st.markdown(f"M4: {'✅' if atas.get('Ata Mês 4') else '❌'}"); st.download_button("📥 PDF M4", "Mock PDF", key=f"dm4_{banca['id']}", use_container_width=True)
                    
                    st.markdown("---")
                    notas = banca.get("notas_lancadas", {})
                    col_n1, col_n2, col_n3, col_n4 = st.columns(4)
                    
                    if banca['modulo'] not in ["MCM V", "PIEPE"]:
                        with col_n1: 
                            ori_status = "✅ Lançada" if isinstance(notas.get("Orientador"), dict) and notas.get("Orientador") else ("✅ "+str(notas.get("Orientador")) if notas.get("Orientador") else "❌")
                            st.markdown(f"<div class='{'ata-ok' if notas.get('Orientador') else 'ata-pendente'}'>Orientador: {ori_status}</div>", unsafe_allow_html=True)
                    with col_n2: 
                        st.markdown(f"<div class='{'ata-ok' if notas.get('Avaliador 1') is not None else 'ata-pendente'}'>Avaliador 1: {'✅ ('+str(notas.get('Avaliador 1'))+')' if notas.get('Avaliador 1') is not None else '❌'}</div>", unsafe_allow_html=True)
                    with col_n3: 
                        st.markdown(f"<div class='{'ata-ok' if notas.get('Avaliador 2') is not None else 'ata-pendente'}'>Avaliador 2: {'✅ ('+str(notas.get('Avaliador 2'))+')' if notas.get('Avaliador 2') is not None else '❌'}</div>", unsafe_allow_html=True)
                    
                    st.write(f"**Média Banca (Avaliadores):** {f'{media_geral:.1f}' if media_geral is not None else 'Pendente'}")
                    
                    if banca['modulo'] in ["TCC II", "MCM V"]:
                        assinaturas = banca.get("assinaturas_defesa", [])
                        qtd_necessaria = len([e for e in [banca.get('orientador_email'), banca.get('avaliador_1_email'), banca.get('avaliador_2_email'), banca.get('avaliador_sup_email')] if e])
                        st.write(f"**Assinaturas da Ata de Defesa:** {len(assinaturas)} de {qtd_necessaria} assinadas.")
                    
                    st.download_button("📥 Baixar Ata de Defesa (PDF)", "Mock Ata Defesa", key=f"d_def_{banca['id']}")

    elif aba_ativa == "📈 Diário de Notas":
        col_m1, col_m2 = st.columns(2)
        with col_m1: filtro_mod_dia = st.selectbox("🔍 Módulo:", ["Todos"] + st.session_state.usuario_bancas["modulos"], key="dia_mod")
        with col_m2: filtro_sem_dia = st.selectbox("📅 Semestre:", ["Todos"] + lista_semestres, key="dia_sem")
        st.markdown("---")

        bancas_diario = [b for b in st.session_state.bancos_avaliacoes if (filtro_mod_dia == "Todos" or b['modulo'] == filtro_mod_dia) and (filtro_sem_dia == "Todos" or b.get('semestre') == filtro_sem_dia)]
        if not bancas_diario:
            st.warning("Não existem grupos cadastrados para este semestre/módulo.")
        else:
            lista_alunos_notas = []
            for b in bancas_diario:
                for aluno in b.get("alunos", []):
                    media_calc = calcular_media_final(b, aluno)
                    media_str = f"{media_calc:.1f}" if media_calc is not None else "Pendente"
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
                        worksheet.column_dimensions[chr(65 + idx)].width = min(max_len, 45)
                st.download_button("📥 Baixar Diário de Notas (.xlsx)", data=buffer_notas.getvalue(), file_name=f"Diario_Notas_{filtro_mod_dia}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ==========================================
# PAINEL DO PROFESSOR 
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
                
                with st.expander("📅 Ver Controle e Formulários de Atas Mensais"):
                    atas = banca.get("atas_mensais", {"Ata Mês 1": False, "Ata Mês 2": False, "Ata Mês 3": False, "Ata Mês 4": False})
                    cont_atas = banca.get("conteudo_atas", {})
                    
                    for mes in ["Ata Mês 1", "Ata Mês 2", "Ata Mês 3", "Ata Mês 4"]:
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.markdown(f"**{mes}**: {'✅ Concluída' if atas.get(mes) else '❌ Pendente'}")
                        with col2:
                            with st.popover(f"📝 Preencher {mes}"):
                                with st.form(key=f"form_ata_{mes}_{banca['id']}"):
                                    st.write(f"**Reunião - {mes}**")
                                    dt_reuniao = st.date_input("Data da Reunião:")
                                    resumo = st.text_area("Resumo das atividades discutidas:", value=cont_atas.get(mes, {}).get('resumo', ''))
                                    encaminha = st.text_area("Encaminhamentos definidos:", value=cont_atas.get(mes, {}).get('encaminha', ''))
                                    resp = st.multiselect("Responsáveis por cada tarefa:", banca.get('alunos', []))
                                    prox_dt = st.date_input("Data da próxima reunião:")
                                    assinado = st.checkbox("Assinar eletronicamente esta Ata")
                                    
                                    if st.form_submit_button("Salvar Ata"):
                                        if not assinado: st.error("Marque a assinatura eletrônica.")
                                        else:
                                            st.session_state.bancos_avaliacoes[indice_real]['conteudo_atas'][mes] = {'resumo': resumo, 'encaminha': encaminha, 'resp': resp}
                                            st.session_state.bancos_avaliacoes[indice_real]['atas_mensais'][mes] = True
                                            recarregar_com_sucesso(f"{mes} salva com sucesso!")

                if banca['modulo'] not in ["MCM V", "PIEPE"]:
                    st.markdown("---")
                    st.write("**Rubrica de Avaliação do Orientador**")
                    notas_existentes = banca['notas_lancadas'].get('Orientador', {})
                    if not isinstance(notas_existentes, dict): notas_existentes = {}
                    
                    pendentes = [a for a in banca.get('alunos', []) if a not in notas_existentes]
                    
                    if not pendentes:
                        st.success("✅ Todos os alunos deste grupo já foram avaliados pelo Orientador.")
                    else:
                        mesma_nota = st.checkbox("Atribuir a mesma nota para os alunos pendentes", value=True, key=f"msm_{banca['id']}")
                        if mesma_nota:
                            st.write("*Avaliação Geral (Aplica-se aos pendentes)*")
                            if banca['modulo'] in ["TCC I", "TCC II"]:
                                o1 = st.slider("Envolvimento e Responsabilidade (0 a 10):", 0.0, 10.0, 0.0, step=0.5, key=f"o1_g_{banca['id']}", help="Participação proativa e responsabilidade no processo.")
                                o2 = st.slider("Relação com Orientador/Diálogo (0 a 10):", 0.0, 10.0, 0.0, step=0.5, key=f"o2_g_{banca['id']}", help="Relação colaborativa, abertura ao diálogo e sugestões.")
                                o3 = st.slider("Desempenho e Tarefas (0 a 8):", 0.0, 8.0, 0.0, step=0.5, key=f"o3_g_{banca['id']}", help="Competência nas atividades.")
                                o4 = st.slider("Pontualidade e Compromisso (0 a 6):", 0.0, 6.0, 0.0, step=0.5, key=f"o4_g_{banca['id']}", help="Compromisso com prazos.")
                                o5 = st.slider("Resp. com Aprendizagem (0 a 6):", 0.0, 6.0, 0.0, step=0.5, key=f"o5_g_{banca['id']}", help="Busca ativa por aprendizado e aprimoramento.")
                                nota_ori = o1 + o2 + o3 + o4 + o5
                            else: # MCM IV (Máx 70)
                                o1 = st.slider("Envolvimento e Responsabilidade (0 a 14):", 0.0, 14.0, 0.0, step=0.5, key=f"o1_g_{banca['id']}")
                                o2 = st.slider("Relação com Orientador/Diálogo (0 a 14):", 0.0, 14.0, 0.0, step=0.5, key=f"o2_g_{banca['id']}")
                                o3 = st.slider("Desempenho e Tarefas (0 a 14):", 0.0, 14.0, 0.0, step=0.5, key=f"o3_g_{banca['id']}")
                                o4 = st.slider("Pontualidade e Compromisso (0 a 14):", 0.0, 14.0, 0.0, step=0.5, key=f"o4_g_{banca['id']}")
                                o5 = st.slider("Resp. com Aprendizagem (0 a 14):", 0.0, 14.0, 0.0, step=0.5, key=f"o5_g_{banca['id']}")
                                nota_ori = o1 + o2 + o3 + o4 + o5
                                
                            st.write(f"**Total a ser atribuído:** {nota_ori:.1f}")
                            if st.button("Salvar Nota para Pendentes", key=f"s_no_g_{banca['id']}"):
                                for a in pendentes: notas_existentes[a] = nota_ori
                                st.session_state.bancos_avaliacoes[indice_real]['notas_lancadas']['Orientador'] = notas_existentes
                                recarregar_com_sucesso("Notas aplicadas com sucesso! Alunos avaliados.")
                        else:
                            st.write("*Avaliação Individual (Apenas Pendentes)*")
                            tabs_alunos = st.tabs(pendentes)
                            for idx_aluno, aluno in enumerate(pendentes):
                                with tabs_alunos[idx_aluno]:
                                    if banca['modulo'] in ["TCC I", "TCC II"]:
                                        o1 = st.slider("Envolvimento (0-10):", 0.0, 10.0, 0.0, step=0.5, key=f"o1_{idx_aluno}_{banca['id']}")
                                        o2 = st.slider("Diálogo (0-10):", 0.0, 10.0, 0.0, step=0.5, key=f"o2_{idx_aluno}_{banca['id']}")
                                        o3 = st.slider("Tarefas (0-8):", 0.0, 8.0, 0.0, step=0.5, key=f"o3_{idx_aluno}_{banca['id']}")
                                        o4 = st.slider("Pontualidade (0-6):", 0.0, 6.0, 0.0, step=0.5, key=f"o4_{idx_aluno}_{banca['id']}")
                                        o5 = st.slider("Aprendizagem (0-6):", 0.0, 6.0, 0.0, step=0.5, key=f"o5_{idx_aluno}_{banca['id']}")
                                        nota_ind = o1 + o2 + o3 + o4 + o5
                                    else:
                                        o1 = st.slider("Envolvimento (0-14):", 0.0, 14.0, 0.0, step=0.5, key=f"o1_{idx_aluno}_{banca['id']}")
                                        o2 = st.slider("Diálogo (0-14):", 0.0, 14.0, 0.0, step=0.5, key=f"o2_{idx_aluno}_{banca['id']}")
                                        o3 = st.slider("Tarefas (0-14):", 0.0, 14.0, 0.0, step=0.5, key=f"o3_{idx_aluno}_{banca['id']}")
                                        o4 = st.slider("Pontualidade (0-14):", 0.0, 14.0, 0.0, step=0.5, key=f"o4_{idx_aluno}_{banca['id']}")
                                        o5 = st.slider("Aprendizagem (0-14):", 0.0, 14.0, 0.0, step=0.5, key=f"o5_{idx_aluno}_{banca['id']}")
                                        nota_ind = o1 + o2 + o3 + o4 + o5
                                    
                                    st.write(f"**Total Individual:** {nota_ind:.1f}")
                                    if st.button(f"Salvar Nota de {aluno}", key=f"s_ind_{idx_aluno}_{banca['id']}"):
                                        notas_existentes[aluno] = nota_ind
                                        st.session_state.bancos_avaliacoes[indice_real]['notas_lancadas']['Orientador'] = notas_existentes
                                        recarregar_com_sucesso(f"Nota de {aluno} salva com sucesso! O aluno foi movido para os avaliados.")
                
                # Assinatura de Ata de Defesa pelo Orientador (Se TCC II / MCM V)
                if banca['modulo'] in ["TCC II", "MCM V"] and meu_email not in banca.get("assinaturas_defesa", []):
                    st.markdown("---")
                    if st.button("✍️ Assinar Ata de Defesa Eletronicamente (Orientador)", key=f"assina_ori_{banca['id']}", use_container_width=True):
                        st.session_state.bancos_avaliacoes[indice_real]['assinaturas_defesa'].append(meu_email)
                        recarregar_com_sucesso("Assinatura eletrônica computada na Ata de Defesa!")

    elif aba_prof == "🎓 Bancas Pendentes":
        bancas_pendentes = [b for b in st.session_state.bancos_avaliacoes if meu_email in [b.get('avaliador_1_email'), b.get('avaliador_2_email'), b.get('avaliador_sup_email')] and meu_email not in b.get('avaliadores_concluidos', [])]
        
        if not bancas_pendentes: st.success("🎉 Você não tem bancas pendentes de avaliação no momento.")
        else:
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
                        with st.container(height=450, border=True):
                            st.markdown("<div class='zona-segura'>", unsafe_allow_html=True)
                            nota_final_calc = 0.0
                            zeros = False
                            
                            if banca['modulo'] == "TCC I":
                                st.markdown("##### 📝 Parte Escrita - Projeto (Máx 30 pontos)")
                                c1 = st.slider("1. Problema e Justificativa (0 a 7.5):", 0.0, 7.5, 0.0, step=0.5, key=f"c1_{banca['id']}", help="Problema claramente formulado, justificativa altamente persuasiva e relevante.")
                                c2 = st.slider("2. Objetivos e Hipóteses (0 a 6.0):", 0.0, 6.0, 0.0, step=0.5, key=f"c2_{banca['id']}", help="Objetivos bem formulados e alinhados, e hipóteses pertinentes.")
                                c3 = st.slider("3. Revisão de Literatura (0 a 6.0):", 0.0, 6.0, 0.0, step=0.5, key=f"c3_{banca['id']}", help="Abrangente, crítica e identifica claramente a relevância na literatura existente.")
                                c4 = st.slider("4. Metodologia (0 a 6.0):", 0.0, 6.0, 0.0, step=0.5, key=f"c4_{banca['id']}", help="Detalhada e abrangente, compreensão completa dos procedimentos.")
                                c5 = st.slider("5. Ética e Viabilidade (0 a 4.5):", 0.0, 4.5, 0.0, step=0.5, key=f"c5_{banca['id']}", help="Considerações éticas apropriadas e viabilidade do estudo abordada.")
                                n_escrita = c1+c2+c3+c4+c5
                                
                                st.markdown("##### 🗣️ Apresentação Oral (Máx 30 pontos)")
                                o1 = st.slider("Domínio do Tema e Clareza (0 a 10):", 0.0, 10.0, 0.0, step=0.5, key=f"o1_{banca['id']}", help="Segurança na exposição do conteúdo.")
                                o2 = st.slider("Capacidade de Síntese e Tempo (0 a 10):", 0.0, 10.0, 0.0, step=0.5, key=f"o2_{banca['id']}", help="Uso adequado do tempo e recursos visuais.")
                                o3 = st.slider("Arguição e Defesa (0 a 10):", 0.0, 10.0, 0.0, step=0.5, key=f"o3_{banca['id']}", help="Coerência e consistência nas respostas à banca.")
                                n_oral = o1+o2+o3
                                
                                nota_final_calc = n_escrita + n_oral
                                notas_dit = {"Problema/Justif": c1, "Objetivos": c2, "Revisão": c3, "Metodologia": c4, "Ética/Viabilidade": c5, "Domínio Oral": o1, "Síntese/Tempo": o2, "Arguição": o3, "Total da Banca": nota_final_calc}
                                if any(v == 0 for v in [c1, c2, c3, c4, c5, o1, o2, o3]): zeros = True
                                
                            elif banca['modulo'] == "TCC II":
                                st.markdown("##### 📝 Parte Escrita - Artigo (Máx 30 pontos)")
                                c1 = st.slider("1. Estruturação e Escrita Científica (0 a 7.5):", 0.0, 7.5, 0.0, step=0.5, key=f"c1_{banca['id']}", help="Estrutura organizada, linguagem fluida, concisão e excelência na redação.")
                                c2 = st.slider("2. Fundamentação Teórica (0 a 6.0):", 0.0, 6.0, 0.0, step=0.5, key=f"c2_{banca['id']}", help="Crítica, bem estruturada e com autores atuais e pertinentes.")
                                c3 = st.slider("3. Apresentação/Discussão de Resultados (0 a 6.0):", 0.0, 6.0, 0.0, step=0.5, key=f"c3_{banca['id']}", help="Resultados claros, discussão crítica e integração aos achados da literatura.")
                                c4 = st.slider("4. Rigor Metodológico (0 a 6.0):", 0.0, 6.0, 0.0, step=0.5, key=f"c4_{banca['id']}", help="Métodos bem descritos, compatíveis com os objetivos do estudo.")
                                c5 = st.slider("5. Conclusão e Relevância (0 a 4.5):", 0.0, 4.5, 0.0, step=0.5, key=f"c5_{banca['id']}", help="Conclusão clara, alinhada aos objetivos e destaque à relevância.")
                                n_escrita = c1+c2+c3+c4+c5
                                
                                st.markdown("##### 🗣️ Apresentação Oral (Máx 30 pontos)")
                                o1 = st.slider("Domínio do Tema e Clareza (0 a 10):", 0.0, 10.0, 0.0, step=0.5, key=f"o1_{banca['id']}", help="Segurança na exposição do conteúdo.")
                                o2 = st.slider("Capacidade de Síntese e Tempo (0 a 10):", 0.0, 10.0, 0.0, step=0.5, key=f"o2_{banca['id']}", help="Uso adequado do tempo e recursos visuais.")
                                o3 = st.slider("Arguição e Defesa (0 a 10):", 0.0, 10.0, 0.0, step=0.5, key=f"o3_{banca['id']}", help="Coerência e consistência nas respostas à banca.")
                                n_oral = o1+o2+o3
                                
                                nota_final_calc = n_escrita + n_oral
                                notas_dit = {"Estrutura/Escrita": c1, "Fundamentação": c2, "Resultados": c3, "Rigor Metodológico": c4, "Conclusão/Relevância": c5, "Domínio Oral": o1, "Síntese/Tempo": o2, "Arguição": o3, "Total da Banca": nota_final_calc}
                                if any(v == 0 for v in [c1, c2, c3, c4, c5, o1, o2, o3]): zeros = True

                            elif banca['modulo'] == "MCM IV":
                                st.markdown("##### 📝 Avaliação Global do Projeto MCM IV (Máx 30 pontos)")
                                c1 = st.slider("1. Justificativa do Estudo (0 a 6):", 0.0, 6.0, 0.0, step=0.5, key=f"m4_1_{banca['id']}", help="Apresenta clareza e relevância científica/social.")
                                c2 = st.slider("2. Objetivos (Geral e Específicos) (0 a 6):", 0.0, 6.0, 0.0, step=0.5, key=f"m4_2_{banca['id']}", help="Objetivo geral claro e específicos bem formulados.")
                                c3 = st.slider("3. Fundamentação Teórica (0 a 6):", 0.0, 6.0, 0.0, step=0.5, key=f"m4_3_{banca['id']}", help="Referencial teórico relevante, atualizado (5 anos) e articulado.")
                                c4 = st.slider("4. Metodologia Proposta (0 a 6):", 0.0, 6.0, 0.0, step=0.5, key=f"m4_4_{banca['id']}", help="Método bem descrito e adequado aos objetivos.")
                                c5 = st.slider("5. Cronograma (0 a 3):", 0.0, 3.0, 0.0, step=0.5, key=f"m4_5_{banca['id']}", help="Cronograma bem estruturado e prazos viáveis.")
                                c6 = st.slider("6. Estrutura, Linguagem e Formatação (0 a 3):", 0.0, 3.0, 0.0, step=0.5, key=f"m4_6_{banca['id']}", help="Texto bem escrito e segue normas ABNT/Vancouver.")
                                nota_final_calc = c1+c2+c3+c4+c5+c6
                                notas_dit = {"Justificativa": c1, "Objetivos": c2, "Fundamentação": c3, "Metodologia": c4, "Cronograma": c5, "Estrutura/Normas": c6, "Total da Banca": nota_final_calc}
                                if any(v == 0 for v in [c1, c2, c3, c4, c5, c6]): zeros = True

                            elif banca['modulo'] == "PIEPE":
                                formato = banca.get('formato_piepe', 'Slide')
                                st.markdown(f"##### 📝 Avaliação PIEPE - {formato} (Máx 100 pontos)")
                                p1 = st.slider("1. Relevância e Impacto Social (0 a 20):", 0.0, 20.0, 0.0, step=0.5, key=f"p1_{banca['id']}", help="Adequação às necessidades identificadas e impacto na comunidade.")
                                p2 = st.slider("2. Coerência entre Objetivos, Ações e Resultados (0 a 15):", 0.0, 15.0, 0.0, step=0.5, key=f"p2_{banca['id']}", help="Articulação lógica entre etapas do projeto.")
                                p3 = st.slider("3. Evidência de Resultados e Indicadores (0 a 10):", 0.0, 10.0, 0.0, step=0.5, key=f"p3_{banca['id']}", help="Utilização de dados que demonstrem alcance/efeitos.")
                                if formato == 'Slide':
                                    p4 = st.slider("4. Organização e Qualidade Técnico-Científica (0 a 10):", 0.0, 10.0, 0.0, step=0.5, key=f"p4_{banca['id']}", help="Clareza das informações, estrutura visual dos slides, adequação da linguagem.")
                                else:
                                    p4 = st.slider("4. Clareza e Organização Visual do Banner (0 a 10):", 0.0, 10.0, 0.0, step=0.5, key=f"p4_{banca['id']}", help="Disposição gráfica, legibilidade e síntese no banner.")
                                p5 = st.slider("5. Inovação em Saúde (0 a 10):", 0.0, 10.0, 0.0, step=0.5, key=f"p5_{banca['id']}", help="Abordagens, tecnologias ou metodologias novas aplicadas.")
                                p6 = st.slider("6. Domínio do Conteúdo e Comunicação Oral (0 a 15):", 0.0, 15.0, 0.0, step=0.5, key=f"p6_{banca['id']}", help="Segurança na apresentação e coerência nas respostas à banca.")
                                p7 = st.slider("7. Adequação das Ações ao Nível de Formação (0 a 10):", 0.0, 10.0, 0.0, step=0.5, key=f"p7_{banca['id']}", help="Compatibilidade com as competências esperadas para o período.")
                                p8 = st.slider("8. Vinculação aos Objetivos de Desenv. Sustentável (ODS) (0 a 10):", 0.0, 10.0, 0.0, step=0.5, key=f"p8_{banca['id']}", help="Articulação com metas de promoção da saúde e sustentabilidade.")
                                nota_final_calc = p1+p2+p3+p4+p5+p6+p7+p8
                                notas_dit = {"Impacto Social": p1, "Coerência Obj/Res": p2, "Indicadores": p3, f"Qualidade ({formato})": p4, "Inovação": p5, "Domínio Oral": p6, "Adequação": p7, "ODS": p8, "Total da Banca": nota_final_calc}
                                if any(v == 0 for v in [p1, p2, p3, p4, p5, p6, p7, p8]): zeros = True

                            else: # MCM V
                                st.markdown("##### 📝 Avaliação Clínica Global MCM V (Máx 100 pontos)")
                                m1 = st.slider("1. Complexidade e Raciocínio Clínico (0 a 20):", 0.0, 20.0, 0.0, step=0.5, key=f"m5_1_{banca['id']}", help="Capacidade de analisar casos complexos e formular diagnósticos precisos.")
                                m2 = st.slider("2. Adequação às Diretrizes (0 a 20):", 0.0, 20.0, 0.0, step=0.5, key=f"m5_2_{banca['id']}", help="Fundamentação baseada em diretrizes oficiais (SBC, SBPT, PCDT, etc).")
                                m3 = st.slider("3. Abordagem Terapêutica/Farmacológica (0 a 20):", 0.0, 20.0, 0.0, step=0.5, key=f"m5_3_{banca['id']}", help="Precisão na escolha de condutas terapêuticas.")
                                m4 = st.slider("4. Estruturação Científica e Metodológica (0 a 20):", 0.0, 20.0, 0.0, step=0.5, key=f"m5_4_{banca['id']}", help="Qualidade da redação e organização dos dados.")
                                m5 = st.slider("5. Defesa Oral e Arguição (0 a 20):", 0.0, 20.0, 0.0, step=0.5, key=f"m5_5_{banca['id']}", help="Segurança, clareza e capacidade de defender a conduta.")
                                nota_final_calc = m1+m2+m3+m4+m5
                                notas_dit = {"Raciocínio Clínico": m1, "Diretrizes Clínicas": m2, "Terapêutica/Farma": m3, "Estruturação": m4, "Defesa Oral": m5, "Total da Banca": nota_final_calc}
                                if any(v == 0 for v in [m1, m2, m3, m4, m5]): zeros = True
                            
                            st.markdown("---")
                            if zeros: st.warning("⚠️ Atenção: Há critérios avaliados com nota ZERO.")
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
            indice_real = next((i for i, d in enumerate(st.session_state.bancos_avaliacoes) if d["id"] == banca["id"]), None)
            with st.container(border=True):
                st.write(f"✅ **{banca['modulo']}** - {banca.get('titulo')} | Alunos: {', '.join(banca['alunos'])}")
                with st.expander("Ver Resumo da Rubrica Atribuída (Detalhado)"):
                    minhas_notas = banca.get('notas_detalhadas', {}).get(meu_email, {})
                    for criterio, valor in minhas_notas.items():
                        if "Total" in criterio: st.markdown(f"<br><b>{criterio}: {valor:.1f}</b>", unsafe_allow_html=True)
                        else: st.write(f"🔹 {criterio}: {valor:.1f} pontos")
                
                # Assinatura de Ata de Defesa pelo Avaliador (Se TCC II / MCM V)
                if banca['modulo'] in ["TCC II", "MCM V"] and meu_email not in banca.get("assinaturas_defesa", []):
                    st.markdown("---")
                    if st.button("✍️ Assinar Ata de Defesa Eletronicamente (Banca)", key=f"assina_banca_{banca['id']}", use_container_width=True):
                        st.session_state.bancos_avaliacoes[indice_real]['assinaturas_defesa'].append(meu_email)
                        recarregar_com_sucesso("Assinatura eletrônica computada na Ata de Defesa!")

# ==========================================
# ROTEADOR DE TELAS
# ==========================================
if st.session_state.usuario_bancas is None:
    tela_login()
elif st.session_state.usuario_bancas["perfil"] == "Administrador":
    tela_administracao()
elif st.session_state.usuario_bancas["perfil"] == "Coordenação":
    tela_coordenacao()
elif st.session_state.usuario_bancas["perfil"] == "Professor":
    tela_professor()
