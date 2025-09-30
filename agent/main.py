#!/usr/bin/env python3
"""
AgentForce Local Assistant
Main entry point for the conversational agent
"""
import sys
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint

# Import agent modules
from doc_fetcher import DocFetcher
from rag_engine import RAGEngine
from llm_client import LLMClient
from business_analyst import BusinessAnalyst
from spec_generator import SpecGenerator
from code_generator import CodeGenerator
from sf_deployer import SalesforceDeployer

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
    
    # Step 2: Initialize components
    console.print("[dim]Initializing AI components...[/dim]")
    rag = RAGEngine()
    llm = LLMClient()
    ba = BusinessAnalyst(llm, rag)
    spec_gen = SpecGenerator(llm, rag)
    code_gen = CodeGenerator(llm, rag)
    deployer = SalesforceDeployer()
    
    # Step 3: Check Salesforce CLI
    console.print("\n[bold]Checking environment...[/bold]")
    if not deployer.check_sf_cli(verbose=verbose):
        console.print("[red]❌ Salesforce CLI is required but not found.[/red]")
        console.print("Please install it from: https://developer.salesforce.com/tools/sfdxcli")
        sys.exit(1)
    
    console.print("\n[green]✅ All systems ready![/green]\n")
    console.print("─" * 60)
    
    try:
        # Step 4: Business Analysis - Gather Requirements
        console.print("\n[bold yellow]Step 1/7: Business Requirements Analysis[/bold yellow]\n")
        requirements = ba.gather_requirements(verbose=verbose)
        
        # Step 5: Generate Specification
        console.print("\n[bold yellow]Step 2/7: Technical Specification[/bold yellow]\n")
        spec = spec_gen.generate_spec(requirements, verbose=verbose)
        
        # Confirmation before code generation
        if not Confirm.ask("\n[bold]Proceed with code generation?[/bold]", default=True):
            console.print("[yellow]Operation cancelled by user.[/yellow]")
            sys.exit(0)
        
        # Step 6: Check for Documentation Updates
        console.print("\n[bold yellow]Step 3/7: Documentation Verification[/bold yellow]\n")
        fetcher = DocFetcher()
        updates_found = fetcher.check_updates(verbose=verbose)
        
        if updates_found:
            console.print("[yellow]⚠️  Documentation updates detected![/yellow]")
            if Confirm.ask("Re-download documentation for latest examples?", default=True):
                fetcher.fetch_all_docs(verbose=verbose)
                # Reload RAG engine with updated docs
                rag = RAGEngine()
                code_gen = CodeGenerator(llm, rag)
        
        # Step 7: Generate Code
        console.print("\n[bold yellow]Step 4/7: Code Generation[/bold yellow]\n")
        generated_files = code_gen.generate_all_code(spec, verbose=verbose)
        
        # Show generated code summary
        if verbose:
            console.print("\n[bold]Generated Files:[/bold]")
            for filename in generated_files.keys():
                console.print(f"  ✓ {filename}")
        
        # Step 8: Create Salesforce Project
        console.print("\n[bold yellow]Step 5/7: Salesforce Project Creation[/bold yellow]\n")
        if not deployer.create_project(spec, verbose=verbose):
            console.print("[red]❌ Failed to create Salesforce project[/red]")
            sys.exit(1)
        
        # Step 9: Implement Code
        console.print("\n[bold yellow]Step 6/7: Code Implementation[/bold yellow]\n")
        if not deployer.implement_code(spec, generated_files, verbose=verbose):
            console.print("[red]❌ Failed to implement code[/red]")
            sys.exit(1)
        
        # Step 10: Select Target Org and Deploy
        console.print("\n[bold yellow]Step 7/7: Deployment[/bold yellow]\n")
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
        
        console.print(f"\n[bold]Deploying to: [cyan]{target_org}[/cyan][/bold]")
        if not Confirm.ask("Confirm deployment?", default=True):
            console.print("[yellow]Deployment cancelled.[/yellow]")
            sys.exit(0)
        
        # Deploy
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
