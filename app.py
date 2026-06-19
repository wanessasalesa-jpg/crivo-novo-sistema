import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import time
import pytz 

# 1. CONFIGURAÇÃO DA PÁGINA E LIMPEZA TOTAL DE CACHE
st.set_page_config(page_title="CRIVO - Gestão Acadêmica", layout="centered")
st.cache_data.clear()

# 2. FUSO HORÁRIO DE BRASÍLIA
fuso_bruta = pytz.timezone('America/Sao_Paulo')

def obter_agora():
    return datetime.now(fuso_bruta)

# FUNÇÃO PARA ENCURTAR NOMES NA EXIBIÇÃO DO APP (IGNORA PREPOSIÇÕES)
def tratar_nome_curto(nome_completo):
    if not nome_completo or pd.isna(nome_completo):
        return ""
    partes = str(nome_completo).strip().split()
    if len(partes) == 1:
        return partes[0]
    preposicoes = ['de', 'da', 'do', 'das', 'dos', 'e']
    if partes[1].lower() in preposicoes and len(partes) > 2:
        return f"{partes[0]} {partes[1]} {partes[2]}"
    return f"{partes[0]} {partes[1]}"

# 3. CONEXÃO COM GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Aumentado o TTL base para aliviar o servidor, limpezas serão cirúrgicas.
    df_escalacao = conn.read(worksheet="Escalacao", ttl=60)
    df_escalacao.columns = df_escalacao.columns.astype(str).str.strip().str.lower()
except:
    st.error("Conectando ao banco de dados... Aguarde.")
    time.sleep(1)
    st.rerun()

# --- MAPEAMENTO BLINDADO DE COLUNAS (O RADAR) ---
def buscar_coluna(palavras_chave, evitar=None):
    for col in df_escalacao.columns:
        if all(p in col for p in palavras_chave):
            if evitar and evitar in col:
                continue
            return col
    return None

c_av1_email = buscar_coluna(['email', '1'])
c_av1_nome = buscar_coluna(['avaliador', '1'], evitar='email')

c_av2_email = buscar_coluna(['email', '2'])
c_av2_nome = buscar_coluna(['avaliador', '2'], evitar='email')

c_sup_email = buscar_coluna(['email', 'suplente'])
c_sup_nome = buscar_coluna(['suplente'], evitar='email')

c_ori_email = buscar_coluna(['email', 'orientador'])
c_ori_nome = buscar_coluna(['orientador'], evitar='email')

c_turma = buscar_coluna(['turma'])
c_titulo = buscar_coluna(['titulo']) or buscar_coluna(['título'])
c_data = buscar_coluna(['data'])
c_horario = buscar_coluna(['horario']) or buscar_coluna(['horário'])

c_aptidao_col = buscar_coluna(['aptid', 'defesa'])
c_assinatura_col = buscar_coluna(['assinatura', 'orientador'])

c_aluno1 = buscar_coluna(['aluno', '1'])
c_aluno2 = buscar_coluna(['aluno', '2'])
c_aluno3 = buscar_coluna(['aluno', '3'])
c_aluno4 = buscar_coluna(['aluno', '4'])
c_aluno5 = buscar_coluna(['aluno', '5'])

def verificar_presenca_email(email, coluna_real):
    if not coluna_real or coluna_real not in df_escalacao.columns:
        return False
    return email in df_escalacao[coluna_real].astype(str).str.strip().str.lower().unique()

colunas_respostas_obrigatorias = ["Avaliador", "Email_Avaliador", "Alunos", "Nota_Final", "Papel", "Data_Hora"]
try:
    df_respostas = conn.read(worksheet="Respostas", ttl=60)
    if df_respostas.empty or not all(col in df_respostas.columns for col in colunas_respostas_obrigatorias):
        df_respostas = pd.DataFrame(columns=colunas_respostas_obrigatorias)
except:
    df_respostas = pd.DataFrame(columns=colunas_respostas_obrigatorias)

# --- TRAVA DE LOGOUT E IDENTIFICAÇÃO DE PAPEL ---
if 'email' not in st.session_state:
    if "user" in st.query_params:
        st.session_state.email = st.query_params["user"]

