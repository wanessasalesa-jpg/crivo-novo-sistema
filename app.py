import streamlit as st
import pandas as pd

st.title("Sistema Crivo")

# COLE AQUI O LINK QUE O GOOGLE TE DEU APÓS "PUBLICAR NA WEB"
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT66dKuSdRkQiZzhsxc2ZwS8Gph7GeKo-OOtLfSkCo9UkhY6CdtzlZQxqE7aI8AQZ-nLwARbT3AYt8f/pub?gid=0&single=true&output=csv" 

try:
    df = pd.read_csv(sheet_url)
    st.success("Dados carregados com sucesso!")
    st.dataframe(df) # Isso mostra a tabela organizada
except Exception as e:
    st.error(f"Erro ao ler os dados: {e}")
