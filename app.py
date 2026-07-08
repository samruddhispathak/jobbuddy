import streamlit as st
from groq import Groq
import PyPDF2
import os
from dotenv import load_dotenv
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from io import BytesIO
import streamlit.components.v1 as components
import requests

# --- RATE LIMITING ---
MAX_REQUESTS_PER_SESSION = 10

if "request_count" not in st.session_state:
    st.session_state.request_count = 0

def check_rate_limit():
    if st.session_state.request_count >= MAX_REQUESTS_PER_SESSION:
        st.error(f"⚠️ Limit reached ({MAX_REQUESTS_PER_SESSION} requests per session). Refresh to reset.")
        st.stop()
    st.session_state.request_count += 1

# --- SETUP ---
load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="JobBuddy",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE INIT ---
if "history" not in st.session_state:
    st.session_state.history = []
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "cover_letter" not in st.session_state:
    st.session_state.cover_letter = ""
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

# --- THEME COLORS ---
if st.session_state.dark_mode:
    bg_color = "#1a1a2e"
    card_bg = "#16213e"
    text_color = "#eaeaea"
    accent = "#e94560"
    soft_bg = "#0f3460"
else:
    bg_color = "#fdfcf7"
    card_bg = "#ffffff"
    text_color = "#2c2c2c"
    accent = "#7c5cff"
    soft_bg = "#f5f2ff"

