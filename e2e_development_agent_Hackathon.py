import streamlit as st
import os
import tempfile
import time
import pdfplumber
import openai
from fpdf import FPDF
import traceback
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set page configuration
st.set_page_config(
    page_title="PDF Requirements Processor",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define the Agent class for multi-agent architecture
class Agent:
    def __init__(self, name, role, model="gpt-4o-mini"):
        self.name = name
        self.role = role
        self.model = model
        self.history = []
    
    def process(self, prompt, content=None, max_retries=3):
        if not openai.api_key:
            return "Error: OpenAI API key is not set in environment variables. Please check your .env file."
        
        full_prompt = f"""
        You are a {self.role}. 
        
        {prompt}
        
        Content: {content if content else 'No additional content provided'}
        
        Respond in a structured, clear format.
        """
        
        for attempt in range(max_retries):
            try:
                response=openai.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": full_prompt}]
                )
                result = response.choices[0].message.content
                self.history.append({"prompt": prompt, "response": result})
                return result
            except Exception as e:
                if attempt == max_retries - 1:
                    return f"Error: {str(e)}"
                time.sleep(2)  # Wait before retrying

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name
    
    text = ""
    try:
        with pdfplumber.open(tmp_file_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n\n"
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        st.error(traceback.format_exc())
    finally:
        os.unlink(tmp_file_path)
    
    return text

# Function to generate PDF from content
def generate_pdf(content_dict):
    # Create a custom PDF class to add headers and footers
    class PDF(FPDF):
        def header(self):
            # Logo - using a placeholder since we don't have an actual logo
            # self.image('logo.png', 10, 8, 33)
            # Set font for header
            self.set_font('Arial', 'B', 12)
            # Title
            self.cell(0, 10, 'Requirements Processing Report', 0, 1, 'C')
            # Line break
            self.ln(5)
        
        def footer(self):
            # Position at 1.5 cm from bottom
            self.set_y(-15)
            # Set font for footer
            self.set_font('Arial', 'I', 8)
            # Page number
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    # Create PDF instance
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Set default font
    pdf.set_font("Arial", size=11)
    
    # Add title and document info
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Requirements Processing Report", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, f"Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
    pdf.ln(10)
    
    # Add table of contents header
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Table of Contents", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Add table of contents
    pdf.set_font("Arial", size=11)
    y_position = pdf.get_y()
    page_start = pdf.page_no()
    
    # Placeholder for TOC items - we'll fill these in later
    toc_placeholders = {}
    for section in content_dict.keys():
        toc_placeholders[section] = {'y': y_position, 'page': page_start}
        pdf.cell(0, 10, f"{section}...", ln=True)
        y_position += 10
    
    # Add each section with improved formatting
    section_page_numbers = {}
    for section, content in content_dict.items():
        # Add a page break for each new section
        pdf.add_page()
        
        # Store the page number for this section for the TOC
        section_page_numbers[section] = pdf.page_no()
        
        # Section header with background
        pdf.set_fill_color(230, 230, 230)  # Light gray background
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, section, ln=True, fill=True)
        pdf.ln(5)
        
        # Section content
        pdf.set_font("Arial", size=11)
        
        # Make sure content is str
        if not isinstance(content, str):
            content = str(content)
        
        # Enhanced character replacement to handle more Unicode characters
        content = (content
            # Basic replacements from original code
            .replace('\u2019', "'")  # Replace right single quote
            .replace('\u2018', "'")  # Replace left single quote
            .replace('\u201c', '"')  # Replace left double quote
            .replace('\u201d', '"')  # Replace right double quote
            .replace('\u2013', '-')  # Replace en dash
            .replace('\u2014', '--') # Replace em dash
            .replace('\u2026', '...') # Replace ellipsis
            .replace('\u00a0', ' ')  # Replace non-breaking space
            .replace('\u2022', '*')  # Replace bullet point
            .replace('\u2192', '->') # Replace right arrow
            .replace('\u2190', '<-')  # Replace left arrow
            .replace('\u2191', '^')   # Replace up arrow
            .replace('\u2193', 'v')   # Replace down arrow
            .replace('\u25b2', '^')   # Replace up triangle
            .replace('\u25bc', 'v')   # Replace down triangle
            .replace('\u2212', '-')   # Replace minus sign
            .replace('\u00d7', 'x')   # Replace multiplication sign
            .replace('\u00f7', '/')   # Replace division sign
            .replace('\u2032', "'")   # Replace prime
            .replace('\u2033', '"')   # Replace double prime
            .replace('\u2265', '>=')  # Replace greater than or equal to
            .replace('\u2264', '<=')  # Replace less than or equal to
            .replace('\u2248', '~=')  # Replace approximately equal
            .replace('\u00b1', '+/-') # Replace plus-minus
        )
        
        # Catch-all for any other non-Latin-1 characters
        content = content.encode('latin-1', 'replace').decode('latin-1')
        
        # Identify and format headings and bullet points
        paragraphs = content.split('\n')
        for paragraph in paragraphs:
            if not paragraph.strip():
                pdf.ln(5)
                continue
                
            # Check if this is a heading (assuming headings end with colon or are all caps)
            if paragraph.strip().endswith(':') or paragraph.strip().isupper():
                pdf.set_font("Arial", 'B', 12)
                pdf.multi_cell(0, 10, paragraph.strip())
                pdf.set_font("Arial", size=11)
                continue
                
            # Check if this is a bullet point
            if paragraph.strip().startswith('- ') or paragraph.strip().startswith('* '):
                pdf.set_x(15)  # Indent bullet points
                pdf.multi_cell(0, 7, paragraph)
                continue
                
            # Check if this is a numbered item
            if (paragraph.strip()[0].isdigit() and 
                paragraph.strip()[1:].startswith('. ')):
                pdf.set_x(15)  # Indent numbered items
                pdf.multi_cell(0, 7, paragraph)
                continue
                
            # Regular paragraph
            pdf.multi_cell(0, 7, paragraph)
        
        pdf.ln(10)
    
    # Now go back and fill in the table of contents with the correct page numbers
    # Save current position
    current_page = pdf.page_no()
    current_position = pdf.get_y()
    
    # Go back to the TOC page
    pdf_toc_page = PDF()  # Create a new instance for TOC updates
    pdf_toc_page.set_auto_page_break(auto=True, margin=15)
    
    # Copy the current PDF up to the TOC page
    for i in range(1, page_start + 1):
        pdf_toc_page.add_page()
    
    # Set position for TOC updates
    pdf_toc_page.set_font("Arial", 'B', 14)
    pdf_toc_page.cell(0, 10, "Table of Contents", ln=True)
    pdf_toc_page.line(10, pdf_toc_page.get_y(), 200, pdf_toc_page.get_y())
    pdf_toc_page.ln(5)
    
    # Update TOC with actual page numbers
    pdf_toc_page.set_font("Arial", size=11)
    for section, placeholder in toc_placeholders.items():
        pdf_toc_page.set_y(placeholder['y'])
        pdf_toc_page.set_x(10)
        pdf_toc_page.cell(160, 10, section)
        pdf_toc_page.cell(0, 10, f"Page {section_page_numbers[section]}", ln=True, align='R')
    
    # Merge the TOC page with the rest of the content
    # We'll handle this by creating the final PDF in memory
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_path = tmp_file.name
    
    pdf.output(tmp_path)
    with open(tmp_path, "rb") as f:
        pdf_data = f.read()
    
    os.unlink(tmp_path)
    return pdf_data

