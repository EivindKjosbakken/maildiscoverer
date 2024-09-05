import streamlit as st
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from openai import OpenAI
from tqdm.auto import tqdm
from pinecone import Pinecone
import hashlib

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)
openai_client = OpenAI()




class RagAgent:
	def __init__(self, index):
		self.index = index

	def get_embedding(self, text, model="text-embedding-3-small"):
		return openai_client.embeddings.create(input = [text], model=model).data[0].embedding


	def query_pinecone_index(self, 
		query: list, top_k: int = 2, include_metadata: bool = True
	) -> dict[str, any]:
		"""
		Query a Pinecone index.

		Args:
		- index (Any): The Pinecone index object to query.
		- vectors (List[List[float]]): List of query vectors.
		- top_k (int): Number of nearest neighbors to retrieve (default: 2).
		- include_metadata (bool): Whether to include metadata in the query response (default: True).

		Returns:
		- query_response (Dict[str, Any]): Query response containing nearest neighbors.
		"""
		query_embedding = self.get_embedding(query)
		query_response = self.index.query(
			vector=query_embedding, top_k=top_k, include_metadata=include_metadata
		)
		return query_response
	

	def extract_text_from_query_response(self, query_response: dict[str, any]) -> str:
		"""
		Extract the text from the metadata in the query response, to feed into LLM for response.

		Args:
		- query_response (Dict[str, Any]): Query response containing metadata.

		Returns:
		- text_answer (str): The extracted text from the query response.
		"""
		texts = [doc['metadata']['text'] for doc in query_response['matches']]
		return texts

