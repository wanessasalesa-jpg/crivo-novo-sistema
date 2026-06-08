import streamlit as st
import pandas as pd

st.title("Sistema Crivo")

# Substitua pela URL real da sua planilha
sheet_url = "https://docs.google.com/spreadsheets/d/1VF1FPqUy2tZrqwFPuJ0SlWVdPLKm6gBn3yu0IctJK44/edit?gid=0#gid=0"

try:
    # Este formato exporta a planilha como CSV, sem precisar de chaves
    url = sheet_url.replace("/edit#gid=", "/export?format=csv&gid=")
    df = pd.read_csv(url)
    
    st.success("Conexão estabelecida!")
    st.write(df.head())
except Exception as e:
    st.error(f"Erro na conexão: {e}")
