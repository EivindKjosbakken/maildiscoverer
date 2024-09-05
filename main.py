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
import html  # To escape special characters


from rag_agent import RagAgent
from pinecone_utility import PineconeUtility
from utility import authorize_gmail_api

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)
client = OpenAI()

index = pc.Index("mails") # server index
rag_agent = RagAgent(index)
pinecone_utility = PineconeUtility(index)    


MAX_EMAILS = 5 # TODO INCREASE AFTER TESTING

st.title("Hello world")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


      
if "creds" not in st.session_state:
  st.session_state.creds = None

if "most_relevant_mails" not in st.session_state:
  st.session_state.most_relevant_mails = None

if "selected_mail" not in st.session_state:
    st.session_state.selected_mail = None


def login():
    creds = authorize_gmail_api()
    st.session_state.creds = creds



if st.button("Login"):
    login()


if st.button("Upload mail contents"):
    pinecone_utility.upload_email_content(index, max_emails=MAX_EMAILS)
    st.success("Emails uploaded successfully")


st.write("## Query for specific emails (returns specific emails you are looking for)")
prompt_specific_mail = st.text_input("Enter what emails you are looking for")
if st.button("Get specific mails by content"):
    pass # TODO only query for most similar emails

    response = rag_agent.query_pinecone_index(prompt_specific_mail, top_k=2, include_metadata=True)
    mails = [response["matches"][i]["metadata"] for i in range(len(response["matches"]))]

    st.session_state.most_relevant_mails = mails
    st.session_state.selected_mail = mails[0] # select the first mail by default (most similar)
 

def render_mail(selected_mail):
    email_subject = html.escape(selected_mail["subject"])
    email_sender = html.escape(selected_mail["sender"])
    email_date = html.escape(selected_mail["date"])
    email_content = html.escape(selected_mail["text"])
    # Custom CSS for styling the box
    st.markdown(
        """
        <style>
        .email-box {
            background-color: #f0f9ff;
            border: 1px solid #d1e7dd;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .email-content {
            color: #333333;
            font-size: 16px;
            margin-top: 10px;
        }
        .email-header {
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 5px;
        }
        .email-subheader {
            color: #6c757d;
            font-size: 14px;
            margin-bottom: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Display the email inside a styled box
    st.markdown(f"""
    <div class="email-box">
        <div class="email-header">Subject: <span>{email_subject}</span></div>
        <div class="email-subheader">From: <span>{email_sender}</span> | Date: <span>{email_date}</span></div>
        <div class="email-content"><span>{email_content}</span></div>
    </div>
    """, unsafe_allow_html=True)

if st.session_state.most_relevant_mails and st.session_state.selected_mail:
   render_mail(st.session_state.selected_mail)





st.write("## Ask questions about your emails (provides answers to your questions, and the emails containing the answer)")
prompt_question_answering = st.text_input("Enter some text")
if st.button("Query your emails"):
   pass # #TODO do full rag



# TODO ha noe prompt formattering ellerno