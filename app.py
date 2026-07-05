import streamlit as st
from groq import Groq
import PyPDF2
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

st.title("JobBuddy 🤖")
st.write("AI Job Application Assistant")

uploaded_file = st.file_uploader("Upload your CV (PDF)", type="pdf")
jd_text = st.text_area("Paste Job Description", height=200)

if st.button("🔍 Analyze"):
    if uploaded_file and jd_text:
        reader = PyPDF2.PdfReader(uploaded_file)
        cv_text = ""
        for page in reader.pages:
            cv_text += page.extract_text()
        
        prompt = f"""Analyze this CV against the Job Description.
Give me:
1. Match percentage
2. Top 5 missing keywords
3. 3 suggestions to improve

CV:
{cv_text}

Job Description:
{jd_text}"""

        with st.spinner("AI is analyzing..."):
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            )
        
        st.subheader("🔍 Analysis Result:")
        st.write(response.choices[0].message.content)
    else:
        st.warning("Please upload CV and paste JD")

if st.button("📝 Generate Cover Letter"):
    if uploaded_file and jd_text:
        reader = PyPDF2.PdfReader(uploaded_file)
        cv_text = ""
        for page in reader.pages:
            cv_text += page.extract_text()
        
        prompt = f"""Based on this CV and Job Description, write a professional cover letter (250 words).

CV:
{cv_text}

Job Description:
{jd_text}"""

        with st.spinner("Generating cover letter..."):
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            )
        
        st.subheader("📝 Cover Letter:")
        st.write(response.choices[0].message.content)
    else:
        st.warning("Please upload CV and paste JD")