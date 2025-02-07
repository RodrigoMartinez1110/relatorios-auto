import json
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd

# 🟢 Configuração da página no Streamlit
st.set_page_config(page_title="Processador de Campanhas", layout="wide")
st.title("📊 Processador de Dados de Campanhas")

# 🟢 Função para autenticar no Google Sheets
def autenticar_google_sheets():
    """Autentica e retorna o cliente gspread"""
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    try:
        # Lê as credenciais do Streamlit secrets como dicionário
        secrets_dict = dict(st.secrets["credenciais"])  # Converte AttrDict para dict

        # Corrige a formatação da private_key
        secrets_dict["private_key"] = secrets_dict["private_key"].replace("\\n", "\n")
        
        # Cria as credenciais e autentica
        creds = Credentials.from_service_account_info(secrets_dict, scopes=SCOPES)
        client = gspread.authorize(creds)

        return client

    except Exception as e:
        st.error(f"Erro na autenticação com Google Sheets: {e}")
        return None


# 🟢 Upload do arquivo CSV
uploaded_file = st.file_uploader("📂 Faça upload do arquivo CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Ler o arquivo CSV e tratar possíveis erros
        base = pd.read_csv(uploaded_file, sep=';', encoding='utf-8', low_memory=False)

        if "NOME CAMPANHA" not in base.columns:
            st.error("❌ O arquivo não contém a coluna 'NOME CAMPANHA'. Verifique o formato do CSV.")
            st.stop()  # Para a execução do código aqui

    except Exception as e:
        st.error(f"❌ Erro ao carregar o arquivo CSV: {e}")
        st.stop()

    # 🟢 Mapeamento para normalizar convênios
    mapeamento_convenios = {
        "GOV SP": ["governo de sp", "gov sp", "governo sp"],
        "GOV CE": ["gov ce", "ceara", "governo do ceara"],
        "GOV RJ": ["governo de rj", "gov rj", "governo rio"],
        "GOV AL": ["governo de al", "gov al", "governo alagoas"],
        "PREF SP": ["pref sp", "prefeitura de são paulo"],
        "PREF RJ": ["pref rj", "prefeitura do rio de janeiro"]
    }

    def normalizar_convenio(nome_campanha):
        """ Normaliza os convênios """
        if pd.notna(nome_campanha):
            nome_campanha = nome_campanha.lower().strip()
            for convenio, nomes_possiveis in mapeamento_convenios.items():
                if any(nome in nome_campanha for nome in nomes_possiveis):
                    return convenio
        return "OUTRO"

    base["CONVENIO"] = base["NOME CAMPANHA"].apply(normalizar_convenio)

    # 🟢 Mapeamento para normalizar produtos
    mapeamento_produto = {
        "NOVO": ["novo", "credito novo", "negativos", "tomador"],
        "BENEFICIO E CARTÃO": ["cartões", "cartoes", "benef & cartao"],
        "CARTÃO": ["cartão", "cartao", "consignado"],
        "BENEFICIO": ["benef", "beneficio", "complementar"]
    }

    def normalizar_produto(nome_produto):
        """ Normaliza os produtos """
        if pd.notna(nome_produto):
            nome_produto = nome_produto.lower().strip()
            for produto, nomes_possiveis in mapeamento_produto.items():
                if any(nome in nome_produto for nome in nomes_possiveis):
                    return produto
        return "OUTRO"

    base["PRODUTO"] = base["NOME CAMPANHA"].apply(normalizar_produto)

    # 🟢 Converter data/hora
    base['DATA/HORA DISPARO'] = pd.to_datetime(base['DATA/HORA DISPARO'], errors='coerce', dayfirst=True)
    base['DATA DISPARO'] = base['DATA/HORA DISPARO'].dt.strftime("%d/%m/%Y")
    base['HORA DISPARO'] = base['DATA/HORA DISPARO'].dt.strftime("%H:%M")

    base['HORA DISPARO'] = base.groupby(['DATA DISPARO', 'CONVENIO', 'PRODUTO'])['HORA DISPARO'].transform('min')

    # 🟢 Criar tabela agrupada
    tabela = base.groupby(['DATA DISPARO', 'HORA DISPARO', 'CONVENIO', 'PRODUTO'])['ID CAMPANHA'].size().reset_index(name='quantidade')
    tabela['canal'] = 'RCS'
    tabela['gasto'] = tabela['quantidade'] * 0.105

    # 🟢 Exibir DataFrames no Streamlit
    st.subheader("📋 Base de Dados Formatada (Amostra)")
    st.dataframe(base.head(50))  # Exibe apenas as 50 primeiras linhas para evitar lentidão

    st.subheader("📊 Tabela Agrupada")
    st.dataframe(tabela)

    # 🟢 Função para enviar ao Google Sheets
    def enviar_para_sheets(df):
        """ Envia os dados para o Google Sheets """
        client = autenticar_google_sheets()
    
        if client is None:
            st.error("❌ Autenticação falhou. Verifique suas credenciais.")
            return

        try:
            sheet = client.open("controle_disparos").sheet1
            existing = sheet.get_all_values()
            start_row = len(existing) + 1  
            data_to_insert = df.values.tolist()
            sheet.insert_rows(data_to_insert, row=start_row)

            st.success("✅ Dados enviados para o Google Sheets com sucesso!")
    
        except Exception as e:
            st.error(f"❌ Erro ao enviar dados para o Google Sheets: {e}")

    # 🟢 Botão para enviar dados ao Google Sheets
    if st.button("🔍 Testar Conexão com Google Sheets"):
    client = autenticar_google_sheets()
    if client:
        try:
            sheet = client.open("controle_disparos").sheet1
            st.success("✅ Conexão com o Google Sheets bem-sucedida!")
        except Exception as e:
            st.error(f"❌ Erro ao acessar a planilha: {e}")
    else:
        st.error("❌ Autenticação falhou. Verifique suas credenciais.")
    # 🟢 Botão para baixar os dados processados
    st.download_button(
        label="📥 Baixar Tabela Agrupada",
        data=tabela.to_csv(index=False, sep=';').encode('utf-8'),
        file_name="tabela_formatada.csv",
        mime="text/csv"
    )
