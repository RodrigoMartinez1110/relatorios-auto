import pandas as pd
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configuração da página no Streamlit
st.set_page_config(page_title="Processador de Campanhas", layout="wide")
st.title("📊 Processador de Dados de Campanhas")

# Upload do arquivo CSV
uploaded_file = st.file_uploader("📂 Faça upload do arquivo CSV", type=["csv"])

if uploaded_file is not None:
    # Ler o arquivo CSV
    base = pd.read_csv(uploaded_file, sep=';', low_memory=False)

    # Dicionário para normalização dos convênios
    mapeamento_convenios = {
        "GOV SP": ["governo de sp", "gov sp", "governo sp"],
        "GOV CE": ["gov ce", "ceara", "governo do ceara"],
        "GOV RJ": ["governo de rj", "gov rj", "governo rio"],
        "GOV AL": ["governo de al", "gov al", "governo alagoas"],
        "GOV AM": ["governo de am", "gov am", "governo amazonas"],
        "GOV ES": ["governo de es", "gov es", "governo espírito santo"],
        "GOV GO": ["governo de go", "gov go", "governo goiás"],
        "GOV MA": ["governo de ma", "gov ma", "governo maranhão"],
        "GOV MS": ["governo de ms", "gov ms", "governo mato grosso do sul"],
        "GOV MT": ["governo de mt", "gov mt", "governo mato grosso"],
        "GOV PE": ["governo de pe", "gov pe", "governo pernambuco"],
        "GOV PI": ["governo de pi", "gov pi", "governo piauí"],
        "GOV PR": ["governo de pr", "gov pr", "governo paraná"],
        "PREF GYN": ["pref gyn", "pref goiania", "prefeitura de goiânia"],
        "PREF JP": ["pref jp", "prefeitura de joão pessoa"],
        "PREF MARINGA": ["pref maringa", "prefeitura de maringá"],
        "PREF RECIFE": ["pref recife", "prefeitura de recife"],
        "PREF RJ": ["pref rj", "prefeitura do rio de janeiro"],
        "PREF SP": ["pref sp", "prefeitura de são paulo"],
        "PREF SSA": ["pref ssa", "prefeitura de salvador"]
    }

    # Função para normalizar os convênios
    def normalizar_convenio(nome_campanha):
        if pd.notna(nome_campanha):
            nome_campanha = nome_campanha.lower().strip()
            for convenio, nomes_possiveis in mapeamento_convenios.items():
                if any(nome in nome_campanha for nome in nomes_possiveis):
                    return convenio
        return "outro"

    # Aplicar normalização dos convênios
    base["CONVENIO"] = base["NOME CAMPANHA"].apply(normalizar_convenio)

    # Dicionário para normalização dos produtos
    mapeamento_produto = {
        "NOVO": ["novo", "credito novo", "negativos", "tomador", "super", "hubspot", "resgate", "carteira", "menor50", "menor 50", "virada"],
        "BENEFICIO E CARTÃO": ["cartões", "cartoes", "benef & cartao", "cartões consignados"],
        "CARTÃO": ["cartão", "cartao", "consignado"],
        "BENEFICIO": ["benef", "beneficio", "complementar"],
        "NQB": ["nqb"]
    }

    # Função para normalizar os produtos
    def normalizar_produto(nome_produto):
        if pd.notna(nome_produto):
            nome_produto = nome_produto.lower().strip()
            for produto, nomes_possiveis in mapeamento_produto.items():
                if any(nome in nome_produto for nome in nomes_possiveis):
                    return produto
        return "outro"

    # Aplicar normalização dos produtos
    base["PRODUTO"] = base["NOME CAMPANHA"].apply(normalizar_produto)

    # Converter data/hora para datetime
    base['DATA/HORA DISPARO'] = pd.to_datetime(base['DATA/HORA DISPARO'], errors='coerce', dayfirst=True)

    # Criar colunas separadas para data e horário
    base['DATA DISPARO'] = base['DATA/HORA DISPARO'].dt.strftime("%d/%m/%Y")
    base['HORA DISPARO'] = base['DATA/HORA DISPARO'].dt.strftime("%H:%M")
    base['HORA DISPARO'] = base.groupby(['DATA DISPARO', 'CONVENIO', 'PRODUTO'])['HORA DISPARO'].transform('min')

    # Criar tabela agrupada
    tabela = base.groupby(['DATA DISPARO', 'HORA DISPARO', 'CONVENIO', 'PRODUTO'])['ID CAMPANHA'].size().reset_index(name='quantidade')
    tabela['canal'] = 'RCS'
    tabela['gasto'] = tabela['quantidade'] * 0.105

    # Exibir DataFrames no Streamlit
    st.subheader("📋 Base de Dados Formatada")
    st.dataframe(base)

    st.subheader("📊 Tabela Agrupada")
    st.dataframe(tabela)

    # Função para enviar os dados para o Google Sheets
    def enviar_para_sheets(df):
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credencial.json", scope)
        client = gspread.authorize(creds)

        # Abrir a planilha
        sheet = client.open("controle_disparos").sheet1  # Nome da planilha no Google Sheets


        # Obter os dados existentes
        existing = pd.DataFrame(sheet.get_all_records())

        # Descobrir a próxima linha vazia
        start_row = len(existing) + 2  # Pular cabeçalho e ir para a próxima linha vazia

        # Converter DataFrame para lista de listas e adicionar ao Google Sheets
        sheet.insert_rows(df.values.tolist(), row=start_row)

        st.success("✅ Dados enviados para o Google Sheets!")

    # Botão para enviar dados para o Google Sheets
    if st.button("📤 Enviar para Google Sheets"):
        enviar_para_sheets(tabela)

    # Botão para exportar os dados processados
    st.download_button(
        label="📥 Baixar Tabela Agrupada",
        data=tabela.to_csv(index=False, sep=';').encode('utf-8'),
        file_name="tabela_formatada.csv",
        mime="text/csv"
    )