if 'email' not in st.session_state:
    st.markdown("""
        <style>
        header {visibility: hidden !important;}
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden;}
        .stButton button {
            width: 100% !important;
            border-radius: 10px !important;
            height: 3.5em !important;
            background-color: #002147 !important;
            color: white !important;
            font-weight: bold !important;
            border: none !important;
        }
        </style>
        """, unsafe_allow_html=True)

    st.title("🎓 CRIVO")
    # MARCADOR VISUAL DE SUCESSO DA ATUALIZAÇÃO ANTITRAVAMENTO:
    st.subheader("🚀 CRIVO - V5 TURBO")
    st.caption("© 2026 Desenvolvido por Wanessa Sales de Almeida")
    st.divider()

    st.write("### Identificação do Docente")
    email_raw = st.text_input("Digite seu e-mail cadastrado:").strip()
    if st.button("Acessar Sistema"):
        if email_raw:
            email_limpo = email_raw.lower().strip()
            
            id_banca1 = verificar_presenca_email(email_limpo, c_av1_email)
            id_banca2 = verificar_presenca_email(email_limpo, c_av2_email)
            id_suplente = verificar_presenca_email(email_limpo, c_sup_email)
            id_orienta = verificar_presenca_email(email_limpo, c_ori_email)
            
            if id_banca1 or id_banca2 or id_suplente or id_orienta:
                st.session_state.clear()
                st.session_state.email = email_limpo
                st.query_params["user"] = email_limpo
                st.rerun()
            else:
                st.error("E-mail não autorizado ou não encontrado na escalação.")
    st.stop()

# --- DEFINIÇÃO DO PAPEL LOGADO ---
email_user = st.session_state.email

tem_papel_ori = verificar_presenca_email(email_user, c_ori_email)
tem_papel_av1 = verificar_presenca_email(email_user, c_av1_email)
tem_papel_av2 = verificar_presenca_email(email_user, c_av2_email)
tem_papel_sup = verificar_presenca_email(email_user, c_sup_email)
tem_papel_banca = tem_papel_av1 or tem_papel_av2 or tem_papel_sup

if "perfil_ativo" not in st.session_state:
    if tem_papel_banca:
        st.session_state.perfil_ativo = "Banca"
    else:
        st.session_state.perfil_ativo = "Orientador"

eh_orientador = (st.session_state.perfil_ativo == "Orientador")
eh_banca = not eh_orientador

nome_completo_docente = ""
if eh_orientador and tem_papel_ori:
    nome_completo_docente = df_escalacao[df_escalacao[c_ori_email].astype(str).str.strip().str.lower() == email_user][c_ori_nome].iloc[0]
else:
    if tem_papel_av1 and not df_escalacao[df_escalacao[c_av1_email].astype(str).str.strip().str.lower() == email_user].empty:
        nome_completo_docente = df_escalacao[df_escalacao[c_av1_email].astype(str).str.strip().str.lower() == email_user][c_av1_nome].iloc[0]
    elif tem_papel_av2 and not df_escalacao[df_escalacao[c_av2_email].astype(str).str.strip().str.lower() == email_user].empty:
        nome_completo_docente = df_escalacao[df_escalacao[c_av2_email].astype(str).str.strip().str.lower() == email_user][c_av2_nome].iloc[0]
    elif tem_papel_sup and not df_escalacao[df_escalacao[c_sup_email].astype(str).str.strip().str.lower() == email_user].empty:
        nome_completo_docente = df_escalacao[df_escalacao[c_sup_email].astype(str).str.strip().str.lower() == email_user][c_sup_nome].iloc[0]

nome_exibicao = tratar_nome_curto(nome_completo_docente)

# --- DEFINIÇÃO DINÂMICA DE CORES ---
cor_primaria = "#002147" if not eh_orientador else "#FF1493"
cor_texto_bloco = "#ffffff"

