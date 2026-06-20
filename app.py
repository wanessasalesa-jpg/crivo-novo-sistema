import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta
import time
import pytz 

# 1. CONFIGURAÇÃO DA PÁGINA (SEM LIMPEZA GLOBAL DE CACHE AQUI)
st.set_page_config(page_title="CRIVO - Gestão Acadêmica", layout="centered")

# Inicia a memória local do celular do professor para não depender de baixar a planilha o tempo todo
if 'concluidos' not in st.session_state:
    st.session_state.concluidos = []

# 2. FUSO HORÁRIO DE BRASÍLIA
fuso_bruta = pytz.timezone('America/Sao_Paulo')

def obter_agora():
    return datetime.now(fuso_bruta)

# FUNÇÃO PARA ENCURTAR NOMES
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
    # Memória de 5 minutos: impede que o app trave ao mover os sliders
    df_escalacao = conn.read(worksheet="Escalacao", ttl=300)
    df_escalacao.columns = df_escalacao.columns.astype(str).str.strip().str.lower()
except:
    st.error("Conectando ao banco de dados... Aguarde.")
    time.sleep(1)
    st.rerun()

# --- MAPEAMENTO BLINDADO DE COLUNAS ---
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
        .stButton button { width: 100% !important; border-radius: 10px !important; height: 3.5em !important; background-color: #002147 !important; color: white !important; font-weight: bold !important; border: none !important; }
        </style>
        """, unsafe_allow_html=True)

    # MARCADOR VISUAL DE QUE O SISTEMA ANTI-TRAVAMENTO ESTÁ NO AR
    st.title("🎓 CRIVO - VERSÃO ESTÁVEL")
    st.subheader("Sistema de Gestão de Bancas Acadêmicas")
    st.caption("© 2026 Desenvolvido por Wanessa Sales de Almeida")
    st.divider()

    st.write("### Identificação do Docente")
    email_raw = st.text_input("Digite seu e-mail cadastrado:").strip()
    if st.button("Acessar Sistema"):
        if email_raw:
            email_limpo = email_raw.lower().strip()
            
            # Leitura ao vivo apenas no login
            df_fresh = conn.read(worksheet="Escalacao", ttl=0)
            df_fresh.columns = df_fresh.columns.astype(str).str.strip().str.lower()
            
            id_banca1 = email_limpo in df_fresh[c_av1_email].astype(str).str.strip().str.lower().unique() if c_av1_email else False
            id_banca2 = email_limpo in df_fresh[c_av2_email].astype(str).str.strip().str.lower().unique() if c_av2_email else False
            id_suplente = email_limpo in df_fresh[c_sup_email].astype(str).str.strip().str.lower().unique() if c_sup_email else False
            id_orienta = email_limpo in df_fresh[c_ori_email].astype(str).str.strip().str.lower().unique() if c_ori_email else False
            
            if id_banca1 or id_banca2 or id_suplente or id_orienta:
                st.session_state.clear()
                st.session_state.concluidos = []
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
    .bloco-cabecalho {{ background-color: {cor_primaria} !important; padding: 25px !important; border-radius: 12px !important; color: {cor_texto_bloco} !important; margin-bottom: 25px !important; box-shadow: 0px 4px 10px rgba(0,0,0,0.1) !important; }}
    .bloco-cabecalho h1, .bloco-cabecalho h3, .bloco-cabecalho p {{ color: {cor_texto_bloco} !important; margin: 0 !important; padding: 2px 0 !important; }}
    .stButton button {{ width: 100% !important; border-radius: 10px !important; height: 3.5em !important; background-color: {cor_primaria} !important; color: white !important; font-weight: bold !important; border: none !important; }}
    </style>
    """, unsafe_allow_html=True)

