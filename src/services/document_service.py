
from src.db import MilvusDB, DataEntry, DocumentInsert
from src.parsers.tika_parser import TikaParser 
from src.embs import LocalEmbedder

import uuid 

class DocumentService:
    def __init__(self, milvus_uri: str = "http://localhost:19530"):
        self.milvus_db = MilvusDB(uri=milvus_uri)
        self.tika_parser = TikaParser()
        self.embedder = LocalEmbedder()

    async def create_document(self, collection_name: str, document: DocumentInsert):
        """Creates a document entry in the Milvus database."""
        try:
            document = DataEntry(
                id=uuid.uuid4(),
                vector=await self.embedder.embed(document.text),
                text=document.text,
                metadata=document.metadata
            )
            await self.milvus_db.insert_data(collection_name=collection_name, data=[document])
            return {"status": "success", "message": "Document created successfully."}
        except Exception as e:
            return {"status": "error", "message": str(e)} 

    async def search_documents(self, collection_name: str, query_text: str, limit: int = 5):
        """Searches for documents in the Milvus database based on a query text."""
        try:
            query_vector = await self.embedder.embed(query_text)
            results = await self.milvus_db.search_data(collection_name=collection_name, query_vectors=[query_vector], limit=limit)
            return {"status": "success", "results": results}
        except Exception as e:
            return {"status": "error", "message": str(e)}