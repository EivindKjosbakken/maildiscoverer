SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/userinfo.email", "openid"]

PROJECT_ID = "maildiscoverer"
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_PROVIDER_X509_CERT_URL = "https://www.googleapis.com/oauth2/v1/certs"

MAX_CHARACTER_LENGTH_EMAIL = 12000

MAIN_REDIRECT_URI = 'https://maildiscoverer.streamlit.app/'
# MAIN_REDIRECT_URI = 'http://localhost:8080/'

ALL_REDIRECT_URIS = ["http://localhost:8080/", 'https://maildiscoverer.streamlit.app/']
ALL_JAVASCRIPT_ORIGINS = ["http://localhost:8080", 'https://maildiscoverer.streamlit.app/']