from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from modules.llm import get_llm_chain
from modules.query_handlers import query_chain
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone
from pydantic import Field
from pathlib import Path
from typing import List, Optional
from logger import logger
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / ".env")

PINECONE_INDEX_NAME = "medicalindex"

router=APIRouter()

@router.post("/ask/")
async def ask_question(question: str = Form(...)):
    try:
        logger.info(f"user query: {question}")

        # Embed model + Pinecone setup
        pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        index = pc.Index(PINECONE_INDEX_NAME)
        embed_model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=os.environ.get("GOOGLE_API_KEY")
        )
        embedded_query = embed_model.embed_query(question)
        res = index.query(vector=embedded_query, top_k=3, include_metadata=True)

        docs = [
            Document(
                page_content=match["metadata"].get("text", ""),
                metadata=match["metadata"]
            ) for match in res["matches"]
        ]

        class SimpleRetriever(BaseRetriever):
            docs: List[Document]

            def _get_relevant_documents(self, query: str) -> List[Document]:
                return self.docs

        retriever = SimpleRetriever(docs=docs)
        chain = get_llm_chain(retriever)
        result = query_chain(chain, question)

        logger.info("query successful")
        return result

    except Exception as e:
        logger.exception("Error processing question")
        return JSONResponse(status_code=500, content={"error": str(e)})