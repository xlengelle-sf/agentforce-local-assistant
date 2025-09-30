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
    
    def generate_spec(self, requirements, object_metadata, verbose=True):
        """
        Generate detailed specification from requirements
        NOW uses object metadata for accurate field types and relationships
        """
        if verbose:
            console.print("[bold blue]📋 Generating detailed specification...[/bold blue]")
        
        # Get relevant documentation for spec generation
        context = self.rag.get_relevant_context(
            f"Lightning Types structure schema renderer {requirements.get('visual_style', '')}",
            max_length=3000,
            verbose=verbose
        )
        
        # Build field details from metadata
        field_map = {f['name']: f for f in object_metadata['fields']}
        selected_field_details = []
        
        for field_name in requirements['selected_fields']:
            field = field_map.get(field_name)
            if field:
                field_detail = {
                    'name': field['name'],
                    'label': field['label'],
                    'type': field['type'],
                    'required': field['required'],
                    'length': field.get('length', 0)
                }
                
                # Add relationship info
                if field['type'] == 'reference':
                    field_detail['referenceTo'] = field.get('referenceTo', [])
                    field_detail['relationshipName'] = field.get('relationshipName', '')
                
                # Add picklist values
                if field['type'] in ['picklist', 'multipicklist']:
                    field_detail['picklistValues'] = field.get('picklistValues', [])
                
                selected_field_details.append(field_detail)
        
        # Generate specification using LLM
        prompt = f"""Create a detailed technical specification for a Lightning Type:

Object: {object_metadata['label']} ({object_metadata['name']})
Purpose: {requirements['display_purpose']}
Visual Style: {requirements['visual_style']}
Features: {', '.join(requirements['special_features'])}

Selected Fields (with actual metadata):
{json.dumps(selected_field_details, indent=2)}

Documentation context:
{context}

Provide a JSON specification with:
1. type_name: camelCase name for the Lightning Type
2. object_api_name: Salesforce object API name
3. title: Display title
4. description: Brief description
5. fields: Array of field objects with name, type, label, and display properties
6. lwc_component_name: Name for the LWC renderer component
7. features: List of features to implement
8. styling: Visual styling approach
9. field_handlers: Object mapping field types to display strategies

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
                    # Fallback: create spec from metadata
                    self.spec = self._create_spec_from_metadata(
                        requirements, 
                        object_metadata, 
                        selected_field_details
                    )
            except json.JSONDecodeError:
                if verbose:
                    console.print("[yellow]⚠️  Could not parse LLM response, creating spec from metadata[/yellow]")
                self.spec = self._create_spec_from_metadata(
                    requirements, 
                    object_metadata, 
                    selected_field_details
                )
        else:
            self.spec = self._create_spec_from_metadata(
                requirements, 
                object_metadata, 
                selected_field_details
            )
        
        # Ensure spec has all required metadata
        self.spec['object_metadata'] = {
            'name': object_metadata['name'],
            'label': object_metadata['label'],
            'custom': object_metadata['custom']
        }
        
        if verbose:
            console.print(Panel(
                json.dumps(self.spec, indent=2),
                title="📋 Generated Specification",
                expand=False
            ))
        
        return self.spec
    
    def _create_spec_from_metadata(self, requirements, object_metadata, selected_field_details):
        """Create specification directly from object metadata (fallback)"""
        object_name = object_metadata['name']
        type_name = ''.join(
            word.capitalize() 
            for word in object_name.replace('__c', '').replace('_', ' ').split()
        )
        
        spec = {
            "type_name": type_name.lower(),
            "object_api_name": object_name,
            "title": requirements['display_purpose'],
            "description": f"Custom Lightning Type for {object_metadata['label']}",
            "fields": selected_field_details,
            "lwc_component_name": f"{type_name.lower()}Detail",
            "features": requirements['special_features'],
            "styling": requirements['visual_style'],
            "field_handlers": self._generate_field_handlers(selected_field_details)
        }
        
        return spec
    
    def _generate_field_handlers(self, field_details):
        """Generate appropriate handlers for different field types"""
        handlers = {}
        
        for field in field_details:
            field_type = field['type']
            
            if field_type == 'reference':
                handlers[field['name']] = {
                    'component': 'lightning-formatted-name',
                    'property': f"{field.get('relationshipName', field['name'])}.Name"
                }
            elif field_type == 'currency':
                handlers[field['name']] = {
                    'component': 'lightning-formatted-number',
                    'format': 'currency'
                }
            elif field_type in ['date', 'datetime']:
                handlers[field['name']] = {
                    'component': 'lightning-formatted-date-time',
                    'type': field_type
                }
            elif field_type in ['picklist', 'multipicklist']:
                handlers[field['name']] = {
                    'component': 'lightning-badge',
                    'variant': 'inverse'
                }
            elif field_type == 'email':
                handlers[field['name']] = {
                    'component': 'lightning-formatted-email'
                }
            elif field_type == 'phone':
                handlers[field['name']] = {
                    'component': 'lightning-formatted-phone'
                }
            elif field_type == 'url':
                handlers[field['name']] = {
                    'component': 'lightning-formatted-url'
                }
            else:
                handlers[field['name']] = {
                    'component': 'lightning-formatted-text'
                }
        
        return handlers
    
    def save_spec(self, output_path="spec.json"):
        """Save specification to file"""
        with open(output_path, 'w') as f:
            json.dump(self.spec, f, indent=2)
        
        console.print(f"[green]✅ Specification saved to {output_path}[/green]")
