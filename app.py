import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.title("Sistema Crivo")

# Lista de escopos necessária para acessar o Drive e Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    # Em vez de um JSON corrompido, vamos usar uma forma que garante a integridade da chave
    # Certifique-se de que o Secrets contém os campos exatos como chaves individuais
    creds = ServiceAccountCredentials.from_json_keyfile_dict({
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"].replace('\\n', '\n'), # CORREÇÃO CRÍTICA AQUI
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"]
    }, scope)

    gc = gspread.authorize(creds)
    # Abre pela URL (certifique-se de que a planilha está compartilhada com o client_email)
    sh = gc.open_by_url("COLE_AQUI_A_SUA_URL_DA_PLANILHA")
    
    st.success("Conexão estabelecida com sucesso!")
except Exception as e:
    st.error(f"Erro na conexão: {e}")
