import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
import pandas as pd

# 🔹 Função para autenticação no Google Sheets (sem conversão para JSON)
def autenticar_google_sheets():
    """
    Autentica no Google Sheets usando as credenciais armazenadas no secrets do Streamlit.
    """
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    try:
        # Lê as credenciais diretamente do st.secrets sem conversão para JSON
        secrets_dict = st.secrets["credenciais"]

        # Corrige a formatação da private_key (substitui \\n por \n)
        secrets_dict["private_key"] = secrets_dict["private_key"].replace("\\n", "\n")

        # Cria as credenciais e autentica
        creds = Credentials.from_service_account_info(secrets_dict, scopes=SCOPES)
        client = gspread.authorize(creds)

        return client
    except Exception as e:
        st.error(f"❌ Erro na autenticação com Google Sheets: {e}")
        return None

# 🔹 Teste de conexão
if st.button("🔍 Testar Conexão com Google Sheets"):
    client = autenticar_google_sheets()
    if client:
        st.success("✅ Autenticação bem-sucedida!")
    else:
        st.error("❌ Falha na autenticação. Verifique suas credenciais.")
