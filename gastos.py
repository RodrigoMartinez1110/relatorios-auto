import streamlit as st
import gspread
import json
import pandas as pd
from google.oauth2.service_account import Credentials

# 📌 Carregar credenciais do Streamlit Secrets
if "GOOGLE_CREDENTIALS" in st.secrets:
    credentials_info = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    
    # 🔥 Corrigir o formato da private_key substituindo '\\n' por '\n'
    credentials_info["private_key"] = credentials_info["private_key"].replace("\\n", "\n")

    creds = Credentials.from_service_account_info(credentials_info, scopes=[
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ])
    client = gspread.authorize(creds)
else:
    st.error("Erro: Credenciais do Google não encontradas! Configure no Streamlit Cloud.")
    st.stop()

# 📌 ID e Nome da Planilha
SHEET_ID = "1RKk3kn8hkhjAQswgyhoMIlwVyHDSZAD72mF4BsRYAHs"  # ID da sua planilha
SHEET_NAME = "controle"  # Substitua pelo nome real da aba

# 📌 Conectar ao Google Sheets
try:
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
except Exception as e:
    st.error(f"Erro ao conectar à planilha: {e}")
    st.stop()

st.title("📊 Alimentação de Dados no Google Sheets")

# 📌 Criar campos de entrada no Streamlit
nome = st.text_input("Nome")
email = st.text_input("Email")
idade = st.number_input("Idade", min_value=0, max_value=100, step=1)

# 📌 Botão para enviar os dados
if st.button("Enviar Dados"):
    if nome and email and idade:
        sheet.append_row([nome, email, idade])
        st.success("✅ Dados adicionados com sucesso!")
    else:
        st.warning("⚠️ Preencha todos os campos antes de enviar.")

# 📌 Exibir os dados da planilha
st.subheader("📋 Dados na Planilha:")
dados = sheet.get_all_records()
df = pd.DataFrame(dados)
st.dataframe(df)
