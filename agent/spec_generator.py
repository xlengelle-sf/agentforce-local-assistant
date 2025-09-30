"""Specification generator for Lightning Types"""
import json
from rich.console import Console
from rich.panel import Panel

console = Console()

class SpecGenerator:
    def __init__(self, llm_client, rag_engine):
        self.llm = llm_client
        self.rag = rag_engine
        self.spec = {}
    
    def generate_spec(self, requirements, verbose=True):
        """Generate detailed specification from requirements"""
        if verbose:
            console.print("[bold blue]📑 Generating detailed specification...[/bold blue]")
        
        # Get relevant documentation for spec generation
        context = self.rag.get_relevant_context(
            f"Lightning Types structure schema renderer {requirements.get('visual_style', '')}",
            max_length=3000,
            verbose=verbose
        )
        
        # Generate specification using LLM
        prompt = f"""Create a detailed technical specification for a Lightning Type based on these requirements:

Object: {requirements['object_name']}
Purpose: {requirements['display_purpose']}
Key Fields: {requirements['key_fields']}
Visual Style: {requirements['visual_style']}
Special Features: {requirements['special_features']}

Documentation context:
{context}

Provide a JSON specification with:
1. type_name: camelCase name for the Lightning Type
2. object_api_name: Salesforce object API name
3. title: Display title
4. description: Brief description
5. fields: List of field API names to display
6. lwc_component_name: Name for the LWC renderer component
7. features: List of features to implement
8. styling: Visual styling approach

Return ONLY the JSON, no explanations.
"""
        
        response = self.llm.generate(
            prompt,
            system="You are an expert Salesforce architect. Provide clean, valid JSON only.",
            verbose=verbose
        )
        
        if response:
            try:
                # Extract JSON from response
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    self.spec = json.loads(json_str)
                else:
                    # Fallback: create basic spec
                    self.spec = self._create_basic_spec(requirements)
            except json.JSONDecodeError:
                if verbose:
                    console.print("[yellow]⚠️  Could not parse LLM response, creating basic spec[/yellow]")
                self.spec = self._create_basic_spec(requirements)
        else:
            self.spec = self._create_basic_spec(requirements)
        
        if verbose:
            console.print(Panel(
                json.dumps(self.spec, indent=2),
                title="📑 Generated Specification",
                expand=False
            ))
        
        return self.spec
    
    def _create_basic_spec(self, requirements):
        """Create a basic specification as fallback"""
        object_name = requirements['object_name']
        type_name = ''.join(word.capitalize() for word in object_name.replace('__c', '').split('_'))
        
        fields = [f.strip() for f in requirements['key_fields'].split(',')]
        
        return {
            "type_name": type_name.lower(),
            "object_api_name": object_name,
            "title": requirements['display_purpose'],
            "description": f"Custom Lightning Type for {object_name}",
            "fields": fields,
            "lwc_component_name": f"{type_name.lower()}Detail",
            "features": requirements['special_features'].split(','),
            "styling": requirements['visual_style']
        }
    
    def save_spec(self, output_path="spec.json"):
        """Save specification to file"""
        with open(output_path, 'w') as f:
            json.dump(self.spec, f, indent=2)
        
        console.print(f"[green]✅ Specification saved to {output_path}[/green]")
