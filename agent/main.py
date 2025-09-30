#!/usr/bin/env python3
"""
AgentForce Local Assistant
Main entry point with interactive workflow
Supports both conversational mode and object discovery mode
"""
import sys
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import print as rprint

# Import agent modules
from doc_fetcher import DocFetcher
from rag_engine import RAGEngine
from llm_client import LLMClient
from business_analyst import BusinessAnalyst
from spec_generator import SpecGenerator
from code_generator import CodeGenerator
from sf_deployer import SalesforceDeployer
from object_discoverer import ObjectDiscoverer

console = Console()

def print_banner():
    """Print welcome banner"""
    banner = """
[bold cyan]╔══════════════════════════════════════════════════╗
║                                                  ║
║   🤖  AgentForce Local Assistant                ║
║                                                  ║
║   Lightning Types Generator                      ║
║   100% Local • Powered by Llama 3.2             ║
║                                                  ║
╚══════════════════════════════════════════════════╝[/bold cyan]
    """
    console.print(banner)

def initialize_knowledge_base(verbose=True):
    """Initialize or update the knowledge base"""
    docs_file = Path("knowledge_base/processed/all_docs.json")
    
    if not docs_file.exists():
        console.print("[yellow]📚 Knowledge base not found. Initializing...[/yellow]")
        fetcher = DocFetcher()
        fetcher.fetch_all_docs(verbose=verbose)
    else:
        if verbose:
            console.print("[green]✅ Knowledge base loaded[/green]")
        
        # Ask if user wants to check for updates
        if Confirm.ask("Check for documentation updates?", default=False):
            fetcher = DocFetcher()
            if fetcher.check_updates(verbose=verbose):
                if Confirm.ask("Updates found. Download now?", default=True):
                    fetcher.fetch_all_docs(verbose=verbose)

def select_working_mode():
    """Let user choose between conversational and discovery mode"""
    console.print("\n[bold yellow]🎯 Select Working Mode[/bold yellow]\n")
    
    mode_table = Table(show_header=False, box=None, padding=(0, 2))
    mode_table.add_column("Option", style="cyan bold", width=10)
    mode_table.add_column("Description", style="white")
    
    mode_table.add_row(
        "1", 
        "[bold]Conversational Mode[/bold]\n"
        "Chat with the AI to describe what you want to build.\n"
        "Best for: Complex requirements, custom logic"
    )
    mode_table.add_row(
        "2", 
        "[bold]Object Discovery Mode[/bold]\n"
        "Select a Salesforce object and fields interactively.\n"
        "Best for: Quick setup, standard objects"
    )
    
    console.print(mode_table)
    console.print()
    
    choice = Prompt.ask(
        "[bold]Choose mode[/bold]",
        choices=["1", "2"],
        default="2"
    )
    
    return "conversational" if choice == "1" else "discovery"

def conversational_workflow(config, verbose=True):
    """Original conversational workflow"""
    console.print("\n[bold cyan]💬 Conversational Mode[/bold cyan]\n")
    console.print("[dim]The AI will ask you questions to understand your requirements...[/dim]\n")
    
    # Initialize components
    rag = RAGEngine()
    llm = LLMClient()
    ba = BusinessAnalyst(llm, rag)
    spec_gen = SpecGenerator(llm, rag)
    
    # Gather requirements through conversation
    console.print("[bold yellow]Step 1/4: Requirements Gathering[/bold yellow]\n")
    requirements = ba.gather_requirements(verbose=verbose)
    
    # Generate specification
    console.print("\n[bold yellow]Step 2/4: Technical Specification[/bold yellow]\n")
    spec = spec_gen.generate_spec(requirements, verbose=verbose)
    
    return spec

