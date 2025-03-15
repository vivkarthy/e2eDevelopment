import tempfile
import streamlit as st
from PyPDF2 import PdfReader
from io import BytesIO
import re
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
import json
from dotenv import load_dotenv
import os
from typing import TypedDict, List, Dict, Any, Optional

# Load environment variables
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
# Configuration
st.set_page_config(page_title="Multi-Agent App Development System", layout="wide")

# Initialize OpenAI Mini model
def init_llm():
    # Using OpenAI Mini - you'll need to replace with your own API key and endpoint
    # For demo purposes, we're using a standard OpenAI model, but you'd replace this with Mini
    return ChatOpenAI(
        model="gpt-4o-mini",  # Replace with OpenAI Mini model name
        temperature=0.2,
    )

# Define agent roles
ROLES = {
    "project_manager": "Analyzes requirements and coordinates tasks.",
    "designer": "Creates UI/UX designs and wireframes.",
    "developer": "Writes code and implements features.",
    "tester": "Tests functionality and identifies bugs.",
    "presenter": "Prepares presentations of the final product."
}

# Define the typed system state
class AppState(TypedDict):
    requirements: str
    messages: List[Any]
    current_stage: str
    design_docs: Dict[str, Any]
    code_modules: Dict[str, Any]
    test_results: Dict[str, Any]
    presentation: Dict[str, Any]
    current_agent: str

# Extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(BytesIO(pdf_file.read()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Define agent nodes
def create_agent_node(role, llm):
    def agent_fn(state: AppState):
        # Create a prompt based on the role and current state
        prompt_templates = {
            "project_manager": """You are the Project Manager. Analyze the following requirements and provide a structured project plan:
            
Requirements:
{requirements}

Current conversation:
{conversation}

Your response should include:
1. Project scope
2. Main features to implement
3. Technical requirements
4. Timeline and milestones
5. Task assignments for the team
6. Next steps
""",
            "designer": """You are the UI/UX Designer. Create design specifications based on the following requirements and project plan:
            
Requirements:
{requirements}

Project Plan:
{project_plan}

Current conversation:
{conversation}

Your response should include:
1. Wireframes description (describe key screens)
2. UI components needed
3. User flow diagrams
4. Design system suggestions (colors, typography, etc.)
5. Responsive design considerations
""",
            "developer": """You are the Developer. Write code based on the requirements and design specifications:
            
Requirements:
{requirements}

Design Specifications:
{design_specs}

Current conversation:
{conversation}

Your response should include:
1. Architecture overview
2. Implementation approach
3. Code structure
4. Sample code for key components
5. Dependencies and libraries needed
6. Setup instructions
""",
            "tester": """You are the Tester. Create a test plan and test cases based on the requirements and implemented code:
            
Requirements:
{requirements}

Implementation:
{implementation}

Current conversation:
{conversation}

Your response should include:
1. Test plan overview
2. Test scenarios
3. Test cases with expected results
4. Testing approach (manual/automated)
5. Edge cases to consider
6. Potential bugs to look for
""",
            "presenter": """You are the Presenter. Create a presentation of the final product based on all the work done:
            
Requirements:
{requirements}

Design:
{design}

Implementation:
{implementation}

Test Results:
{test_results}

Current conversation:
{conversation}

Your response should include:
1. Introduction to the product
2. Key features and functionality
3. Technical highlights
4. Implementation challenges and solutions
5. Demo script
6. Future enhancements
"""
        }
        
        # Format conversation history
        conversation_str = ""
        for msg in state["messages"]:
            if isinstance(msg, HumanMessage):
                conversation_str += f"Human: {msg.content}\n"
            else:
                conversation_str += f"AI ({msg.name if hasattr(msg, 'name') else 'Assistant'}): {msg.content}\n"
        
        # Get the right template and format it
        template = prompt_templates[role]
        prompt = template.format(
            requirements=state["requirements"],
            conversation=conversation_str,
            project_plan=state["messages"][0].content if len(state["messages"]) > 0 and state["current_stage"] != "requirements" else "",
            design_specs=state["design_docs"].get("specifications", "") if state["current_stage"] not in ["requirements"] else "",
            implementation=json.dumps(state["code_modules"], indent=2) if state["current_stage"] not in ["requirements", "design"] else "",
            design=json.dumps(state["design_docs"], indent=2) if state["current_stage"] not in ["requirements"] else "",
            test_results=json.dumps(state["test_results"], indent=2) if state["current_stage"] not in ["requirements", "design", "development"] else ""
        )
        
        # Call the LLM
        response = llm.invoke(prompt)
        
        # Update state with the agent's response
        new_messages = state["messages"] + [AIMessage(content=response.content, name=role)]
        
        # Create new dictionaries to ensure we're properly updating mutable values
        new_design_docs = state["design_docs"].copy() 
        new_code_modules = state["code_modules"].copy()
        new_test_results = state["test_results"].copy()
        new_presentation = state["presentation"].copy()
        
        # Update specific artifacts based on the current stage
        new_current_stage = state["current_stage"]
        new_current_agent = state["current_agent"]
        
        if role == "project_manager" and state["current_stage"] == "requirements":
            new_current_stage = "design"
            new_current_agent = "designer"
        elif role == "designer" and state["current_stage"] == "design":
            new_design_docs["specifications"] = response.content
            new_current_stage = "development"
            new_current_agent = "developer"
        elif role == "developer" and state["current_stage"] == "development":
            # Extract code blocks from the response
            code_blocks = re.findall(r"```(\w+)?\n(.*?)```", response.content, re.DOTALL)
            for i, (lang, code) in enumerate(code_blocks):
                new_code_modules[f"module_{i+1}"] = {
                    "language": lang.strip() if lang else "text",
                    "code": code.strip()
                }
            new_current_stage = "testing"
            new_current_agent = "tester"
        elif role == "tester" and state["current_stage"] == "testing":
            new_test_results["test_plan"] = response.content
            new_current_stage = "presentation"
            new_current_agent = "presenter"
        elif role == "presenter" and state["current_stage"] == "presentation":
            new_presentation["content"] = response.content
            new_current_stage = "complete"
        
        # Return only the updated values
        return {
            "messages": new_messages,
            "current_stage": new_current_stage,
            "current_agent": new_current_agent,
            "design_docs": new_design_docs,
            "code_modules": new_code_modules,
            "test_results": new_test_results, 
            "presentation": new_presentation
        }
    
    return agent_fn