# Function to process requirements
def process_requirements(pdf_text, resource_constraints=None):
    results = {}
    
    try:
        # Check if API key is set
        if not openai.api_key:
            results["Error"] = "OpenAI API key is not set in environment variables. Please check your .env file."
            return results
            
        # Initialize agents
        user_story_agent = Agent("User Story Generator", "User Story Specialist")
        tech_design_agent = Agent("Technology Designer", "Technology Architect")
        test_scenario_agent = Agent("Test Scenario Generator", "QA Specialist")
        test_case_agent = Agent("Test Case Generator", "Test Engineer")
        
        # Initialize new agents
        project_manager_agent = Agent("Project Manager", "Project Manager")
        designer_agent = Agent("Designer", "UI/UX Designer")
        developer_agent = Agent("Developer", "Software Developer")
        
        # Set initial progress percentage
        st.session_state.progress_percentage = 10
        st.session_state.progress_bar.progress(st.session_state.progress_percentage / 100)
        st.session_state.progress_text.text(f"Progress: {st.session_state.progress_percentage}%")
        
        # Generate user stories
        st.session_state.status = "Generating User Stories..."
        user_stories = user_story_agent.process(
            "Create user stories based on the following requirements. Format them as 'As a [user], I want [action] so that [benefit]'. Provide at least 5-7 user stories that cover the main functionality.",
            pdf_text
        )
        results["User Stories"] = user_stories
        st.session_state.progress_percentage = 20
        st.session_state.progress_bar.progress(st.session_state.progress_percentage / 100)
        st.session_state.progress_text.text(f"Progress: {st.session_state.progress_percentage}%")
        
        # Generate project management plan
        st.session_state.status = "Creating Project Management Plan..."
        
        project_plan_prompt = f"""
        Create a detailed project management plan based on these requirements. 
        
        Include the following sections:
        1. Project Timeline - with specific dates
        2. Milestones
        3. Resource Allocation - always specify exact resource counts (number of people) instead of percentages
        4. Risk Assessment
        5. Coordination Strategy
        
        Format with clear sections.
        """
        
        project_plan = project_manager_agent.process(
            project_plan_prompt,
            pdf_text + "\n\nUser Stories:\n" + user_stories
        )
        results["Project Management Plan"] = project_plan
        st.session_state.progress_percentage = 40
        st.session_state.progress_bar.progress(st.session_state.progress_percentage / 100)
        st.session_state.progress_text.text(f"Progress: {st.session_state.progress_percentage}%")
        
        # Generate UI/UX design documents
        st.session_state.status = "Creating UI/UX Designs..."
        ui_design = designer_agent.process(
            "Create detailed UI/UX design specifications based on these requirements. Include wireframe descriptions, user flow diagrams, style guide recommendations, and accessibility considerations. Format with clear sections for each design component.",
            pdf_text + "\n\nUser Stories:\n" + user_stories
        )
        results["UI/UX Design Specifications"] = ui_design
        st.session_state.progress_percentage = 60
        st.session_state.progress_bar.progress(st.session_state.progress_percentage / 100)
        st.session_state.progress_text.text(f"Progress: {st.session_state.progress_percentage}%")
        
        # Generate development plan
        st.session_state.status = "Creating Development Plan..."
        
        dev_plan_prompt = "Create a detailed development plan based on these requirements. Include component architecture, data models, API specifications, implementation strategy, and technical considerations. Format with clear sections for frontend, backend, and database components."
        
        dev_plan = developer_agent.process(
            dev_plan_prompt,
            pdf_text + "\n\nUser Stories:\n" + user_stories + "\n\nUI/UX Design:\n" + ui_design
        )
        results["Development Plan"] = dev_plan
        st.session_state.progress_percentage = 70
        st.session_state.progress_bar.progress(st.session_state.progress_percentage / 100)
        st.session_state.progress_text.text(f"Progress: {st.session_state.progress_percentage}%")
        
        # Generate technology design
        st.session_state.status = "Creating Technology Design..."
        tech_design = tech_design_agent.process(
            "Create a detailed technology design based on these requirements. Include frontend, backend, database, and integration components. For each technology choice, provide justification on why it's the best fit. Format as bullet points with clear sections.",
            pdf_text + "\n\nDevelopment Plan:\n" + dev_plan
        )
        results["Technology Design"] = tech_design  # Changed from "Technology Design with Justification"
        st.session_state.progress_percentage = 80
        st.session_state.progress_bar.progress(st.session_state.progress_percentage / 100)
        st.session_state.progress_text.text(f"Progress: {st.session_state.progress_percentage}%")
        
        # Generate test scenarios
        st.session_state.status = "Generating Test Scenarios..."
        test_scenarios = test_scenario_agent.process(
            "Create test scenarios based on these requirements. Focus on key user journeys and critical functionality. Format as numbered scenarios with brief descriptions.",
            pdf_text + "\n\nUser Stories:\n" + user_stories + "\n\nDevelopment Plan:\n" + dev_plan
        )
        results["Test Scenarios"] = test_scenarios
        st.session_state.progress_percentage = 90
        st.session_state.progress_bar.progress(st.session_state.progress_percentage / 100)
        st.session_state.progress_text.text(f"Progress: {st.session_state.progress_percentage}%")
        
        # Generate test cases
        st.session_state.status = "Creating Test Cases..."
        test_cases = test_case_agent.process(
            "Create detailed test cases based on these requirements. Include test case ID, description, preconditions, steps, expected results, and pass/fail criteria. Format in a structured way for clarity.",
            pdf_text + "\n\nTest Scenarios:\n" + test_scenarios + "\n\nUser Stories:\n" + user_stories
        )
        results["Test Cases"] = test_cases
        st.session_state.progress_percentage = 100
        st.session_state.progress_bar.progress(st.session_state.progress_percentage / 100)
        st.session_state.progress_text.text(f"Progress: {st.session_state.progress_percentage}%")
    
    except Exception as e:
        error_msg = f"Error during processing: {str(e)}\n\n{traceback.format_exc()}"
        st.error(error_msg)
        results["Error"] = error_msg
    
    st.session_state.status = "Processing Complete"
    return results