def discovery_workflow(config, deployer, verbose=True):
    """New object discovery workflow"""
    console.print("\n[bold cyan]🔍 Object Discovery Mode[/bold cyan]\n")
    
    # Step 1: Select target org
    console.print("[bold yellow]Step 1/6: Select Salesforce Org[/bold yellow]\n")
    orgs = deployer.list_orgs(verbose=verbose)
    
    if not orgs:
        console.print("[red]❌ No Salesforce orgs found.[/red]")
        console.print("Please authenticate an org first: [cyan]sf org login web[/cyan]")
        return None
    
    # Let user choose org
    org_choices = [org.get('alias', org.get('username', 'Unknown')) for org in orgs]
    console.print("\n[bold]Available orgs:[/bold]")
    for i, choice in enumerate(org_choices, 1):
        console.print(f"  {i}. {choice}")
    
    choice_idx = int(Prompt.ask("Enter number", choices=[str(i) for i in range(1, len(org_choices) + 1)])) - 1
    selected_org = org_choices[choice_idx]
    
    console.print(f"\n[green]✅ Selected org: {selected_org}[/green]\n")
    
    # Step 2: Initialize object discoverer
    console.print("[bold yellow]Step 2/6: Object Discovery[/bold yellow]\n")
    discoverer = ObjectDiscoverer()
    
    # Step 3: Select object interactively
    console.print("[dim]Loading Salesforce objects...[/dim]\n")
    selected_object = discoverer.select_object_interactive(selected_org, verbose=verbose)
    
    if not selected_object:
        console.print("[yellow]Object selection cancelled[/yellow]")
        return None
    
    console.print(f"\n[green]✅ Selected object: {selected_object}[/green]\n")
    
    # Step 4: Discover object metadata
    console.print("[bold yellow]Step 3/6: Fetching Object Metadata[/bold yellow]\n")
    metadata = discoverer.discover_object(selected_object, selected_org, use_cache=True, verbose=verbose)
    
    if not metadata:
        console.print("[red]❌ Failed to fetch object metadata[/red]")
        return None
    
    # Display object summary
    discoverer.display_object_summary(metadata, verbose=verbose)
    
    if not Confirm.ask("\n[bold]Continue with this object?[/bold]", default=True):
        return None
    
    # Step 5: Select fields interactively
    console.print("\n[bold yellow]Step 4/6: Field Selection[/bold yellow]\n")
    
    # Initialize LLM for AI recommendations
    llm = LLMClient()
    selected_fields = discoverer.select_fields_interactive(metadata, llm_client=llm, verbose=verbose)
    
    if not selected_fields:
        console.print("[yellow]Field selection cancelled[/yellow]")
        return None
    
    console.print(f"\n[green]✅ Selected {len(selected_fields)} fields:[/green]")
    for field_name in selected_fields:
        field = next((f for f in metadata['fields'] if f['name'] == field_name), None)
        if field:
            console.print(f"  • {field['label']} ({field['name']}) - {field['type']}")
    
    # Step 6: Generate specification from discovery
    console.print("\n[bold yellow]Step 5/6: Generating Specification[/bold yellow]\n")
    spec = generate_spec_from_discovery(metadata, selected_fields, verbose=verbose)
    
    # Step 7: Review and confirm
    console.print("\n[bold yellow]Step 6/6: Review Specification[/bold yellow]\n")
    display_spec_summary(spec)
    
    if not Confirm.ask("\n[bold]Proceed with this specification?[/bold]", default=True):
        return None
    
    return spec, selected_org

def generate_spec_from_discovery(metadata, selected_fields, verbose=True):
    """Generate specification from discovered object and selected fields"""
    # Create spec based on object metadata
    spec = {
        'type_name': f"{metadata['name']}Display",
        'object_api_name': metadata['name'],
        'object_label': metadata['label'],
        'object_metadata': metadata,
        'fields': [],
        'lwc_component_name': f"{metadata['name'].lower()}DisplayCard"
    }
    
    # Add selected fields with their metadata
    for field_name in selected_fields:
        field = next((f for f in metadata['fields'] if f['name'] == field_name), None)
        if field:
            # Determine appropriate handler/formatter
            handler = _get_field_handler(field)
            
            spec['fields'].append({
                'api_name': field['name'],
                'label': field['label'],
                'type': field['type'],
                'handler': handler,
                'required': field['required'],
                'metadata': field
            })
    
    if verbose:
        console.print(f"[green]✅ Specification generated with {len(spec['fields'])} fields[/green]")
    
    return spec

