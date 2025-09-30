"""Code generator for Lightning Types with field type awareness"""
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
        
        files = {}
        
        # Generate JS
        files[f"{spec['lwc_component_name']}.js"] = self._generate_lwc_js_enhanced(spec, verbose)
        
        # Generate HTML
        files[f"{spec['lwc_component_name']}.html"] = self._generate_lwc_html_enhanced(spec, verbose)
        
        # Generate meta.xml
        files[f"{spec['lwc_component_name']}.js-meta.xml"] = self._generate_lwc_meta(spec, verbose)
        
        return files
    
    def _generate_lwc_js_enhanced(self, spec, verbose):
        """Generate enhanced LWC JavaScript with proper type handling"""
        # Build @api properties
        api_properties = []
        getters = []
        
        for field in spec['fields']:
            field_name = field['name']
            field_type = field['type']
            
            # Add @api property
            if field_type == 'reference' and field.get('relationshipName'):
                # For relationships, we need both the ID and the relationship
                api_properties.append(f"    @api {field_name};")
                api_properties.append(f"    @api {field['relationshipName']}__r;")
                
                # Add getter for relationship name
                getters.append(f"""    get {field_name.lower()}Name() {{
        return this.{field['relationshipName']}__r?.Name || '';
    }}""")
            else:
                api_properties.append(f"    @api {field_name};")
            
            # Add formatting getters based on type
            if field_type == 'currency':
                getters.append(f"""    get formatted{field_name}() {{
        return this.{field_name} ? new Intl.NumberFormat('en-US', {{
            style: 'currency',
            currency: 'USD'
        }}).format(this.{field_name}) : '';
    }}""")
            
            elif field_type in ['date', 'datetime']:
                getters.append(f"""    get formatted{field_name}() {{
        if (!this.{field_name}) return '';
        const date = new Date(this.{field_name});
        return new Intl.DateTimeFormat('en-US', {{
            {'dateStyle: \'medium\', timeStyle: \'short\'' if field_type == 'datetime' else 'dateStyle: \'medium\''}
        }}).format(date);
    }}""")
        
        # Add display title getter
        title_field = next((f['name'] for f in spec['fields'] if 'name' in f['name'].lower() or f == spec['fields'][0]), spec['fields'][0]['name'])
        getters.append(f"""    get displayTitle() {{
        return this.{title_field} || 'Untitled';
    }}""")
        
        js_code = f"""import {{ LightningElement, api }} from 'lwc';

export default class {spec['lwc_component_name'].capitalize()} extends LightningElement {{
{chr(10).join(api_properties)}
    
{chr(10).join(getters)}
}}
"""
        
        return js_code
    
    def _generate_lwc_html_enhanced(self, spec, verbose):
        """Generate enhanced LWC HTML with proper field rendering"""
        field_handlers = spec.get('field_handlers', {})
        
        # Build field sections
        field_sections = []
        
        for field in spec['fields']:
            field_name = field['name']
            field_label = field['label']
            handler = field_handlers.get(field_name, {'component': 'lightning-formatted-text'})
            
            # Determine the display component
            if handler['component'] == 'lightning-formatted-name':
                field_display = f"{{{{ {handler['property']} }}}}"
            elif handler['component'] == 'lightning-badge':
                field_display = f'''<lightning-badge label="{{{{{field_name}}}}}" variant="inverse"></lightning-badge>'''
            elif handler['component'] == 'lightning-formatted-date-time':
                field_display = f'''<lightning-formatted-date-time value="{{{{{field_name}}}}}"></lightning-formatted-date-time>'''
            elif handler['component'] == 'lightning-formatted-number' and handler.get('format') == 'currency':
                field_display = f'''<lightning-formatted-number value="{{{{{field_name}}}}}" format-style="currency" currency-code="USD"></lightning-formatted-number>'''
            elif handler['component'] == 'lightning-formatted-email':
                field_display = f'''<lightning-formatted-email value="{{{{{field_name}}}}}"></lightning-formatted-email>'''
            elif handler['component'] == 'lightning-formatted-phone':
                field_display = f'''<lightning-formatted-phone value="{{{{{field_name}}}}}"></lightning-formatted-phone>'''
            elif handler['component'] == 'lightning-formatted-url':
                field_display = f'''<lightning-formatted-url value="{{{{{field_name}}}}}" target="_blank"></lightning-formatted-url>'''
            else:
                field_display = f"{{{{ {field_name} }}}}"
            
            field_section = f"""                <div class="slds-col slds-size_1-of-1 slds-medium-size_1-of-2 slds-p-vertical_x-small">
                    <div class="slds-text-title_caps">{field_label}</div>
                    <div class="slds-text-body_regular">{field_display}</div>
                </div>"""
            
            field_sections.append(field_section)
        
        html_template = f"""<template>
    <lightning-card title="{{{{displayTitle}}}}" icon-name="standard:record">
        <div slot="actions">
            <lightning-button-group>
                <lightning-button label="View Details" variant="brand"></lightning-button>
            </lightning-button-group>
        </div>
        
        <div class="slds-p-around_medium">
            <div class="slds-grid slds-wrap slds-gutters">
{chr(10).join(field_sections)}
            </div>
        </div>
        
        <div slot="footer">
            <div class="slds-text-align_center slds-text-body_small slds-text-color_weak">
                {spec['object_metadata']['label']}
            </div>
        </div>
    </lightning-card>
</template>
"""
        
        return html_template
    
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