# Initialize session state variables
if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'results' not in st.session_state:
    st.session_state.results = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'feedback_history' not in st.session_state:
    st.session_state.feedback_history = {}
if 'status' not in st.session_state:
    st.session_state.status = "Ready"
if 'resource_constraints' not in st.session_state:
    st.session_state.resource_constraints = None
if 'progress_percentage' not in st.session_state:
    st.session_state.progress_percentage = 0

# Main application UI
st.title("Kryon Nexus AI-Limitless Intelligence. Infinite Innovation")
st.write("Upload a PDF with requirements and get user stories, tech design, and test materials automatically generated.")

# Progress bar placeholder created at the start
if 'progress_bar' not in st.session_state:
    st.session_state.progress_bar = st.empty()
    
# Progress text placeholder
if 'progress_text' not in st.session_state:
    st.session_state.progress_text = st.empty()

# Initialize progress bar
if st.session_state.processing or st.session_state.progress_percentage > 0:
    st.session_state.progress_bar.progress(st.session_state.progress_percentage / 100)
    st.session_state.progress_text.text(f"Progress: {st.session_state.progress_percentage}%")

# Status indicator
status_placeholder = st.empty()
status_placeholder.info(f"Current status: {st.session_state.status}")

# Sidebar for uploading PDF
with st.sidebar:
    st.header("Upload Requirements Document")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None and st.button("Process Document"):
        if not openai.api_key:
            st.error("OpenAI API key is not found in environment variables. Please check your .env file.")
        else:
            with st.spinner("Extracting text from PDF..."):
                st.session_state.pdf_text = extract_text_from_pdf(uploaded_file)
                if st.session_state.pdf_text:
                    st.session_state.processing = True
                    st.session_state.results = {}
                    st.session_state.chat_history = []
                    st.session_state.feedback_history = {}
                    st.session_state.resource_constraints = None
                    st.session_state.status = "Processing started..."
                    st.session_state.progress_percentage = 0
                    status_placeholder.info(f"Current status: {st.session_state.status}")
                    st.rerun()
                else:
                    st.error("Failed to extract text from the PDF. Please try another file.")
    
    # Removed the "Download Results as PDF" button from here
    
    if st.session_state.processing or st.session_state.results:
        if st.button("End Session"):
            st.session_state.pdf_text = None
            st.session_state.processing = False
            st.session_state.results = {}
            st.session_state.chat_history = []
            st.session_state.feedback_history = {}
            st.session_state.resource_constraints = None
            st.session_state.status = "Ready"
            st.session_state.progress_percentage = 0
            status_placeholder.info(f"Current status: {st.session_state.status}")
            st.rerun()

