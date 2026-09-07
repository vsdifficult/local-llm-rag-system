from pymilvus import AsyncMilvusClient, DataType
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class FieldConfig(BaseModel):
    """Configuration schema for an individual Milvus field."""
    name: str
    datatype: DataType
    is_primary: bool = False
    max_length: Optional[int] = None
    dim: Optional[int] = None

class CollectionSchemaConfig(BaseModel):
    """Defines the schema for a Milvus collection using Pydantic."""
    fields: List[FieldConfig]
    description: str = ""
    auto_id: bool = False

    def to_milvus_schema(self, client: AsyncMilvusClient):
        """Converts the Pydantic configuration into a native Milvus Schema object."""
        milvus_schema = client.create_schema(
            auto_id=self.auto_id, 
            description=self.description
        )
        
        for f in self.fields:
            milvus_schema.add_field(
                field_name=f.name,
                datatype=f.datatype,
                is_primary=f.is_primary,
                max_length=f.max_length,
                dim=f.dim
            )
        return milvus_schema

class DataEntry(BaseModel):
    """Represents a single data entry for insertion into Milvus."""
    id: str
    vector: List[float]
    text: str
    metadata: Dict[str, Any] 

class DocumentInsert(BaseModel): 
    text: str 
    metadata: Dict[str, Any]

class MilvusDB:

    """
    # Asynchronous wrapper for managing Milvus collection operations.
    
    import asyncio

    async def main():
        db = MilvusDB(uri="http://localhost:19530")
        
        # Define an optimized schema blueprint for RAG pipelines
        rag_schema = CollectionSchemaConfig(
            description="Knowledge base for RAG pipeline applications",
            fields=[
                FieldConfig(name="id", datatype=DataType.VARCHAR, max_length=64, is_primary=True),
                FieldConfig(name="vector", datatype=DataType.FLOAT_VECTOR, dim=1536), # 1536 for OpenAI models
                FieldConfig(name="text", datatype=DataType.VARCHAR, max_length=65535),
                FieldConfig(name="metadata", datatype=DataType.JSON)
            ]
        )
        
        # 1. Create the database collection
        await db.create_collection("rag_documents_v1", rag_schema)
        
        # 2. Build mock dataset chunks
        dummy_vector = [0.1] * 1536
        mock_data = [
            {
                "id": "chunk_001",
                "vector": dummy_vector,
                "text": "Milvus is an open-source vector database built for AI applications.",
                "metadata": {"source": "architecture_guide.pdf", "page": 4}
            }
        ]
        await db.insert_data("rag_documents_v1", mock_data)
        
        # 3. Perform a vector search similarity query
        search_results = await db.search_data("rag_documents_v1", query_vectors=[dummy_vector])
        print("Search Results Execution Output:", search_results)
        
        await db.close()

    if __name__ == "__main__":
        asyncio.run(main())

    """
    def __init__(self, uri="http://localhost:19530"):
        self.uri = uri
        self.client = AsyncMilvusClient(uri=self.uri)

    async def create_collection(self, collection_name: str, schema_config: CollectionSchemaConfig, vector_field_name: str = "vector"):
        """Creates a collection and automatically configures the HNSW index."""
        try:
            milvus_schema = schema_config.to_milvus_schema(self.client)
            
            # Prepare indexing parameters (required for vector search)
            index_params = self.client.prepare_index_params()
            index_params.add_index(
                field_name=vector_field_name,
                metric_type="COSINE",  # Recommended metric for text embeddings
                index_type="HNSW"      # High-performance in-memory vector index
            )
            
            await self.client.create_collection(
                collection_name=collection_name,
                schema=milvus_schema,
                index_params=index_params
            )
            print(f"INFO: Collection '{collection_name}' created successfully with vector indexes.")
        except Exception as e:
            print(f"ERROR: Failed to create collection '{collection_name}': {e}")

    async def insert_data(self, collection_name: str, data: List[DocumentInsert]):
        """Inserts a list of dictionaries into the specified collection."""
        try:
            await self.client.insert(collection_name=collection_name, data=data)
            print(f"INFO: Data inserted into collection '{collection_name}' successfully.")
        except Exception as e:
            print(f"ERROR: Failed to insert data into collection '{collection_name}': {e}")

    async def search_data(self, collection_name: str, query_vectors: List[List[float]], vector_field_name: str = "vector", limit: int = 5):
        """Searches for top-K similar documents using query vectors."""
        try:
            results = await self.client.search(
                collection_name=collection_name,
                data=query_vectors,
                anns_field=vector_field_name,
                limit=limit,
                output_fields=["text", "metadata"]  # Fields fetched to pass into the LLM context
            )
            return results
        except Exception as e:
            print(f"ERROR: Failed to search data in collection '{collection_name}': {e}")
            return None

    async def delete_collection(self, collection_name: str):
        """Drops the specified collection from the database."""
        try:
            await self.client.drop_collection(collection_name)
            print(f"INFO: Collection '{collection_name}' deleted successfully.")
        except Exception as e:
            print(f"ERROR: Failed to delete collection '{collection_name}': {e}")
            
    async def close(self):
        """Closes the underlying asynchronous client connection."""
        await self.client.close()
        print("INFO: Milvus client connection closed.")
