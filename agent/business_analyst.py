"""Business analyst module for understanding user requirements"""
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
import json

console = Console()

class BusinessAnalyst:
    def __init__(self, llm_client, rag_engine):
        self.llm = llm_client
        self.rag = rag_engine
        self.requirements = {}
    
    def gather_requirements(self, object_metadata, recommended_fields=None, verbose=True):
        """
        Interactive session to gather business requirements
        NOW takes object metadata as input for context-aware analysis
        """
        if verbose:
            console.print(Panel(
                f"[bold blue]Business Requirements Analysis[/bold blue]\n"
                f"Lightning Type for: [cyan]{object_metadata['label']} ({object_metadata['name']})[/cyan]",
                expand=False
            ))
        
        # Store object context
        self.requirements['object_name'] = object_metadata['name']
        self.requirements['object_label'] = object_metadata['label']
        self.requirements['is_custom'] = object_metadata['custom']
        
        # Step 1: Purpose / Use Case
        console.print("\n[bold cyan]Step 1: Purpose & Context[/bold cyan]")
        console.print("What's the main use case for displaying this object?")
        console.print("[dim](e.g., 'Show booking details to customers', 'Display order status')[/dim]")
        
        purpose = Prompt.ask("Use case")
        self.requirements['display_purpose'] = purpose
        
        # Step 2: Field Selection (Hybrid approach)
        console.print("\n[bold cyan]Step 2: Field Selection[/bold cyan]")
        
        selected_fields = self._select_fields_hybrid(
            object_metadata, 
            recommended_fields, 
            purpose,
            verbose
        )
        self.requirements['selected_fields'] = selected_fields
        
        # Step 3: Visual Style
        console.print("\n[bold cyan]Step 3: Visual Style[/bold cyan]")
        console.print("What visual layout would work best?")
        
        style_options = [
            "Card (single item view)",
            "Timeline (chronological events)",
            "Dashboard (multiple metrics)",
            "List (compact table)",
            "Custom (describe it)"
        ]
        
        for idx, style in enumerate(style_options, 1):
            console.print(f"  {idx}. {style}")
        
        style_choice = Prompt.ask(
            "Select style",
            choices=[str(i) for i in range(1, len(style_options) + 1)],
            default="1"
        )
        
        visual_style = style_options[int(style_choice) - 1]
        
        if "Custom" in visual_style:
            visual_style = Prompt.ask("Describe your custom layout")
        
        self.requirements['visual_style'] = visual_style
        
        # Step 4: Special Features
        console.print("\n[bold cyan]Step 4: Interactive Features[/bold cyan]")
        console.print("What interactive elements do you want?")
        console.print("[dim](Select all that apply, comma-separated)[/dim]")
        
        feature_options = {
            "1": "Status badges/pills",
            "2": "Progress indicators",
            "3": "Action buttons",
            "4": "Icon indicators",
            "5": "Date/time formatting",
            "6": "Currency formatting",
            "7": "Related records preview",
            "8": "None"
        }
        
        for key, value in feature_options.items():
            console.print(f"  {key}. {value}")
        
        feature_input = Prompt.ask("Features", default="1,5")
        selected_features = [
            feature_options[f.strip()] 
            for f in feature_input.split(',') 
            if f.strip() in feature_options
        ]
        
        self.requirements['special_features'] = selected_features
        
        # Step 5: Additional Context
        console.print("\n[bold cyan]Step 5: Additional Context (Optional)[/bold cyan]")
        
        if Confirm.ask("Any special display rules or conditions?", default=False):
            special_rules = Prompt.ask("Describe them")
            self.requirements['special_rules'] = special_rules
        else:
            self.requirements['special_rules'] = "None"
        
        # Confirm understanding with LLM analysis
        if verbose:
            console.print("\n[yellow]🧠 Analyzing your requirements...[/yellow]")
        
        self._analyze_requirements(object_metadata, verbose)
        
        return self.requirements
    
    def _select_fields_hybrid(self, object_metadata, recommended_fields, purpose, verbose):
        """
        Hybrid field selection:
        1. Show AI recommendations
        2. Allow user to accept, modify, or choose custom
        """
        console.print("\n[bold]Available fields to display:[/bold]")
        
        # Show recommended fields
        if recommended_fields:
            console.print(f"\n[green]✨ AI Recommended ({len(recommended_fields)} fields):[/green]")
            
            rec_table = Table(show_header=True, header_style="bold cyan")
            rec_table.add_column("#", width=4)
            rec_table.add_column("Field Name", width=30)
            rec_table.add_column("Label", width=25)
            rec_table.add_column("Type", width=15)
            
            field_map = {f['name']: f for f in object_metadata['fields']}
            
            for idx, field_name in enumerate(recommended_fields, 1):
                field = field_map.get(field_name)
                if field:
                    rec_table.add_row(
                        str(idx),
                        field['name'],
                        field['label'],
                        field['type']
                    )
            
            console.print(rec_table)
        
        # Ask user for choice
        console.print("\n[bold]Field Selection Options:[/bold]")
        console.print("  1. Use recommended fields (quick)")
        console.print("  2. Modify recommendations (add/remove)")
        console.print("  3. Select manually from all fields")
        
        choice = Prompt.ask("Your choice", choices=["1", "2", "3"], default="1")
        
        if choice == "1":
            # Use recommendations as-is
            return recommended_fields
        
        elif choice == "2":
            # Modify recommendations
            return self._modify_field_selection(
                object_metadata, 
                recommended_fields, 
                verbose
            )
        
        else:
            # Manual selection from all fields
            return self._manual_field_selection(object_metadata, verbose)
    
    def _modify_field_selection(self, object_metadata, current_selection, verbose):
        """Allow user to add/remove fields from recommendations"""
        selected = list(current_selection)
        
        while True:
            console.print(f"\n[cyan]Current selection ({len(selected)} fields):[/cyan]")
            console.print(", ".join(selected))
            
            console.print("\n[bold]Actions:[/bold]")
            console.print("  1. Add more fields")
            console.print("  2. Remove fields")
            console.print("  3. Done")
            
            action = Prompt.ask("Action", choices=["1", "2", "3"], default="3")
            
            if action == "1":
                # Show available fields not yet selected
                available = [
                    f for f in object_metadata['fields'] 
                    if f['name'] not in selected 
                    and not f['name'].startswith('System')
                    and f['name'] not in ['Id', 'IsDeleted']
                ]
                
                if not available:
                    console.print("[yellow]No more fields available[/yellow]")
                    continue
                
                console.print(f"\n[bold]Available fields ({len(available)}):[/bold]")
                for idx, field in enumerate(available[:20], 1):  # Show first 20
                    console.print(f"  {idx}. {field['name']} ({field['label']}) - {field['type']}")
                
                if len(available) > 20:
                    console.print(f"  ... and {len(available) - 20} more")
                
                add_input = Prompt.ask(
                    "Enter field name(s) to add (comma-separated)",
                    default=""
                )
                
                if add_input:
                    for field_name in add_input.split(','):
                        field_name = field_name.strip()
                        if any(f['name'] == field_name for f in available):
                            if field_name not in selected:
                                selected.append(field_name)
                                console.print(f"[green]✓ Added {field_name}[/green]")
            
            elif action == "2":
                # Remove fields
                console.print("\n[bold]Current fields:[/bold]")
                for idx, field_name in enumerate(selected, 1):
                    console.print(f"  {idx}. {field_name}")
                
                remove_input = Prompt.ask(
                    "Enter field name(s) to remove (comma-separated)",
                    default=""
                )
                
                if remove_input:
                    for field_name in remove_input.split(','):
                        field_name = field_name.strip()
                        if field_name in selected:
                            selected.remove(field_name)
                            console.print(f"[yellow]✗ Removed {field_name}[/yellow]")
            
            else:
                # Done
                break
        
        return selected
    
    def _manual_field_selection(self, object_metadata, verbose):
        """Full manual field selection"""
        console.print("\n[bold]All available fields:[/bold]")
        
        # Filter out system fields
        available_fields = [
            f for f in object_metadata['fields']
            if not f['name'].startswith('System')
            and f['name'] not in ['Id', 'IsDeleted', 'CreatedById', 
                                  'LastModifiedById', 'LastModifiedDate', 'CreatedDate']
        ]
        
        # Display in table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", width=4)
        table.add_column("Field Name", width=30)
        table.add_column("Label", width=25)
        table.add_column("Type", width=15)
        table.add_column("Required", justify="center", width=8)
        
        for idx, field in enumerate(available_fields, 1):
            table.add_row(
                str(idx),
                field['name'],
                field['label'][:25],
                field['type'],
                "✓" if field['required'] else ""
            )
            
            # Limit display
            if idx >= 30:
                console.print(f"  ... and {len(available_fields) - 30} more fields")
                break
        
        console.print(table)
        
        console.print("\n[bold]Enter field names to include (comma-separated):[/bold]")
        console.print("[dim]Example: Name,Status__c,Amount__c[/dim]")
        
        field_input = Prompt.ask("Fields")
        
        selected = [
            f.strip() for f in field_input.split(',')
            if any(field['name'] == f.strip() for field in available_fields)
        ]
        
        console.print(f"[green]✓ Selected {len(selected)} fields[/green]")
        
        return selected
    
    def _analyze_requirements(self, object_metadata, verbose):
        """Use LLM to analyze and enhance requirements"""
        # Search for relevant documentation
        search_query = f"Lightning Types {self.requirements.get('visual_style', 'card')} {self.requirements.get('display_purpose', '')}"
        relevant_docs = self.rag.search(search_query, top_k=2, verbose=False)
        
        # Build context
        doc_context = "\n".join([
            f"Reference: {r['doc']['title']}\n{r['doc']['content'][:500]}..."
            for r in relevant_docs
        ])
        
        # Prepare field details
        field_map = {f['name']: f for f in object_metadata['fields']}
        selected_field_details = []
        
        for field_name in self.requirements['selected_fields']:
            field = field_map.get(field_name)
            if field:
                detail = f"{field['name']} ({field['label']}) - {field['type']}"
                if field['type'] == 'reference':
                    detail += f" [Lookup: {', '.join(field['referenceTo'])}]"
                selected_field_details.append(detail)
        
        # Ask LLM to analyze
        prompt = f"""Analyze these Lightning Type requirements:

Object: {object_metadata['label']} ({object_metadata['name']})
Purpose: {self.requirements['display_purpose']}
Selected Fields ({len(self.requirements['selected_fields'])}):
{chr(10).join(selected_field_details)}

Visual Style: {self.requirements['visual_style']}
Features: {', '.join(self.requirements['special_features'])}
Special Rules: {self.requirements.get('special_rules', 'None')}

Documentation context:
{doc_context}

Provide a brief analysis (max 150 words):
1. Key components needed
2. Potential UX challenges
3. Implementation recommendations

Be specific about handling the field types present.
"""
        
        analysis = self.llm.generate(
            prompt,
            system="You are an expert Salesforce UX architect specializing in Lightning Types.",
            verbose=verbose
        )
        
        if analysis and verbose:
            console.print(Panel(
                f"[bold green]Analysis:[/bold green]\n{analysis}",
                title="🧠 Requirements Analysis",
                expand=False
            ))
        
        self.requirements['analysis'] = analysis
        
        # Confirm with user
        confirm = Prompt.ask(
            "\n[bold]Proceed with these requirements?[/bold]",
            choices=["yes", "no", "modify"],
            default="yes"
        )
        
        if confirm == "no":
            console.print("[yellow]Let's start over...[/yellow]")
            return self.gather_requirements(object_metadata, verbose=verbose)
        elif confirm == "modify":
            console.print("[yellow]Which aspect would you like to modify?[/yellow]")
            console.print("  1. Field selection")
            console.print("  2. Visual style")
            console.print("  3. Features")
            
            modify_choice = Prompt.ask("Modify", choices=["1", "2", "3"])
            
            if modify_choice == "1":
                # Re-select fields
                new_fields = self._modify_field_selection(
                    object_metadata,
                    self.requirements['selected_fields'],
                    verbose
                )
                self.requirements['selected_fields'] = new_fields
            
            # Re-analyze after modifications
            return self._analyze_requirements(object_metadata, verbose)
        
        return self.requirements
