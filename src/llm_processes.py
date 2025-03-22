from typing import Any, Dict
import groq
import streamlit as st
import json
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AIProcessor:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        self.client = groq.Client(api_key=api_key)
    
    def analyze_process(self, requirements):
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
        return f"""Analyze the following system design requirements and provide a brief technical implementation plan. Format the response as a structured JSON document.

System Requirements:
{requirements['description']}

Focus on these areas:
1. Scalability
2. Security
3. Error Handling

Include a simple diagram using Mermaid.js with these components:
- Client
- API Gateway
- Database

Example diagram structure:
graph TD
    Client -->|Request| API[API Gateway]
    API -->|Query| DB[Database]
    API -->|Cache Check| Cache[Cache Layer]
    Cache -->|Cache Hit| Client
    Cache -->|Cache Miss| DB

Return the response in this JSON structure:
{{
    "overview": "Brief overview of the system",
    "components": [
        {{
            "name": "Component name",
            "purpose": "Purpose of the component",
            "steps": [
                {{
                    "step": "1",
                    "action": "Action performed",
                    "details": ["Detail 1", "Detail 2"]
                }}
            ]
        }}
    ],
    "diagram": "mermaid flowchart code"
}}
"""

    def _parse_response(self, response_text):
        """
        Parses the response and handles Mermaid.js diagrams.
        """
        try:
            # Print the raw response for debugging
            st.write("Raw response received:")
            st.code(response_text[:200] + "...", language="text")

            # Remove markdown code blocks
            cleaned_text = re.sub(r'```(?:json|mermaid)?\s*|\s*```', '', response_text)
            
            # Replace backtick-wrapped diagram with proper JSON string
            cleaned_text = re.sub(r':\s*`\s*(graph TD[\s\S]*?)`\s*([,}])', r': "\1"\2', cleaned_text)
            
            # Extract JSON content
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
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Clean up diagram if present
            if 'diagram' in data:
                diagram = data['diagram']
                diagram = diagram.strip('"`\'').replace('\\n', '\n')
                
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
                
                # Replace standalone '-->' with ' ' (space) while preserving '---->'
                diagram = re.sub(r'(?<!-)-(?!-)>', ' ', diagram)
                
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
    
    def _validate_keywords(self, diagram):
        """
        Validates the presence of key components in the diagram.
        """
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
        
        missing = {}
        for category, keywords in required_components.items():
            missing_keywords = [k for k in keywords if k.lower() not in diagram.lower()]
            if missing_keywords:
                missing[category] = missing_keywords
        
        if missing:
            st.warning("Missing Components:")
            for category, keywords in missing.items():
                st.write(f"- {category}: {', '.join(keywords)}")
        
        return missing