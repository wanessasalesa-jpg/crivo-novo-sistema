import streamlit as st
import pandas as pd

st.title("Sistema Crivo")

# Substitua pela URL real da sua planilha
sheet_url = "COLE_AQUI_A_URL_DA_SUA_PLANILHA"

try:
    # Este formato exporta a planilha como CSV, sem precisar de chaves
    url = sheet_url.replace("/edit#gid=", "/export?format=csv&gid=")
    df = pd.read_csv(url)
    
    st.success("Conexão estabelecida!")
    st.write(df.head())
except Exception as e:
    st.error(f"Erro na conexão: {e}")
