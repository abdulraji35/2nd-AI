import os
import streamlit as st
from dotenv import load_dotenv
from google import generativeai as genai
import pdfplumber
import docx


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure()
model = genai.GenerativeModel('gemini-1.5-flash')

###

st.set_page_config(
    page_title="Medical Diagnostics AI",
    page_icon="🏥", 
    layout="centered"
)

###

st.header("🏥Medical Symptom Explainer & Appointment Guide")
st.markdown("---")
st.subheader("🗄️Let's Get your Medical Information")

# Patients Symptoms 
st.markdown("Upload or type your symptoms and get an easy-to-understand summary, questions for your doctor, and a printable appointment guide.")
uploaded_file = st.file_uploader("Upload Resume (.pdf or .docx)", type=["pdf", "docx"])

extracted_ms = ""
if uploaded_file:
    file_type = uploaded_file.name.split('.')[-1]
    try:
        if file_type == "pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                extracted_ms = "\n".join([page.extract_text() or "" for page in pdf.pages])
        elif file_type == "docx":
            doc = docx.Document(uploaded_file)
            extracted_ms = "\n".join([para.text for para in doc.paragraphs])
        else:
            st.warning("Unsupported file type.")
    except Exception as e:
        st.error(f"Error extracting text: {e}")
        
symptom_text = st.text_area("🧾 Paste your Resume here", height=300, value=extracted_ms, help="Copy and paste your resume.")

###

st.subheader("🧑‍⚕️Choose Doctor or Appointment Type")
doctor_type = st.selectbox("Appointment type:", ["General Practitioner", "Cardiologist", "Dermatologist", "Pediatrician", "Other"])

st.text("")

col1, col2, col3 = st.columns(3)
with col1:
    gen_expl = st.checkbox("🔍 Explain Symptoms", value=True)
with col2:
    gen_qs = st.checkbox("❓ Suggested Questions", value=True)
with col3:
    gen_summary = st.checkbox("📝 Summary Sheet", value=True)

st.text("")

# === Creativity Slider ===
st.slider("🎛️ Gemini Creativity (Temperature)", 0.0, 1.0, 0.7, 0.1, key="temperature")

###

st.subheader("📤 Get Your AI-Generated Appointment Guide")
if st.button("🚀 Generate Appointment Guide"):
    if not symptom_text or not doctor_type:
        st.warning("⚠️ Please fill out both Medical Information and Appointment Type")
    elif not (gen_expl or gen_qs or gen_summary):
        st.warning("⚠️ Please select at least one generation option.")
    else:
        with st.spinner("🧠 Thinking..."):
            items = []

            if gen_expl:
                items.append("""### 🔍 Explain Symptoms

Explain the patient's symptoms in **simple, friendly language** without diagnosing. Mention possible contributing factors gently (like sleep, hydration, posture), but make it clear this is not a diagnosis.
""")
            if gen_qs:
                items.append("""### ❓ Suggested Questions

List 3–5 helpful, respectful questions** the patient can ask their doctor to:
- Explore possible causes
- Ask about medication, diet, or sleep habits
- Understand if any tests or referrals are needed
""")
            if gen_summary:
                items.append("""### 📝 Summary Sheet

Create a **short summary** the patient can bring to the doctor:
- Include when the symptoms happen
- How frequent
- Any patterns (e.g. in mornings)
- Context (like stress, sleep, diet)
Use 3–4 bullet points or short paragraphs.
""")

            full_prompt = f"""
You are a compassionate and knowledgeable virtual health assistant designed to support patients in preparing for medical consultations. You are not a doctor, and you do not provide diagnoses or medical advice. Your role is to help patients understand their symptoms in plain, accessible language, guide them on what to ask during a medical visit, and assist them in organizing their thoughts for better communication with their healthcare provider.

The patient is going to a **{doctor_type}** appointment.
Their symptoms are: {symptom_text}

Respond only to the selected tasks below, and format your output clearly using the following headers:

{''.join(items)}
"""

            try:
                response_stream = model.generate_content(full_prompt, stream=True,
                    generation_config={"temperature": st.session_state.temperature})

                full_output = ""
                response_box = st.empty()

                for chunk in response_stream:
                    full_output += chunk.text
                    response_box.markdown(full_output + "▌")

            except Exception as e:
                st.error(f"An error occurred: {e}")