# Process the document if needed
if st.session_state.processing:
    with st.spinner("Processing document... This may take a few minutes."):
        st.session_state.results = process_requirements(
            st.session_state.pdf_text,
            st.session_state.resource_constraints
        )
        st.session_state.processing = False
        st.rerun()

# Display results when available
if st.session_state.results:
    if "Error" in st.session_state.results:
        st.error(st.session_state.results["Error"])
    else:
        # Add a prominent download button at the top
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📥 Download Complete Report as PDF", use_container_width=True):
                pdf_data = generate_pdf(st.session_state.results)
                st.download_button(
                    label="Click to Download PDF",
                    data=pdf_data,
                    file_name="requirements_processing_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        st.header("Generated Content")
        
        # Create tabs for each section
        tabs = st.tabs([
            "Project Management Plan", 
            "User Stories",
            "UI/UX Design Specifications",
            "Development Plan",
            "Technology Design",
            "Test Scenarios",
            "Test Cases"
        ])
        
        tab_mapping = {
            "Project Management Plan": 0,
            "User Stories": 1,
            "UI/UX Design Specifications": 2,
            "Development Plan": 3,
            "Technology Design": 4,
            "Test Scenarios": 5,
            "Test Cases": 6
        }
        
        # Display content in tabs
        for section, content in st.session_state.results.items():
            if section in tab_mapping:
                tab_index = tab_mapping[section]
                with tabs[tab_index]:
                    st.markdown(content)
                    
                    # Initialize feedback history for this section if it doesn't exist
                    if section not in st.session_state.feedback_history:
                        st.session_state.feedback_history[section] = []
                    
                    # Add feedback functionality for each section
                    feedback = st.text_area(f"Provide feedback for {section}:", key=f"feedback_{section}")
                    
                    if st.button(f"Submit Feedback for {section}", key=f"submit_{section}"):
                        if feedback.strip():  # Only process if feedback is not empty
                            st.session_state.chat_history.append({"role": "user", "content": f"Feedback on {section}: {feedback}"})
                            
                            # Process feedback with an agent
                            with st.spinner(f"Processing feedback for {section}..."):
                                # Reset progress for feedback processing
                                st.session_state.progress_percentage = 0
                                st.session_state.progress_bar.progress(st.session_state.progress_percentage / 100)
                                st.session_state.progress_text.text(f"Progress: {st.session_state.progress_percentage}%")
                                
                                st.session_state.status = f"Processing feedback for {section}..."
                                status_placeholder.info(f"Current status: {st.session_state.status}")
                                
                                # Update progress to 30%
                                st.session_state.progress_percentage = 30
                                st.session_state.progress_bar.progress(st.session_state.progress_percentage / 100)
                                st.session_state.progress_text.text(f"Progress: {st.session_state.progress_percentage}%")
                                time.sleep(0.5)  # Short delay to show progress
                                
                                feedback_agent = Agent("Feedback Processor", "Feedback Specialist")
                                improved_content = feedback_agent.process(
                                    f"Revise the following {section.lower()} based on this feedback: {feedback}",
                                    st.session_state.results[section]
                                )
                                
                                # Update progress to 70%
                                st.session_state.progress_percentage = 70
                                st.session_state.progress_bar.progress(st.session_state.progress_percentage / 100)
                                st.session_state.progress_text.text(f"Progress: {st.session_state.progress_percentage}%")
                                time.sleep(0.5)  # Short delay to show progress
                                
                                # Create descriptive response about changes made
                                changes_description = feedback_agent.process(
                                    f"Describe in detail what changes you made to the {section.lower()} based on this feedback: {feedback}. Be specific about what was modified, added, or removed.",
                                    f"Original content: {st.session_state.results[section]}\n\nUpdated content: {improved_content}"
                                )
                                
                                # Update progress to 100%
                                st.session_state.progress_percentage = 100
                                st.session_state.progress_bar.progress(st.session_state.progress_percentage / 100)
                                st.session_state.progress_text.text(f"Progress: {st.session_state.progress_percentage}%")
                                
                                # Store the feedback and response in history
                                st.session_state.feedback_history[section].append({
                                    "feedback": feedback,
                                    "response": changes_description
                                })
                                
                                st.session_state.chat_history.append({"role": "ai_support", "content": changes_description})
                                st.session_state.results[section] = improved_content
                                st.session_state.status = "Feedback processed"
                                status_placeholder.info(f"Current status: {st.session_state.status}")
                                st.rerun()

        # Chat History section as an expandable area with italic font
        if "Error" not in st.session_state.results:
            with st.expander("Chat History", expanded=False):
                # Display chat history with italic font
                chat_container = st.container()
                with chat_container:
                    for message in st.session_state.chat_history:
                        if message["role"] == "user":
                            st.markdown(f"**You:** *{message['content']}*")
                        else:
                            # Changed "Assistant" to "AI Support" with italic font
                            st.markdown(f"**AI Support:** *{message['content']}*")

# Instructions when no PDF is uploaded
if not st.session_state.pdf_text and not st.session_state.processing and not st.session_state.results:
    st.info("Please upload a PDF document with requirements in the sidebar to begin processing.")
    
    with st.expander("How It Works", expanded=True):
        st.markdown("""
        **This application uses a multi-agent architecture to process requirements from PDF documents:**
        
        1. **Upload a PDF** containing your project requirements
        2. **Get automatically generated:**
           - User stories based on requirements
           - Project management plan
           - UI/UX design specifications
           - Development plan
           - Technology design with justification
           - Test scenarios
           - Test cases
        3. **Interact with the chatbot** to provide feedback
        4. **Download the final output** as a PDF
        
                """)