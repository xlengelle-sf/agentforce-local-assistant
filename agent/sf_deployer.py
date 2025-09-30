"""Salesforce CLI integration and deployment manager"""
import subprocess
import json
import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

console = Console()

class SalesforceDeployer:
    def __init__(self, config_path="config/settings.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.auto_cleanup = self.config.get('auto_cleanup', True)
        self.project_dir = None
    
    def check_sf_cli(self, verbose=True):
        """Check if Salesforce CLI is installed"""
        try:
            result = subprocess.run(
                ['sf', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                if verbose:
                    console.print(f"[green]✅ Salesforce CLI: {result.stdout.strip()}[/green]")
                return True
            else:
                if verbose:
                    console.print("[red]❌ Salesforce CLI not found[/red]")
                return False
        
        except Exception as e:
            if verbose:
                console.print(f"[red]❌ Error checking SF CLI: {e}[/red]")
            return False
    
    def list_orgs(self, verbose=True):
        """List all authenticated Salesforce orgs"""
        try:
            result = subprocess.run(
                ['sf', 'org', 'list', '--json'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                orgs = data.get('result', {}).get('nonScratchOrgs', [])
                
                if verbose and orgs:
                    table = Table(title="Available Salesforce Orgs")
                    table.add_column("Alias", style="cyan")
                    table.add_column("Username", style="green")
                    table.add_column("Org ID", style="yellow")
                    table.add_column("Type", style="magenta")
                    
                    for org in orgs:
                        table.add_row(
                            org.get('alias', 'N/A'),
                            org.get('username', 'N/A'),
                            org.get('orgId', 'N/A')[:15] + '...',
                            org.get('connectedStatus', 'N/A')
                        )
                    
                    console.print(table)
                
                return orgs
            else:
                if verbose:
                    console.print("[yellow]⚠️  No orgs found or error listing orgs[/yellow]")
                return []
        
        except Exception as e:
            if verbose:
                console.print(f"[red]Error listing orgs: {e}[/red]")
            return []
    
    def create_project(self, spec, verbose=True):
        """Create a new Salesforce DX project"""
        if verbose:
            console.print("[bold blue]📚 Creating Salesforce project...[/bold blue]")
        
        project_name = f"{spec['type_name']}_project"
        self.project_dir = Path(f"projects/{project_name}")
        
        # Remove existing project if any
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)
        
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Generate project structure
            result = subprocess.run(
                ['sf', 'project', 'generate', '--name', project_name],
                cwd='projects',
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                if verbose:
                    console.print(f"[green]✅ Project created: {self.project_dir}[/green]")
                return True
            else:
                if verbose:
                    console.print(f"[red]❌ Error creating project: {result.stderr}[/red]")
                return False
        
        except Exception as e:
            if verbose:
                console.print(f"[red]Error: {e}[/red]")
            return False
    
    def implement_code(self, spec, generated_files, verbose=True):
        """Implement generated code in the Salesforce project"""
        if verbose:
            console.print("[bold blue]📝 Implementing code...[/bold blue]")
        
        if not self.project_dir or not self.project_dir.exists():
            console.print("[red]❌ No project directory found[/red]")
            return False
        
        try:
            # Create Lightning Type directory structure
            type_dir = self.project_dir / 'force-app' / 'main' / 'default' / 'lightningTypes' / spec['type_name']
            renderer_dir = type_dir / 'lightningDesktopGenAi'
            lwc_dir = self.project_dir / 'force-app' / 'main' / 'default' / 'lwc' / spec['lwc_component_name']
            
            type_dir.mkdir(parents=True, exist_ok=True)
            renderer_dir.mkdir(parents=True, exist_ok=True)
            lwc_dir.mkdir(parents=True, exist_ok=True)
            
            # Write schema.json
            (type_dir / 'schema.json').write_text(generated_files['schema.json'])
            if verbose:
                console.print("[dim]  ✓ schema.json[/dim]")
            
            # Write renderer.json
            (renderer_dir / 'renderer.json').write_text(generated_files['renderer.json'])
            if verbose:
                console.print("[dim]  ✓ renderer.json[/dim]")
            
            # Write LWC files
            for filename, content in generated_files.items():
                if filename not in ['schema.json', 'renderer.json']:
                    (lwc_dir / filename).write_text(content)
                    if verbose:
                        console.print(f"[dim]  ✓ {filename}[/dim]")
            
            if verbose:
                console.print("[green]✅ Code implemented successfully[/green]")
            
            return True
        
        except Exception as e:
            if verbose:
                console.print(f"[red]Error implementing code: {e}[/red]")
            return False
    
    def deploy_to_org(self, org_alias, verbose=True):
        """Deploy Lightning Type to specified org"""
        if verbose:
            console.print(f"[bold blue]🚀 Deploying to {org_alias}...[/bold blue]")
        
        if not self.project_dir or not self.project_dir.exists():
            console.print("[red]❌ No project directory found[/red]")
            return False
        
        try:
            result = subprocess.run(
                ['sf', 'project', 'deploy', 'start', '-o', org_alias],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                if verbose:
                    console.print(Panel(
                        "[bold green]✅ Deployment successful![/bold green]\n"
                        f"Lightning Type deployed to {org_alias}",
                        title="🎉 Success",
                        expand=False
                    ))
                return True
            else:
                if verbose:
                    console.print(Panel(
                        f"[bold red]❌ Deployment failed[/bold red]\n"
                        f"Error: {result.stderr}",
                        title="❌ Error",
                        expand=False
                    ))
                return False
        
        except Exception as e:
            if verbose:
                console.print(f"[red]Error during deployment: {e}[/red]")
            return False
    
    def verify_deployment(self, org_alias, spec, verbose=True):
        """Verify the deployment was successful"""
        if verbose:
            console.print("[blue]🔍 Verifying deployment...[/blue]")
        
        try:
            # Check if Lightning Type exists
            result = subprocess.run(
                ['sf', 'project', 'retrieve', 'start', 
                 '-m', f'LightningTypeBundle:{spec["type_name"]}',
                 '-o', org_alias],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                if verbose:
                    console.print("[green]✅ Deployment verified[/green]")
                return True
            else:
                if verbose:
                    console.print("[yellow]⚠️  Could not verify deployment[/yellow]")
                return False
        
        except Exception as e:
            if verbose:
                console.print(f"[yellow]Verification warning: {e}[/yellow]")
            return False
    
    def cleanup_project(self, verbose=True):
        """Clean up project directory after successful deployment"""
        if self.auto_cleanup and self.project_dir and self.project_dir.exists():
            try:
                shutil.rmtree(self.project_dir)
                if verbose:
                    console.print("[green]✅ Project cleaned up[/green]")
            except Exception as e:
                if verbose:
                    console.print(f"[yellow]⚠️  Could not clean up: {e}[/yellow]")
