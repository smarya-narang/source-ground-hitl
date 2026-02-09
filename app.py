import streamlit as st
import os
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
# Using the supported Llama 3.3 model
llm = ChatGroq(temperature=0, model_name="llama-3.3-70b-versatile", groq_api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)

# --- UI HEADER ---
st.title("🕵️ Source-Grounded Agent (HITL)")
st.markdown("### Human-in-the-Loop Verification Experiment")
st.markdown("---")

# --- SESSION STATE MANAGEMENT ---
if "step" not in st.session_state:
    st.session_state.step = "input" 
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "research_data" not in st.session_state:
    st.session_state.research_data = None
if "ai_summary" not in st.session_state:
    st.session_state.ai_summary = ""
if "verification_status" not in st.session_state:
    st.session_state.verification_status = None

# --- STEP 1: INPUT PHASE ---
if st.session_state.step == "input":
    st.header("Step 1: Define Research Topic")
    topic_input = st.text_input("Enter a topic to research:", placeholder="e.g., Current world record for solar cell efficiency 2024")
    
    if st.button("🚀 Start Agent"):
        if not topic_input:
            st.warning("Please enter a topic.")
        else:
            with st.spinner("Agent is searching the web and generating a claim..."):
                try:
                    # 1. Search Action
                    search_result = tavily.search(
                        query=topic_input,
                        search_depth="basic",
                        max_results=1
                    )
                    
                    if not search_result.get('results'):
                        st.error("No results found. Try a different topic.")
                        st.stop()

                    st.session_state.topic = topic_input
                    st.session_state.research_data = search_result['results'][0]
                    
                    # 2. Summarization Action
                    source_text = st.session_state.research_data['content']
                    prompt = f"""
                    You are a rigorous research assistant.
                    Based ONLY on the following text, extract the key factual claim.
                    Do not add outside knowledge.
                    Limit to 2 sentences.

                    Text:
                    {source_text}
                    """

                    response = llm.invoke(prompt)
                    st.session_state.ai_summary = response.content

                    st.session_state.step = "review"
                    st.rerun()

                except Exception as e:
                    st.error(f"Error: {e}")

# --- STEP 2: VERIFICATION PHASE (Reader Mode) ---
elif st.session_state.step == "review":
    st.header("Step 2: Human Verification Loop")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🤖 AI Generated Claim")
        st.info(st.session_state.ai_summary)
        st.caption("The agent extracted this claim automatically.")

    with col2:
        st.subheader("📄 Source Context (Reader Mode)")
        
        if st.session_state.research_data:
            # Clickable Link
            url = st.session_state.research_data['url']
            st.markdown(f"**Source URL:** [{url}]({url})")
            
            # The "Reader Mode" HTML Block
            content = st.session_state.research_data['content']
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 20px;
                    height: 400px;
                    overflow-y: auto;
                    background-color: #f9f9f9;
                    color: #2c3e50;
                    font-family: 'Arial', sans-serif;
                    font-size: 15px;
                    line-height: 1.6;
                    box-shadow: inset 0 0 10px rgba(0,0,0,0.05);
                ">
                    {content}
                </div>
                """,
                unsafe_allow_html=True
            )
            st.caption("This window shows the exact raw text the AI analyzed.")
    
    st.markdown("---")
    st.write("### 🔍 Verification Decision")

    c1, c2, c3 = st.columns(3)

    if c1.button("✅ Approve"):
        st.session_state.verification_status = "Verified Accurate"
        st.session_state.step = "verified"
        st.rerun()

    if c2.button("❌ Reject"):
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
        st.success("✅ Success! The agent's claim matched the source evidence.")
    else:
        st.error("⚠️ Correction! The human verifier caught a hallucination.")
        
    log_data = {
        "topic": st.session_state.topic,
        "agent_claim": st.session_state.ai_summary,
        "source_url": st.session_state.research_data['url'],
        "human_verdict": st.session_state.verification_status
    }
    st.json(log_data)
    
    st.markdown("---")
    if st.button("🔬 Test Another Topic"):
        st.session_state.step = "input"
        st.rerun()