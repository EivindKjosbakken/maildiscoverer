import hashlib
from tqdm.auto import tqdm
import streamlit as st
from googleapiclient.discovery import build
from rag_agent import RagAgent



class PineconeUtility():
	def __init__(self, index) -> None:
		pass
		self.rag_agent = RagAgent(index)

	def _generate_short_id(self, content: str) -> str:
		"""
		Generate a short ID based on the content using SHA-256 hash.

		Args:
		- content (str): The content for which the ID is generated.

		Returns:
		- short_id (str): The generated short ID.
		"""
		hash_obj = hashlib.sha256()
		hash_obj.update(content.encode("utf-8"))
		return hash_obj.hexdigest()


	def _combine_vector_and_text(self,
		documents: list[any], doc_embeddings: list[list[float]]
	) -> list[dict[str, any]]:
		"""
		Process a list of documents along with their embeddings.

		Args:
		- documents (List[Any]): A list of documents (strings or other types).
		- doc_embeddings (List[List[float]]): A list of embeddings corresponding to the documents.

		Returns:
		- data_with_metadata (List[Dict[str, Any]]): A list of dictionaries, each containing an ID, embedding values, and metadata.
		"""
		data_with_metadata = []

		for doc, embedding in zip(documents, doc_embeddings):
			doc_text = doc["snippet"]
			doc_date = doc["date"]
			doc_sender = doc["from"]
			doc_subject = doc["subject"]


			# Generate a unique ID based on the text content
			doc_id = self._generate_short_id(doc_text)

			# Create a data item dictionary
			data_item = {
				"id": doc_id,
				"values": embedding,
				"metadata": {"text": doc_text, "date": doc_date, "sender": doc_sender, "subject": doc_subject},  # Include the text as metadata
			}

			# Append the data item to the list
			data_with_metadata.append(data_item)

		return data_with_metadata
	

	def _upsert_data_to_pinecone(self, index, data_with_metadata: list[dict[str, any]]) -> None:
		"""
		Upsert data with metadata into a Pinecone index.

		Args:
		- data_with_metadata (List[Dict[str, Any]]): A list of dictionaries, each containing data with metadata.

		Returns:
		- None
		"""
		index.upsert(vectors=data_with_metadata)


	# Function to list emails with a max limit and additional details
	def _list_emails_with_details(self, service, max_emails=100):
		all_emails = []
		results = service.users().messages().list(userId='me', maxResults=max_emails).execute()
		
		# Fetch the first page of messages
		messages = results.get('messages', [])
		all_emails.extend(messages)

		# Keep fetching emails until we reach the max limit or there are no more pages
		while 'nextPageToken' in results and len(all_emails) < max_emails:
			page_token = results['nextPageToken']
			results = service.users().messages().list(userId='me', pageToken=page_token).execute()
			messages = results.get('messages', [])
			all_emails.extend(messages)

			# Break if we exceed the max limit
			if len(all_emails) >= max_emails:
				all_emails = all_emails[:max_emails]  # Trim to max limit
				break

		progress_bar2 = st.progress(0)
		status_text2 = st.text("Retrieving your emails...")


		email_details = []
		for idx, email in tqdm(enumerate(all_emails), desc="Fetching email details"):
			# Fetch full email details
			msg = service.users().messages().get(userId='me', id=email['id']).execute()
			headers = msg['payload']['headers']
			
			# Extract date, sender, and subject from headers
			email_data = {
				'snippet': msg.get('snippet', ''),
				'id': msg['id'],
				'date': next((header['value'] for header in headers if header['name'] == 'Date'), None),
				'from': next((header['value'] for header in headers if header['name'] == 'From'), None),
				'subject': next((header['value'] for header in headers if header['name'] == 'Subject'), None)
			}
			email_details.append(email_data)
			progress_bar2.progress((idx + 1) / len(all_emails))  # Progress bar update
			status_text2.text(f"Retrieving email {idx + 1} of {len(all_emails)}")

		return email_details
	


	def upload_email_content(self, index, max_emails=100):
		# Build Gmail service
		if not st.session_state.creds: 
			st.error("Please login first")
			return
		service = build('gmail', 'v1', credentials=st.session_state.creds)
		emails = self._list_emails_with_details(service, max_emails=max_emails)

		progress_bar = st.progress(0)
		status_text = st.text("Creating embeddings...")

		# embed emails
		embeddings = []
		for idx, email in tqdm(enumerate(emails), desc="Creating embeddings"):
			embeddings.append(self.rag_agent.get_embedding(email["snippet"]))
			# Update the progress bar and status text
			progress_bar.progress((idx + 1) / len(emails))  # Progress bar update
			status_text.text(f"Creating embedding {idx + 1} of {len(emails)}")
			
		data_with_meta_data = self._combine_vector_and_text(documents=emails, doc_embeddings=embeddings) 
		self._upsert_data_to_pinecone(index, data_with_metadata=data_with_meta_data)
