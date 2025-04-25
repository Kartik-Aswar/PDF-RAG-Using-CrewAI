import os
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field, ConfigDict

from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient # it is a vectordatabase Using Qdrant to store/retrieve document embeddings
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from qdrant_client.models import PointStruct, VectorParams, Distance
load_dotenv()

class DocumentSearchToolInput(BaseModel):
    """Input schema for DocumentSearchTool."""
    query: str = Field(..., description="Query to search the document.")



class DocumentSearchTool(BaseTool):
    name: str = "DocumentSearchTool"
    description: str = "Search document content using natural language queries."
    args_schema: Type[BaseModel] = DocumentSearchToolInput
    
    model_config = ConfigDict(extra="allow") #If the input data has extra fields not defined in the model, allow them instead of raising an error.
    """                 class MyModel(BaseModel):
                        model_config = ConfigDict(extra="allow")
                        name: str

                        # Input with an extra field "age"
                        data = MyModel(name="Kartik", age=23)
                        print(data)                          This will work and keep the age=23 even though it's not defined in the model."""
    def __init__(self, file_path: str):
        """Initialize the searcher with a PDF file path and set up the Qdrant collection."""
        super().__init__() #This line calls the constructor of the parent class (the class you're inheriting from).
        self.file_path = file_path
        self.client = QdrantClient(":memory:")  # For small experiments  
        """   Initializes a Qdrant vector database client.
              ":memory:" tells Qdrant to store data in RAM (not on disk) — useful for testing or small-scale experiments."""
        self.embedding_model = HuggingFaceEmbeddings(model_name="intfloat/e5-large-v2")
        self._process_document()
#def _name means This method is intended to be private — it’s for internal use only inside the class. But can be used outside it is developers notaion not related to language compilation means will work perfectly if called .
    
    def _extract_text(self) -> str: # it is extracting txt from pdf you can use different types of loaders like pdfloaders etc
        """Extract raw text from PDF using MarkItDown."""
        file_path = self.file_path
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        return "\n".join([doc.page_content for doc in docs])


    def _create_chunks(self, raw_text: str) -> list:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # How big the chunk should be
            chunk_overlap=150,
            length_function=len, #How to measure that size (chunk) like by characters otherwise it will chunk anything based like words, tokens etc
            separators=["\n\n", "\n", " ", ""] 
            #it tries to split at double newlines (\n\n) first → if not possible, then single newline (\n) → then space → then anywhere ("")
        )
        chunks = text_splitter.split_text(raw_text)
        # The split_text function returns a list of strings.
        # Wrap each string in a dictionary with a 'text' key.
        return [{"text": chunk} for chunk in chunks] # returns a list of dictionaries of key as text ans value will chunk

    def _process_document(self):
        """Process the document and add chunks to Qdrant collection."""
        raw_text = self._extract_text()
        chunks = self._create_chunks(raw_text) # calling list of dictionaries and assigning it to variable chunks so chunks is list of dicts

        # Access the 'text' attribute from the dictionaries in 'chunks'
        docs = [chunk['text'] for chunk in chunks] 
        vectors = self.embedding_model.embed_documents(docs)
        
        # Keep the rest of the code the same
        metadata = [{
        "source": os.path.basename(self.file_path),
        "text": chunk['text']  # ✅ Critical addition
        } for chunk in chunks]

        
        ids = list(range(len(chunks)))  
        """                                If len(chunks) = 3, then:
                                            ids = [0, 1, 2]"""

        # Recreate collection (sets vector size and similarity metric)
        self.client.recreate_collection(
            collection_name="demo_collection",
            vectors_config=VectorParams(
                size=len(vectors[0]),
                distance=Distance.COSINE
            )
        )

        # Upsert points into Qdrant
        self.client.upsert(
            collection_name="demo_collection",
            points=[
                PointStruct(id=ids[i], vector=vectors[i], payload=metadata[i])
                for i in range(len(vectors))
            ]
        )

    # def _run(self, query: str) -> str:
    #     """Search the document with a query string."""
        
    #     query_vetcor = self.embedding_model.embed_query(query)
    #     relevant_chunks = self.client.query(
    #         collection_name="demo_collection",
    #         query_vetcor=query_vetcor,
    #         top_k =5
    #     )
    #     docs = [chunk.document for chunk in relevant_chunks]
    #     separator = "\n___\n"
    #     return separator.join(docs)


    def _run(self, query: str) -> str:
        query_vector = self.embedding_model.embed_query(query)
        relevant_chunks = self.client.search(
            collection_name="demo_collection",
            query_vector=query_vector,
            limit=5  # ✅ search uses 'limit' instead of 'top_k'
        )
        return "\n___\n".join([chunk.payload['text'] for chunk in relevant_chunks])