def _get_field_handler(field):
    """Determine the appropriate Lightning component handler for a field"""
    field_type = field['type'].lower()
    
    # Map Salesforce field types to Lightning components
    type_handlers = {
        'string': {'component': 'lightning-formatted-text'},
        'textarea': {'component': 'lightning-formatted-text'},
        'email': {'component': 'lightning-formatted-email'},
        'phone': {'component': 'lightning-formatted-phone'},
        'url': {'component': 'lightning-formatted-url'},
        'currency': {'component': 'lightning-formatted-number', 'format': 'currency'},
        'percent': {'component': 'lightning-formatted-number', 'format': 'percent'},
        'double': {'component': 'lightning-formatted-number'},
        'int': {'component': 'lightning-formatted-number'},
        'date': {'component': 'lightning-formatted-date-time', 'format': 'date'},
        'datetime': {'component': 'lightning-formatted-date-time'},
        'boolean': {'component': 'lightning-formatted-text'},
        'picklist': {'component': 'lightning-formatted-text'},
        'multipicklist': {'component': 'lightning-formatted-text'},
        'reference': {'component': 'lightning-formatted-text'},
        'address': {'component': 'lightning-formatted-address'}
    }
    
    return type_handlers.get(field_type, {'component': 'lightning-formatted-text'})

def display_spec_summary(spec):
    """Display a summary of the generated specification"""
    panel_content = f"""[bold cyan]{spec['object_label']}[/bold cyan] ({spec['object_api_name']})

[bold]Lightning Type Name:[/bold] {spec['type_name']}
[bold]LWC Component:[/bold] {spec['lwc_component_name']}
[bold]Fields:[/bold] {len(spec['fields'])}"""
    
    console.print(Panel(panel_content, title="📋 Specification Summary", expand=False))
    
    # Display fields table
    table = Table(title="Selected Fields", show_header=True, header_style="bold magenta")
    table.add_column("Field Label", style="cyan", width=25)
    table.add_column("API Name", style="yellow", width=25)
    table.add_column("Type", style="green", width=15)
    table.add_column("Handler", style="blue", width=30)
    
    for field in spec['fields']:
        handler_name = field['handler'].get('component', 'N/A')
        table.add_row(
            field['label'],
            field['api_name'],
            field['type'],
            handler_name
        )
    
    console.print(table)

