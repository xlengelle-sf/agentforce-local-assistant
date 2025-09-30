"""LLM client for Ollama"""
import ollama
import json
from rich.console import Console

console = Console()

class LLMClient:
    def __init__(self, config_path="config/settings.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.model = self.config['llm']['model']
        self.temperature = self.config['llm']['temperature']
        self.max_tokens = self.config['llm']['max_tokens']
    
    def chat(self, messages, verbose=False):
        """Send chat request to Ollama"""
        try:
            if verbose:
                console.print("[dim]🤖 Thinking...[/dim]")
            
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens
                }
            )
            
            return response['message']['content']
        
        except Exception as e:
            console.print(f"[red]❌ Error communicating with LLM: {e}[/red]")
            return None
    
    def generate(self, prompt, system="You are a helpful AI assistant.", verbose=False):
        """Generate response from prompt"""
        messages = [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': prompt}
        ]
        
        return self.chat(messages, verbose=verbose)
