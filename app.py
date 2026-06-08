import streamlit as st
import pandas as pd
from datetime import datetime
import time

# 1. CONFIGURAÇÃO E VISUAL
st.set_page_config(page_title="CRIVO - Gestão Acadêmica", layout="centered")

st.markdown("""
    <style>
    header {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden;}
    .stButton button { width: 100% !important; border-radius: 10px !important; height: 3.5em !important; background-color: #002147 !important; color: white !important; font-weight: bold !important; border: none !important; }
    .bloco-cabecalho { background-color: #002147 !important; padding: 25px !important; border-radius: 12px !important; color: white !important; margin-bottom: 25px !important; box-shadow: 0px 4px 10px rgba(0,0,0,0.1) !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO (LINK PÚBLICO CSV)
URL_ESCALACAO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT66dKuSdRkQiZzhsxc2ZwS8Gph7GeKo-OOtLfSkCo9UkhY6CdtzlZQxqE7aI8AQZ-nLwARbT3AYt8f/pub?gid=0&single=true&output=csv"
URL_RESPOSTAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT66dKuSdRkQiZzhsxc2ZwS8Gph7GeKo-OOtLfSkCo9UkhY6CdtzlZQxqE7aI8AQZ-nLwARbT3AYt8f/pub?gid=247901801&single=true&output=csv"

@st.cache_data(ttl=60)
def carregar_dados():
    return pd.read_csv(URL_ESCALACAO), pd.read_csv(URL_RESPOSTAS)

df_escalacao, df_respostas = carregar_dados()

# 3. CABEÇALHO
st.markdown("""
    <div class="bloco-cabecalho">
        <h1>🎓 CRIVO</h1>
        <h3>Sistema de Gestão de Bancas Acadêmicas</h3>
    </div>
    """, unsafe_allow_html=True)

# 4. FUNÇÃO DE HORA (SUBSTITUI O PYTZ)
def obter_agora():
    return datetime.now()




# FUNÇÃO PARA ENCURTAR NOMES NA EXIBIÇÃO DO APP
def tratar_nome_curto(nome_completo):
    if not nome_completo or pd.isna(nome_completo):
        return ""
    partes = str(nome_completo).strip().split()
    if len(partes) > 1:
        return f"{partes[0]} {partes[1]}"
    return partes[0]

# 3. CONEXÃO COM GOOGLE SHEETS

def get_data(aba, ttl_sec=2):
    return conn.read(worksheet=aba, ttl=ttl_sec)

try:
    df_escalacao = get_data("Escalacao", ttl_sec=300)
except:
    st.error("Conectando ao banco de dados... Aguarde.")
    time.sleep(1)
    st.rerun()

# --- MAPEAMENTO CASE-INSENSITIVE DAS COLUNAS DA ESCALAÇÃO ---
colunas_reais = {str(col).strip().lower(): col for col in df_escalacao.columns}

c_av1_email = colunas_reais.get('email_avaliador_1')
c_av1_nome = colunas_reais.get('avaliador_1')
c_av2_email = colunas_reais.get('email_avaliador_2')
c_av2_nome = colunas_reais.get('avaliador_2')
c_sup_email = colunas_reais.get('email_suplente')
c_sup_nome = colunas_reais.get('avaliador_suplente')
c_ori_email = colunas_reais.get('email_orientador')
c_ori_nome = colunas_reais.get('orientador')
c_turma = colunas_reais.get('turma')
c_titulo = colunas_reais.get('titulo')
c_data = colunas_reais.get('data')
c_horario = colunas_reais.get('horario')

# COLUNAS REAIS DA PLANILHA PARA SALVAR O FECHAMENTO DE APTIDÃO (IMAGEM 07643f.png)
c_aptidao_col = colunas_reais.get('aptidão defesa')
c_assinatura_col = colunas_reais.get('assinatura orientador')

# MAPEAMENTO DAS COLUNAS SEPARADAS DE ALUNOS
c_aluno1 = colunas_reais.get('aluno_1')
c_aluno2 = colunas_reais.get('aluno_2')
c_aluno3 = colunas_reais.get('aluno_3')
c_aluno4 = colunas_reais.get('aluno_4')
c_aluno5 = colunas_reais.get('aluno_5')

# FUNÇÃO AUXILIAR PARA CHECAR SE O EMAIL EXISTE NA COLUNA MAPEADA
def verificar_presenca_email(email, coluna_real):
    if not coluna_real:
        return False
    return email in df_escalacao[coluna_real].astype(str).str.strip().str.lower().unique()

# --- TRATAMENTO SEGURO DA ABA DE RESPOSTAS ---
colunas_respostas_obrigatorias = ["Avaliador", "Email_Avaliador", "Alunos", "Nota_Final", "Papel", "Data_Hora"]
try:
    df_respostas = get_data("Respostas", ttl_sec=0)
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
    st.subheader("Sistema de Gestão de Bancas Acadêmicas")
    st.caption("© 2026 Desenvolvido por Wanessa Sales de Almeida")
    st.divider()

    st.write("### Identificação do Docente")
    email_raw = st.text_input("Digite seu e-mail cadastrado:").strip()
    if st.button("Acessar Sistema"):
        if email_raw:
            email_limpo = email_raw.lower()
            
            id_banca1 = verificar_presenca_email(email_limpo, c_av1_email)
            id_banca2 = verificar_presenca_email(email_limpo, c_av2_email)
            id_suplente = verificar_presenca_email(email_limpo, c_sup_email)
            id_orienta = verificar_presenca_email(email_limpo, c_ori_email)
            
            if id_banca1 or id_banca2 or id_suplente or id_orienta:
                st.session_state.email = email_limpo
                st.query_params["user"] = email_limpo
                st.rerun()
            else:
                st.error("E-mail não autorizado ou não encontrado na escalação.")
    st.stop()

# --- DEFINIÇÃO DO PAPEL LOGADO ---
email_user = st.session_state.email
eh_orientador = False
eh_banca = False
nome_completo_docente = ""

if verificar_presenca_email(email_user, c_ori_email):
    eh_orientador = True
    nome_completo_docente = df_escalacao[df_escalacao[c_ori_email].astype(str).str.lower() == email_user][c_ori_nome].iloc[0]
elif verificar_presenca_email(email_user, c_av1_email):
    eh_banca = True
    nome_completo_docente = df_escalacao[df_escalacao[c_av1_email].astype(str).str.lower() == email_user][c_av1_nome].iloc[0]
elif verificar_presenca_email(email_user, c_av2_email):
    eh_banca = True
    nome_completo_docente = df_escalacao[df_escalacao[c_av2_email].astype(str).str.lower() == email_user][c_av2_nome].iloc[0]
elif verificar_presenca_email(email_user, c_sup_email):
    eh_banca = True
    nome_completo_docente = df_escalacao[df_escalacao[c_sup_email].astype(str).str.lower() == email_user][c_sup_nome].iloc[0]

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

# CABEÇALHO EM BLOCO IMPACTANTE COM AS CORES DO PAPEL
sub_titulo_texto = "Sistema de Gestão de Bancas Acadêmicas" if not eh_orientador else "Sistema de Gestão de Orientações"
st.markdown(f"""
    <div class="bloco-cabecalho">
        <h1>🎓 CRIVO</h1>
        <h3>{sub_titulo_texto}</h3>
        <p style="font-size: 0.85em; opacity: 0.8;">© 2026 Desenvolvido por Wanessa Sales de Almeida</p>
    </div>
    """, unsafe_allow_html=True)

# FUNÇÃO AUXILIAR PARA MONTAR A LISTA DE ALUNOS REAL DE UMA LINHA DA ESCALAÇÃO
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
        possiveis = df_escalacao[df_escalacao[c_ori_email].astype(str).str.lower() == email_user].copy()
        linhas_pendentes = []
        for idx, row in possiveis.iterrows():
            alunos_grupo = obter_lista_alunos_linha(row)
            turma_check = str(row[c_turma]).strip().upper() if c_turma else ""
            
            # Checa se o orientador já lançou as notas de cada aluno individualmente
            avaliados = df_respostas[(df_respostas["Email_Avaliador"] == email_user) & (df_respostas["Papel"] == "Orientador")]["Alunos"].tolist()
            alunos_restantes = [a for a in alunos_grupo if a not in avaliados]
            
            # LÓGICA DE ETAPA: Se for TCC II e já avaliou todos os alunos, mas NÃO preencheu a aptidão na planilha ainda, continua pendente para a tela seguinte!
            ja_preencheu_aptidao = pd.notna(row.get(c_aptidao_col)) and str(row.get(c_aptidao_col)).strip() != "" if c_aptidao_col else False
            precisa_tela_aptidao = ("TCC II" in turma_check or "TCC 2" in turma_check) and not ja_preencheu_aptidao
            
            if alunos_restantes or precisa_tela_aptidao:
                linhas_pendentes.append(row)
                total_pendencias_contador += len(alunos_restantes) + (1 if precisa_tela_aptidao and not alunos_restantes else 0)
        if lines_pendentes := linhas_pendentes:
            pendentes = pd.DataFrame(lines_pendentes)
    else:
        cond_banca = pd.Series(False, index=df_escalacao.index)
        if c_av1_email:
            cond_banca |= (df_escalacao[c_av1_email].astype(str).str.lower() == email_user)
        if c_av2_email:
            cond_banca |= (df_escalacao[c_av2_email].astype(str).str.lower() == email_user)
        if c_sup_email:
            cond_banca |= (df_escalacao[c_sup_email].astype(str).str.lower() == email_user)
            
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

# --- AMBIENTE VISUAL DO DOCENTE COM BLOCO DE SAÍDA SEGURO ---
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

# --- AVISO DE CONFIRMAÇÃO DE SAÍDA ---
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
        turma_bruta = str(dados[c_turma]).strip().upper() if c_turma else ""
        alunos_reais_lista = obter_lista_alunos_linha(dados)
        string_grupo_completo = ", ".join(alunos_reais_lista)
        
        # Identifica o índice da linha na planilha real para atualizações diretas
        linha_index_planilha = dados.name + 2 
        
        banca_liberada = True
        msg_trava = ""
        
        if not eh_orientador:
            try:
                val_data = str(dados[c_data]).strip() if c_data else ""
                val_horario = str(dados[c_horario]).strip() if c_horario else ""
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
            st.write(f"**Título:** {dados[c_titulo] if c_titulo else ''}")
            st.write(f"**Orientador:** {tratar_nome_curto(dados[c_ori_nome]) if c_ori_nome else ''}")
            st.write(f"**Integrantes do Grupo:** {string_grupo_completo}")
            st.write(f"**Data/Horário Cadastrado:** {dados[c_data] if c_data else ''} às {dados[c_horario] if c_horario else ''}")

        if not banca_liberada:
            st.warning(msg_trava)
        else:
            aluno_alvo_final = string_grupo_completo
            exibir_formulario_notas = True
            exibir_tela_aptidao_final = False

            if eh_orientador:
                if "MCM V" in turma_bruta or "MCM 5" in turma_bruta:
                    exibir_formulario_notas = False
                    st.warning("⚠️ Nota do orientador não aplicável para esta turma. A turma MCM V possui 100% da nota final atribuída exclusivamente pela banca examinadora.")
                else:
                    # Filtra quais alunos deste grupo já ganharam nota do Orientador
                    avaliados_na_aba = df_respostas[(df_respostas["Email_Avaliador"] == email_user) & (df_respostas["Papel"] == "Orientador")]["Alunos"].tolist()
                    lista_alunos_individuais = [a for a in alunos_reais_lista if a not in avaliados_na_aba]
                    
                    if lista_alunos_individuais:
                        aluno_alvo_final = st.selectbox("👤 Selecione o Aluno para atribuir a nota individual:", lista_alunos_individuais)
                    else:
                        exibir_formulario_notas = False
                        # SEGUNDA TELA ATIVADA: Se for TCC II e as notas individuais acabaram, abre o fechamento!
                        if "TCC II" in turma_bruta or "TCC 2" in turma_bruta:
                            exibir_tela_aptidao_final = True
                        else:
                            st.success("Todos os alunos deste grupo já foram avaliados por si!")

            # -----------------------------------------------------------------
            # TELA SEGUINTE DE FECHAMENTO: SÓ VAI APARECER PARA TCC II APÓS AS NOTAS INDIVIDUAIS
            # -----------------------------------------------------------------
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
                    
                    assinatura_texto = st.text_input(
                        "**Assinatura Digital (Digite seu Nome Completo para assinar):**",
                        value=""
                    ).strip()
                    
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
                                    
                                    # Grava direto nas colunas R e S que você criou na planilha (Imagem 07643f.png)
                                    df_atualizar_linha.loc[linha_index_planilha - 2, c_aptidao_col] = resposta_aptidao
                                    df_atualizar_linha.loc[linha_index_planilha - 2, c_assinatura_col] = assinatura_texto
                                    
                                    conn.update(worksheet="Escalacao", data=df_atualizar_linha)
                                    
                                    st.balloons()
                                    st.success("🎉 Ficha de Aptidão registrada e assinada com sucesso! Lote concluído.")
                                    time.sleep(1.5)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao salvar: {e}")

            # --- FORMULÁRIO DE AVALIAÇÃO DE NOTAS (TELA 1) ---
            elif exibir_formulario_notas:
                @st.fragment
                def formulario_avaliacao(aluno_para_salvar):
                    rubrica = {}
                    
                    if eh_orientador:
                        st.info(f"🌱 Avaliando individualmente o discente: **{aluno_para_salvar}**")
                        
                        if "MCM IV" in turma_bruta or "MCM 4" in turma_bruta:
                            rubrica = {
                                "Desenv. - Envolvimento e Responsabilidade": (5, "Participação proativa, demonstrando alta responsabilidade e comprometimento no processo de elaboração."),
                                "Desenv. - Relação com Orientador / Diálogo": (5, "Relação colaborativa, com boa abertura ao diálogo e aceitação de sugestões."),
                                "Desenv. - Desempenho e Cumprimento de Tarefas": (5, "Desempenho satisfatório, com activities realizadas de forma competente e engajada."),
                                "Desenv. - Pontualidade e Compromisso": (5, "Pontualidade é mantida consistentemente, demonstrando compromisso com o processo."),
                                "Responsabilidade com a Aprendizagem": (5, "Responsabilidade evidente em buscar ativamente oportunidades de aprendizado e aprimoramento."),
                                "Texto - Justificativa do Estudo": (6, "Apresenta com clareza a relevância científica, social ou profissional; bem estruturada e relacionada ao problema."),
                                "Texto - Objetivo Geral e Específicos": (6, "Objetivo geral claro, coerente com a justificativa; objetivos específicos bem formulados e articulados."),
                                "Texto - Fundamentação Teórica / Referências": (6, "Referencial teórico relevante, atualizado (últimos 5 anos em sua maioria) e articulado ao tema."),
                                "Texto - Metodologia Proposta": (6, "Método bem descrito, adequado aos objetivos, com definição de tipo de estudo, população e análise."),
                                "Texto - Cronograma de Execução": (3, "Cronograma bem estruturado, com etapas claras e prazos viáveis."),
                                "Texto - Estrutura, Linguagem e Formatação": (3, "Texto bem escrito, estruturado, sem erros relevantes; segue as normas (ABNT ou Vancouver)."),
                                "Relatório - Relatório de Pesquisa": (10, "Apreciação técnica do orientador sobre o documento final de consolidação dos dados compilados pelo discente.")
                            }
                        elif "TCC I" in turma_bruta or "TCC 1" in turma_bruta:
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
                        elif "TCC II" in turma_bruta or "TCC 2" in turma_bruta:
                            rubrica = {
                                "Discente - Envolvimento e Responsabilidade": (5, "Participação proativa, demonstrou alta responsabilidade e comprometimento no processo de elaboração do artigo."),
                                "Discente - Relação com Orientador / Diálogo": (5, "Relação colaborativa, com boa abertura ao diálogo e aceitação de sugestões."),
                                "Discente - Desempenho / Cumprimento de Tarefas": (4, "Desempenho satisfatório, com atividades realizadas de forma competente e engajada."),
                                "Discente - Pontualidade e Compromisso": (3, "Pontualidade é mantida consistentemente, o que demonstra compromisso com o processo."),
                                "Responsabilidade com a Aprendizagem": (3, "Responsabilidade evidente em buscar ativamente oportunidades de aprendizado e de aprimoramento."),
                                "Artigo - Estruturação e Escrita Científica": (5, "Estrutura adequada, com fluidez, concisão e excelência na redação científica."),
                                "Artigo - Fundamentação e Atualização Bibliográfica": (4, "Fundamentação crítica, bem estruturada e com autores atuais e pertinentes à área médica."),
                                "Artigo - Apresentação e Discussão dos Resultados": (4, "Resultados apresentados com clareza, com discussão crítica e integração aos achados da literatura."),
                                "Artigo - Rigor Metodológico": (4, "Métodos bem descritos, compatíveis com o delineamento e objetivos do estudo."),
                                "Artigo - Conclusão e Relevância Científica": (3, "Conclusão clara, alinhada aos objetivos e resultados, com destaque à relevância científica e aplicabilidade prática.")
                            }
                    else:
                        st.info("🎓 Você está visualizando a Rubrica de Avaliação da Banca (Nota para o Grupo todo).")
                        
                        if "MCM IV" in turma_bruta or "MCM 4" in turma_bruta:
                            rubrica = {
                                "Delineamento - Rigor Científico e Metodologia": (10, "Adequação do desenho do estudo, viabilidade técnica e delineamento claro dos procedimentos propostos."),
                                "Apresentação Oral - Clareza e Domínio": (10, "Domínio conceitual do conteúdo exposto, postura, uso do tempo regulamentar e clareza na defesa oral."),
                                "Coerência - Estrutura Geral do Projeto": (10, "Lógica interna do manuscrito, alinhamento fluido entre a justificativa, os objetivos e o método.")
                            }
                        elif "TCC I" in turma_bruta or "TCC 1" in turma_bruta:
                            rubrica = {
                                "Tema": (3, "Clareza, delimitação e a atualidade do tema proposto."),
                                "Resumo": (1, "Objetivo, método, resultados esperados e palavras-chave."),
                                "Introdução": (5, "Contextualização do tema e problema de pesquisa."),
                                "Justificativa": (5, "Importância do trabalho e contribuição científica."),
                                "Objetivos": (5, "Objetivo geral e específicos mensuráveis."),
                                "Metodologia": (10, "Desenho do estudo, critérios e ética."),
                                "Referências": (1, "Uso de normas ABNT/Vancouver."),
                                "Apresentação Oral": (10, "Domínio de conteúdo, postura e clareza."),
                                "Coerência": (10, "Lógica entre introdução, objetivos e métodos."),
                                "Qualidade Visual": (9, "Organização dos slides e recursos."),
                                "Tempo": (1, "Intervalo de 10 a 15 minutos de apresentação.")
                            }
                        elif "TCC II" in turma_bruta or "TCC 2" in turma_bruta or "MCM V" in turma_bruta or "MCM 5" in turma_bruta:
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

                    if not rubrica:
                        return

                    v_max = sum(p for p, h in rubrica.values())
                    st.write(f"### 📝 Critérios (Máximo: {v_max} pontos)")
                    
                    notas = {}
                    for item, (p, help_t) in rubrica.items():
                        notas[item] = st.slider(f"**{item} ({p} pts)**", 0, p, 0, help=help_t, key=f"s_{item}_{aluno_para_salvar}")

                    total = sum(notas.values())
                    st.markdown(f"## Nota Atribuída: {total} / {v_max}")

                    tem_zero = any(v == 0 for v in notas.values())
                    conf_zero = True
                    if tem_zero:
                        st.error("⚠️ Existem critérios com nota zero.")
                        conf_zero = st.checkbox("Confirmo que as notas zero são intencionais.", key=f"c_zero_{aluno_para_salvar}")

                    if st.button("🚀 GRAVAR AVALIAÇÃO NO SISTEMA", key=f"btn_save_{aluno_para_salvar}"):
                        if tem_zero and not conf_zero:
                            st.warning("Confirme as notas zero antes de gravar.")
                        else:
                            with st.spinner("A gravar notas e a sincronizar base de dados..."):
                                try:
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
                                    
                                    st.balloons()
                                    st.success("✅ Avaliação gravada com sucesso!")
                                    time.sleep(1.5)
                                    st.rerun()
                                except:
                                    time.sleep(1)
                                    st.rerun()

                formulario_avaliacao(aluno_alvo_final)

# IMPORTANTE: Remova qualquer linha que tenha 'conn = st.connection...' 
# ou 'from streamlit_gsheets import...' pois elas causam o erro que você está vendo.
