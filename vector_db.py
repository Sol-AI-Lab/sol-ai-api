import chromadb
from chromadb.config import Settings
import os
import re

client = chromadb.PersistentClient(path="./local_db")

document_id = 1

def resetDb():
    client.reset()
    
def isLive():
    client.heartbeat()

def split_text(file):
    # Definimos los separadores
    separator1 = "\n### "
    separator2 = "\n#### "
    
    # Primero, sustituimos todos los separator2 por separator1
    file = file.replace(separator2, separator1)
    
    # Luego, dividimos el texto usando separator1
    parts = file.split(separator1)
    
    return parts

def get_title(file):
    match = re.search(r"title:\s+(.+)\s+", file)
    if match:
        title = match.group(1)
        return title
    else:
        " "
        
def generate_embeddings(chunks, document_title, file_name, collection):
    global document_id
    for chunk in chunks:
        collection.add(
            metadatas={
                "document_title": document_title if document_title is not None else "",
                "file_name": file_name
            },
            documents=chunk,
            ids=[str(document_id)]
        )
        document_id = document_id + 1
    
def process_files_from_directory(directory_path: str):
    collection = client.get_or_create_collection(name="curadeuda_docs")
    
    # Listar todos los archivos en el directorio especificado
    for filename in os.listdir(directory_path):
        # Construir la ruta completa al archivo
        
        file_path = os.path.join(directory_path, filename)
        
        # Verificar que sea un archivo .md
        if os.path.isfile(file_path) and filename.endswith('.md'):
            with open(file_path, 'r', encoding='utf-8') as file:
                markdown_text = file.read()
            
            chunks = split_text(markdown_text)
            
            document_title = filename
            
            print("Document title: " + document_title)
            
            generate_embeddings(chunks, document_title, filename, collection)
            

def query_collection(query):
    collection = client.get_or_create_collection(name="curadeuda_docs")
    return collection.query(
        query_texts=[query],
        n_results=3,
    )
    
def clean_local_db():
    client.delete_collection(name="curadeuda_docs")
    print("The collection 'curadeuda_docs' has been deleted.")