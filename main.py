# Comando para executar o arquivo: streamlit run main.py: streamlit run main.py

import streamlit as st
from azure.storage.blob import BlobServiceClient
import os
import pyodbc
import uuid
import json
from dotenv import load_dotenv
load_dotenv()

# Carregar variáveis de ambiente
blobConnectionString = os.getenv('BLOB_CONNECTION_STRING')
blobContainerName = os.getenv('BLOB_CONTAINER_NAME')
blobAccountName = os.getenv('BLOB_ACCOUNT_NAME')

SQL_SERVER = os.getenv('SQL_SERVER')
SQL_DATABASE = os.getenv('SQL_DATABASE')
SQL_USER = os.getenv('SQL_USER')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')

# form cadastro de produtos
st.title('Cadastro de Produtos')

product_name = st.text_input('Nome do Produto')
product_price = st.number_input('Preço do Produto', min_value=0.0, format="%.2f")
product_description = st.text_input('Descrição do Produto')
product_image = st.file_uploader('Imagem do Produto', type=['jpg', 'jpeg', 'png'])

#salve image on blob storage
def upload_blob(file):
    blob_service_client = BlobServiceClient.from_connection_string(blobConnectionString)
    container_client = blob_service_client.get_container_client(blobContainerName)
    blob_name = str(uuid.uuid4()) + file.name
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(file.read(), overwrite=True)
    image_url = f"https://{blobAccountName}.blob.core.windows.net/{blobContainerName}/{blob_name}"
    return image_url

#salva produto
def insert_product_to_sql(product_name, product_price, product_description, product_image):
    try:
        # Upload da imagem para o blob storage
        image_url = upload_blob(product_image)

        # Conexão com o SQL Server
        conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={SQL_SERVER};'
            f'DATABASE={SQL_DATABASE};'
            f'UID={SQL_USER};'
            f'PWD={SQL_PASSWORD}'
        )

        # Usar contexto "with" para garantir fechamento
        with conn:
            with conn.cursor() as cursor:
                insert_sql = """
                    INSERT INTO Produtos (nome, preco, descricao, imagem_url) 
                    VALUES (?, ?, ?, ?)
                """
                cursor.execute(insert_sql, (product_name, product_price, product_description, image_url))
                conn.commit()

        return True

    except Exception as e:
        st.error(f"Erro ao inserir produto: {e}")
        return False

#lista produtos
def list_products():
    try:
        conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={SQL_SERVER};'
            f'DATABASE={SQL_DATABASE};'
            f'UID={SQL_USER};'
            f'PWD={SQL_PASSWORD}'
        )

        with conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT id, nome, preco, descricao, imagem_url 
                    FROM Produtos
                """
                cursor.execute(query)
                columns = [column[0] for column in cursor.description]
                products = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return products

    except Exception as e:
        st.error(f"Erro ao listar produtos: {e}")
        return []

#screen produtos
def list_products_screen():
    products = list_products()
    if products:
        cards_per_row = 3
        cols = st.columns(cards_per_row)
        for i, product in enumerate(products):
            with cols[i % cards_per_row]:
                st.markdown(f"### {product['nome']}")
                st.write(f"**Descrição:** {product['descricao']}")
                st.write(f"**Preço:** R$ {product['preco']:.2f}")
                if product['imagem_url']:
                    html_img = f'<img src="{product["imagem_url"]}" width="150" height="150" alt="Imagem do produto" />'
                    st.markdown(html_img, unsafe_allow_html=True)
                st.markdown("---")
    else:
        st.info("Nenhum produto cadastrado.")

# Botão para salvar produto 
if st.button('Salvar Produto'):
    if insert_product_to_sql(product_name, product_price, product_description, product_image):
        st.success('Produto salvo com sucesso!')
    
        st.markdown("---")
        # Listando produtos após o cadastro
        list_products_screen()
    else:
        st.error('Erro ao salvar o produto.')

st.header('Produtos Cadastrados')

# Botão para listar produtos
if st.button('Listar Produtos'):
    list_products_screen()
    st.success('Produtos listados com sucesso!')