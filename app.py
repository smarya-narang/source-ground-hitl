import streamlit as st
import os
import csv
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from tavily import TavilyClient

# --- PAGE CONFIGURATION (Must be the first Streamlit command) ---
st.set_page_config(layout="wide", page_title="Agent Verification Lab")

# --- SECURITY SETUP ---
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not GROQ_API_KEY or not TAVILY_API_KEY:
    st.error("🚨 API Keys not found! Make sure you have created a .env file.")
    st.stop()

# --- INITIALIZE CLIENTS ---
llm = ChatGroq(temperature=0, model_name="llama-3.3-70b-versatile", groq_api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

# --- CSV LOGGING SETUP ---
CSV_FILE = "experiment_results3.csv"

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "topic",
            "agent_claim",
            "source_url",
            "human_verdict",
            "verification_mode",
            "verification_time_seconds" # <-- NEW COLUMN FOR THE TIMER
        ])

# --- UI HEADER ---
st.title("🕵️ Source-Grounded Agent (HITL)")
st.markdown("### Human-in-the-Loop Verification Experiment")
st.markdown("---")

# --- SESSION STATE MANAGEMENT ---
if "step" not in st.session_state: st.session_state.step = "input" 
if "topic" not in st.session_state: st.session_state.topic = ""
if "research_data" not in st.session_state: st.session_state.research_data = None
if "ai_summary" not in st.session_state: st.session_state.ai_summary = ""
if "exact_quote" not in st.session_state: st.session_state.exact_quote = ""
if "verification_status" not in st.session_state: st.session_state.verification_status = None
if "experiment_mode" not in st.session_state: st.session_state.experiment_mode = "Source-Grounded (Experimental)"
if "start_time" not in st.session_state: st.session_state.start_time = None # <-- TIMER START STATE
if "verification_time" not in st.session_state: st.session_state.verification_time = None # <-- TIMER END STATE

