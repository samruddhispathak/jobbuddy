import streamlit as st
from groq import Groq
import PyPDF2

# Setup Groq
client = Groq(api_key="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")

st.title("JobBuddy 🤖")
st.write("AI Job Application Assistant")

# Upload CV
uploaded_file = st.file_uploader("Upload your CV (PDF)", type="pdf")

# Job Description
jd_text = st.text_area("Paste Job Description", height=200)

# Analyze button
if st.button("🔍 Analyze"):
    if uploaded_file and jd_text:
        # Extract CV text
        reader = PyPDF2.PdfReader(uploaded_file)
        cv_text = ""
        for page in reader.pages:
            cv_text += page.extract_text()
        
        # Send to AI
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

# Generate Cover Letter Button
if st.button("📝 Generate Cover Letter"):
    if uploaded_file and jd_text:
        # Extract CV text
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