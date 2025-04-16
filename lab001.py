import streamlit as st
from azure.storage.blob import BlobServiceClient
import os
import pymssql
import uuid
from dotenv import dotenv_values

# Carrega as variáveis de ambiente do .env
config = dotenv_values("cloud.env")

blobConnectionString = config.get("BLOB_CONNECTION_STRING")
blobContainerName = config.get("BLOB_CONTAINER_NAME")
blobAccountName = config.get("BLOB_ACCOUNT_NAME")

SQL_SERVER = config.get("SQL_SERVER")
SQL_DATABASE = config.get("SQL_DATABASE")
SQL_USER = config.get("SQL_USER")
SQL_PASSWORD = config.get("SQL_PASSWORD")

# Formulário de cadastro de produtos
st.header("Cadastro de Produto")

product_name = st.text_input("Nome do produto:")
product_price = st.number_input("Preço do produto:", min_value=0.0, format="%.2f")
product_description = st.text_input("Descrição do produto:")
product_image = st.file_uploader("Upload da imagem do produto", type=["jpg", "jpeg", "png"])

# Salvar imagem no Blob Storage
def upload_blob(file):
    blob_service_client = BlobServiceClient.from_connection_string(blobConnectionString)
    container_client = blob_service_client.get_container_client(blobContainerName)
    blob_name = str(uuid.uuid4()) + file.name
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(file, overwrite=True)
    image_url = f"https://{blobAccountName}.blob.core.windows.net/{blobContainerName}/{blob_name}"
    return image_url

# Inserir produto no banco
def insert_product(name, price, description, image_file):
    try:
        image_url = upload_blob(image_file)
        conn = pymssql.connect(server=SQL_SERVER, user=SQL_USER, password=SQL_PASSWORD, database=SQL_DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Produtos (nome, preco, descricao, imagem_url) VALUES (%s, %s, %s, %s)",
            (name, price, description, image_url)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir produto: {e}")
        return False

# Listar produtos
def list_products():
    try:
        conn = pymssql.connect(server=SQL_SERVER, user=SQL_USER, password=SQL_PASSWORD, database=SQL_DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Produtos")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        st.error(f"Erro ao listar produtos: {e}")
        return []

# Tela de listagem de produtos
def list_products_screen():
    products = list_products()
    if products:
        cards_por_linha = 3
        cols = st.columns(cards_por_linha)
        for i, product in enumerate(products):
            with cols[i % cards_por_linha]:
                st.markdown(f'### {product[1]}')  # Nome
                st.write(f'**Descrição:** {product[2]}')  # Descrição
                try:
                    preco_formatado = f'R${float(product[3]):.2f}'  # Preço
                except (ValueError, TypeError):
                    preco_formatado = 'Preço inválido'
                st.write(f'**Preço:** {preco_formatado}')
                if product[4]:  # Imagem
                    html_img = f'<img src="{product[4]}" width="200" height="200" alt="{product[1]}">'
                    st.markdown(html_img, unsafe_allow_html=True)
                st.markdown('---')
    else:
        st.write("Nenhum produto cadastrado.")

# Botão de salvar
if st.button("Salvar"):
    if product_name and product_description and product_price and product_image is not None:
        success = insert_product(product_name, product_price, product_description, product_image)
        if success:
            st.success("Produto salvo com sucesso.")
    else:
        st.warning("Por favor, preencha todos os campos e envie uma imagem.")

# Botão para listar produtos
st.header('Produtos Cadastrados')
if st.button('Listar Produtos'):
    list_products_screen()