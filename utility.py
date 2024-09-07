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

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        st.info("Alreadt logged in")
      # If there are no (valid) credentials available, let the user log in.
      if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
          creds.refresh(Request())
        else:
          flow = InstalledAppFlow.from_client_config(
              CLIENT_CONFIG, SCOPES
          )
          flow.redirect_uri = 'https://maildiscoverer.streamlit.app/'
        #   flow.redirect_uri = 'http://localhost:8080/' #TODO change when in prod

          authorization_url, state = flow.authorization_url(
              access_type='offline',
              include_granted_scopes='true',
              prompt='consent')


          st.markdown(
            f"""
            <style>
            .custom-button {{
                display: inline-block;
                background-color: #4CAF50; /* Green background */
                color: white !important;  /* White text */
                padding: 10px 24px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                border-radius: 5px;
                margin-top: 5px; /* Reduce space above the button */
                margin-bottom: 5px; /* Reduce space above the button */
            }}
            .custom-button:hover {{
                background-color: #45a049;
            }}
            </style>
            <a href="{authorization_url}" target="_self" class="custom-button">Authorize with Google</a>
            """,
            unsafe_allow_html=True
        )
            

def authenticate_user():
    """after loggin in with google, you have a code in the url. This function retrieves the code and fetches the credentials and authenticates user"""
    auth_code = st.query_params.get('code', None)
    if auth_code is not None:
        logger.info("INSIDE CODE")
        from utility import CLIENT_CONFIG
        
        # make a new flow to fetch tokens
        flow = InstalledAppFlow.from_client_config(
                CLIENT_CONFIG, SCOPES, 
            )
        flow.redirect_uri = 'http://localhost:8080/' #TODO change when in prod
        
        flow.fetch_token(code=auth_code)
        st.query_params.clear()
        creds = flow.credentials
        if creds:
            # Save the credentials for future use
            with open('token.json', 'w') as token_file:
                token_file.write(creds.to_json())
            st.success("Authorization successful! Credentials have been saved.")

            # Save the credentials for the next run
            with open("token.json", "w") as token: 
                token.write(creds.to_json())
            # get user email
            user_email = get_user_info(creds)
            st.session_state.user_email = user_email
            st.rerun()
    else: st.error("Could not log in user")