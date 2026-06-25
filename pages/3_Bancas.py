import streamlit as st
import uuid
import pandas as pd
import io
from datetime import datetime, time

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Portal de Bancas - CRIVO", page_icon="🎓", layout="wide")

# 2. DESIGN CUSTOMIZADO (CSS) E CORES DOS MÓDULOS
st.markdown("""
    <style>
    .titulo-principal { color: #800040; font-family: 'Arial'; font-weight: bold; margin-bottom: 5px; }
    .cartao-banca { background-color: #ffffff; padding: 20px; border-radius: 8px; border-left: 6px solid #800040; margin-bottom: 15px; box-shadow: 0px 2px 8px rgba(0,0,0,0.08); }
    
    .badge-tcci { background-color: #3498db; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-tccii { background-color: #2980b9; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-mcmiv { background-color: #2ecc71; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-mcmv { background-color: #27ae60; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    .badge-piepe { background-color: #e67e22; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# 3. FUNÇÕES UTILITÁRIAS
def forçar_recarregamento_tela():
    try: st.rerun()
    except AttributeError: st.experimental_rerun()

def obter_classe_cor(modulo):
    cores = {"TCC I": "badge-tcci", "TCC II": "badge-tccii", "MCM IV": "badge-mcmiv", "MCM V": "badge-mcmv", "PIEPE": "badge-piepe"}
    return cores.get(modulo, "badge-piepe")

def formatar_nome_email(email):
    try: return " ".join([p.capitalize() for p in email.split('@')[0].split('.')])
    except: return email

def liberar_acesso_professor(email_prof, perfil_prof):
    if email_prof and email_prof not in st.session_state.permissoes_acesso:
        st.session_state.permissoes_acesso[email_prof] = {"perfil": perfil_prof, "modulos": []}

# Função do Radar de Conflitos
def verificar_conflito_horario(data, horario, lista_emails, id_ignorar=None):
    if horario == "N/A" or not horario:
        return False, ""
    
    # Remove e-mails vazios da lista
    emails_validos = set([e for e in lista_emails if e])
    
    for b in st.session_state.bancos_avaliacoes:
        if b['id'] == id_ignorar:
            continue
        
        # Se bater no mesmo dia e na mesma hora...
        if b['data'] == data and b['horario'] == horario:
            emails_da_banca_existente = set(filter(None, [
                b.get('orientador_email'), b.get('coorientador_email'),
                b.get('avaliador_1_email'), b.get('avaliador_2_email'),
                b.get('avaliador_sup_email')
            ]))
            
            # Verifica se há intersecção (alguém está nas duas)
            conflitos = emails_validos.intersection(emails_da_banca_existente)
            if conflitos:
                return True, ", ".join(conflitos)
                
    return False, ""

ADMIN_EMAILS = ["wanessa.almeida@afya.com.br", "wanessa.salmeida@yahoo.com.br"]
lista_horarios = [time(h, 0) for h in range(8, 21)]

# 4. BANCO DE DADOS TEMPORÁRIO E CONTROLE DE ACESSO
if "bancos_avaliacoes" not in st.session_state: st.session_state.bancos_avaliacoes = [] 
if "permissoes_acesso" not in st.session_state: st.session_state.permissoes_acesso = {}
if "usuario_bancas" not in st.session_state: st.session_state.usuario_bancas = None 

# ==========================================
# MÓDULO DE LOGIN
# ==========================================
def tela_login():
    st.markdown("<h2 class='titulo-principal'>🎓 Portal de Bancas e Avaliações</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_login"):
            st.write("**1. Escolha o seu Perfil de Acesso:**")
            tipo_acesso = st.radio("Perfil:", ["👑 Administrador (Gestão de Acessos)", "⚙️ Coordenador (Gestão de Bancas)", "📚 Professor (Avaliador/Orientador)"], label_visibility="collapsed")
            
            st.write("**2. Insira suas credenciais:**")
            email = st.text_input("E-mail Institucional:").lower().strip()
            senha = st.text_input("Senha:", type="password")
            submit = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if submit:
                if senha != "afya2026": 
                    st.error("Senha incorreta.")
                else:
                    if "Administrador" in tipo_acesso:
                        if email in ADMIN_EMAILS:
                            st.session_state.usuario_bancas = {"perfil": "Administrador", "email": email, "nome": formatar_nome_email(email), "modulos": []}
                            forçar_recarregamento_tela()
                        else: st.error("Este e-mail não possui privilégios de Administrador Master.")
                    
                    elif "Coordenador" in tipo_acesso:
                        dados_acesso = st.session_state.permissoes_acesso.get(email)
                        if dados_acesso and dados_acesso.get("perfil") == "Coordenação":
                            st.session_state.usuario_bancas = {"perfil": "Coordenação", "email": email, "nome": formatar_nome_email(email), "modulos": dados_acesso.get("modulos", [])}
                            forçar_recarregamento_tela()
                        else: st.error("E-mail não cadastrado como Coordenador. Peça à Administração para liberar seu acesso.")
                    
                    elif "Professor" in tipo_acesso:
                        is_prof = False
                        nome_encontrado = formatar_nome_email(email)
                        for b in st.session_state.bancos_avaliacoes:
                            emails_vinculados = [b.get("orientador_email"), b.get("coorientador_email"), b.get("avaliador_1_email"), b.get("avaliador_2_email"), b.get("avaliador_sup_email")]
                            if email in emails_vinculados:
                                is_prof = True
                                if email == b.get("orientador_email"): nome_encontrado = b.get("orientador_nome")
                                elif email == b.get("coorientador_email"): nome_encontrado = b.get("coorientador_nome")
                                elif email == b.get("avaliador_1_email"): nome_encontrado = b.get("avaliador_1_nome")
                                elif email == b.get("avaliador_2_email"): nome_encontrado = b.get("avaliador_2_nome")
                                elif email == b.get("avaliador_sup_email"): nome_encontrado = b.get("avaliador_sup_nome")
                                break
                        
                        if is_prof:
                            st.session_state.usuario_bancas = {"perfil": "Professor", "email": email, "nome": nome_encontrado}
                            forçar_recarregamento_tela()
                        else: st.error("E-mail não vinculado a nenhuma banca ativa como Orientador ou Avaliador.")

# ==========================================
# PAINEL 0: ADMINISTRAÇÃO (Master)
# ==========================================
def tela_administracao():
    col_titulo, col_logout = st.columns([4, 1])
    with col_titulo: st.markdown(f"### 👑 Painel de Administração Master | Olá, {st.session_state.usuario_bancas['nome']}")
    with col_logout:
        if st.button("Sair (Logout)"):
            st.session_state.usuario_bancas = None
            forçar_recarregamento_tela()
            
    st.info("Nesta área, você delega ou revoga os acessos dos coordenadores.")
    
    with st.expander("➕ Adicionar Novo Coordenador", expanded=True):
        with st.form("form_add_coord", clear_on_submit=True):
            novo_email_coord = st.text_input("E-mail do Coordenador (@afya.com.br):").lower().strip()
            modulos_delegados = st.multiselect("Selecione os módulos sob responsabilidade deste coordenador:", ["TCC I", "TCC II", "MCM IV", "MCM V", "PIEPE"])
            
            if st.form_submit_button("Conceder Acesso de Coordenação"):
                if not novo_email_coord.endswith("@afya.com.br") and not novo_email_coord.endswith("@yahoo.com.br"): st.error("Insira um e-mail válido da instituição.")
                elif not modulos_delegados: st.error("Selecione pelo menos um módulo.")
                else:
                    st.session_state.permissoes_acesso[novo_email_coord] = {"perfil": "Coordenação", "modulos": modulos_delegados}
                    st.toast(f"✅ Acesso concedido para {novo_email_coord}!", icon="🔐")
                    forçar_recarregamento_tela()
                
    st.markdown("#### Gestão de Coordenadores Cadastrados")
    for email, dados in list(st.session_state.permissoes_acesso.items()):
        if isinstance(dados, dict) and dados.get("perfil") == "Coordenação":
            with st.container(border=True):
                st.markdown(f"**👤 {formatar_nome_email(email)}** ({email})")
                mods_atuais = dados.get("modulos", [])
                novos_mods = st.multiselect(f"Módulos autorizados:", ["TCC I", "TCC II", "MCM IV", "MCM V", "PIEPE"], default=mods_atuais, key=f"mod_{email}")
                
                col1, col2, col3 = st.columns([2, 2, 6])
                with col1:
                    if st.button("💾 Salvar Módulos", key=f"save_{email}", use_container_width=True):
                        st.session_state.permissoes_acesso[email]["modulos"] = novos_mods
                        st.toast("Módulos atualizados!", icon="✅")
                with col2:
                    if st.button("🗑️ Revogar", key=f"del_{email}", use_container_width=True):
                        del st.session_state.permissoes_acesso[email]
                        forçar_recarregamento_tela()

# ==========================================
# PAINEL 1: COORDENAÇÃO 
# ==========================================
def tela_coordenacao():
    col_titulo, col_logout = st.columns([4, 1])
    with col_titulo: st.markdown(f"### ⚙️ Painel da Coordenação | Olá, {st.session_state.usuario_bancas['nome']}")
    with col_logout:
        if st.button("Sair (Logout)"):
            st.session_state.usuario_bancas = None
            forçar_recarregamento_tela()
            
    aba_criar, aba_gerenciar = st.tabs(["➕ Criar Novo Grupo/Banca", "📋 Controle e Edição"])
    
    with aba_criar:
        modulos_permitidos = st.session_state.usuario_bancas["modulos"]
        if not modulos_permitidos: st.warning("Você não tem módulos atribuídos à sua coordenação. Fale com a Administração.")
        else:
            modulo_selecionado = st.selectbox("Selecione o Módulo da Avaliação:", modulos_permitidos, index=None)
            
            formato_piepe = None
            if modulo_selecionado == "PIEPE": formato_piepe = st.radio("Formato de Avaliação:", ["Slide", "Banner"], horizontal=True)

            if modulo_selecionado:
                with st.form("form_nova_banca", clear_on_submit=True):
                    col_dt, col_hr = st.columns(2)
                    with col_dt: data_banca = st.date_input("Data da Defesa:", format="DD/MM/YYYY")
                    with col_hr:
                        if modulo_selecionado != "PIEPE": horario_banca = st.selectbox("Horário de Início:", lista_horarios, format_func=lambda t: t.strftime('%H:%M'))
                        else: horario_banca = None

                    titulo = st.text_input("Título do Projeto/Trabalho:")
                    
                    st.markdown("---")
                    st.write("**Orientação** *(Domínio @afya.com.br ou @parceiro.afya.com.br)*")
                    col_o1, col_o2 = st.columns(2)
                    with col_o1: o_nome = st.text_input("Nome Completo do Orientador:")
                    with col_o2: o_email = st.text_input("E-mail do Orientador:").lower().strip()
                    
                    # SUBSTITUIÇÃO DA CHECKBOX PELO EXPANDER (Sem travar o formulário!)
                    with st.expander("➕ Adicionar Co-orientador (Opcional)"):
                        col_co1, col_co2 = st.columns(2)
                        with col_co1: co_nome = st.text_input("Nome Completo do Co-orientador:")
                        with col_co2: co_email = st.text_input("E-mail do Co-orientador:").lower().strip()
                        
                    st.markdown("---")
                    st.write("**Composição da Banca Avaliadora** *(Avaliadores externos não possuem restrição de e-mail)*")
                    
                    col_b1n, col_b1e = st.columns(2)
                    with col_b1n: b1_nome = st.text_input("Nome Completo Titular 1:")
                    with col_b1e: b1_email = st.text_input("E-mail Titular 1:").lower().strip()
                    
                    col_b2n, col_b2e = st.columns(2)
                    with col_b2n: b2_nome = st.text_input("Nome Completo Titular 2:")
                    with col_b2e: b2_email = st.text_input("E-mail Titular 2:").lower().strip()

                    bs_nome, bs_email = "", ""
                    if modulo_selecionado not in ["TCC I", "MCM IV"]:
                        col_bsn, col_bse = st.columns(2)
                        with col_bsn: bs_nome = st.text_input("Nome Completo Suplente:")
                        with col_bse: bs_email = st.text_input("E-mail Suplente (Obrigatório):").lower().strip()
                        
                    st.markdown("---")
                    st.write("**Integrantes do Grupo**")
                    lista_alunos = st.text_area("Nomes dos Alunos (um por linha):", height=150)
                    
                    if st.form_submit_button("Salvar e Gerar Banca"):
                        ori_valido = o_email.endswith("@afya.com.br") or o_email.endswith("@parceiro.afya.com.br")
                        co_valido = True
                        if co_email:
                            co_valido = co_email.endswith("@afya.com.br") or co_email.endswith("@parceiro.afya.com.br")

                        precisa_sup = modulo_selecionado not in ["TCC I", "MCM IV"]
                        hora_str = horario_banca.strftime("%H:%M") if horario_banca else "N/A"

                        # Validação de Conflito de Horário
                        teve_conflito, emails_em_conflito = verificar_conflito_horario(
                            data_banca.strftime("%d/%m/%Y"), 
                            hora_str, 
                            [o_email, co_email, b1_email, b2_email, bs_email]
                        )

                        if not titulo or not o_nome or not o_email or not b1_nome or not b1_email or not b2_nome or not b2_email or not lista_alunos:
                            st.error("Preencha todos os nomes e e-mails obrigatórios dos titulares e orientação.")
                        elif co_email and not co_nome:
                            st.error("Preencha o Nome do Co-orientador (ou apague o e-mail se não houver).")
                        elif precisa_sup and (not bs_nome or not bs_email):
                            st.error("Nome e E-mail do Avaliador Suplente são obrigatórios para este módulo.")
                        elif not ori_valido:
                            st.error("O E-mail do Orientador deve pertencer ao domínio @afya.com.br ou parceiro.")
                        elif not co_valido:
                            st.error("O E-mail do Co-orientador deve pertencer ao domínio @afya.com.br ou parceiro.")
                        elif teve_conflito:
                            st.error(f"🚨 ALERTA DE CONFLITO! Os seguintes e-mails já estão agendados em outra banca nesta mesma data ({data_banca.strftime('%d/%m/%Y')}) e horário ({hora_str}): {emails_em_conflito}")
                        else:
                            alunos_processados = [nome.strip() for nome in lista_alunos.split('\n') if nome.strip()]

                            nova_banca = {
                                "id": str(uuid.uuid4())[:8], "modulo": modulo_selecionado, "formato_piepe": formato_piepe,
                                "data": data_banca.strftime("%d/%m/%Y"), "horario": hora_str, "titulo": titulo,
                                "orientador_email": o_email, "orientador_nome": o_nome,
                                "coorientador_email": co_email, "coorientador_nome": co_nome,
                                "avaliador_1_email": b1_email, "avaliador_1_nome": b1_nome,
                                "avaliador_2_email": b2_email, "avaliador_2_nome": b2_nome,
                                "avaliador_sup_email": bs_email, "avaliador_sup_nome": bs_nome,
                                "alunos": alunos_processados, "status": "Aguardando Avaliação", "notas_banca": [], "nota_orientador": None, "nota_final": None
                            }
                            st.session_state.bancos_avaliacoes.append(nova_banca)
                            
                            liberar_acesso_professor(o_email, "Professor")
                            if co_email: liberar_acesso_professor(co_email, "Professor")
                            liberar_acesso_professor(b1_email, "Professor")
                            liberar_acesso_professor(b2_email, "Professor")
                            if bs_email: liberar_acesso_professor(bs_email, "Professor")
                            
                            st.toast("✅ Banca criada com sucesso!", icon="🎉")

    with aba_gerenciar:
        if not st.session_state.bancos_avaliacoes:
            st.info("Nenhuma banca cadastrada.")
        else:
            with st.expander("📊 Relatório Consolidado (Exportar Excel)"):
                df_export = pd.DataFrame(st.session_state.bancos_avaliacoes)
                if not df_export.empty:
                    max_alunos = df_export['alunos'].apply(lambda x: len(x) if isinstance(x, list) else 0).max()
                    for i in range(max_alunos):
                        df_export[f'Aluno {i+1}'] = df_export['alunos'].apply(lambda x: x[i] if isinstance(x, list) and i < len(x) else "")
                    
                    df_export = df_export.drop(columns=['alunos']) 

                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_export.to_excel(writer, index=False, sheet_name='Bancas')
                        worksheet = writer.sheets['Bancas']
                        for idx, col in enumerate(df_export.columns):
                            max_len = max([len(str(x)) for x in df_export[col].values] + [len(str(col))]) + 2
                            col_letter = chr(65 + idx) if idx < 26 else chr(64 + idx // 26) + chr(65 + idx % 26)
                            worksheet.column_dimensions[col_letter].width = min(max_len, 40)
                    
                    st.download_button("📥 Baixar Planilha (.xlsx)", data=buffer.getvalue(), file_name=f"Relatorio_Bancas_{datetime.now().strftime('%d_%m_%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            
            st.markdown("---")
            for i, banca in enumerate(reversed(st.session_state.bancos_avaliacoes)):
                indice_real = len(st.session_state.bancos_avaliacoes) - 1 - i
                classe_cor = obter_classe_cor(banca['modulo'])
                hora_texto = f" às {banca.get('horario')}" if banca.get('horario') and banca.get('horario') != "N/A" else ""
                info_extras = f"{banca['data']}{hora_texto}"
                if banca.get('formato_piepe'): info_extras += f" | Formato: {banca['formato_piepe']}"
                
                ori_str = f"{banca['orientador_nome']}"
                if banca.get('coorientador_nome'): ori_str += f" | <b>Co-orientador:</b> {banca['coorientador_nome']}"
                
                av_str = f"{banca['avaliador_1_nome']} | {banca['avaliador_2_nome']}"
                if banca.get('avaliador_sup_nome'): av_str += f" | {banca['avaliador_sup_nome']} (Suplente)"
                
                edit_key = f"edit_{banca['id']}"
                if edit_key not in st.session_state: st.session_state[edit_key] = False
                
                with st.container(border=True):
                    st.markdown(f"""
                    <div style='border-left: 5px solid #800040; padding-left: 15px; margin-bottom: 15px;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div><span class='{classe_cor}'>{banca['modulo']}</span> <span style='color: #666; font-size: 14px;'> | {info_extras}</span></div>
                            <div style='font-size: 13px; color: #800040;'><b>Status:</b> {banca['status']}</div>
                        </div>
                        <h4 style='margin-top: 10px; margin-bottom: 5px; color: #333;'>{banca['titulo']}</h4>
                        <p style='margin: 0; font-size: 14px;'><strong>Orientação:</strong> {ori_str}</p>
                        <p style='margin: 0; font-size: 14px;'><strong>Avaliadores:</strong> {av_str}</p>
                        <p style='margin: 8px 0 0 0; font-size: 14px;'><strong>Alunos ({len(banca.get('alunos', []))}):</strong> {', '.join(banca.get('alunos', []))}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_btn1, col_btn2, col_vazia = st.columns([2, 2, 6])
                    with col_btn1:
                        if st.button("✏️ Editar Banca", key=f"btn_{edit_key}", use_container_width=True):
                            st.session_state[edit_key] = not st.session_state[edit_key]
                            st.rerun()
                    with col_btn2:
                        if st.button("🗑️ Excluir", key=f"del_{banca['id']}", use_container_width=True):
                            st.session_state.bancos_avaliacoes.pop(indice_real)
                            st.rerun()
                    
                    if st.session_state[edit_key]:
                        st.markdown("---")
                        st.markdown("#### ✏️ Alterar Dados da Banca")
                        with st.form(key=f"form_edit_{banca['id']}"):
                            try: data_obj = datetime.strptime(banca['data'], "%d/%m/%Y").date()
                            except: data_obj = datetime.now().date()
                                
                            try:
                                h, m = map(int, banca.get('horario', '08:00').split(':'))
                                hora_obj = time(h, m)
                                if hora_obj not in lista_horarios: hora_obj = time(8, 0)
                            except: hora_obj = time(8, 0)
                                
                            col_ed1, col_ed2 = st.columns(2)
                            with col_ed1: edit_data = st.date_input("Data da Defesa:", value=data_obj, format="DD/MM/YYYY")
                            with col_ed2:
                                if banca['modulo'] != "PIEPE": edit_hora = st.selectbox("Horário:", lista_horarios, index=lista_horarios.index(hora_obj), format_func=lambda t: t.strftime('%H:%M'))
                                else: edit_hora = None
                                    
                            edit_titulo = st.text_input("Título do Projeto/Trabalho:", value=banca['titulo'])
                            
                            st.markdown("---")
                            col_e1, col_e2 = st.columns(2)
                            with col_e1: 
                                edit_o_nome = st.text_input("Nome Completo Orientador:", value=banca.get('orientador_nome', ''))
                                edit_o_email = st.text_input("E-mail Orientador:", value=banca['orientador_email'])
                            
                            with st.expander("➕ Alterar Co-orientador (Opcional)", expanded=bool(banca.get('coorientador_email'))):
                                col_eco1, col_eco2 = st.columns(2)
                                with col_eco1: edit_co_nome = st.text_input("Nome Co-orientador:", value=banca.get('coorientador_nome', ''))
                                with col_eco2: edit_co_email = st.text_input("E-mail Co-orientador:", value=banca.get('coorientador_email', ''))
                                
                            st.markdown("---")
                            col_e3, col_e4 = st.columns(2)
                            with col_e3: 
                                edit_b1_nome = st.text_input("Nome Completo Titular 1:", value=banca.get('avaliador_1_nome', ''))
                                edit_b1_email = st.text_input("E-mail Titular 1:", value=banca['avaliador_1_email'])
                            with col_e4:
                                edit_b2_nome = st.text_input("Nome Completo Titular 2:", value=banca.get('avaliador_2_nome', ''))
                                edit_b2_email = st.text_input("E-mail Titular 2:", value=banca.get('avaliador_2_email', ''))
                                
                            col_e5, col_e6 = st.columns(2)
                            with col_e5:
                                edit_bs_nome = st.text_input("Nome Completo Suplente:", value=banca.get('avaliador_sup_nome', ''))
                                edit_bs_email = st.text_input("E-mail Suplente:", value=banca.get('avaliador_sup_email', ''))
                                
                            edit_alunos = st.text_area("Alunos (um por linha):", value="\n".join(banca.get('alunos', [])), height=100)
                            
                            if st.form_submit_button("Salvar Alterações"):
                                ori_valido = edit_o_email.endswith("@afya.com.br") or edit_o_email.endswith("@parceiro.afya.com.br")
                                co_valido = edit_co_email.endswith("@afya.com.br") or edit_co_email.endswith("@parceiro.afya.com.br") if edit_co_email else True
                                precisa_sup = banca['modulo'] not in ["TCC I", "MCM IV"]
                                hora_str = edit_hora.strftime("%H:%M") if edit_hora else "N/A"

                                teve_conflito, emails_em_conflito = verificar_conflito_horario(
                                    edit_data.strftime("%d/%m/%Y"), 
                                    hora_str, 
                                    [edit_o_email, edit_co_email, edit_b1_email, edit_b2_email, edit_bs_email],
                                    id_ignorar=banca['id'] # O sistema não conflita a banca com ela mesma na edição
                                )

                                if not edit_titulo or not edit_o_nome or not edit_o_email or not edit_b1_nome or not edit_b1_email or not edit_b2_nome or not edit_b2_email or not edit_alunos: 
                                    st.error("Preencha todos os nomes e e-mails obrigatórios dos titulares e orientação.")
                                elif edit_co_email and not edit_co_nome:
                                    st.error("Preencha o Nome do Co-orientador (ou apague o e-mail se não houver).")
                                elif precisa_sup and (not edit_bs_nome or not edit_bs_email): 
                                    st.error("Nome e E-mail do Avaliador Suplente são obrigatórios para este módulo.")
                                elif not ori_valido: 
                                    st.error("E-mail do Orientador deve ser @afya.com.br ou parceiro.")
                                elif not co_valido:
                                    st.error("E-mail do Co-orientador deve ser @afya.com.br ou parceiro.")
                                elif teve_conflito:
                                    st.error(f"🚨 ALERTA DE CONFLITO! Os seguintes e-mails já estão agendados em outra banca nesta mesma data e horário: {emails_em_conflito}")
                                else:
                                    st.session_state.bancos_avaliacoes[indice_real].update({
                                        "data": edit_data.strftime("%d/%m/%Y"), "horario": hora_str,
                                        "titulo": edit_titulo, 
                                        "orientador_email": edit_o_email, "orientador_nome": edit_o_nome,
                                        "coorientador_email": edit_co_email, "coorientador_nome": edit_co_nome,
                                        "avaliador_1_email": edit_b1_email, "avaliador_1_nome": edit_b1_nome,
                                        "avaliador_2_email": edit_b2_email, "avaliador_2_nome": edit_b2_nome,
                                        "avaliador_sup_email": edit_bs_email, "avaliador_sup_nome": edit_bs_nome,
                                        "alunos": [nome.strip() for nome in edit_alunos.split('\n') if nome.strip()]
                                    })
                                    
                                    liberar_acesso_professor(edit_o_email, "Professor")
                                    if edit_co_email: liberar_acesso_professor(edit_co_email, "Professor")
                                    liberar_acesso_professor(edit_b1_email, "Professor")
                                    liberar_acesso_professor(edit_b2_email, "Professor")
                                    if edit_bs_email: liberar_acesso_professor(edit_bs_email, "Professor")
                                    
                                    st.session_state[edit_key] = False 
                                    st.toast("✅ Banca atualizada com sucesso!", icon="🔄")
                                    forçar_recarregamento_tela()

# ==========================================
# PAINEL DO PROFESSOR
# ==========================================
def tela_professor():
    col_titulo, col_logout = st.columns([4, 1])
    with col_titulo: st.markdown(f"### 📚 Painel do Professor | Olá, {st.session_state.usuario_bancas['nome']}")
    with col_logout:
        if st.button("Sair (Logout)"):
            st.session_state.usuario_bancas = None
            forçar_recarregamento_tela()
            
    st.info("🚧 Módulo de preenchimento de notas e emissão de Atas será construído aqui na próxima etapa!")

# ROTEADOR
if st.session_state.usuario_bancas is None: tela_login()
elif st.session_state.usuario_bancas["perfil"] == "Administrador": tela_administracao()
elif st.session_state.usuario_bancas["perfil"] == "Coordenação": tela_coordenacao()
elif st.session_state.usuario_bancas["perfil"] == "Professor": tela_professor()
