# Multi-Agent App Development System

![Project Banner](https://via.placeholder.com/1200x300?text=Multi-Agent+App+Development+System)

## Overview

The Multi-Agent App Development System is an innovative tool that automates the software development lifecycle using AI agents. This system orchestrates a team of specialized AI agents, each performing a distinct role in the software development process to transform PDF requirements into a full application prototype.

## Features

- **PDF Requirement Processing**: Upload PDF documents containing project requirements for automatic extraction and analysis
- **Multi-Agent Collaboration**: Simulates a full development team with specialized AI roles
- **End-to-End Development Pipeline**: Automatically progresses through requirements analysis, design, development, testing, and presentation
- **Code Generation**: Produces working code modules based on project requirements
- **Streamlit Web Interface**: Provides an intuitive UI to monitor and interact with the development process
- **Downloadable Artifacts**: Export generated code, design documents, and other project assets

## Agent Roles

The system employs five specialized AI agents:

| Agent | Role Description |
|-------|-----------------|
| Project Manager | Analyzes requirements and coordinates tasks |
| Designer | Creates UI/UX designs and wireframes |
| Developer | Writes code and implements features |
| Tester | Tests functionality and identifies bugs |
| Presenter | Prepares presentations of the final product |

## Prerequisites

- Python 3.8+
- OpenAI API key (for GPT-4o-mini model access)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/vivkarthy/e2eDevelopment.git
   cd e2eDevelopment
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

1. Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```

2. Open your browser and navigate to the displayed URL (typically http://localhost:8501)

3. Upload a PDF file containing your project requirements

4. Click "Process Requirements" to start the development process

5. Observe as each agent works through their role in the development cycle

6. Download generated code and artifacts when the process completes

## Application Interface

The application features a tabbed interface:

- **Conversation**: View the dialogue between agents as they work through the development process
- **Artifacts**: Explore design specifications, test plans, and presentation materials
- **Code**: Review and download generated code modules
- **Final Product**: See a summary of the completed application (available after all stages are complete)

## Project Workflow

The system follows a sequential development workflow:

1. **Requirements Analysis**: The Project Manager analyzes the PDF requirements and creates a structured project plan
2. **Design**: The Designer creates UI/UX specifications based on requirements
3. **Development**: The Developer writes code to implement the designed features
4. **Testing**: The Tester creates a comprehensive test plan and identifies potential issues
5. **Presentation**: The Presenter creates a final presentation of the completed product

## Technical Architecture

This application is built using:

- **Streamlit**: For the web interface
- **LangChain**: For agent orchestration and interaction
- **LangGraph**: For managing the state and workflow between agents
- **OpenAI API**: For the underlying AI model (GPT-4o-mini)
- **PyPDF2**: For PDF text extraction

## Limitations

- Generated code requires additional implementation to be fully functional
- The system is dependent on the quality of the provided requirements
- The AI models have limitations in understanding complex technical specifications

## Future Enhancements

- Integration with version control systems
- Real-time collaboration features
- Support for additional file formats beyond PDF
- Deployment automation for generated applications
- Integration with testing frameworks for automated testing

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Developed by Karthik Vivekanandhan
- Powered by OpenAI's language models
- Built with Streamlit, LangChain, and LangGraph

## Contact

For questions or feedback, please open an issue on the [GitHub repository](https://github.com/vivkarthy/e2eDevelopment).
