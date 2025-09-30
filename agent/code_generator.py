"""Code generator for Lightning Types"""
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

class CodeGenerator:
    def __init__(self, llm_client, rag_engine):
        self.llm = llm_client
        self.rag = rag_engine
        self.generated_files = {}
    
    def generate_all_code(self, spec, verbose=True):
        """Generate all code files for the Lightning Type"""
        if verbose:
            console.print("[bold blue]💻 Generating code files...[/bold blue]")
        
        # Generate schema.json
        self.generated_files['schema.json'] = self._generate_schema(spec, verbose)
        
        # Generate renderer.json
        self.generated_files['renderer.json'] = self._generate_renderer(spec, verbose)
        
        # Generate LWC files
        lwc_files = self._generate_lwc(spec, verbose)
        self.generated_files.update(lwc_files)
        
        if verbose:
            console.print(f"[green]✅ Generated {len(self.generated_files)} files[/green]")
        
        return self.generated_files
    
    def _generate_schema(self, spec, verbose):
        """Generate schema.json"""
        if verbose:
            console.print("[dim]  → Generating schema.json...[/dim]")
        
        schema = {
            "title": spec['title'],
            "description": spec['description'],
            "lightning:type": spec['object_api_name']
        }
        
        return json.dumps(schema, indent=2)
    
    def _generate_renderer(self, spec, verbose):
        """Generate renderer.json"""
        if verbose:
            console.print("[dim]  → Generating renderer.json...[/dim]")
        
        renderer = {
            "$": f"c/{spec['lwc_component_name']}"
        }
        
        return json.dumps(renderer, indent=2)
    
    def _generate_lwc(self, spec, verbose):
        """Generate LWC component files"""
        if verbose:
            console.print("[dim]  → Generating LWC component...[/dim]")
        
        # Get examples from documentation
        context = self.rag.get_relevant_context(
            f"Lightning Web Component example {spec['styling']} renderer",
            max_length=2000,
            verbose=False
        )
        
        files = {}
        
        # Generate JS
        files[f"{spec['lwc_component_name']}.js"] = self._generate_lwc_js(spec, context, verbose)
        
        # Generate HTML
        files[f"{spec['lwc_component_name']}.html"] = self._generate_lwc_html(spec, context, verbose)
        
        # Generate meta.xml
        files[f"{spec['lwc_component_name']}.js-meta.xml"] = self._generate_lwc_meta(spec, verbose)
        
        return files
    
    def _generate_lwc_js(self, spec, context, verbose):
        """Generate LWC JavaScript file"""
        prompt = f"""Generate a Lightning Web Component JavaScript file for this specification:

{json.dumps(spec, indent=2)}

Documentation context:
{context}

Requirements:
1. Import LightningElement and api from 'lwc'
2. Create @api properties for each field: {', '.join(spec['fields'])}
3. Add getter methods to format the data
4. Include any computed properties needed for {spec['features']}
5. Use SLDS styling approach

Return ONLY the JavaScript code, no explanations.
"""
        
        js_code = self.llm.generate(
            prompt,
            system="You are an expert Lightning Web Component developer. Provide clean, production-ready code.",
            verbose=verbose
        )
        
        return js_code if js_code else self._get_fallback_js(spec)
    
    def _generate_lwc_html(self, spec, context, verbose):
        """Generate LWC HTML template"""
        prompt = f"""Generate a Lightning Web Component HTML template for this specification:

{json.dumps(spec, indent=2)}

Documentation context:
{context}

Requirements:
1. Use <template> wrapper
2. Use lightning-card for main container
3. Display fields: {', '.join(spec['fields'])}
4. Implement {spec['styling']} layout style
5. Include features: {spec['features']}
6. Use SLDS utility classes

Return ONLY the HTML code, no explanations.
"""
        
        html_code = self.llm.generate(
            prompt,
            system="You are an expert Lightning Web Component developer. Provide clean, production-ready HTML.",
            verbose=verbose
        )
        
        return html_code if html_code else self._get_fallback_html(spec)
    
    def _generate_lwc_meta(self, spec, verbose):
        """Generate LWC meta.xml file"""
        meta = f"""<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__AgentforceOutput</target>
    </targets>
</LightningComponentBundle>
"""
        return meta
    
    def _get_fallback_js(self, spec):
        """Fallback JavaScript template"""
        fields_code = '\n    '.join([f"@api {field};" for field in spec['fields']])
        
        return f"""import {{ LightningElement, api }} from 'lwc';

export default class {spec['lwc_component_name'].capitalize()} extends LightningElement {{
    {fields_code}
    
    get displayTitle() {{
        return this.{spec['fields'][0]} || 'Untitled';
    }}
}}
"""
    
    def _get_fallback_html(self, spec):
        """Fallback HTML template"""
        fields_html = '\n'.join([
            f"""                <div class="slds-col slds-size_1-of-2">
                    <div class="slds-text-title_caps">{field.replace('__c', '').replace('_', ' ')}</div>
                    <div class="slds-text-body_regular">{{{field}}}</div>
                </div>"""
            for field in spec['fields']
        ])
        
        return f"""<template>
    <lightning-card title="{{displayTitle}}">
        <div class="slds-p-around_medium">
            <div class="slds-grid slds-wrap slds-gutters">
{fields_html}
            </div>
        </div>
    </lightning-card>
</template>
"""
