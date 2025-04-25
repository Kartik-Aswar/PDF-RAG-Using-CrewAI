import streamlit as st
import os
import tempfile
import gc
import base64
import time
from crewai import LLM
from tools.document_tool import DocumentSearchTool
#from crewai_tools import FirecrawlSearchTool
from crewai_tools import SerperDevTool 
from src.agent import retriever_agent, response_synthesizer_agent
from src.tasks import synthesizer_task, retrival_task
from crew import Agentic_rag
from dotenv import load_dotenv
load_dotenv()


@st.cache_resource
def load_llm():
    llm = LLM(
        model="gemini/gemini-2.0-flash",
        temperature=0.7
    )
    return llm

api_key = os.getenv("SERPER_API_KEY")

def create_agents_and_tasks(pdf_tool):
    web_search_tool = SerperDevTool(
            api_key=api_key,
            params={
                "num_results": 5,  # Optional: number of results to return
                "include_domains": [],  # Optional: specific domains to search
                "exclude_domains": []  # Optional: domains to exclude
            }
        )
    llm=load_llm()
    rag = Agentic_rag(pdf_tool=pdf_tool, web_search_tool=web_search_tool)
    crew = rag.crew(llm=llm)
    return crew





# ===========================
#   Streamlit Setup
# ===========================
if "messages" not in st.session_state:
    st.session_state.messages = []  # Chat history

if "pdf_tool" not in st.session_state:
    st.session_state.pdf_tool = None  # Store the DocumentSearchTool

if "crew" not in st.session_state:
    st.session_state.crew = None      # Store the Crew object

def reset_chat():
    st.session_state.messages = []
    gc.collect()

def display_pdf(file_bytes: bytes, file_name: str):
    """Displays the uploaded PDF in an iframe."""
    base64_pdf = base64.b64encode(file_bytes).decode("utf-8")
    pdf_display = f"""
    <iframe 
        src="data:application/pdf;base64,{base64_pdf}" 
        width="100%" 
        height="600px" 
        type="application/pdf"
    >
    </iframe>
    """
    st.markdown(f"### Preview of {file_name}")
    st.markdown(pdf_display, unsafe_allow_html=True)

# ===========================
#   Sidebar
# ===========================
with st.sidebar:
    st.header("Add Your PDF Document")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        # If there's a new file 
        os.makedirs("knowledge", exist_ok=True) 
        local_path = os.path.join("knowledge", "uploaded.pdf")
                
        with open(local_path, "wb") as f:
                f.write(uploaded_file.getvalue())

        if st.session_state.pdf_tool is None:
            with st.spinner("Indexing PDF... Please wait..."):
                    st.session_state.pdf_tool = DocumentSearchTool(file_path=local_path)
            
            st.success("PDF indexed! Ready to chat.")

        # Optionally display the PDF in the sidebar
        display_pdf(uploaded_file.getvalue(), uploaded_file.name)

    st.button("Clear Chat", on_click=reset_chat)

# ===========================
#   Main Chat Interface
# ===========================
st.markdown("""
    # Agentic RAG powered by <img src="data:image/png;base64,{}" width="120" style="vertical-align: -3px;">
""".format(base64.b64encode(open("assets/gemini.webp", "rb").read()).decode()), unsafe_allow_html=True)

# Render existing conversation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
prompt = st.chat_input("Ask a question about your PDF...")

if prompt:
    # 1. Show user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Build or reuse the Crew (only once after PDF is loaded)
    if st.session_state.crew is None:
        st.session_state.crew = create_agents_and_tasks(st.session_state.pdf_tool)

    # 3. Get the response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Get the complete response first
        with st.spinner("Thinking..."):
            inputs = {"query": prompt}
            result = st.session_state.crew.kickoff(inputs=inputs).raw
        
        # Split by lines first to preserve code blocks and other markdown
        lines = result.split('\n')
        for i, line in enumerate(lines):
            full_response += line
            if i < len(lines) - 1:  # Don't add newline to the last line
                full_response += '\n'
            message_placeholder.markdown(full_response + "▌")
            time.sleep(0.15)  # Adjust the speed as needed
        
        # Show the final response without the cursor
        message_placeholder.markdown(full_response)

    # 4. Save assistant's message to session
    st.session_state.messages.append({"role": "assistant", "content": result})