st.markdown(f"""
    <style>
    header {{visibility: hidden !important;}}
    #MainMenu {{visibility: hidden !important;}}
    footer {{visibility: hidden;}}
    
    .bloco-cabecalho {{
        background-color: {cor_primaria} !important;
        padding: 25px !important;
        border-radius: 12px !important;
        color: {cor_texto_bloco} !important;
        margin-bottom: 25px !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1) !important;
    }}
    .bloco-cabecalho h1, .bloco-cabecalho h3, .bloco-cabecalho p {{
        color: {cor_texto_bloco} !important;
        margin: 0 !important;
        padding: 2px 0 !important;
    }}
    
    .stButton button {{
        width: 100% !important;
        border-radius: 10px !important;
        height: 3.5em !important;
        background-color: {cor_primaria} !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

sub_titulo_texto = "Sistema de Gestão de Bancas Acadêmicas" if not eh_orientador else "Sistema de Gestão de Orientações"
st.markdown(f"""
    <div class="bloco-cabecalho">
        <h1>🎓 CRIVO</h1>
        <h3>{sub_titulo_texto}</h3>
        <p style="font-size: 0.85em; opacity: 0.8;">© 2026 Desenvolvido por Wanessa Sales de Almeida</p>
    </div>
    """, unsafe_allow_html=True)

if tem_papel_ori and tem_papel_banca:
    st.info("🔄 **Perfil Duplo Detectado:** Você atua como Orientador e também como Avaliador de Banca.")
    novo_perfil = st.radio("Selecione qual painel acessar agora:", ["Orientador", "Banca"], index=1 if st.session_state.perfil_ativo == "Banca" else 0, horizontal=True)
    if novo_perfil != st.session_state.perfil_ativo:
        st.session_state.perfil_ativo = novo_perfil
        st.rerun()

def obter_lista_alunos_linha(row):
    lista = []
    for col_aluno in [c_aluno1, c_aluno2, c_aluno3, c_aluno4, c_aluno5]:
        if col_aluno and col_aluno in row and pd.notna(row[col_aluno]):
            nome = str(row[col_aluno]).strip()
            if nome and nome.lower() != "nan" and nome != "":
                lista.append(nome)
    return lista

# --- FILTRAGEM DE GRUPOS PENDENTES EM TEMPO REAL ---
pendentes = pd.DataFrame()
total_pendencias_contador = 0

if not df_escalacao.empty:
    if eh_orientador:
        possiveis = df_escalacao[df_escalacao[c_ori_email].astype(str).str.strip().str.lower() == email_user].copy()
        linhas_pendentes = []
        for idx, row in possiveis.iterrows():
            turma_check = str(row.get(c_turma, "")).strip().upper()
            tb_clean_check = turma_check.replace(" ", "")
            
            if "MCMV" in tb_clean_check or "MCM5" in tb_clean_check:
                continue
                
            alunos_grupo = obter_lista_alunos_linha(row)
            avaliados = df_respostas[(df_respostas["Email_Avaliador"] == email_user) & (df_respostas["Papel"] == "Orientador")]["Alunos"].tolist()
            alunos_restantes = [a for a in alunos_grupo if a not in avaliados]
            
            ja_preencheu_aptidao = pd.notna(row.get(c_aptidao_col)) and str(row.get(c_aptidao_col)).strip() != "" if c_aptidao_col else False
            precisa_tela_aptidao = ("TCCII" in tb_clean_check or "TCC2" in tb_clean_check) and not ja_preencheu_aptidao
            
            if alunos_restantes or precisa_tela_aptidao:
                linhas_pendentes.append(row)
                total_pendencias_contador += len(alunos_restantes) + (1 if precisa_tela_aptidao and not alunos_restantes else 0)
        if linhas_pendentes:
            pendentes = pd.DataFrame(linhas_pendentes)
    else:
        cond_banca = pd.Series(False, index=df_escalacao.index)
        if c_av1_email and c_av1_email in df_escalacao.columns:
            cond_banca |= (df_escalacao[c_av1_email].astype(str).str.strip().str.lower() == email_user)
        if c_av2_email and c_av2_email in df_escalacao.columns:
            cond_banca |= (df_escalacao[c_av2_email].astype(str).str.strip().str.lower() == email_user)
        if c_sup_email and c_sup_email in df_escalacao.columns:
            cond_banca |= (df_escalacao[c_sup_email].astype(str).str.strip().str.lower() == email_user)
            
        possiveis = df_escalacao[cond_banca].copy()
        linhas_pendentes = []
        for idx, row in possiveis.iterrows():
            alunos_grupo = obter_lista_alunos_linha(row)
            string_grupo_banca = ", ".join(alunos_grupo)
            
            ja_avaliou = df_respostas[(df_respostas["Email_Avaliador"] == email_user) & (df_respostas["Papel"] == "Banca") & (df_respostas["Alunos"] == string_grupo_banca)]
            if ja_avaliou.empty and alunos_grupo:
                linhas_pendentes.append(row)
                total_pendencias_contador += 1
        if linhas_pendentes:
            pendentes = pd.DataFrame(linhas_pendentes)

col_user, col_exit = st.columns([3, 1])
with col_user:
    st.write(f"**Docente:** {nome_exibicao} ({'Orientador' if eh_orientador else 'Banca Examinadora'})")
with col_exit:
    if st.button("Sair"):
        if total_pendencias_contador > 0:
            st.session_state.tentou_sair_com_pendencia = True
        else:
            st.session_state.clear()
            st.query_params.clear()
            st.rerun()

if st.session_state.get("tentou_sair_com_pendencia", False):
    st.warning(f"⚠️ **Atenção:** Ainda possui **{total_pendencias_contador}** avaliações pendentes registadas no seu nome!")
    col_cancela, col_confirma = st.columns(2)
    with col_cancela:
        if st.button("🔄 Voltar e Avaliar"):
            st.session_state.tentou_sair_com_pendencia = False
            st.rerun()
    with col_confirma:
        if st.button("🏃 Sair Mesmo Assim"):
            st.session_state.clear()
            st.query_params.clear()
            st.rerun()
    st.stop()

if pendentes.empty:
    st.balloons()
    st.success("🎉 Todas as suas avaliações pendentes foram concluídas!")
else:
    def gerar_display_grupo(row):
        alunos = obter_lista_alunos_linha(row)
        return ", ".join([tratar_nome_curto(n) for n in alunos])
        
    pendentes['Display_Grupo'] = pendentes.apply(gerar_display_grupo, axis=1)
    lista_grupos_display = pendentes["Display_Grupo"].tolist()
    
    selecionado_display = st.selectbox("🎯 Escolha o Grupo para Avaliar:", [""] + lista_grupos_display)

    if selecionado_display and selecionado_display != "":
        dados = pendentes[pendentes["Display_Grupo"] == selecionado_display].iloc[0]
        turma_bruta = str(dados.get(c_turma, "")).strip()
        tb_clean = turma_bruta.replace(" ", "").upper()
        
        alunos_reais_lista = obter_lista_alunos_linha(dados)
        string_grupo_completo = ", ".join(alunos_reais_lista)
        
        linha_index_planilha = dados.name + 2 
        banca_liberada = True
        msg_trava = ""
        
        if not eh_orientador:
            try:
                val_data = str(dados.get(c_data, "")).strip()
                val_horario = str(dados.get(c_horario, "")).strip().lower().replace("h", ":")
                data_banca = datetime.strptime(val_data, "%d/%m/%Y").date()
                horario_banca = datetime.strptime(val_horario, "%H:%M").time()
                dt_banca_completa = fuso_bruta.localize(datetime.combine(data_banca, horario_banca))
                
                agora = obter_agora()
                limite_liberacao = dt_banca_completa - timedelta(minutes=5)
                
                if agora < limite_liberacao:
                    banca_liberada = False
                    msg_trava = f"⏳ Esta avaliação de Banca só estará disponível a partir das {limite_liberacao.strftime('%H:%M')} do dia {data_banca.strftime('%d/%m/%Y')}."
            except:
                pass

        with st.expander("📖 Informações do Trabalho", expanded=True):
            st.write(f"**Turma:** {turma_bruta}")
            st.write(f"**Título:** {dados.get(c_titulo, '')}")
            st.write(f"**Orientador:** {str(dados.get(c_ori_nome, '')).strip() if pd.notna(dados.get(c_ori_nome, '')) else ''}")
            st.write(f"**Integrantes do Grupo:** {string_grupo_completo}")
            st.write(f"**Data/Horário Cadastrado:** {dados.get(c_data, '')} às {dados.get(c_horario, '')}")

        if not banca_liberada:
            st.warning(msg_trava)
        else:
            aluno_alvo_final = string_grupo_completo
            exibir_formulario_notas = True
            exibir_tela_aptidao_final = False

            if eh_orientador:
                if "MCMV" in tb_clean or "MCM5" in tb_clean:
                    exibir_formulario_notas = False
                    st.warning("⚠️ Nota do orientador não aplicável para esta turma. A turma MCM V possui 100% da nota final atribuída exclusivamente pela banca examinadora.")
                else:
                    avaliados_na_aba = df_respostas[(df_respostas["Email_Avaliador"] == email_user) & (df_respostas["Papel"] == "Orientador")]["Alunos"].tolist()
                    lista_alunos_individuais = [a for a in alunos_reais_lista if a not in avaliados_na_aba]
                    
                    if lista_alunos_individuais:
                        aluno_alvo_final = st.selectbox(
                            "👤 Selecione o Aluno para atribuir a nota individual:", 
                            lista_alunos_individuais,
                            format_func=tratar_nome_curto
                        )
                    else:
                        exibir_formulario_notas = False
                        if "TCCII" in tb_clean or "TCC2" in tb_clean:
                            exibir_tela_aptidao_final = True
                        else:
                            st.success("Todos os alunos deste grupo já foram avaliados por si!")

            if eh_orientador and exibir_tela_aptidao_final:
                st.markdown("---")
                st.subheader("📋 TELA 2: Ficha de Aptidão de Defesa (Exclusivo TCC II)")
                st.info("Parabéns! As avaliações individuais dos alunos foram concluídas. Agora, preencha o parecer de aptidão do grupo para fechar a banca.")
                
                with st.form("form_aptidao_tcc2"):
                    resposta_aptidao = st.radio(
                        "**O projeto de Trabalho de Conclusão de Curso (TCC II) entregue pelo grupo encontra-se:**",
                        ["", "APTO para apresentação", "INAPTO para apresentação"],
                        index=0,
                        help="Marque a condição de aceitabilidade do trabalho para a defesa."
                    )
                    assinatura_texto = st.text_input("**Assinatura Digital (Digite seu Nome Completo para assinar):**", value="").strip()
                    
                    if st.form_submit_button("🚀 ENVIAR PARECER E CONCLUIR BANCA"):
                        if resposta_aptidao == "":
                            st.error("Por favor, selecione se o grupo está APTO ou INAPTO.")
                        elif assinatura_texto == "":
                            st.error("Por favor, digite seu nome no campo de assinatura para validar o documento.")
                        else:
                            with st.spinner("Gravando parecer de aptidão na planilha..."):
                                try:
                                    st.cache_data.clear()
                                    df_atualizar_linha = conn.read(worksheet="Escalacao", ttl=0)
                                    df_atualizar_linha.columns = df_atualizar_linha.columns.astype(str).str.strip().str.lower()
                                    
                                    if c_aptidao_col in df_atualizar_linha.columns:
                                        df_atualizar_linha[c_aptidao_col] = df_atualizar_linha[c_aptidao_col].astype(object)
                                    if c_assinatura_col in df_atualizar_linha.columns:
                                        df_atualizar_linha[c_assinatura_col] = df_atualizar_linha[c_assinatura_col].astype(object)
                                    
                                    df_atualizar_linha.loc[linha_index_planilha - 2, c_aptidao_col] = resposta_aptidao
                                    df_atualizar_linha.loc[linha_index_planilha - 2, c_assinatura_col] = assinatura_texto
                                    conn.update(worksheet="Escalacao", data=df_atualizar_linha)
                                    
                                    st.success("🎉 Ficha de Aptidão registrada e assinada com sucesso! Lote concluído.")
                                    time.sleep(1.5)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao salvar: {e}")

            elif exibir_formulario_notas:
                aluno_para_salvar = aluno_alvo_final
                rubrica = {}
                
                if eh_orientador:
                    st.info(f"🌱 Avaliando individualmente o discente: **{tratar_nome_curto(aluno_para_salvar)}**")
                    
                    if "MCMIV" in tb_clean or "MCM4" in tb_clean:
                        rubrica = {
                            "Desenv. - Envolvimento e Responsabilidade": (5, "Participação proativa, demonstrando alta responsabilidade e comprometimento no processo de elaboração."),
                            "Desenv. - Relação com Orientador / Diálogo": (5, "Relação colaborativa, com boa abertura ao diálogo e aceitação de sugestões."),
                            "Desenv. - Desempenho e Cumprimento de Tarefas": (5, "Desempenho satisfatório, com activities realizadas de forma competente e engajada."),
                            "Desenv. - Pontualidade e Compromisso": (5, "Pontualidade é mantida consistentemente, demonstrando compromisso com o processo."),
                            "Responsabilidade com a Aprendizagem": (5, "Responsabilidade evidente em buscar ativamente oportunidades de aprendizado e aprimoramento."),
                            "Texto - Justificativa do Estudo": (6, "Apresenta com clareza a relevância científica, social ou profissional; bem estruturada e relacionada ao problema."),
                            "Texto - Objetivo Geral e Específicos": (6, "Objetivo geral claro, coerente com a justificativa; objetivos específicos bem formulados e articulados."),
                            "Texto - Fundamentação Teórica / Referências": (6, "Referencial teórico relevante, atualizado (últimos 5 anos em sua maioria) e articulado ao tema."),
                            "Texto - Metodologia Proposta": (10, "Método bem descrito, adequado aos objetivos, com definição de tipo de estudo, população e análise."),
                            "Texto - Cronograma de Execução": (1, "Cronograma bem estruturado, com etapas claras e prazos viáveis."),
                            "Texto - Estrutura, Linguagem e Formatação": (6, "Texto bem escrito, estruturado, sem erros relevantes; segue as normas (ABNT ou Vancouver)."),
                            "Relatório - Relatório de Pesquisa": (10, "Apreciação técnica do orientador sobre o documento final de conclusão dos dados compilados.")
                        }
                    elif "TCCII" in tb_clean or "TCC2" in tb_clean:
                        rubrica = {
                            "Discente - Envolvimento e Responsabilidade": (5, "Participação proativa, demonstrou alta responsabilidade e comprometimento no processo de elaboração do artigo."),
                            "Discente - Relação com Orientador / Diálogo": (5, "Relação colaborativa, com boa abertura ao diálogo e aceitação de sugestões."),
                            "Discente - Desempenho / Cumprimento de Tarefas": (4, "Desempenho satisfatório, com atividades realizadas de forma competente e engajada."),
                            "Discente - Pontualidade e Compromisso": (3, "Pontualidade é mantida consistentemente, o que demonstra compromisso com o processo."),
                            "Responsabilidade com a Aprendizagem": (3, "Responsabilidade evidente em buscar ativamente oportunidades de aprendizado e de aprimoramento."),
                            "Artigo - Estruturação e Escrita Científica": (5, "Estrutura adequada, com fluidez, concisão e excelência na redação científica."),
                            "Artigo - Fundamentação e Atualização Bibliográfica": (4, "Fundamentação crítica, bem estruturada e com autores atuais e pertinentes à área médica."),
                            "Artigo - Apresentação e Discussão dos Resultados": (4, "Resultados apresentados com clareza, com discussão crítica e integration aos achados da literatura."),
                            "Artigo - Rigor Metodológico": (4, "Métodos bem descritos, compatíveis com o delineamento e objetivos do estudo."),
                            "Artigo - Conclusão e Relevância Científica": (3, "Conclusão clara, alinhada aos objetivos e resultados, com destaque à relevância científica e aplicabilidade prática.")
                        }
                    elif "TCCI" in tb_clean or "TCC1" in tb_clean:
                        rubrica = {
                            "Discente - Envolvimento e Responsabilidade": (5, "Participação proativa, demonstrou alta responsabilidade e comprometimento no processo de elaboração do projeto."),
                            "Discente - Relação com Orientador / Diálogo": (5, "Relação colaborativa, com boa abertura ao diálogo e aceitação de sugestões."),
                            "Discente - Desempenho / Cumprimento de Tarefas": (4, "Desempenho satisfatório, com atividades realizadas de forma competente e engajada."),
                            "Discente - Pontualidade e Compromisso": (3, "Pontualidade é mantida consistentemente, demonstrando compromisso com os prazos."),
                            "Responsabilidade com a Aprendizagem": (3, "Responsabilidade evidente em buscar ativamente oportunidades de aprendizado e de aprimoramento."),
                            "Projeto - Formulação do Problema e Justificativa": (5, "Problema de pesquisa é excepcionalmente formulado, e a justificativa é altamente persuasiva, atualizada e relevante."),
                            "Projeto - Objetivos e Hipóteses": (4, "Objetivos são bem formulados e alinhados, e as hipóteses são pertinentes e testáveis."),
                            "Projeto - Revisão de Literatura": (4, "Revisão de literatura é abrangente, crítica e identifica claramente a relevância do estudo na literatura existente."),
                            "Projeto - Metodologia e ABNT": (4, "Metodologia é detalhada e abrangente, proporcionando uma compreensão completa; projeto formatado conforme ABNT."),
                            "Projeto - Considerações Éticas e Viabilidade": (3, "Considerações éticas são discutidas de maneira apropriada, e a viabilidade do estudo é abordada.")
                        }
                else:
                    st.info("🎓 Você está visualizando a Rubrica de Avaliação da Banca (Nota para o Grupo todo).")
                    
                    if "MCMIV" in tb_clean or "MCM4" in tb_clean:
                        rubrica = {
                            "Delineamento - Rigor Científico e Metodologia": (10, "Adequação do desenho do estudo, viabilidade técnica e delineamento claro dos procedimentos propostos."),
                            "Apresentação Oral - Clareza e Domínio": (10, "Domínio conceitual do conteúdo exposto, postura, uso do tempo regulamentar e clareza na defesa oral."),
                            "Coerência - Estrutura Geral do Projeto": (10, "Lógica interna do manuscrito, alinhamento fluido entre a justificativa, os objetivos e o método.")
                        }
                    elif "MCMV" in tb_clean or "MCM5" in tb_clean:
                        rubrica = {
                            "Tema/Resumo": (5, "Qualidade técnica do resumo e aderência ao tema."),
                            "Introdução": (10, "Fundamentação teórica sólida e revisão."),
                            "Metodologia": (15, "Execução real do método proposto."),
                            "Resultados": (15, "Apresentação clara dos dados obtidos."),
                            "Discussão": (20, "Capacidade crítica de comparar resultados."),
                            "Referências": (5, "Rigor técnico nas citações e bibliografia."),
                            "Apresentação Oral": (15, "Segurança na defesa dos resultados."),
                            "Coerência": (10, "União lógica de todas as partes do trabalho."),
                            "Qualidade Visual": (4, "Profissionalismo na apresentação visual."),
                            "Tempo": (1, "Intervalo de 15 a 20 minutos de apresentação.")
                        }
                    elif "TCCII" in tb_clean or "TCC2" in tb_clean:
                        rubrica = {
                            "Tema/Resumo": (4, "Qualidade técnica do resumo e aderência ao tema."),
                            "Introdução": (5, "Fundamentação teórica sólida e revisão."),
                            "Metodologia": (5, "Execução real do método proposto."),
                            "Resultados": (5, "Apresentação clara dos dados obtidos."),
                            "Discussão": (10, "Capacidade crítica de comparar resultados."),
                            "Referências": (1, "Rigor técnico nas citações e bibliografia."),
                            "Apresentação Oral": (10, "Segurança na defesa dos resultados."),
                            "Coerência": (10, "União lógica de todas as partes do trabalho."),
                            "Qualidade Visual": (9, "Profissionalismo na apresentação visual."),
                            "Tempo": (1, "Intervalo de 15 a 20 minutos de apresentação.")
                        }
                    elif "TCCI" in tb_clean or "TCC1" in tb_clean:
                        rubrica = {
                            "Tema": (3, "Clareza, delimitação e a atualidade do tema proposto."),
                            "Resumo": (1, "Objetivo, método, resultados esperados e palavras-chave."),
                            "Introdução": (5, "Contextualização do tema e problema de pesquisa."),
                            "Justificativa": (5, "Importância do trabalho e contribuição científica."),
                            "Objetivos": (5, "Objetivo geral e específicos mensuráveis."),
                            "Metodologia": (10, "Desenho do estudo, criteria e ética."),
                            "Referências": (1, "Uso de normas ABNT/Vancouver."),
                            "Apresentação Oral": (10, "Domínio de conteúdo, postura e clareza."),
                            "Coerência": (10, "Lógica entre introdução, objetivos e métodos."),
                            "Qualidade Visual": (9, "Organização dos slides e recursos."),
                            "Tempo": (1, "Intervalo de 10 a 15 minutos de apresentação.")
                        }

                if rubrica:
                    v_max = sum(p for p, h in rubrica.values())
                    st.write(f"### 📝 Ficha de Avaliação (Máximo: {v_max} pontos)")
                    st.info("💡 **Dica Rápida:** Ajuste todas as notas deslizando os botões. O aplicativo agora é ultrarrápido e não travará. O total será calculado apenas quando clicar em Gravar.")
                    
                    # -------------------------------------------------------------
                    # A MÁGICA ANTI-TRAVAMENTO ESTÁ NESTE FORMULÁRIO BLINDADO
                    # -------------------------------------------------------------
                    with st.form(key=f"form_aval_{aluno_para_salvar}"):
                        notas = {}
                        for item, (p, help_t) in rubrica.items():
                            if p == 1:
                                notas[item] = st.slider(f"**{item} ({p} pts)**", 0.0, 1.0, 0.0, step=0.5, help=help_t)
                            else:
                                notas[item] = st.slider(f"**{item} ({p} pts)**", 0, p, 0, help=help_t)

                        st.markdown("---")
                        conf_zero = st.checkbox("Confirmo que eventuais notas zero atribuídas acima são intencionais.")
                        
                        submit_btn = st.form_submit_button("🚀 CALCULAR E GRAVAR AVALIAÇÃO NO SISTEMA")
                        
                        if submit_btn:
                            total = sum(notas.values())
                            tem_zero = any(v == 0 for v in notas.values())
                            
                            if tem_zero and not conf_zero:
                                st.error(f"⚠️ O sistema calculou a sua nota total provisória como **{total}**. Como existem critérios com nota zero, por favor, marque a caixa de confirmação acima e clique em Gravar novamente.")
                            else:
                                with st.spinner(f"Gravando a nota total de {total} pontos. Sincronizando com a planilha..."):
                                    try:
                                        # Limpa o cache cirurgicamente apenas na hora de escrever no banco
                                        st.cache_data.clear()
                                        df_at = conn.read(worksheet="Respostas", ttl=0)
                                        if df_at.empty or not all(col in df_at.columns for col in colunas_respostas_obrigatorias):
                                            df_at = pd.DataFrame(columns=colunas_respostas_obrigatorias)
                                        
                                        nova_l = pd.DataFrame([{
                                            "Avaliador": nome_completo_docente, 
                                            "Email_Avaliador": email_user, 
                                            "Alunos": aluno_para_salvar, 
                                            "Nota_Final": total, 
                                            "Papel": "Orientador" if eh_orientador else "Banca",
                                            "Data_Hora": obter_agora().strftime("%d/%m/%Y %H:%M")
                                        }])
                                        df_f = pd.concat([df_at, nova_l], ignore_index=True)
                                        conn.update(worksheet="Respostas", data=df_f)
                                        st.cache_data.clear()
                                        
                                        st.success(f"✅ Sucesso! Nota oficial {total}/{v_max} gravada na planilha.")
                                        time.sleep(2)
                                        st.rerun()
                                    except Exception as e:
                                        time.sleep(1)
                                        st.rerun()
