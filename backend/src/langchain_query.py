"""
LangChain RAG Chain for GitHub Analytics with Elasticsearch + Vertex AI
FIXED: Proper prompt template and context passing
"""

import os
from datetime import datetime
from dotenv import load_dotenv
import json

from langchain_google_vertexai import ChatVertexAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.embeddings.base import Embeddings
from langchain.schema import BaseRetriever, Document
from elasticsearch import Elasticsearch
from vertexai.language_models import TextEmbeddingModel
from typing import List, Any
from pydantic import Field

load_dotenv()

# ---------------- ENV SETUP ----------------
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "hackathon-github-ai")
LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
INDEX_NAME = os.getenv("ELASTIC_INDEX", "github_issues")

ELASTIC_CLOUD_ID = os.getenv("YOUR_CLOUD_ID")
ELASTIC_PASSWORD = os.getenv("YOUR_PASSWORD")

# ---------------- Custom Gemini Embeddings (3072 dimensions) ----------------
class GeminiEmbeddings(Embeddings):
    """Custom embeddings class for Gemini that returns 3072-dimensional vectors"""
    
    def __init__(self, project: str, location: str, model_name: str = "gemini-embedding-001"):
        self.project = project
        self.location = location
        self.model_name = model_name
        self.model = TextEmbeddingModel.from_pretrained(self.model_name)
        print(f"✅ Initialized {model_name} (3072 dimensions)")
    
    def embed_documents(self, texts: list) -> list:
        """Embed multiple documents"""
        embeddings = self.model.get_embeddings(texts)
        return [e.values for e in embeddings]

    def embed_query(self, text: str) -> list:
        """Embed a single query"""
        embeddings = self.model.get_embeddings([text])
        return embeddings[0].values

# Initialize custom embeddings
embeddings = GeminiEmbeddings(project=PROJECT_ID, location=LOCATION)

# ---------------- Elasticsearch Client ----------------
es_client = Elasticsearch(
    cloud_id=ELASTIC_CLOUD_ID,
    basic_auth=("elastic", ELASTIC_PASSWORD),
    request_timeout=300
)

# ---------------- Custom Retriever with Metadata ----------------

class ElasticsearchMetadataRetriever(BaseRetriever):
    """Custom retriever that properly extracts all metadata from Elasticsearch"""
    
    es_client: Any = Field(description="Elasticsearch client")
    index_name: str = Field(description="Elasticsearch index name")
    embeddings: Any = Field(description="Embeddings model")
    k: int = Field(default=10, description="Number of documents to retrieve")
    
    class Config:
        arbitrary_types_allowed = True
    
    def _get_relevant_documents(self, query: str) -> List[Document]:
        """Search Elasticsearch and return documents with full metadata"""
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # Build Elasticsearch KNN query
        es_query = {
            "size": self.k,
            "knn": {
                "field": "embedding",
                "query_vector": query_embedding,
                "k": self.k,
                "num_candidates": self.k * 2
            },
            "_source": ["title", "body", "contributor_login", "commit_count", 
                       "created_at", "closed_at", "state", "labels", "repo_name",
                       "creator", "html_url", "number"]
        }
        
        # Execute search
        results = self.es_client.search(index=self.index_name, body=es_query)
        
        # Build Document objects with full metadata
        docs = []
        for hit in results["hits"]["hits"]:
            source = hit["_source"]
            
            # Build readable content for LLM context
            content = f"""Title: {source.get('title', 'N/A')}
Body: {source.get('body', 'N/A')[:500]}
Contributor: {source.get('contributor_login', 'Unknown')}
Commit Count: {source.get('commit_count', 0)}
State: {source.get('state', 'unknown')}
Created: {source.get('created_at', 'N/A')}
Closed: {source.get('closed_at', 'N/A')}
Labels: {', '.join(source.get('labels', []))}
Repo: {source.get('repo_name', 'N/A')}"""
            
            # Create Document with full metadata
            doc = Document(
                page_content=content,
                metadata={
                    "title": source.get("title", ""),
                    "body": source.get("body", ""),
                    "contributor_login": source.get("contributor_login", "Unknown"),
                    "commit_count": source.get("commit_count", 0),
                    "created_at": source.get("created_at", ""),
                    "closed_at": source.get("closed_at", ""),
                    "state": source.get("state", ""),
                    "labels": source.get("labels", []),
                    "repo_name": source.get("repo_name", ""),
                    "creator": source.get("creator", ""),
                    "html_url": source.get("html_url", ""),
                    "number": source.get("number", 0)
                }
            )
            docs.append(doc)
        
        return docs
    
    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        """Async version - just calls sync version"""
        return self._get_relevant_documents(query)

