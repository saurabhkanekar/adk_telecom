import os
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import json
from langchain_core.documents import Document
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from dotenv import load_dotenv
load_dotenv()


# with open("NexTel_FAQ.txt", "r", encoding="utf-8") as f:
#     text = f.read()
# Initialize embeddings and vector store
embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
collection_name = "NexTel_faq_v2"

current_dir = os.path.dirname(os.path.abspath(__file__))
collection_config_file = os.path.join(current_dir, "qdrant_collection_config_v2.json")

# collection_config_file = "qdrant_collection_config_v2.json"

# Initialize Qdrant client
# client = QdrantClient(path="./qdrant_db")

qdrant_db_path = os.path.join(current_dir, "qdrant_db")
client = QdrantClient(path=qdrant_db_path)

def setup_vector_store():
    """Setup and initialize the vector store."""

    current_dir = os.path.dirname(os.path.abspath(__file__))
    faq_path = os.path.join(current_dir, "NexTel_FAQ.txt")
    with open(faq_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    global collection_name
    
    if os.path.exists(collection_config_file):
        with open(collection_config_file, "r") as f:
            config = json.load(f)
            collection_name = config["collection_name"]
            print(f"Loading existing collection: {collection_name}")
            
        # Check if collection exists
        collections = client.get_collections()
        collection_exists = any(collection.name == collection_name for collection in collections.collections)
        
        if not collection_exists:
            # Recreate collection if it doesn't exist
            print(f"Collection {collection_name} not found, recreating...")
            vector_size = len(embedding_model.embed_query("test"))
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
            chunks = splitter.split_text(text)
            
            vector_store = Qdrant(
                client=client,
                collection_name=collection_name,
                embeddings=embedding_model
            )
            
            # Add the documents
            docs = [Document(page_content=chunk) for chunk in chunks]
            vector_store.add_documents(docs)
        else:
            # Use existing collection
            vector_store = Qdrant(
                client=client, 
                collection_name=collection_name, 
                embeddings=embedding_model
            )
    else:
        # Create new collection and index documents
        print(f"Creating new collection: {collection_name}")
        vector_size = len(embedding_model.embed_query("test"))
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        
        # Index content in two steps
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        chunks = splitter.split_text(text)
        
        # Step 1: Create the vector store
        vector_store = Qdrant(
            client=client,
            collection_name=collection_name,
            embeddings=embedding_model
        )
        
        # Step 2: Add the documents
        docs = [Document(page_content=chunk) for chunk in chunks]
        vector_store.add_documents(docs)
        
        # Save collection info for future reference
        with open(collection_config_file, "w") as f:
            json.dump({"collection_name": collection_name}, f)
    
    return vector_store

# Set up vector store
vector_store = setup_vector_store()

@FunctionTool
def retrieve(query: str) -> str:
    """Retrieve relevant chunks from indexed text."""
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    docs = retriever.get_relevant_documents(query)
    return "\n\n".join([doc.page_content for doc in docs])

# Create the FAQ agent
faq_agent = Agent(
    name="faq_agent",
    model="gemini-2.0-flash",
    description="FAQ agent for NexTel network provider",
    instruction="""
    You are the FAQ specialist for NexTel network provider.
    Your role is to answer customer questions accurately by retrieving information from the NexTel FAQ database.
    
    **Core Capabilities:**
    
    1. Answer FAQ Questions
       - Retrieve accurate answers from the NexTel FAQ database:
            NexTel Xstream Box & NexTel Smart TV 
            NexTel Xstream Fiber Mesh FAQs
            NexTel Xstream Box & NexTel Smart TV FAQs
    
    **Customer Information:**
    <customer_info>
    Customer ID: {customer_info.customer_id}
    Name: {customer_info.first_name} {customer_info.last_name}
    Email: {customer_info.email}
    Phone: {customer_info.phone}
    </customer_info>
    
    
    Always use the `retrieve` tool to search for relevant information before answering customer questions.
    Provide accurate and helpful responses based on the retrieved information.
    
    When responding to questions:
    - Be clear and concise
    - Cite information directly from the NexTel FAQ database
    - If the FAQ database doesn't have the answer, say so and suggest contacting customer support
    - Personalize responses using the customer's information when appropriate
    
    Always maintain a helpful and professional tone.
    """,
    tools=[retrieve],
)

# Expose the agent as 'agent' for the module to be compatible with the ADK framework
agent = faq_agent

session_service = InMemorySessionService()
runner = Runner(
    app_name="NexTel_faq",
    agent=faq_agent,
    session_service=session_service,
)

# Create a session for testing
session_service.create_session(
    app_name="NexTel_faq",
    session_id="session-1",
    user_id="user-1"
)

