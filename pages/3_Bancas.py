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

# 3. FUNÇÕES UTILITÁRIAS E LISTA DE HORÁRIOS
def forçar_recarregamento_tela():
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

def formatar_nome_email(email):
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

def liberar_acesso_professor(email_prof, perfil_prof):
    if email_prof and email_prof not in st.session_state.permissoes_acesso:
        st.session_state.permissoes_acesso[email_prof] = {"perfil": perfil_prof, "modulos": []}

# Lista de Horários Inteiros (08:00 até 20:00)
lista_horarios = [time(h, 0) for h in range(8, 21)]

# 4. BANCO DE DADOS TEMPORÁRIO E CONTROLE DE ACESSO
if "bancos_avaliacoes" not in st.session_state:
    st.session_state.bancos_avaliacoes = [] 

if "permissoes_acesso" not in st.session_state or isinstance(st.session_state.permissoes_acesso.get("wanessa.almeida@afya.com.br"), str):
    st.session_state.permissoes_acesso = {
        "wanessa.almeida@afya.com.br": {"perfil": "Administrador", "modulos": ["Todos"]}
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
            email = st.text_input("E-mail de Acesso:").lower().strip()
            senha = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if submit:
                if email not in st.session_state.permissoes_acesso:
                    st.error("Email não cadastrado. Procure a coordenação do módulo.")
                elif senha != "afya2026": 
                    st.error("Senha incorreta.")
                else:
                    dados_acesso = st.session_state.permissoes_acesso[email]
                    nome_formatado = formatar_nome_email(email)
                    st.session_state.usuario_bancas = {
                        "perfil": dados_acesso["perfil"], 
                        "email": email, 
                        "nome": nome_formatado,
                        "modulos": dados_acesso.get("modulos", [])
                    }
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
            
    st.info("Nesta área, você delega ou revoga os acessos dos coordenadores.")
    
    with st.expander("➕ Adicionar Novo Coordenador", expanded=True):
        with st.form("form_add_coord", clear_on_submit=True):
            novo_email_coord = st.text_input("E-mail do Coordenador (@afya.com.br):").lower().strip()
            
            modulos_delegados = st.multiselect(
                "Selecione os módulos sob responsabilidade deste coordenador:", 
                ["TCC I", "TCC II", "MCM IV", "MCM V", "PIEPE"],
                placeholder="Escolha uma ou mais opções..."
            )
            
            if st.form_submit_button("Conceder Acesso de Coordenação"):
                if not novo_email_coord.endswith("@afya.com.br"):
                    st.error("Insira um e-mail válido da Afya.")
                elif not modulos_delegados:
                    st.error("Selecione pelo menos um módulo para este coordenador.")
                else:
                    st.session_state.permissoes_acesso[novo_email_coord] = {
                        "perfil": "Coordenação", 
                        "modulos": modulos_delegados
                    }
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
    with col_titulo:
        st.markdown(f"### ⚙️ Painel da Coordenação | Olá, {st.session_state.usuario_bancas['nome']}")
    with col_logout:
        if st.button("Sair (Logout)"):
            st.session_state.usuario_bancas = None
            forçar_recarregamento_tela()
            
    aba_criar, aba_gerenciar = st.tabs(["➕ Criar Novo Grupo/Banca", "📋 Controle e Edição"])
    
    # --- ABA DE CRIAÇÃO ---
    with aba_criar:
        modulos_permitidos = st.session_state.usuario_bancas["modulos"]
        
        if not modulos_permitidos:
            st.warning("Você não tem módulos atribuídos à sua coordenação. Fale com a Administração.")
        else:
            modulo_selecionado = st.selectbox(
                "Selecione o Módulo da Avaliação:", 
                modulos_permitidos,
                index=None,
                placeholder="Selecione um módulo..."
            )
            
            formato_piepe = None
            if modulo_selecionado == "PIEPE":
                st.warning("⚠️ PIEPE: Defina o formato da apresentação.")
                formato_piepe = st.radio("Formato de Avaliação:", ["Slide", "Banner"], horizontal=True)

            if modulo_selecionado:
                with st.form("form_nova_banca", clear_on_submit=True):
                    col_dt, col_hr = st.columns(2)
                    with col_dt:
                        data_banca = st.date_input("Data da Defesa:", format="DD/MM/YYYY")
                    with col_hr:
                        if modulo_selecionado != "PIEPE":
                            horario_banca = st.selectbox("Horário de Início:", lista_horarios, format_func=lambda t: t.strftime('%H:%M'))
                        else:
                            horario_banca = None

                    titulo = st.text_input("Título do Projeto/Trabalho:")
                    
                    st.markdown("---")
                    st.write("**Orientação**")
                    col_o1, col_o2 = st.columns(2)
                    with col_o1:
                        orientador_email = st.text_input("E-mail do Orientador (@afya.com.br ou @parceiro.afya.com.br):").lower().strip()
                        
                    st.markdown("---")
                    st.write("**Composição da Banca Avaliadora** *(Avaliadores externos não possuem restrição de e-mail)*")
                    
                    if modulo_selecionado in ["TCC I", "MCM IV"]:
                        st.write("*Regra do Módulo: Dois avaliadores titulares obrigatórios. Sem suplente.*")
                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            avaliador_1_email = st.text_input("E-mail Avaliador Titular 1:").lower().strip()
                        with col_b2:
                            avaliador_2_email = st.text_input("E-mail Avaliador Titular 2:").lower().strip()
                        avaliador_sup_email = ""
                    else:
                        st.write("*Regra do Módulo: Dois avaliadores titulares e um suplente obrigatório.*")
                        col_b1, col_b2, col_b3 = st.columns(3)
                        with col_b1:
                            avaliador_1_email = st.text_input("E-mail Avaliador Titular 1:").lower().strip()
                        with col_b2:
                            avaliador_2_email = st.text_input("E-mail Avaliador Titular 2:").lower().strip()
                        with col_b3:
                            avaliador_sup_email = st.text_input("E-mail Avaliador Suplente (Obrigatório):").lower().strip()
                        
                    st.markdown("---")
                    st.write("**Integrantes do Grupo**")
                    lista_alunos = st.text_area("Nomes dos Alunos (um por linha):", height=150)
                    
                    btn_salvar = st.form_submit_button("Salvar e Gerar Banca")
                    
                    if btn_salvar:
                        ori_valido = orientador_email.endswith("@afya.com.br") or orientador_email.endswith("@parceiro.afya.com.br")
                        precisa_sup = modulo_selecionado not in ["TCC I", "MCM IV"]

                        if not titulo or not orientador_email or not avaliador_1_email or not avaliador_2_email or not lista_alunos:
                            st.error("Preencha todos os campos obrigatórios.")
                        elif precisa_sup and not avaliador_sup_email:
                            st.error("O E-mail do Avaliador Suplente é obrigatório para este módulo.")
                        elif not ori_valido:
                            st.error("O E-mail do Orientador deve pertencer ao domínio @afya.com.br ou @parceiro.afya.com.br.")
                        else:
                            alunos_processados = [nome.strip() for nome in lista_alunos.split('\n') if nome.strip()]
                            hora_str = horario_banca.strftime("%H:%M") if horario_banca else "N/A"

                            nova_banca = {
                                "id": str(uuid.uuid4())[:8],
                                "modulo": modulo_selecionado,
                                "formato_piepe": formato_piepe,
                                "data": data_banca.strftime("%d/%m/%Y"),
                                "horario": hora_str,
                                "titulo": titulo,
                                "orientador_email": orientador_email,
                                "orientador_nome": formatar_nome_email(orientador_email),
                                "avaliador_1_email": avaliador_1_email,
                                "avaliador_1_nome": formatar_nome_email(avaliador_1_email),
                                "avaliador_2_email": avaliador_2_email,
                                "avaliador_2_nome": formatar_nome_email(avaliador_2_email),
                                "avaliador_sup_email": avaliador_sup_email,
                                "avaliador_sup_nome": formatar_nome_email(avaliador_sup_email) if avaliador_sup_email else "",
                                "alunos": alunos_processados,
                                "status": "Aguardando Avaliação",
                                "notas_banca": [],
                                "nota_orientador": None,
                                "nota_final": None
                            }
                            st.session_state.bancos_avaliacoes.append(nova_banca)
                            
                            liberar_acesso_professor(orientador_email, "Orientador")
                            liberar_acesso_professor(avaliador_1_email, "Avaliador")
                            liberar_acesso_professor(avaliador_2_email, "Avaliador")
                            if avaliador_sup_email:
                                liberar_acesso_professor(avaliador_sup_email, "Avaliador")
                            
                            st.toast("✅ Banca criada com sucesso e acessos liberados!", icon="🎉")

    # --- ABA DE GERENCIAMENTO E EDIÇÃO ---
    with aba_gerenciar:
        if not st.session_state.bancos_avaliacoes:
            st.info("Nenhuma banca cadastrada.")
        else:
            with st.expander("📊 Relatório Consolidado (Exportar Excel)"):
                df_export = pd.DataFrame(st.session_state.bancos_avaliacoes)
                
                # O BLINDAGEM DO EXCEL: Só roda se existirem bancas
                if not df_export.empty:
                    df_export['alunos'] = df_export['alunos'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_export.to_excel(writer, index=False, sheet_name='Bancas')
                        worksheet = writer.sheets['Bancas']
                        for idx, col in enumerate(df_export.columns):
                            series = df_export[col]
                            max_len = max(series.astype(str).map(len).max() if not series.empty else 0, len(str(col))) + 2
                            col_letter = chr(65 + idx) if idx < 26 else chr(64 + idx // 26) + chr(65 + idx % 26)
                            worksheet.column_dimensions[col_letter].width = max_len
                    
                    st.download_button(
                        label="📥 Baixar Planilha de Notas e Grupos (.xlsx)",
                        data=buffer.getvalue(),
                        file_name=f"Relatorio_Bancas_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            
            st.markdown("---")
            for i, banca in enumerate(reversed(st.session_state.bancos_avaliacoes)):
                indice_real = len(st.session_state.bancos_avaliacoes) - 1 - i
                classe_cor = obter_classe_cor(banca['modulo'])
                
                hora_texto = f" às {banca.get('horario')}" if banca.get('horario') and banca.get('horario') != "N/A" else ""
                info_extras = f"{banca['data']}{hora_texto}"
                if banca.get('formato_piepe'): info_extras += f" | Formato: {banca['formato_piepe']}"
                
                avaliadores_str = banca['avaliador_1_nome']
                if banca.get('avaliador_2_nome'): avaliadores_str += f" | {banca['avaliador_2_nome']}"
                if banca.get('avaliador_sup_nome'): avaliadores_str += f" | {banca['avaliador_sup_nome']} (Suplente)"
                
                edit_key = f"edit_{banca['id']}"
                if edit_key not in st.session_state:
                    st.session_state[edit_key] = False
                
                with st.container(border=True):
                    cartao_html = (
                        f"<div style='border-left: 5px solid #800040; padding-left: 15px; margin-bottom: 15px;'>"
                        f"<div style='display: flex; justify-content: space-between; align-items: center;'>"
                        f"<div><span class='{classe_cor}'>{banca['modulo']}</span> <span style='color: #666; font-size: 14px;'> | {info_extras}</span></div>"
                        f"<div style='font-size: 13px; color: #800040;'><b>Status:</b> {banca['status']}</div>"
                        f"</div>"
                        f"<h4 style='margin-top: 10px; margin-bottom: 5px; color: #333;'>{banca['titulo']}</h4>"
                        f"<p style='margin: 0; font-size: 14px;'><strong>Orientador:</strong> {banca['orientador_nome']}</p>"
                        f"<p style='margin: 0; font-size: 14px;'><strong>Avaliadores:</strong> {avaliadores_str}</p>"
                        f"<p style='margin: 8px 0 0 0; font-size: 14px;'><strong>Alunos ({len(banca['alunos'])}):</strong> {', '.join(banca['alunos'])}</p>"
                        f"</div>"
                    )
                    st.markdown(cartao_html, unsafe_allow_html=True)
                    
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
                            try:
                                data_obj = datetime.strptime(banca['data'], "%d/%m/%Y").date()
                            except:
                                data_obj = datetime.now().date()
                                
                            try:
                                h, m = map(int, banca.get('horario', '08:00').split(':'))
                                hora_obj = time(h, m)
                                if hora_obj not in lista_horarios: hora_obj = time(8, 0)
                            except:
                                hora_obj = time(8, 0)
                                
                            col_ed1, col_ed2 = st.columns(2)
                            with col_ed1:
                                edit_data = st.date_input("Data da Defesa:", value=data_obj, format="DD/MM/YYYY")
                            with col_ed2:
                                if banca['modulo'] != "PIEPE":
                                    edit_hora = st.selectbox("Horário:", lista_horarios, index=lista_horarios.index(hora_obj), format_func=lambda t: t.strftime('%H:%M'))
                                else:
                                    edit_hora = None
                                    
                            edit_titulo = st.text_input("Título do Projeto/Trabalho:", value=banca['titulo'])
                            
                            col_e1, col_e2 = st.columns(2)
                            with col_e1:
                                edit_ori = st.text_input("E-mail Orientador:", value=banca['orientador_email'])
                                edit_av1 = st.text_input("E-mail Avaliador Titular 1:", value=banca['avaliador_1_email'])
                            with col_e2:
                                edit_av2 = st.text_input("E-mail Avaliador Titular 2:", value=banca.get('avaliador_2_email', ''))
                                edit_sup = st.text_input("E-mail Avaliador Suplente:", value=banca.get('avaliador_sup_email', ''))
                                
                            edit_alunos = st.text_area("Alunos (um por linha):", value="\n".join(banca['alunos']), height=100)
                            
                            if st.form_submit_button("Salvar Alterações"):
                                ori_valido = edit_ori.endswith("@afya.com.br") or edit_ori.endswith("@parceiro.afya.com.br")
                                precisa_sup = banca['modulo'] not in ["TCC I", "MCM IV"]

                                if not edit_ori or not edit_av1 or not edit_av2:
                                    st.error("Orientador e os dois Avaliadores Titulares são obrigatórios.")
                                elif precisa_sup and not edit_sup:
                                    st.error("O E-mail do Avaliador Suplente é obrigatório para este módulo.")
                                elif not ori_valido:
                                    st.error("O E-mail do Orientador deve pertencer ao domínio @afya.com.br ou @parceiro.afya.com.br.")
                                else:
                                    alunos_atualizados = [nome.strip() for nome in edit_alunos.split('\n') if nome.strip()]
                                    hora_str = edit_hora.strftime("%H:%M") if edit_hora else "N/A"
                                    
                                    st.session_state.bancos_avaliacoes[indice_real].update({
                                        "data": edit_data.strftime("%d/%m/%Y"),
                                        "horario": hora_str,
                                        "titulo": edit_titulo,
                                        "orientador_email": edit_ori,
                                        "orientador_nome": formatar_nome_email(edit_ori),
                                        "avaliador_1_email": edit_av1,
                                        "avaliador_1_nome": formatar_nome_email(edit_av1),
                                        "avaliador_2_email": edit_av2,
                                        "avaliador_2_nome": formatar_nome_email(edit_av2),
                                        "avaliador_sup_email": edit_sup,
                                        "avaliador_sup_nome": formatar_nome_email(edit_sup) if edit_sup else "",
                                        "alunos": alunos_atualizados
                                    })
                                    
                                    liberar_acesso_professor(edit_ori, "Orientador")
                                    liberar_acesso_professor(edit_av1, "Avaliador")
                                    liberar_acesso_professor(edit_av2, "Avaliador")
                                    if edit_sup: liberar_acesso_professor(edit_sup, "Avaliador")
                                    
                                    st.session_state[edit_key] = False 
                                    st.toast("✅ Banca atualizada com sucesso!", icon="🔄")
                                    forçar_recarregamento_tela()

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
# ROTEADOR DE TELAS
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