# Initialize custom retriever with metadata extraction
retriever = ElasticsearchMetadataRetriever(
    es_client=es_client,
    index_name=INDEX_NAME,
    embeddings=embeddings,
    k=10
)

# ---------------- Vertex AI Model ----------------
llm = ChatVertexAI(
    model_name="gemini-2.5-flash",
    project=PROJECT_ID,
    location=LOCATION,
    temperature=0.2,
    max_output_tokens=1024
)

# ---------------- Prompt Template (FIXED) ----------------
# Use proper variable syntax without f-string confusion
PROMPT_TEMPLATE = """You are an expert GitHub analytics assistant analyzing GitHub issues, body, contributor, commit_count understand user query and reply with witty and smartness summarize the whole data and user query.

Today's date is: {date}

Based on ONLY the retrieved GitHub issues data provided below, answer the user's question directly and accurately with summary.

=== RETRIEVED GITHUB ISSUES DATA ===
{context}
=== END DATA ===

USER QUESTION: {question}

ANALYSIS INSTRUCTIONS:
1. Read through each issue's metadata (title, contributor_login, commit_count, created_at, state, closed_at, body, labels, repo_name, creator, html_url, number)
2. For "who has most commit" → Find the issue/contributor with the HIGHEST commit_count value and name them
3. For "how many commit X done" → Find issues where contributor_login matches X and s their commit_count
4. For "most recent" → Show the issue with the LATEST created_at date
5. ALWAYS extract and quote exact values from the data
6. If you find relevant data, cite specific contributor names, numbers, and dates
7. If truly no relevant data exists, only then say "No matching data found"

Please provide a direct, factual answer based on the data above:"""

today_date = datetime.now().strftime("%Y-%m-%d")

analytics_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=PROMPT_TEMPLATE,
    partial_variables={"date": today_date}
)

# ---------------- RAG Chain ----------------
def create_rag_chain():
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": analytics_prompt},
        return_source_documents=True,
        verbose=False  # Set to True to debug
    )

# ---------------- Query Function ----------------
def query_github_analytics(user_question: str) -> dict:
    print(f"\n{'='*60}")
    print(f"🔍 Question: {user_question}")
    print(f"{'='*60}")
    
    try:
        qa_chain = create_rag_chain()
        print("🔎 Searching Elasticsearch...")
        
        # Debug: Verify query embedding is generated correctly
        try:
            query_embedding = embeddings.embed_query(user_question)
            print(f"✅ Query embedding generated: {len(query_embedding)} dimensions")
            print(f"   First 5 values: {query_embedding[:5]}")
            
            # Additional debug: Check if vector size matches expected dimensions
            expected_dims = 3072  # gemini-embedding-001 produces 3072-dimensional vectors
            if len(query_embedding) != expected_dims:
                print(f"⚠️ Warning: Expected {expected_dims} dimensions, got {len(query_embedding)}")
            
        except Exception as embed_error:
            print(f"⚠️ Embedding generation error: {embed_error}")
        
        result = qa_chain.invoke({"query": user_question})
        
        answer = result["result"]
        source_docs = result.get("source_documents", [])
        
        print(f"\n✅ Found {len(source_docs)} relevant issues")
        
        # Debug: Show what was retrieved
        if source_docs:
            print(f"\n📊 Top retrieved issues:")
            for i, doc in enumerate(source_docs[:3], 1):
                print(f"  {i}. {doc.metadata.get('title', 'N/A')[:50]}")
                print(f"     Contributor: {doc.metadata.get('contributor_login', 'N/A')}, Commits: {doc.metadata.get('commit_count', 'N/A')}")
        
        print(f"\n💡 Answer:")
        print(f"{'-'*60}")
        print(answer)
        print(f"{'-'*60}")
        
        sources = [{
            "title": doc.metadata.get("title", ""),
            "contributor": doc.metadata.get("contributor_login", ""),
            "commit_count": doc.metadata.get("commit_count", 0),
            "created_at": doc.metadata.get("created_at", ""),
            "state": doc.metadata.get("state", "")
        } for doc in source_docs]
        
        return {
            "answer": answer,
            "sources": sources,
            "num_sources": len(source_docs)
        }

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "answer": f"Error: {str(e)}",
            "sources": [],
            "num_sources": 0
        }

# ---------------- CLI for Live Questions ----------------
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 DevInsight: LangChain RAG for GitHub Analytics")
    print("="*60)
    
    while True:
        user_input = input("\n💬 Ask a question (or type 'exit' to quit):\n> ")
        if user_input.lower() in ["exit", "quit"]:
            break
        result = query_github_analytics(user_input)
        print(f"📄 Sources returned: {result['num_sources']}\n")