# Define the router function
def router(state):
    current_stage = state["current_stage"]
    if current_stage == "complete":
        return END
    return state["current_agent"]

# Build the LangGraph
def build_graph(llm):
    # Create agent nodes
    nodes = {}
    for role in ROLES.keys():
        nodes[role] = create_agent_node(role, llm)
    
    # Create the graph with TypedDict state and proper config
    workflow = StateGraph(AppState)
    
    # Add nodes to the graph with specific state keys they can modify
    all_state_keys = ["messages", "current_stage", "current_agent", "design_docs", 
                      "code_modules", "test_results", "presentation"]
    
    for role, node_fn in nodes.items():
        workflow.add_node(role, node_fn)
    
    # Add edges from START to the first agent (project_manager)
    workflow.add_edge(START, "project_manager")
    
    # Add conditional edges based on the workflow stages
    for role in ROLES.keys():
        workflow.add_conditional_edges(
            role,
            router,
            {
                "project_manager": "project_manager",
                "designer": "designer",
                "developer": "developer",
                "tester": "tester",
                "presenter": "presenter",
                END: END
            }
        )
    
    return workflow.compile()

# Streamlit UI
def main():
    st.title("Multi-Agent App Development System")
    
    # Initialize session state
    if "initialized" not in st.session_state:
        st.session_state.graph = None
        st.session_state.state = None
        st.session_state.requirements = ""
        st.session_state.llm = init_llm()
        st.session_state.initialized = True
        st.session_state.process_started = False
    
    # Sidebar for uploading requirements
    with st.sidebar:
        st.header("Upload Requirements")
        uploaded_file = st.file_uploader("Upload PDF with requirements", type="pdf")
        
        if uploaded_file and not st.session_state.process_started:
            if st.button("Process Requirements"):
                with st.spinner("Extracting text from PDF..."):
                    requirements_text = extract_text_from_pdf(uploaded_file)
                    st.session_state.requirements = requirements_text
                    
                    # Initialize the state
                    initial_state = {
                        "requirements": requirements_text,
                        "messages": [],
                        "current_stage": "requirements",
                        "design_docs": {},
                        "code_modules": {},
                        "test_results": {},
                        "presentation": {},
                        "current_agent": "project_manager",
                    }
                    st.session_state.state = initial_state
                    
                    # Build the graph
                    st.session_state.graph = build_graph(st.session_state.llm)
                    
                    # Start the process
                    st.session_state.state = st.session_state.graph.invoke(st.session_state.state)
                    
                    # Mark process as started
                    st.session_state.process_started = True
                    
        st.subheader("Development Stages")
        stages = ["Requirements", "Design", "Development", "Testing", "Presentation"]
        current_stage = st.session_state.state["current_stage"] if st.session_state.state else "requirements"
        
        for i, stage in enumerate(stages):
            if current_stage.lower() == stage.lower():
                st.markdown(f"**→ {stage} ←**")
            elif current_stage.lower() == "complete" or (stages.index(stage) < stages.index([s for s in stages if s.lower() == current_stage][0])):
                st.markdown(f"✅ {stage}")
            else:
                st.markdown(f"⬜ {stage}")
                
    # Main content area
    if not st.session_state.process_started:
        st.info("Please upload a PDF with requirements to get started.")
    else:
        # Tab layout for different views
        tabs = st.tabs(["Conversation", "Artifacts", "Code", "Final Product"])
        
        with tabs[0]:  # Conversation
            st.subheader("Agent Conversation")
            
            # Display conversation
            for msg in st.session_state.state["messages"]:
                if isinstance(msg, HumanMessage):
                    st.markdown(f"**You**: {msg.content}")
                else:
                    st.markdown(f"**{msg.name}**: {msg.content}")
            
            # Button to advance the workflow
            if st.session_state.state["current_stage"] != "complete":
                current_agent = st.session_state.state["current_agent"]
                if st.button(f"Let {current_agent.replace('_', ' ').title()} work"):
                    with st.spinner(f"{current_agent.replace('_', ' ').title()} is working..."):
                        # Run the next step in the workflow
                        st.session_state.state = st.session_state.graph.invoke(st.session_state.state)
                        st.experimental_rerun()
            else:
                st.success("Development process complete!")
                
        with tabs[1]:  # Artifacts
            st.subheader("Project Artifacts")
            
            # Display design docs
            if st.session_state.state["design_docs"]:
                with st.expander("Design Specifications", expanded=True):
                    st.markdown(st.session_state.state["design_docs"].get("specifications", ""))
            
            # Display test results
            if st.session_state.state["test_results"]:
                with st.expander("Test Plan", expanded=True):
                    st.markdown(st.session_state.state["test_results"].get("test_plan", ""))
            
            # Display presentation
            if st.session_state.state["presentation"]:
                with st.expander("Presentation", expanded=True):
                    st.markdown(st.session_state.state["presentation"].get("content", ""))
        
        with tabs[2]:  # Code
            st.subheader("Generated Code")
            
            if st.session_state.state["code_modules"]:
                for module_name, module_data in st.session_state.state["code_modules"].items():
                    with st.expander(f"Module: {module_name}", expanded=True):
                        st.code(module_data["code"], language=module_data["language"])
                        
                        # Add a download button for each code module
                        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{module_data['language']}")
                        with open(tmp_file.name, 'w',encoding='utf-8') as f:
                            f.write(module_data["code"])
                        
                        with open(tmp_file.name, 'rb') as f:
                            st.download_button(
                                label=f"Download {module_name}.{module_data['language']}",
                                data=f,
                                file_name=f"{module_name}.{module_data['language']}",
                                mime="text/plain"
                            )
                        
                        # Clean up temp file
                        try:
                            os.unlink(tmp_file.name)
                        except:
                            pass  # Silently ignore if deletion fails
        with tabs[3]:  # Final Product
            if st.session_state.state["current_stage"] == "complete":
                st.subheader("Final Product Showcase")
                
                # Display a summary of the final product
                st.markdown("### Project Summary")
                
                # Extract project name and description from PM's response
                pm_response = st.session_state.state["messages"][0].content if st.session_state.state["messages"] else ""
                project_name_match = re.search(r"# (.+?)(\n|$)", pm_response)
                project_name = project_name_match.group(1) if project_name_match else "Application"
                
                st.markdown(f"**Project Name**: {project_name}")
                
                # Display key features from PM's response
                features_section = re.search(r"(?:Features|Main features|Key features):(.*?)(?:\n#|\n\n\d\.|\Z)", 
                                            pm_response, re.DOTALL | re.IGNORECASE)
                if features_section:
                    st.markdown("**Key Features**:")
                    features_text = features_section.group(1).strip()
                    features = re.findall(r"[-\*•]?\s*(.*?)(?:\n[-\*•]|\n\n|\Z)", features_text, re.DOTALL)
                    for feature in features:
                        st.markdown(f"- {feature.strip()}")
                
                # Display a fake screenshot placeholder
                st.markdown("### Application Preview")
                st.image("https://via.placeholder.com/800x500?text=Application+Preview", 
                        caption="Application Preview", use_column_width=True)
                
                # Add a demo section
                st.markdown("### Demo")
                st.info("In a real implementation, this section would contain an interactive demo of your application.")
                
                # Add download buttons for all artifacts
                st.markdown("### Download Project Artifacts")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Create a zip file with all artifacts (not implemented)
                    st.button("Download Complete Project")
                
                with col2:
                    # Create documentation PDF (not implemented)
                    st.button("Download Documentation")
                
                with col3:
                    # Create presentation (not implemented)
                    st.button("Download Presentation")
            else:
                st.info("The final product will be available once all development stages are complete.")

if __name__ == "__main__":
    main()
st.markdown("<div class='footer'>Developed by <b>Karthik Vivekanandhan</b></div>", unsafe_allow_html=True)