sub_titulo_texto = "Sistema de Gestão de Bancas Acadêmicas" if not eh_orientador else "Sistema de Gestão de Orientações"
st.markdown(f"""
    <div class="bloco-cabecalho">
        <h1>🎓 CRIVO</h1>
        <h3>{sub_titulo_texto}</h3>
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

# --- FILTRAGEM DE GRUPOS PENDENTES USANDO MEMÓRIA LOCAL DO CELULAR ---
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
            
            # Combina quem está no banco E quem acabou de ser salvo na memória local
            avaliados_banco = df_respostas[(df_respostas["Email_Avaliador"] == email_user) & (df_respostas["Papel"] == "Orientador")]["Alunos"].tolist()
            avaliados_total = list(set(avaliados_banco + st.session_state.concluidos))
            alunos_restantes = [a for a in alunos_grupo if a not in avaliados_total]
            
            ja_preencheu_banco = pd.notna(row.get(c_aptidao_col)) and str(row.get(c_aptidao_col)).strip() != "" if c_aptidao_col else False
            string_grupo_banca = ", ".join(alunos_grupo)
            ja_preencheu_sessao = f"aptidao_{string_grupo_banca}" in st.session_state.concluidos
            
            precisa_tela_aptidao = ("TCCII" in tb_clean_check or "TCC2" in tb_clean_check) and not ja_preencheu_banco and not ja_preencheu_sessao
            
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
            
            ja_avaliou_banco = not df_respostas[(df_respostas["Email_Avaliador"] == email_user) & (df_respostas["Papel"] == "Banca") & (df_respostas["Alunos"] == string_grupo_banca)].empty
            ja_avaliou_sessao = string_grupo_banca in st.session_state.concluidos
            
            if (not ja_avaliou_banco) and (not ja_avaliou_sessao) and alunos_grupo:
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
                avaliados_banco = df_respostas[(df_respostas["Email_Avaliador"] == email_user) & (df_respostas["Papel"] == "Orientador")]["Alunos"].tolist()
                avaliados_total = list(set(avaliados_banco + st.session_state.concluidos))
                lista_alunos_individuais = [a for a in alunos_reais_lista if a not in avaliados_total]
                
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

            if eh_orientador and exibir_tela_aptidao_final:
                st.markdown("---")
                st.subheader("📋 TELA 2: Ficha de Aptidão de Defesa (Exclusivo TCC II)")
                
                with st.form("form_aptidao_tcc2"):
                    resposta_aptidao = st.radio(
                        "**O projeto de Trabalho de Conclusão de Curso (TCC II) entregue pelo grupo encontra-se:**",
                        ["", "APTO para apresentação", "INAPTO para apresentação"], index=0
                    )
                    assinatura_texto = st.text_input("**Assinatura Digital (Digite seu Nome Completo para assinar):**", value="").strip()
                    
                    if st.form_submit_button("🚀 ENVIAR PARECER E CONCLUIR BANCA"):
                        if resposta_aptidao == "" or assinatura_texto == "":
                            st.error("Por favor, preencha todos os campos obrigatórios.")
                        else:
                            with st.spinner("Gravando parecer de aptidão na planilha..."):
                                sucesso_apt = False
                                for tentativa in range(5):
                                    try:
                                        df_atualizar_linha = conn.read(worksheet="Escalacao", ttl=0)
                                        df_atualizar_linha.columns = df_atualizar_linha.columns.astype(str).str.strip().str.lower()
                                        
                                        if c_aptidao_col in df_atualizar_linha.columns:
                                            df_atualizar_linha[c_aptidao_col] = df_atualizar_linha[c_aptidao_col].astype(object)
                                        if c_assinatura_col in df_atualizar_linha.columns:
                                            df_atualizar_linha[c_assinatura_col] = df_atualizar_linha[c_assinatura_col].astype(object)
                                        
                                        df_atualizar_linha.loc[linha_index_planilha - 2, c_aptidao_col] = resposta_aptidao
                                        df_atualizar_linha.loc[linha_index_planilha - 2, c_assinatura_col] = assinatura_texto
                                        conn.update(worksheet="Escalacao", data=df_atualizar_linha)
                                        sucesso_apt = True
                                        break
                                    except:
                                        time.sleep(1 + tentativa)
                                
                                if sucesso_apt:
                                    st.session_state.concluidos.append(f"aptidao_{string_grupo_completo}")
                                    st.success("🎉 Ficha de Aptidão registrada e assinada com sucesso! Lote concluído.")
                                    time.sleep(1.5)
                                    st.rerun()
                                else:
                                    st.error("❌ Servidor instável. Por favor, CLIQUE NOVAMENTE no botão.")

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
                    st.write(f"### 📝 Critérios (Máximo: {v_max} pontos)")
                    
                    notas = {}
                    for item, (p, help_t) in rubrica.items():
                        if p == 1:
                            notas[item] = st.slider(f"**{item} ({p} pts)**", 0.0, 1.0, 0.0, step=0.5, help=help_t, key=f"s_{item}_{aluno_para_salvar}")
                        else:
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
                            with st.spinner("Sincronizando nota com a planilha... Por favor, aguarde."):
                                sucesso_nota = False
                                for tentativa in range(5):
                                    try:
                                        # Puxa as respostas ao vivo no exato milissegundo da gravação
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
                                        sucesso_nota = True
                                        break
                                    except:
                                        time.sleep(1 + tentativa)
                                
                                if sucesso_nota:
                                    # Grava localmente que o trabalho foi feito! O app não vai procurar no Google mais.
                                    st.session_state.concluidos.append(aluno_para_salvar)
                                    st.success(f"✅ Sucesso! Nota oficial {total}/{v_max} gravada na planilha.")
                                    time.sleep(1.5)
                                    st.rerun()
                                else:
                                    st.error("❌ O servidor do Google Sheets está instável pelo alto tráfego concorrente. Sua nota NÃO foi perdida. Por favor, CLIQUE NOVAMENTE no botão acima para retransmitir.")
