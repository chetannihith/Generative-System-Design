from typing import Any, Dict
import groq
import streamlit as st
import json
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIProcessor:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        self.client = groq.Client(api_key=api_key)
    
    def analyze_process(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Processes system design requirements using Groq AI and returns structured JSON output."""
        prompt = self._generate_prompt(requirements)
        
        try:
            completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                max_tokens=4000,
            )
            
            response_text = completion.choices[0].message.content
            return self._parse_response(response_text)
            
        except Exception as e:
            raise Exception(f"Analysis error: {str(e)}")
    
    def _generate_prompt(self, requirements: Dict[str, Any]) -> str:
        """Generates a structured prompt for Groq AI to follow a strict JSON response format."""
        return f"""
Analyze the following system design requirements and generate a structured technical implementation plan. 

### **System Requirements:**
{requirements['description']}

    System Requirements:
    {requirements['description']}

    Create a comprehensive system design with these key focus areas:
    1. Scalability & Performance
    2. Reliability & Fault Tolerance
    3. Security & Data Protection
    4. Monitoring & 
    
Diagram Rules (Mermaid.js)

    Start with graph TD (Top-down)

    Nodes: [Label] for boxes, ((Label)) for circles, [(Label)] for databases/storage

    Arrows: --> for connections, -->|text| for labeled connections

    Ensure no extra > after labeled connections (use -->|text| B, not -->|text|> B)

    Use line breaks \n for readability

    Format the diagram properly for rendering, keeping structure clean and consistent

    DO not solely add this > symbol in single after the connection like use -->|text| B, not -->|text|> B 

    Changed connections like -->|User Interaction|> to -->|User Interaction|

    Do not imagine or hallucinate the diagram, use the provided information only
**Expected JSON Format:**
```json
{{
        "overview": "Comprehensive overview of the system architecture and design principles",
        "components": [
            {{
                "name": "Component name (Start with user interaction, follow the data flow through the system, and end with user feedback where applicable)",
                "purpose": "Detailed purpose and responsibility of this component",
                "steps": [
                    {{
                        "step": "1",
                        "action": "Specific action or operation",
                        "details": [
                            "Implementation detail with specific technology/algorithm (e.g., 'JWT for authentication using RS256 algorithm')",
                            "Configuration or setup detail with example (e.g., 'Redis cache with 1 hour TTL, LRU eviction')"
                        ]
                    }}
                ],
                "technologies": [
                    {{
                        "name": "Technology name (specific version if relevant)",
                        "purpose": "Specific use case and benefits",
                        "configuration": "Detailed configuration with examples"
                    }}
                ],
                "data_flow": {{
                    "input": "Incoming data format and validation requirements",
                    "process": "Data transformation and business logic",
                    "output": "Response format and error handling"
                }}
            }}
        ],
        "flow_steps": [
            {{
                "step": "1",
                "title": "Clear step title",
                "description": "Detailed process description",
                "technical_details": [
                    "Specific implementation detail with technology choice",
                    "Configuration or setup requirement with example"
                ]
            }}
        ],
        "diagram": "mermaid flowchart code"
    }}

example code graph TD:
graph TD
%% Style definitions
classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;
classDef subgraphStyle fill:#e8e8e8,stroke:#666,stroke-width:2px;

A[User Interaction] -->|User Input| B[Data Processing]
and not like this:
A[User Interaction] -->|User Input|> B[Data Processing]
"""


    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parses AI response, extracts JSON, and ensures valid Mermaid.js formatting."""
        try:
            # Debugging: Show raw AI response
            st.write("Raw response received:")
            st.code(response_text[:200] + "...", language="text")
            
            # Clean markdown and extract JSON content
            cleaned_text = re.sub(r'(?:json|mermaid)?\s*|\s*', '', response_text)
            
            # Handle Mermaid.js inside JSON field, ensuring no extra '>' in labeled connections
            cleaned_text = re.sub(r':\s`\s(graph TD[\s\S]*?)`\s([,}])', r': "\1"\2', cleaned_text)
            
            # Extract valid JSON
            start_idx, end_idx = cleaned_text.find("{"), cleaned_text.rfind("}")
            if start_idx == -1 or end_idx == -1:
                raise ValueError("No valid JSON structure found")
            
            json_str = cleaned_text[start_idx:end_idx + 1]
            json_str = re.sub(r'\s+', ' ', json_str).replace('\\"', '"').replace('""', '"')
            
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                st.error(f"JSON Parse Error at position {e.pos}:")
                st.code(f"...{json_str[max(0, e.pos - 100):min(len(json_str), e.pos + 100)]}...", language="json")
                data = json.loads(re.sub(r':\s"([^"?graph TD[^"]*?)]"', r': "\1"', json_str))
            
            # Clean up and validate the Mermaid.js diagram
            if 'diagram' in data:
                data['diagram'] = self._format_mermaid(data['diagram'])
                st.write("Diagram code:")
                st.code(data['diagram'], language="mermaid")
            
            return data
        
        except json.JSONDecodeError as e:
            st.error(f"JSON Parse Error: {str(e)}")
            st.code(json_str, language="json")
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.code(response_text[:500] + "...", language="text")
            raise ValueError(f"Error processing response: {str(e)}")

    def _format_mermaid(diagram: str) -> str:
        """Ensures proper formatting of Mermaid.js diagrams."""
        diagram = diagram.strip('"`\'').replace('\\n', '\n')
        
        # Ensure it starts with "graph TD"
        if not diagram.strip().startswith('graph'):
            diagram = 'graph TD\n' + diagram
        
        # Ensure proper formatting for labeled connections (removes extra '>' after labels)
        diagram = re.sub(r'--\|([^|]+)\|>', r'--|\1|', diagram)
        
        # Add style definitions
        style_defs = '''    %% Style definitions
        classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;
        classDef subgraphStyle fill:#e8e8e8,stroke:#666,stroke-width:2px;
        '''
        if '%% Style definitions' not in diagram:
            diagram = diagram.replace('graph TD', f'graph TD\n{style_defs}')
        
        return '\n'.join(line.strip() for line in diagram.split('\n'))

    def _parse_response(self, response_text):
        """
        More robust response parser that handles different diagram formats
        """
        try:
            # First, let's print the raw response for debugging
            st.write("Raw response received:")
            st.code(response_text[:200] + "...", language="text")

            # Remove markdown code blocks
            cleaned_text = re.sub(r'```(?:json|mermaid)?\s*|\s*```', '', response_text)
            
            # Replace backtick-wrapped diagram with proper JSON string
            cleaned_text = re.sub(r':\s*`\s*(graph TD[\s\S]*?)`\s*([,}])', r': "\1"\2', cleaned_text)
            
            # Find the JSON content between first { and last }
            start_idx = cleaned_text.find("{")
            end_idx = cleaned_text.rfind("}")
            
            if start_idx == -1 or end_idx == -1:
                raise ValueError("No valid JSON structure found")
            
            json_str = cleaned_text[start_idx:end_idx + 1]
            
            # Normalize whitespace
            json_str = re.sub(r'\s+', ' ', json_str)
            
            # Handle escaped quotes
            json_str = json_str.replace('\\"', '"')
            json_str = json_str.replace('""', '"')
            
            try:
                # Try to parse JSON
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                # If parsing fails, show context around error
                st.error(f"JSON Parse Error at position {e.pos}:")
                context_start = max(0, e.pos - 100)
                context_end = min(len(json_str), e.pos + 100)
                st.code(f"...{json_str[context_start:context_end]}...", language="json")
                
                # Additional cleanup for another attempt
                json_str = re.sub(r':\s*"([^"]*?graph TD[^"]*?)"', r': "\1"', json_str)
                json_str = json_str.replace('\n', ' ')
                data = json.loads(json_str)  # Try one more time
                
            # Clean up diagram if present
            if 'diagram' in data:
                diagram = data['diagram']
                
                # Remove any surrounding quotes or backticks
                diagram = diagram.strip('"`\'')
                
                # Ensure proper line breaks
                diagram = diagram.replace('\\n', '\n')
                
                # Ensure it starts with graph TD
                if not diagram.strip().startswith('graph'):
                    diagram = 'graph TD\n' + diagram
                
                # Add style definitions if not present
                style_defs = '''    %% Style definitions
        classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;
        classDef subgraphStyle fill:#e8e8e8,stroke:#666,stroke-width:2px;
    '''
                if '%% Style definitions' not in diagram:
                    diagram = diagram.replace('graph TD', f'graph TD\n{style_defs}')
                
                # Clean up formatting
                diagram = '\n'.join(line.strip() for line in diagram.split('\n'))
                
                # Store cleaned diagram
                data['diagram'] = diagram
                
                # Display the diagram code
                st.write("Diagram code:")
                st.code(diagram, language="mermaid")
            
            return data
            
        except json.JSONDecodeError as e:
            st.error(f"JSON Parse Error: {str(e)}")
            st.code(json_str, language="json")
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.write("Response text that caused the error:")
            st.code(response_text[:500] + "...", language="text")
            raise ValueError(f"Error processing response: {str(e)}")


    def _validate_keywords(self, diagram: str) -> Dict[str, list]:
        """Checks if the Mermaid diagram contains all necessary components."""
        required_components = {
            "Frontend": ["Client", "UI", "Frontend", "Web", "Mobile"],
            "Network": ["CDN", "Load Balancer", "API Gateway", "WAF"],
            "Security": ["Auth", "OAuth", "JWT", "WAF", "DDoS"],
            "Application": ["Service", "Microservice", "API", "Business Logic"],
            "Data": ["Database", "Cache", "Storage", "Redis"],
            "Messaging": ["Queue", "Message", "Event", "Stream"],
            "Processing": ["Worker", "Processor", "Handler", "Service"],
            "Monitoring": ["Monitor", "Log", "Trace", "Alert"],
            "DevOps": ["Deploy", "CI/CD", "Container", "Pipeline"]
        }
        
        missing = {category: [k for k in keywords if k.lower() not in diagram.lower()]
                for category, keywords in required_components.items() if any(k.lower() not in diagram.lower() for k in keywords)}
        
        if missing:
            st.warning("Missing Components:")
            for category, keywords in missing.items():
                st.write(f"- {category}: {', '.join(keywords)}")

        return missing
