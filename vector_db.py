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
    separator1 = "\n## "
    separator2 = "\n### "
    
    file = file.replace(separator2, separator1)
    
    parts = file.split(separator1)
    
    return parts

def get_title(file):
    match = re.search(r"title:\s+(.+)\s+", file)
    if match:
        title = match.group(1)
        return title
    else:
        " "

def format_chunk(text: str) -> str:
    formatted_chunk = text.strip().lower().replace(" ", "-")
    return formatted_chunk
        
def generate_embeddings(chunks, file_name, collection):
    global document_id
    
    for chunk in chunks:
        formatted_chunk = format_chunk(chunk)
        chunk_id = f"{document_id}-{formatted_chunk}"
        
        collection.add(
            metadatas={
                "document_title": formatted_chunk if formatted_chunk is not None else "",
                "file_name": file_name
            },
            documents=chunk,
            ids=[chunk_id]
        )
        document_id = document_id + 1
    
def process_files_from_directory(directory_path: str, collection: str):
    collection = client.get_or_create_collection(name=collection)
    
    for filename in os.listdir(directory_path):
        
        file_path = os.path.join(directory_path, filename)
        
        if os.path.isfile(file_path) and filename.endswith('.md'):
            with open(file_path, 'r', encoding='utf-8') as file:
                markdown_text = file.read()
            
            chunks = split_text(markdown_text)
                        
            print("filenam: " + filename)
            
            generate_embeddings(chunks, filename, collection)
            

def query_collection(query: str, collection: str, n_results: int):
    collection = client.get_or_create_collection(name=collection)
    return collection.query(
        query_texts=[query],
        n_results=n_results,
    )
    
def clean_collection(collection: str):
    client.delete_collection(name=collection)
    print("The collection 'solana_projects' has been deleted.")