# --- CUSTOM CSS ---
st.markdown(f"""
<style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    .main-card {{
        background: {card_bg};
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }}
    .keyword-tag {{
        display: inline-block;
        background: linear-gradient(135deg, #ff6b6b, #ee5a6f);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        margin: 4px;
        font-size: 13px;
        font-weight: 500;
        box-shadow: 0 2px 6px rgba(238, 90, 111, 0.3);
    }}
    .suggestion-box {{
        background: {soft_bg};
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 10px;
        border-left: 4px solid {accent};
    }}
    .stButton > button {{
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        transition: all 0.2s !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    .match-container {{
        background: {soft_bg};
        border-radius: 20px;
        padding: 30px;
        text-align: center;
    }}
    .match-number {{
        font-size: 64px;
        font-weight: 800;
        margin: 0;
    }}
    .progress-bar-bg {{
        background: #e0e0e0;
        border-radius: 10px;
        height: 20px;
        overflow: hidden;
        margin-top: 15px;
    }}
    .progress-bar-fill {{
        height: 100%;
        border-radius: 10px;
        transition: width 1s ease;
    }}
    .history-item {{
        background: {soft_bg};
        padding: 10px 14px;
        border-radius: 10px;
        margin-bottom: 8px;
        font-size: 13px;
    }}
    .cover-letter-box {{
        background: {card_bg};
        border: 2px dashed {accent};
        padding: 25px;
        border-radius: 15px;
        line-height: 1.8;
        font-family: 'Georgia', serif;
    }}
    h1, h2, h3 {{
        color: {text_color} !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    dark = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
    if dark != st.session_state.dark_mode:
        st.session_state.dark_mode = dark
        st.rerun()
    
    st.divider()
    st.markdown("### 💡 How to use")
    st.markdown("""
    1. 📄 Upload your CV
    2. 📋 Paste job description
    3. 🔍 Click Analyze
    4. 📝 Generate cover letter
    """)
    
    st.divider()
    
    if st.button("🗑️ Clear All", use_container_width=True):
        st.session_state.analysis_result = None
        st.session_state.cover_letter = ""
        st.rerun()
    
    st.divider()
    
    st.markdown("### 📚 Recent Analyses")
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history[-5:])):
            st.markdown(f"""
            <div class="history-item">
                <b>{item['match']}%</b> — {item['time']}<br>
                <small>{item['jd_preview']}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No analyses yet. Run one to see history!")

    st.divider()
    remaining = MAX_REQUESTS_PER_SESSION - st.session_state.request_count
    st.caption(f"🔋 {remaining}/{MAX_REQUESTS_PER_SESSION} requests remaining")
    
    # --- FEEDBACK SECTION ---
    st.divider()
    st.markdown("### 💬 Send Feedback")
    
    with st.expander("Share your thoughts"):
        feedback_rating = st.slider("Rate JobBuddy", 1, 5, 5)
        feedback_text = st.text_area("Your feedback", height=100, placeholder="What did you like? What can be better?")
        
        if st.button("📤 Submit Feedback", use_container_width=True):
            if feedback_text.strip():
                try:
                    FEEDBACK_URL = "https://script.google.com/macros/s/AKfycbwJS4g3tIML7z2xdGq9ogO4Pe7anzT3bH1TTVAcDRWIEFZZbfQgaKVBcih1mYqOndAn/exec"
                    response = requests.post(
                        FEEDBACK_URL,
                        json={"feedback": feedback_text, "rating": feedback_rating},
                        timeout=5
                    )
                    st.success("✅ Thank you! Feedback sent 💜")
                except Exception as e:
                    st.error("Couldn't send. Please try again later.")
            else:
                st.warning("Please write something first!")
    
    st.divider()
    st.caption("JobBuddy 🤖 | Made with ❤️ by Samruddhi")
    st.caption("Powered by Groq AI")

# --- MAIN HEADER ---
st.markdown(f"""
<div style="text-align:center; padding:20px 0;">
    <h1 style="font-size:48px; margin-bottom:0;">JobBuddy 🤖</h1>
    <p style="font-size:18px; color:{text_color}; opacity:0.7;">Your AI-Powered Job Application Assistant</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# --- INPUTS ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📄 Your CV")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")

with col2:
    st.markdown("### 📋 Job Description")
    jd_text = st.text_area("Paste JD here", height=250, label_visibility="collapsed", placeholder="Paste the job description here...")

# --- EXTRACT CV ---
cv_text = ""
cv_extracted = False

if uploaded_file:
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                cv_text += extracted
        
        if len(cv_text.strip()) < 50:
            st.warning("⚠️ Couldn't extract much text. Is your CV scanned/image-based? Try a text-based PDF.")
            cv_extracted = False
        else:
            cv_extracted = True
            st.success(f"✅ CV uploaded — {len(cv_text)} characters extracted")
    except Exception as e:
        st.error("❌ Couldn't read this PDF. Please try another file.")
        cv_extracted = False

# --- BUTTONS ---
st.divider()
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    analyze_btn = st.button("🔍 Analyze Match", use_container_width=True, type="primary")

with col_btn2:
    cover_btn = st.button("📝 Generate Cover Letter", use_container_width=True)

# --- AI FUNCTIONS ---
def analyze_cv_jd(cv, jd):
    prompt = f"""Analyze this CV against the Job Description.

You MUST respond in this EXACT format:

MATCH: [percentage number only, e.g., 75]

MISSING KEYWORDS: [keyword1, keyword2, keyword3, keyword4, keyword5]

SUGGESTION 1: [specific suggestion]
SUGGESTION 2: [specific suggestion]
SUGGESTION 3: [specific suggestion]

CV:
{cv}

Job Description:
{jd}"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            timeout=30
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error("❌ AI service unavailable right now. Please try again in a moment.")
        st.stop()

def generate_cover(cv, jd):
    prompt = f"""Write a professional cover letter (250-300 words) based on this CV and Job Description.

Rules:
- Start with "Dear Hiring Manager,"
- Be specific about skills that match the JD
- Include a call to action at the end
- Professional but warm tone
- End with "Sincerely,\n[Your Name]"

CV:
{cv}

Job Description:
{jd}"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            timeout=30
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error("❌ Couldn't generate cover letter. Please try again.")
        st.stop()

def create_pdf(cover_letter_text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    story = []
    for para in cover_letter_text.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.replace("\n", "<br/>"), styles["Normal"]))
            story.append(Spacer(1, 12))
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- HANDLE ANALYZE ---
if analyze_btn:
    if not cv_extracted:
        st.warning("⚠️ Please upload your CV first")
    elif not jd_text:
        st.warning("⚠️ Please paste the Job Description")
    else:
        check_rate_limit()
        with st.spinner("🔍 Analyzing your CV..."):
            result = analyze_cv_jd(cv_text, jd_text)
        
        lines = result.strip().split("\n")
        match_pct = "0"
        keywords = []
        suggestions = []
        
        for line in lines:
            line = line.strip()
            if line.startswith("MATCH:"):
                match_pct = line.replace("MATCH:", "").strip().replace("%", "")
            elif line.startswith("MISSING KEYWORDS:"):
                kw_str = line.replace("MISSING KEYWORDS:", "").strip()
                keywords = [k.strip().strip("[]") for k in kw_str.split(",")]
            elif line.startswith("SUGGESTION"):
                suggestions.append(line.split(":", 1)[1].strip() if ":" in line else line)
        
        try:
            match_num = int(match_pct)
        except:
            match_num = 0
        
        st.session_state.analysis_result = {
            "match": match_num,
            "keywords": keywords,
            "suggestions": suggestions
        }
        st.session_state.history.append({
            "match": match_num,
            "time": datetime.now().strftime("%d %b %H:%M"),
            "jd_preview": jd_text[:60] + "..."
        })

# --- SHOW ANALYSIS RESULT ---
if st.session_state.analysis_result:
    res = st.session_state.analysis_result
    match_num = res["match"]
    keywords = res["keywords"]
    suggestions = res["suggestions"]
    
    st.markdown("## 📊 Analysis Results")
    
    color = "#00cc88" if match_num >= 70 else "#ffaa00" if match_num >= 50 else "#ff5555"
    emoji = "💪" if match_num >= 70 else "👍" if match_num >= 50 else "⚠️"
    feedback = "Great match!" if match_num >= 70 else "Good, but can improve" if match_num >= 50 else "Needs improvement"
    
    st.markdown(f"""
    <div class="match-container">
        <p style="font-size:20px; margin-bottom:0;">{emoji} {feedback}</p>
        <p class="match-number" style="color:{color};">{match_num}%</p>
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width:{match_num}%; background:{color};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    if keywords:
        st.markdown("### 🔴 Missing Keywords")
        st.caption("Consider adding these to your CV if relevant")
        tags_html = "".join([f'<span class="keyword-tag">{kw}</span>' for kw in keywords if kw])
        st.markdown(tags_html, unsafe_allow_html=True)
        st.write("")
    
    if suggestions:
        st.markdown("### 💡 Suggestions to Improve")
        for i, sug in enumerate(suggestions, 1):
            with st.expander(f"Suggestion {i}"):
                st.write(sug)

# --- HANDLE COVER LETTER ---
if cover_btn:
    if not cv_extracted:
        st.warning("⚠️ Please upload your CV first")
    elif not jd_text:
        st.warning("⚠️ Please paste the Job Description")
    else:
        check_rate_limit()
        with st.spinner("📝 Generating your cover letter..."):
            st.session_state.cover_letter = generate_cover(cv_text, jd_text)

# --- SHOW COVER LETTER ---
if st.session_state.cover_letter:
    st.markdown("## ✉️ Your Cover Letter")
    
    edited_cover = st.text_area(
        "Edit before downloading:",
        value=st.session_state.cover_letter,
        height=400
    )
    
    col_d1, col_d2, col_d3 = st.columns(3)
    
    with col_d1:
        st.download_button(
            label="📄 Download TXT",
            data=edited_cover,
            file_name="cover_letter.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col_d2:
        pdf_buffer = create_pdf(edited_cover)
        st.download_button(
            label="📕 Download PDF",
            data=pdf_buffer,
            file_name="cover_letter.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    with col_d3:
        safe_text = edited_cover.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        components.html(f"""
        <button onclick="
            navigator.clipboard.writeText(`{safe_text}`);
            this.innerText='✅ Copied!';
            setTimeout(() => this.innerText='📋 Copy to Clipboard', 2000);
        " style="
            width:100%; 
            padding:12px; 
            border-radius:12px; 
            border:none; 
            background:{accent}; 
            color:white; 
            font-weight:600; 
            cursor:pointer;
            font-size:14px;
        ">
            📋 Copy to Clipboard
        </button>
        """, height=60)

# --- FOOTER ---
st.divider()
st.markdown(f"""
<div style="text-align:center; opacity:0.6; padding:20px;">
    JobBuddy © 2026 | Made with ❤️ by Samruddhi Pathak
</div>
""", unsafe_allow_html=True)