"""Object discovery module for comprehensive Salesforce object analysis"""
import subprocess
import json
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns

console = Console()

class ObjectDiscoverer:
    def __init__(self, cache_dir="knowledge_base/object_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def discover_object(self, object_name, org_alias, use_cache=True, verbose=True):
        """
        Comprehensive object discovery
        Returns complete metadata including fields, relationships, picklists, etc.
        """
        if verbose:
            console.print(f"[bold blue]🔍 Discovering object: {object_name}[/bold blue]")
        
        # Check cache first
        cache_file = self.cache_dir / f"{org_alias}_{object_name}.json"
        
        if use_cache and cache_file.exists():
            if verbose:
                console.print("[dim]  ⚡ Loading from cache...[/dim]")
            
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            cache_age = datetime.now() - datetime.fromisoformat(cached_data['cached_at'])
            
            if verbose:
                console.print(f"[dim]  📅 Cache age: {cache_age.days} days, {cache_age.seconds // 3600} hours[/dim]")
            
            return cached_data['metadata']
        
        # Fetch fresh metadata
        if verbose:
            console.print("[dim]  🌐 Fetching from Salesforce...[/dim]")
        
        metadata = self._fetch_object_metadata(object_name, org_alias, verbose)
        
        # Cache the results
        cache_data = {
            'cached_at': datetime.now().isoformat(),
            'object_name': object_name,
            'org_alias': org_alias,
            'metadata': metadata
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        if verbose:
            console.print("[green]  ✅ Discovery complete![/green]")
        
        return metadata
    
    def _fetch_object_metadata(self, object_name, org_alias, verbose):
        """Fetch complete object metadata using SF CLI"""
        try:
            # Execute sf sobject describe
            result = subprocess.run(
                ['sf', 'sobject', 'describe', '--sobject', object_name, 
                 '--target-org', org_alias, '--json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                if verbose:
                    console.print(f"[red]❌ Failed to describe object: {result.stderr}[/red]")
                return None
            
            data = json.loads(result.stdout)
            
            if data['status'] != 0:
                if verbose:
                    console.print(f"[red]❌ Error: {data.get('message', 'Unknown error')}[/red]")
                return None
            
            raw_metadata = data['result']
            
            # Process and enrich metadata
            metadata = self._process_metadata(raw_metadata, verbose)
            
            return metadata
        
        except Exception as e:
            if verbose:
                console.print(f"[red]❌ Error during discovery: {e}[/red]")
            return None
    
    def _process_metadata(self, raw_metadata, verbose):
        """Process and enrich raw metadata"""
        metadata = {
            'name': raw_metadata['name'],
            'label': raw_metadata['label'],
            'labelPlural': raw_metadata['labelPlural'],
            'custom': raw_metadata['custom'],
            'keyPrefix': raw_metadata.get('keyPrefix', ''),
            'fields': [],
            'relationships': [],
            'recordTypeInfos': raw_metadata.get('recordTypeInfos', []),
            'childRelationships': raw_metadata.get('childRelationships', []),
            'stats': {
                'total_fields': 0,
                'custom_fields': 0,
                'required_fields': 0,
                'picklist_fields': 0,
                'relationship_fields': 0,
                'formula_fields': 0,
                'rollup_fields': 0
            }
        }
        
        # Process fields
        for field in raw_metadata['fields']:
            field_info = self._process_field(field)
            metadata['fields'].append(field_info)
            
            # Update stats
            metadata['stats']['total_fields'] += 1
            if field_info['custom']:
                metadata['stats']['custom_fields'] += 1
            if field_info['required']:
                metadata['stats']['required_fields'] += 1
            if field_info['type'] == 'picklist' or field_info['type'] == 'multipicklist':
                metadata['stats']['picklist_fields'] += 1
            if field_info['type'] == 'reference':
                metadata['stats']['relationship_fields'] += 1
                metadata['relationships'].append(field_info)
            if field_info['calculated']:
                metadata['stats']['formula_fields'] += 1
            if field_info.get('aggregatable', False):
                metadata['stats']['rollup_fields'] += 1
        
        return metadata
    
    def _process_field(self, field):
        """Process individual field metadata"""
        field_info = {
            'name': field['name'],
            'label': field['label'],
            'type': field['type'],
            'custom': field['custom'],
            'required': not field['nillable'] and not field['defaultedOnCreate'],
            'length': field.get('length', 0),
            'precision': field.get('precision', 0),
            'scale': field.get('scale', 0),
            'calculated': field.get('calculated', False),
            'aggregatable': field.get('aggregatable', False),
            'externalId': field.get('externalId', False),
            'unique': field.get('unique', False),
            'picklistValues': [],
            'referenceTo': field.get('referenceTo', []),
            'relationshipName': field.get('relationshipName', ''),
            'defaultValue': field.get('defaultValue', None),
            'inlineHelpText': field.get('inlineHelpText', ''),
            'updateable': field.get('updateable', False),
            'createable': field.get('createable', False)
        }
        
        # Process picklist values
        if field['type'] in ['picklist', 'multipicklist']:
            field_info['picklistValues'] = [
                {
                    'label': pv['label'],
                    'value': pv['value'],
                    'active': pv['active'],
                    'defaultValue': pv['defaultValue']
                }
                for pv in field.get('picklistValues', [])
            ]
        
        return field_info
    
    def display_object_summary(self, metadata, verbose=True):
        """Display a beautiful summary of the object"""
        if not metadata:
            console.print("[red]❌ No metadata to display[/red]")
            return
        
        # Header panel
        header = f"""[bold cyan]{metadata['label']}[/bold cyan] ({metadata['name']})
        
Type: {'Custom Object' if metadata['custom'] else 'Standard Object'}
Prefix: {metadata['keyPrefix']}
Plural: {metadata['labelPlural']}"""
        
        console.print(Panel(header, title="📊 Object Information", expand=False))
        
        # Stats panel
        stats = metadata['stats']
        stats_table = Table(show_header=False, box=None, padding=(0, 2))
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Count", style="green", justify="right")
        
        stats_table.add_row("Total Fields", str(stats['total_fields']))
        stats_table.add_row("Custom Fields", str(stats['custom_fields']))
        stats_table.add_row("Required Fields", str(stats['required_fields']))
        stats_table.add_row("Picklist Fields", str(stats['picklist_fields']))
        stats_table.add_row("Relationships", str(stats['relationship_fields']))
        stats_table.add_row("Formula Fields", str(stats['formula_fields']))
        stats_table.add_row("Roll-up Summaries", str(stats['rollup_fields']))
        
        console.print(Panel(stats_table, title="📈 Statistics", expand=False))
        
        if verbose:
            # Top fields preview
            console.print("\n[bold]Preview of key fields:[/bold]")
            self._display_fields_preview(metadata['fields'][:10])
    
    def _display_fields_preview(self, fields):
        """Display a preview of fields"""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Field Name", style="cyan", width=30)
        table.add_column("Label", style="white", width=25)
        table.add_column("Type", style="yellow", width=15)
        table.add_column("Required", style="red", justify="center", width=10)
        
        for field in fields:
            table.add_row(
                field['name'],
                field['label'][:25],
                field['type'],
                "✓" if field['required'] else ""
            )
        
        console.print(table)
    
    def display_all_fields(self, metadata, show_system=False):
        """Display detailed table of all fields"""
        fields = metadata['fields']
        
        if not show_system:
            # Filter out system fields
            fields = [f for f in fields if not f['name'].startswith('System') 
                     and f['name'] not in ['Id', 'IsDeleted', 'CreatedDate', 
                                          'CreatedById', 'LastModifiedDate', 
                                          'LastModifiedById']]
        
        console.print(f"\n[bold]All Fields ({len(fields)} fields):[/bold]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("API Name", style="cyan", width=30)
        table.add_column("Label", style="white", width=25)
        table.add_column("Type", style="yellow", width=15)
        table.add_column("Req", justify="center", width=4)
        table.add_column("Custom", justify="center", width=6)
        table.add_column("Details", style="dim", width=30)
        
        for idx, field in enumerate(fields, 1):
            details = []
            
            if field['calculated']:
                details.append("Formula")
            if field['aggregatable']:
                details.append("Roll-up")
            if field['externalId']:
                details.append("Ext ID")
            if field['unique']:
                details.append("Unique")
            if field['type'] == 'reference':
                details.append(f"→ {', '.join(field['referenceTo'])}")
            if field['length'] > 0 and field['type'] in ['string', 'textarea']:
                details.append(f"Max: {field['length']}")
            
            table.add_row(
                str(idx),
                field['name'],
                field['label'][:25],
                field['type'],
                "✓" if field['required'] else "",
                "✓" if field['custom'] else "",
                ", ".join(details)[:30] if details else ""
            )
        
        console.print(table)
    
    def get_field_recommendations(self, metadata, llm_client, purpose="display", verbose=True):
        """Use LLM to recommend which fields to display"""
        if verbose:
            console.print("\n[bold blue]🤖 Analyzing fields for recommendations...[/bold blue]")
        
        # Prepare field summary for LLM
        field_summary = []
        for field in metadata['fields']:
            # Skip system fields
            if field['name'].startswith('System') or field['name'] in ['Id', 'IsDeleted']:
                continue
            
            summary = f"{field['name']} ({field['label']}) - Type: {field['type']}"
            
            if field['required']:
                summary += " [Required]"
            if field['type'] == 'reference':
                summary += f" [Lookup to: {', '.join(field['referenceTo'])}]"
            if field['calculated']:
                summary += " [Formula]"
            
            field_summary.append(summary)
        
        # Ask LLM for recommendations
        prompt = f"""Given this Salesforce object: {metadata['label']} ({metadata['name']})

Purpose: Create a Lightning Type to {purpose}

Available fields:
{chr(10).join(field_summary[:50])}  # Limit to first 50 fields

Recommend the TOP 8-12 most important fields to display, considering:
1. Business relevance (Name, Status, dates, amounts)
2. User experience (not too technical)
3. Visual appeal (good mix of text, dates, numbers)
4. Relationships (include key lookups)

Return ONLY a JSON array of field API names:
["Field1", "Field2", ...]

No explanations, just the JSON array.
"""
        
        response = llm_client.generate(
            prompt,
            system="You are an expert Salesforce UX designer. Return only valid JSON.",
            verbose=False
        )
        
        try:
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                recommended = json.loads(response[json_start:json_end])
                
                if verbose:
                    console.print(f"[green]✅ Recommended {len(recommended)} fields[/green]")
                
                return recommended
        except:
            if verbose:
                console.print("[yellow]⚠️  Could not parse recommendations, using defaults[/yellow]")
        
        # Fallback: return most common fields
        return self._get_default_field_recommendations(metadata)
    
    def _get_default_field_recommendations(self, metadata):
        """Fallback field recommendations"""
        recommended = []
        
        # Always include Name if exists
        name_field = next((f for f in metadata['fields'] if f['name'] == 'Name'), None)
        if name_field:
            recommended.append('Name')
        
        # Add other important fields
        priority_patterns = ['Status', 'Date', 'Amount', 'Total', 'Type', 'Owner']
        
        for field in metadata['fields']:
            if len(recommended) >= 10:
                break
            
            if any(pattern in field['label'] for pattern in priority_patterns):
                if field['name'] not in recommended:
                    recommended.append(field['name'])
        
        return recommended[:10]
    
    def clear_cache(self, org_alias=None, object_name=None):
        """Clear cache for specific org/object or all"""
        if org_alias and object_name:
            cache_file = self.cache_dir / f"{org_alias}_{object_name}.json"
            if cache_file.exists():
                cache_file.unlink()
                console.print(f"[green]✅ Cache cleared for {org_alias}/{object_name}[/green]")
        else:
            # Clear all cache
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            console.print("[green]✅ All cache cleared[/green]")
