import json
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd


# 🟢 Função para autenticar no Google Sheets
def autenticar_google_sheets():
    """
    Autentica no Google Sheets usando as credenciais armazenadas no secrets do Streamlit.
    """
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    try:
        # Lê as credenciais do Streamlit secrets e converte para dicionário
        secrets_dict = dict(st.secrets["credenciais"])

        # Corrige a formatação da private_key (substitui \\n por \n)
        secrets_dict["private_key"] = secrets_dict["private_key"].replace("\\n", "\n")

        # Cria as credenciais e autentica
        creds = Credentials.from_service_account_info(secrets_dict, scopes=SCOPES)
        client = gspread.authorize(creds)

        return client
    except Exception as e:
        st.error(f"❌ Erro na autenticação com Google Sheets: {e}")
        return None


# 🟢 Função para enviar dados ao Google Sheets
def enviar_dados_google_sheets(client, nome_planilha, df):
    """
    Envia os dados para uma planilha do Google Sheets.
    """
    try:
        sheet = client.open(nome_planilha).sheet1

        # Converte o DataFrame em lista de listas
        dados_para_enviar = df.values.tolist()

        # Envia os dados para o Google Sheets (a partir da linha 2 para não sobrescrever o cabeçalho)
        existing_data = sheet.get_all_values()
        start_row = len(existing_data) + 1
        sheet.insert_rows(dados_para_enviar, row=start_row)

        st.success("✅ Dados enviados para o Google Sheets com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao enviar dados para o Google Sheets: {e}")


# Configuração principal do Streamlit
st.set_page_config(page_title="Envio para Google Sheets", layout="wide")
st.title("📊 Envio de Dados para Google Sheets com Streamlit")

# Nome da planilha no Google Sheets
nome_planilha = "controle_disparos"

# Exemplo de dados para envio
dados_para_envio = {
    "DATA DISPARO": ["05/02/2025", "05/02/2025"],
    "HORA DISPARO": ["08:28", "09:58"],
    "CONVENIO": ["GOV SP", "GOV CE"],
    "PRODUTO": ["CARTÃO", "BENEFICIO"],
    "quantidade": [20324, 11200],
    "canal": ["RCS", "RCS"],
    "gasto": [2134.02, 1186.50]
}
df_novo = pd.DataFrame(dados_para_envio)

# Mostrar o DataFrame no Streamlit
st.dataframe(df_novo)

# Botão para autenticar e enviar os dados
if st.button("📤 Enviar Dados para o Google Sheets"):
    client = autenticar_google_sheets()

    if client:
        enviar_dados_google_sheets(client, nome_planilha, df_novo)
    else:
        st.error("❌ Autenticação falhou. Verifique suas credenciais.")
