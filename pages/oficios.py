import streamlit as st
import random
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Módulo de Ofícios - CRIVO", page_icon="📄", layout="wide")

# 2. DESIGN CUSTOMIZADO (CSS)
st.markdown("""
    <style>
    .titulo-principal { color: #002147; font-family: 'Arial'; font-weight: bold; margin-bottom: 5px; }
    .cartao-ticket { background-color: #ffffff; padding: 20px; border-radius: 8px; border-left: 6px solid #002147