# --- STEP 1: INPUT PHASE ---
if st.session_state.step == "input":
    st.header("Step 1: Define Research Topic")
    
    # 1. Experiment Mode Toggle (For A/B Testing)
    st.session_state.experiment_mode = st.radio(
        "Select Experiment Mode:",
        ["Blind Mode (Control)", "Source-Grounded (Experimental)"],
        horizontal=True
    )
    st.write("---")
    
    # 2. Trap Question Loader (Dropdown)
    trap_questions = []
    dataset_file = "adversarial_dataset2.csv" if os.path.exists("adversarial_dataset2.csv") else "queries.csv"
    
    if os.path.exists(dataset_file):
        with open(dataset_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            q_col = "Question" if "Question" in reader.fieldnames else "query"
            trap_questions = [row[q_col] for row in reader if q_col in row]

    if trap_questions:
        use_dataset = st.checkbox(f"🧪 Load question from {dataset_file}", value=True)
        if use_dataset:
            topic_input = st.selectbox("Select a trap question:", trap_questions)
        else:
            topic_input = st.text_input("Enter a custom topic to research:")
    else:
        topic_input = st.text_input("Enter a topic to research:", placeholder="e.g., What was Nvidia's reported Data Center revenue in Q4 2024?")
    
    if st.button("🚀 Start Agent"):
        if not topic_input:
            st.warning("Please enter a topic.")
        else:
            with st.spinner("Agent is searching the web and generating a claim..."):
                try:
                    search_result = tavily.search(query=topic_input, search_depth="basic", max_results=1)
                    
                    if not search_result.get('results'):
                        st.error("No results found. Try a different topic.")
                        st.stop()

                    st.session_state.topic = topic_input
                    st.session_state.research_data = search_result['results'][0]
                    # UPDATED SYSTEM PROMPT
                    source_text = st.session_state.research_data['content']
                    
                    # Added JSON instructions back in so the highlighter works!
                    prompt = f"""
                    System Instruction: You are a strict financial verification assistant. You will be provided with a user query and raw source context. You must adhere strictly to the following rules:
                    1. Base your answer solely on the provided raw context.
                    2. Do not use any internal knowledge, external facts, or assumptions.
                    3. Your final response must be exactly two sentences long.
                    
                    You MUST return your response as a valid JSON object with exactly two keys:
                    "claim": "Your summary here",
                    "exact_quote": "Copy and paste the EXACT word-for-word sentence from the text that proves your claim. If you cannot find one, leave this empty."

                    Text Context:
                    {source_text}
                    """

                    response = llm.invoke(prompt)
                    
                    try:
                        clean_text = response.content.replace('```json', '').replace('```', '').strip()
                        parsed_data = json.loads(clean_text)
                        
                        st.session_state.ai_summary = parsed_data.get("claim", "Error extracting claim.")
                        st.session_state.exact_quote = parsed_data.get("exact_quote", "")
                    except json.JSONDecodeError:
                        st.session_state.ai_summary = response.content
                        st.session_state.exact_quote = ""

                    # --- START TIMER EXACTLY WHEN AGENT FINISHES ---
                    st.session_state.start_time = datetime.now()
                    st.session_state.step = "review"
                    st.rerun()

                except Exception as e:
                    st.error(f"Error: {e}")

# --- STEP 2: VERIFICATION PHASE ---
elif st.session_state.step == "review":
    st.header("Step 2: Human Verification Loop")
    
    with st.expander("📌 View Original Research Question", expanded=True):
        st.markdown(f"**{st.session_state.topic}**")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    safe_summary = st.session_state.ai_summary.replace("$", "\$")
    
    # If Experimental Mode: Show Split Screen
    if st.session_state.experiment_mode == "Source-Grounded (Experimental)":
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("🤖 AI Generated Claim")
            st.info(safe_summary)
            st.caption("The agent extracted this claim automatically.")

        with col2:
            st.subheader("📄 Source Context")
            if st.session_state.research_data:
                url = st.session_state.research_data['url']
                st.markdown(f"**Source URL:** [{url}]({url})")
                
                content = st.session_state.research_data['content']
                quote = st.session_state.get('exact_quote', '')
                
                if quote and quote in content:
                    highlight_html = f'<mark style="background-color: #ffeb3b; color: #000; padding: 0 4px; border-radius: 4px; font-weight: bold; box-shadow: 0 0 5px #ffeb3b;">{quote}</mark>'
                    highlighted_content = content.replace(quote, highlight_html)
                else:
                    highlighted_content = content 
                
                st.markdown(
                    f"""
                    <div style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; height: 400px; overflow-y: auto; background-color: #f9f9f9; color: #2c3e50; font-family: 'Arial', sans-serif; font-size: 15px; line-height: 1.6; box-shadow: inset 0 0 10px rgba(0,0,0,0.05);">
                        {highlighted_content}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                if not quote or quote not in content:
                    st.caption("⚠️ *AI could not pinpoint an exact quote for this claim. Verify carefully!*")
                else:
                    st.caption("✨ *Evidence automatically highlighted by the agent.*")
                
    # If Control Mode: Hide the Reader Mode
    else:
        st.subheader("🤖 AI Generated Claim")
        st.info(safe_summary)
        st.caption("Standard AI View. Source links and evidence are hidden in Blind Mode. Please verify this claim based entirely on your own knowledge.")
    
    st.markdown("---")
    st.write("### 🔍 Verification Decision")

    def log_to_csv(verdict):
        # --- STOP TIMER AND CALCULATE SECONDS ---
        if st.session_state.start_time:
            time_taken = round((datetime.now() - st.session_state.start_time).total_seconds(), 2)
        else:
            time_taken = 0.0
        st.session_state.verification_time = time_taken

        with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                st.session_state.topic,
                st.session_state.ai_summary,
                st.session_state.research_data['url'],
                verdict,
                st.session_state.experiment_mode,
                time_taken # <-- RECORD THE TIME TO CSV
            ])

    c1, c2, c3 = st.columns(3)

    if c1.button("✅ Approve"):
        log_to_csv("Verified Accurate")
        st.session_state.verification_status = "Verified Accurate"
        st.session_state.step = "verified"
        st.rerun()

    if c2.button("❌ Reject"):
        log_to_csv("Hallucination Detected")
        st.session_state.verification_status = "Hallucination Detected"
        st.session_state.step = "verified"
        st.rerun()

    if c3.button("🔄 Restart"):
        st.session_state.step = "input"
        st.rerun()

# --- STEP 3: LOGGING PHASE ---
elif st.session_state.step == "verified":
    st.header("Step 3: Verification Log")
    
    if st.session_state.verification_status == "Verified Accurate":
        st.success("✅ Success! The claim was approved.")
    else:
        st.error("⚠️ Correction! The human verifier rejected the claim.")
        
    log_data = {
        "topic": st.session_state.topic,
        "agent_claim": st.session_state.ai_summary,
        "source_url": st.session_state.research_data['url'],
        "human_verdict": st.session_state.verification_status,
        "mode_used": st.session_state.experiment_mode,
        "verification_time_seconds": st.session_state.verification_time # <-- SHOW TIME ON SCREEN
    }
    st.json(log_data)
    
    st.markdown("---")
    # FIXED BUTTON AND STATE RESET
    if st.button("🔬 Test Another Topic"):
        st.session_state.step = "input"
        st.rerun()