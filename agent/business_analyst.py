"""Business analyst module for understanding user requirements"""
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
import json

console = Console()

class BusinessAnalyst:
    def __init__(self, llm_client, rag_engine):
        self.llm = llm_client
        self.rag = rag_engine
        self.requirements = {}
    
    def gather_requirements(self, verbose=True):
        """Interactive session to gather business requirements"""
        if verbose:
            console.print(Panel(
                "[bold blue]Business Requirements Analysis[/bold blue]\n"
                "Let's understand what Lightning Type you want to create.",
                expand=False
            ))
        
        # Ask key questions
        questions = [
            {
                "key": "object_name",
                "question": "What is the Salesforce object you want to display?",
                "example": "(e.g., Hotel_Booking__c, Account, Custom_Object__c)"
            },
            {
                "key": "display_purpose",
                "question": "What is the main purpose of this custom display?",
                "example": "(e.g., Show booking details, Display hotel information)"
            },
            {
                "key": "key_fields",
                "question": "What are the key fields to display?",
                "example": "(e.g., Name, Status__c, Check_in_Date__c - comma separated)"
            },
            {
                "key": "visual_style",
                "question": "What visual style do you prefer?",
                "example": "(e.g., Card layout, Table, Timeline, Dashboard)"
            },
            {
                "key": "special_features",
                "question": "Any special features or interactive elements?",
                "example": "(e.g., Progress bar, Status badges, Buttons)"
            }
        ]
        
        for q in questions:
            console.print(f"\n[bold cyan]Q:[/bold cyan] {q['question']}")
            console.print(f"[dim]{q['example']}[/dim]")
            answer = Prompt.ask("Your answer")
            self.requirements[q['key']] = answer
        
        # Confirm understanding
        if verbose:
            console.print("\n[yellow]📝 Analyzing your requirements...[/yellow]")
        
        self._analyze_requirements(verbose)
        
        return self.requirements
    
    def _analyze_requirements(self, verbose):
        """Use LLM to analyze and enhance requirements"""
        # Search for relevant documentation
        search_query = f"Lightning Types {self.requirements.get('visual_style', 'card')} {self.requirements.get('display_purpose', '')}"
        relevant_docs = self.rag.search(search_query, top_k=2, verbose=verbose)
        
        # Build context
        doc_context = "\n".join([
            f"Reference: {r['doc']['title']}\n{r['doc']['content'][:500]}..."
            for r in relevant_docs
        ])
        
        # Ask LLM to analyze
        prompt = f"""Based on these requirements:

Object: {self.requirements['object_name']}
Purpose: {self.requirements['display_purpose']}
Key Fields: {self.requirements['key_fields']}
Visual Style: {self.requirements['visual_style']}
Special Features: {self.requirements['special_features']}

And this documentation context:
{doc_context}

Provide a brief analysis of:
1. What components will be needed
2. Any potential challenges
3. Recommendations for implementation

Keep it concise (max 150 words).
"""
        
        analysis = self.llm.generate(
            prompt,
            system="You are an expert Salesforce developer specializing in Lightning Types.",
            verbose=verbose
        )
        
        if analysis and verbose:
            console.print(Panel(
                f"[bold green]Analysis:[/bold green]\n{analysis}",
                title="📊 Requirements Analysis",
                expand=False
            ))
        
        self.requirements['analysis'] = analysis
        
        # Confirm with user
        confirm = Prompt.ask(
            "\n[bold]Does this sound right?[/bold]",
            choices=["yes", "no"],
            default="yes"
        )
        
        if confirm == "no":
            console.print("[yellow]Let's refine the requirements...[/yellow]")
            return self.gather_requirements(verbose)
        
        return self.requirements
