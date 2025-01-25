import streamlit as st
import pandas as pd
import google.generativeai as genai
from googleapiclient.discovery import build
import requests
from bs4 import BeautifulSoup
from io import StringIO
from fpdf import FPDF
import pyrebase  # Firebase authentication

# Configure the API key securely from Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Set up Google API keys
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
GOOGLE_CX = st.secrets["GOOGLE_SEARCH_ENGINE_ID"]

# Firebase configuration
firebase_config = {
    "apiKey": st.secrets["FIREBASE_API_KEY"],
    "authDomain": st.secrets["FIREBASE_AUTH_DOMAIN"],
    "projectId": st.secrets["FIREBASE_PROJECT_ID"],
    "storageBucket": st.secrets["FIREBASE_STORAGE_BUCKET"],
    "messagingSenderId": st.secrets["FIREBASE_MESSAGING_SENDER_ID"],
    "appId": st.secrets["FIREBASE_APP_ID"],
}
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# User authentication
def firebase_login():
    st.sidebar.title("Login")
    email = st.sidebar.text_input("Email", key="email")
    password = st.sidebar.text_input("Password", type="password", key="password")
    login_btn = st.sidebar.button("Login")
    signup_btn = st.sidebar.button("Sign Up")

    if login_btn:
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state["user"] = user
            st.sidebar.success("Login successful!")
        except Exception as e:
            st.sidebar.error(f"Login failed: {e}")

    if signup_btn:
        try:
            auth.create_user_with_email_and_password(email, password)
            st.sidebar.success("Account created successfully!")
        except Exception as e:
            st.sidebar.error(f"Sign up failed: {e}")

def firebase_logout():
    if "user" in st.session_state:
        if st.sidebar.button("Logout"):
            del st.session_state["user"]
            st.sidebar.info("Logged out successfully!")

# Initialize Karma Points
if "karma_points" not in st.session_state:
    st.session_state["karma_points"] = 0

# Display login/logout in the sidebar
if "user" not in st.session_state:
    firebase_login()
else:
    user = st.session_state["user"]
    st.sidebar.markdown(f"Logged in as: {user['email']}")
    firebase_logout()

# Prevent app access without login
if "user" not in st.session_state:
    st.warning("Please log in to access the application.")
    st.stop()

# Function to update karma points
def update_karma_points():
    st.session_state["karma_points"] += 1

# Function to interact with Google Search API with filtering
def google_search(query):
    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
    response = service.cse().list(q=query, cx=GOOGLE_CX).execute()
    results = response.get("items", [])
    
    # Filter results to remove irrelevant links (e.g., ads, short snippets)
    search_results = []
    for result in results:
        url = result.get("link", "")
        if any(domain in url for domain in ["youtube.com", "ads.google.com"]):  # Add more irrelevant domains if needed
            continue
        snippet = result.get("snippet", "")
        if len(snippet) < 50:  # Skip overly short snippets
            continue
        search_results.append({
            "Title": result.get("title"),
            "URL": url,
            "Snippet": snippet,
        })
    return search_results

# Function to generate a PDF from summaries
def generate_pdf(summaries_df):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Title
    pdf.set_font("Arial", style="B", size=14)
    pdf.cell(200, 10, txt="AI Summarized Web Results", ln=True, align='C')
    pdf.set_font("Arial", size=12)

    # Add each summary as a new section in the PDF
    for index, row in summaries_df.iterrows():
        pdf.ln(10)  # Line break
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(200, 10, txt=f"URL: {row['URL']}", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 10, txt=f"Summary: {row['Summary']}")
    return pdf.output(dest='S').encode('latin1')

# The rest of your app code remains the same...

