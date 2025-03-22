import streamlit as st
from src.llm_processes import AIProcessor
import streamlit.components.v1 as components
import re

def setup_page():
    st.set_page_config(
        page_title="System Design Analyzer",
        page_icon="🔄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    if 'current_analysis' not in st.session_state:
        st.session_state.current_analysis = None

def display_analysis(analysis_data):
    try:
        # Display the system overview
        st.markdown("## System Flow Analysis")
        st.markdown(analysis_data['overview'])
        
        # Display each component
        for component in analysis_data['components']:
            with st.expander(f"📍 {component['name']}", expanded=True):
                st.markdown(f"**Purpose**: {component['purpose']}")
        
        # Display the system flow diagram
        st.markdown("## System Flow Diagram")
        render_mermaid(analysis_data['diagram'])
        
    except Exception as e:
        st.error(f"Error displaying analysis: {str(e)}")

def render_mermaid(mermaid_code):
    """
    Renders a Mermaid diagram with proper formatting and escaping.
    """
    try:
        # Validate the Mermaid code
        if not mermaid_code.strip().startswith("graph"):
            raise ValueError("Invalid Mermaid syntax: Diagram must start with 'graph TD' or 'graph LR'.")

        # Replace standalone '-->' with ' ' (space) while preserving '---->'
        mermaid_code = re.sub(r'(?<!-)-(?!-)>', ' ', mermaid_code)

        # Sanitize the Mermaid code
        sanitized_code = (
            mermaid_code.replace("\\", "\\\\")  # Escape backslashes
            .replace('"', '\\"')               # Escape double quotes
            .replace("\n", "\\n")              # Escape newlines
        )

        # Show the Mermaid code for debugging
        st.markdown("### Mermaid Code")
        st.code(mermaid_code, language="mermaid")
        
        # Render the Mermaid diagram
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/mermaid@9.3.0/dist/mermaid.min.js"></script>
            <style>
                .mermaid {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    margin: 10px 0;
                    overflow: auto;
                }}
                .mermaid svg {{
                    max-width: 100%;
                    height: auto;
                }}
            </style>
        </head>
        <body>
            <div class="mermaid">
                {sanitized_code}
            </div>
            <script>
                mermaid.initialize({{
                    startOnLoad: true,
                    securityLevel: 'loose',
                    theme: 'neutral',
                    flowchart: {{
                        htmlLabels: true,
                        curve: 'basis',
                        useMaxWidth: true,
                        padding: 20,
                        rankSpacing: 50,
                        nodeSpacing: 50,
                        diagramPadding: 20
                    }}
                }});
            </script>
        </body>
        </html>
        """
        return components.html(html, height=800, scrolling=True)
        
    except ValueError as ve:
        st.error(f"Mermaid Syntax Error: {str(ve)}")
        st.markdown("### Mermaid Code (Raw)")
        st.code(mermaid_code, language="mermaid")
    except Exception as e:
        st.error(f"Error rendering diagram: {str(e)}")
        st.markdown("### Mermaid Code (Raw)")
        st.code(mermaid_code, language="mermaid")
                   
def main():
    setup_page()
    
    st.title("System Design Analyzer")
    
    with st.container():
        
        process_input = st.text_area(
            "Enter your system design requirements",
            height=200,
            placeholder="Example: Enter the system requirements here",
            help="Be specific about the technical flow and requirements"
        )
    
    if st.button("Generate Design", type="primary"):
        if not process_input.strip():
            st.warning("Please enter system requirements")
            return
            
        try:
            with st.spinner("Analyzing system requirements..."):
                # Initialize the AI processor
                llm_processes = AIProcessor()
                
                # Process the input
                requirements = {"description": process_input}
                analysis_result = llm_processes.analyze_process(requirements)
                
                # Store in session state
                st.session_state.current_analysis = analysis_result
                
                # Display the analysis
                display_analysis(analysis_result)
                
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    main()