from fastapi import FastAPI 
from src.db import MilvusDB

app = FastAPI() 

milvus_db = MilvusDB(uri="http://localhost:19530") 

@app.post("/create-document")
async def create_document(document: dict):
    pass 
