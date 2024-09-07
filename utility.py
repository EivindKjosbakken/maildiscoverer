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
import json

from dotenv import load_dotenv
load_dotenv()
from safe_constants import SCOPES


os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1' # avoids error being thrown for duplicate scopes (doesnt matter for this use case)

# PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

pc = Pinecone(api_key=PINECONE_API_KEY)
openai_client = OpenAI()


from safe_constants import PROJECT_ID, AUTH_URI, TOKEN_URI, AUTH_PROVIDER_X509_CERT_URL
CLIENT_ID = st.secrets["GMAIL_API_CREDENTIALS"]["CLIENT_ID"]
CLIENT_SECRET = st.secrets["GMAIL_API_CREDENTIALS"]["CLIENT_SECRET"]

CLIENT_CONFIG = {
     "web":{"client_id":CLIENT_ID,"project_id":PROJECT_ID,"auth_uri":AUTH_URI,"token_uri":TOKEN_URI,"auth_provider_x509_cert_url":AUTH_PROVIDER_X509_CERT_URL,"client_secret":CLIENT_SECRET,"redirect_uris":["http://localhost:8080/"],"javascript_origins":["http://localhost:8080"]}
     }


def get_user_info(creds):
    # Build the OAuth2 service to get user info
    oauth2_service = build('oauth2', 'v2', credentials=creds)
    
    # Get user info
    user_info = oauth2_service.userinfo().get().execute()

    return user_info.get('email')


def authorize_gmail_api():
      """Shows basic usage of the Gmail API.
      Lists the user's Gmail labels.
      """
      creds = None
      if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
      # If there are no (valid) credentials available, let the user log in.
      if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
          creds.refresh(Request())
        else:
          flow = InstalledAppFlow.from_client_config(
              CLIENT_CONFIG, SCOPES
          )
          
          # creds = flow.run_local_server(port=8080)
          creds = flow.run_local_server(bind_addr="0.0.0.0", open_browser=False, port=8080)
        # Save the credentials for the next run
        with open("token.json", "w") as token: 
          token.write(creds.to_json())

      # get user email
      user_email = get_user_info(creds)
      st.session_state.user_email = user_email
      return creds