def main():
    """Main workflow"""
    print_banner()
    
    # Load configuration
    try:
        with open("config/settings.json", 'r') as f:
            config = json.load(f)
        verbose = config.get('verbose', True)
    except FileNotFoundError:
        console.print("[red]❌ Configuration file not found. Please run setup.sh first.[/red]")
        sys.exit(1)
    
    console.print("\n[bold]Initializing agent...[/bold]\n")
    
    # Step 1: Initialize knowledge base
    try:
        initialize_knowledge_base(verbose=verbose)
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize knowledge base: {e}[/red]")
        sys.exit(1)
    
    # Step 2: Check Salesforce CLI
    console.print("\n[bold]Checking environment...[/bold]")
    deployer = SalesforceDeployer()
    if not deployer.check_sf_cli(verbose=verbose):
        console.print("[red]❌ Salesforce CLI is required but not found.[/red]")
        console.print("Please install it from: https://developer.salesforce.com/tools/sfdxcli")
        sys.exit(1)
    
    console.print("\n[green]✅ All systems ready![/green]\n")
    console.print("─" * 60)
    
    try:
        # Step 3: Select working mode
        mode = select_working_mode()
        
        spec = None
        target_org = None
        
        if mode == "conversational":
            # Conversational workflow
            spec = conversational_workflow(config, verbose=verbose)
        else:
            # Discovery workflow
            result = discovery_workflow(config, deployer, verbose=verbose)
            if result:
                spec, target_org = result
        
        if not spec:
            console.print("[yellow]⚠️  Workflow cancelled or failed[/yellow]")
            sys.exit(0)
        
        # Step 4: Check for Documentation Updates (if conversational mode)
        if mode == "conversational":
            console.print("\n[bold yellow]Documentation Verification[/bold yellow]\n")
            fetcher = DocFetcher()
            updates_found = fetcher.check_updates(verbose=verbose)
            
            if updates_found:
                console.print("[yellow]⚠️  Documentation updates detected![/yellow]")
                if Confirm.ask("Re-download documentation for latest examples?", default=True):
                    fetcher.fetch_all_docs(verbose=verbose)
        
        # Step 5: Generate Code
        console.print("\n[bold yellow]Code Generation[/bold yellow]\n")
        rag = RAGEngine()
        llm = LLMClient()
        code_gen = CodeGenerator(llm, rag)
        generated_files = code_gen.generate_all_code(spec, verbose=verbose)
        
        # Show generated code summary
        if verbose:
            console.print("\n[bold]Generated Files:[/bold]")
            for filename in generated_files.keys():
                console.print(f"  ✓ {filename}")
        
        # Confirmation before deployment
        if not Confirm.ask("\n[bold]Proceed with deployment?[/bold]", default=True):
            console.print("[yellow]Deployment cancelled by user.[/yellow]")
            sys.exit(0)
        
        # Step 6: Create Salesforce Project
        console.print("\n[bold yellow]Salesforce Project Creation[/bold yellow]\n")
        if not deployer.create_project(spec, verbose=verbose):
            console.print("[red]❌ Failed to create Salesforce project[/red]")
            sys.exit(1)
        
        # Step 7: Implement Code
        console.print("\n[bold yellow]Code Implementation[/bold yellow]\n")
        if not deployer.implement_code(spec, generated_files, verbose=verbose):
            console.print("[red]❌ Failed to implement code[/red]")
            sys.exit(1)
        
        # Step 8: Select Target Org (if not already selected in discovery mode)
        if not target_org:
            console.print("\n[bold yellow]Deployment Target Selection[/bold yellow]\n")
            orgs = deployer.list_orgs(verbose=verbose)
            
            if not orgs:
                console.print("[red]❌ No Salesforce orgs found.[/red]")
                console.print("Please authenticate an org first: sf org login web")
                sys.exit(1)
            
            # Let user choose org
            org_choices = [org.get('alias', org.get('username', 'Unknown')) for org in orgs]
            console.print("\n[bold]Select target org:[/bold]")
            for i, choice in enumerate(org_choices, 1):
                console.print(f"  {i}. {choice}")
            
            choice_idx = int(Prompt.ask("Enter number", choices=[str(i) for i in range(1, len(org_choices) + 1)])) - 1
            target_org = org_choices[choice_idx]
        
        # Step 9: Deploy
        console.print(f"\n[bold]Deploying to: [cyan]{target_org}[/cyan][/bold]")
        if not Confirm.ask("Confirm deployment?", default=True):
            console.print("[yellow]Deployment cancelled.[/yellow]")
            sys.exit(0)
        
        if deployer.deploy_to_org(target_org, verbose=verbose):
            # Verify deployment
            deployer.verify_deployment(target_org, spec, verbose=verbose)
            
            # Clean up
            if config.get('auto_cleanup', True):
                deployer.cleanup_project(verbose=verbose)
            
            # Success message
            console.print("\n" + "═" * 60)
            console.print(Panel(
                f"[bold green]🎉 Lightning Type Successfully Deployed![/bold green]\n\n"
                f"Type Name: [cyan]{spec['type_name']}[/cyan]\n"
                f"Object: [cyan]{spec['object_api_name']}[/cyan]\n"
                f"Target Org: [cyan]{target_org}[/cyan]\n\n"
                f"[dim]You can now use this Lightning Type in your Agentforce actions![/dim]",
                title="✅ Success",
                expand=False
            ))
            console.print("═" * 60 + "\n")
        else:
            console.print("[red]❌ Deployment failed. Check the errors above.[/red]")
            sys.exit(1)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Operation cancelled by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]❌ Unexpected error: {e}[/red]")
        import traceback
        if verbose:
            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        sys.exit(1)

if __name__ == "__main__":
    main()
