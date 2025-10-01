"""Documentation fetcher and processor"""
import requests
import json
import os
from bs4 import BeautifulSoup
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class DocFetcher:
    def __init__(self, config_path="config/settings.json"):
        # Get the repository root directory (parent of agent/)
        script_dir = Path(__file__).parent
        repo_root = script_dir.parent
        
        # Build absolute path to config file
        full_config_path = repo_root / config_path
        
        if not full_config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found at: {full_config_path}\n"
                f"Current directory: {Path.cwd()}\n"
                f"Script directory: {script_dir}\n"
                f"Repository root: {repo_root}"
            )
        
        with open(full_config_path, 'r') as f:
            self.config = json.load(f)
        
        self.docs_urls = self.config['docs_urls']
        
        # Create knowledge_base directories relative to repo root
        self.raw_docs_dir = repo_root / "knowledge_base" / "raw_docs"
        self.processed_dir = repo_root / "knowledge_base" / "processed"
        
        self.raw_docs_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_all_docs(self, verbose=True):
        """Download and process all documentation"""
        if verbose:
            console.print("[bold blue]📥 Fetching Salesforce documentation...[/bold blue]")
        
        all_docs = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"Downloading {len(self.docs_urls)} pages...", 
                total=len(self.docs_urls)
            )
            
            for url in self.docs_urls:
                try:
                    doc_content = self._fetch_single_doc(url)
                    if doc_content:
                        all_docs.append(doc_content)
                    progress.advance(task)
                except Exception as e:
                    if verbose:
                        console.print(f"[yellow]⚠️  Failed to fetch {url}: {e}[/yellow]")
        
        # Save processed docs
        output_file = self.processed_dir / "all_docs.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_docs, f, indent=2)
        
        if verbose:
            console.print(f"[green]✅ Downloaded and processed {len(all_docs)} documents[/green]")
        
        return all_docs
    
    def _fetch_single_doc(self, url):
        """Fetch and process a single documentation page"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Extract title
            title = soup.find('h1')
            title_text = title.get_text().strip() if title else url.split('/')[-1]
            
            return {
                "url": url,
                "title": title_text,
                "content": text,
                "length": len(text)
            }
        
        except Exception as e:
            console.print(f"[red]Error fetching {url}: {e}[/red]")
            return None
    
    def check_updates(self, verbose=True):
        """Check if documentation has been updated"""
        if verbose:
            console.print("[blue]🔄 Checking for documentation updates...[/blue]")
        
        # Simple check: compare current content with saved content
        updates_found = False
        
        for url in self.docs_urls:
            try:
                new_doc = self._fetch_single_doc(url)
                if not new_doc:
                    continue
                
                # Check if we have this doc locally
                output_file = self.processed_dir / "all_docs.json"
                if output_file.exists():
                    with open(output_file, 'r') as f:
                        existing_docs = json.load(f)
                    
                    # Find matching doc
                    existing = next((d for d in existing_docs if d['url'] == url), None)
                    
                    if existing:
                        if existing['content'] != new_doc['content']:
                            if verbose:
                                console.print(f"[yellow]📝 Update found: {new_doc['title']}[/yellow]")
                            updates_found = True
                    else:
                        if verbose:
                            console.print(f"[yellow]🆕 New page: {new_doc['title']}[/yellow]")
                        updates_found = True
            
            except Exception as e:
                if verbose:
                    console.print(f"[yellow]⚠️  Error checking {url}: {e}[/yellow]")
        
        if not updates_found and verbose:
            console.print("[green]✅ Documentation is up to date[/green]")
        
        return updates_found
