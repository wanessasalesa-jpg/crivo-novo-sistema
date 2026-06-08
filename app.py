import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.title("Sistema Crivo")

# 1. Defina as credenciais como um dicionário direto no código 
# (Já que o Secrets está travando o sistema, vamos simplificar)
creds_dict = {
    "type": "service_account",
    "project_id": "bancasafya",
    "private_key_id": "9734b2f4f8a59e2cebb64e1935b87da1d95d80bf",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC3+n9NWeDxy1fE\nKgNBpv4f7svC1cZSr71QiK5PlnVQLRmSIUzoISrKPy7jPI/ZH7veBaJDHZFAnjcb\noVxKahNgtARBZdxX8yLcXbLQXU5vrHNAmlLLTATXn4/shwS1P0n5WuwbwDwNb01Y\nMpmk1KEISTTWG84QwREqV5fPE8u2GD5X1NNi07vHpxGtfcBLTwPCDUwz0w0aJlI4\nwb3prZ3mb8ZVKUwRLPbAWWgFZj8YnLDapVEWhPcS9ND8aE7Uqzi3xNw84OvmYteJ\nwtWaoQ5mugwClFlKnixoYUyB9DFOnscDOTTmTAWTFztFUCThIs/5uJwwTAy52Ulq\nNEYfwT5FAgMBAAECggEAB6rTn9phTsph6b2zfYqzWArYaJIGrh7/VYogs5XqZTE/\n+dBT92+cbCnWbydwukSBjJbxBHmIumftlYPzx/EkRhkyfTQ8ytiJ6SOphlgBIxPN\niNF1pl3QbNkMQzf8SP5ue4sfwGdSSWAMWeLf9tfarzD31/14KMgXCkv0um9Rg9Ds\nJ363J9AERzJ4cmflnqR3L8yBaSFrUcmqEKFrQ1jKUe31Q9VV9N3fEHnYvktTmg1G\ngdBenoVPcxqELocHTkKwigeXECv9paxEzEZfoGFia9rp7Y9nNOYzMbn+E9LEBDO4\nNMKw4ftIBJ5Z4MMMxuifimf+HSRyjwfK/Yd0RlkqWQKBgQDwO+G8GjVKlKQeDavQ\nJM2XJxw86uHYbNAsk/pXBtj68OAsESPnerZPuNQCcyvlGPPYlQUjTCBui7r0wTYe\nT/zSnds+Y1+xcY4++MxqCSF2RxHURIinqdgROeJd0Cn658Lr0EVNk4OVpJ0P8kJz\nA/y9CaXa93dFg8xhJ6INgVSwCQKBgQDEDXsCPRjwUu09WsF2cDdYwa5T5+yYIO42\n3MK5sewHrMbokr6rf7oG/+/yeyPvuGOwo6X/E5Q4oak7SvJIBHWGBOepupGf51pZ\n81bsqFgVCxNNF4Da0UOyEgICOyR3UBVwQUeXTwS0pR9SYDS0y/tofLBEIG6j+IHV\nXeAPEW+zXQKBgDIp/vAddOVW9pJD/o2fMcMPaqkZzwE3b5zvZYYIqwRzigwJpDqw\n+CLbkIHWdOMI+9pM+96sBdWvneF/+wIHZ96/EcoMTC4sbSyfHWhC8dbV7lYp3XNN\nVw35zVgToMCA5sYBHoeddwunbRioWNHVklATFKwNor1EUUg0U3WIfRupAoGBALgb\nkLCBf7Hvrio32AXJS7Bl8beJzHzwL8QFfDe2BdkPP5uYcsXKpH9+SW6EhTLRDY0L\noQ7w6/hil/G+Z9eJmHPKl2KkeayYLhjak36aeF0KkY2LzM2wRsoqbwh5Ub1Zz0gj\nhX9qDRk3FzrcbaJ7DBULQtw3OK9y5znfdlGwJh1hAoGBAMEeH7krDnUK9LzCQuFX\Bw2QHsyt6lxP5E39oNeQd8L037iMiElN1FYttNiW2McNBLeBDS7Z53qMbYEUXphu\nSUiLrrvRT0A6lLL1rvY2qXfI8gEGYoEnaPubjuGwuFQfigi8VuU8o9lPpfjoUjKN\n5TrT9INhLywepAUJMs3EDf4F\n-----END PRIVATE KEY-----",
    "client_email": "bancasafya@bancasafya.iam.gserviceaccount.com",
    "client_id": "102526082455546573533",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/bancasafya%40bancasafya.iam.gserviceaccount.com"
}

try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    gc = gspread.authorize(creds)
    
    st.success("Conexão estável!")
except Exception as e:
    st.error(f"Erro: {e}")
