"""
Command Line Interface for IWSA
"""

import asyncio
import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from .core.engine import ScrapingEngine
from .config import Settings
from .utils.logger import setup_logging


console = Console()


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--config', type=click.Path(), help='Configuration file path')
@click.pass_context
def cli(ctx, debug, config):
    """Intelligent Web Scraping Agent - AI-powered web scraping tool"""
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug
    ctx.obj['config'] = config
    
    # Setup logging
    log_level = 'DEBUG' if debug else 'INFO'
    setup_logging(log_level)


@cli.command()
@click.argument('prompt', required=True)
@click.option('--profile', default='balanced', 
              type=click.Choice(['conservative', 'balanced', 'aggressive', 'stealth']),
              help='Scraping profile to use')
@click.option('--format', 'export_format', default='sheets',
              type=click.Choice(['sheets', 'csv', 'json', 'excel']),
              help='Export format')
@click.option('--estimate', is_flag=True, help='Only estimate cost, don\'t run')
@click.pass_context
def scrape(ctx, prompt, profile, export_format, estimate):
    """Scrape websites based on natural language prompt"""
    
    console.print(Panel.fit(
        f"[bold blue]IWSA - Intelligent Web Scraping Agent[/bold blue]\n"
        f"Prompt: {prompt}\n"
        f"Profile: {profile}\n"
        f"Format: {export_format}",
        title="Scraping Request"
    ))
    
    async def run_scraping():
        try:
            settings = Settings()
            engine = ScrapingEngine(settings)
            
            if estimate:
                # Cost estimation
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("Estimating cost...", total=None)
                    
                    cost_info = await engine.estimate_request_cost(prompt)
                    progress.remove_task(task)
                
                if 'error' in cost_info:
                    console.print(f"[red]Error: {cost_info['error']}[/red]")
                    return
                
                # Display cost estimation
                table = Table(title="Cost Estimation")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Estimated Cost (USD)", f"${cost_info.get('estimated_cost_usd', 0):.3f}")
                table.add_row("Estimated Pages", str(cost_info.get('estimated_pages', 0)))
                table.add_row("Estimated Duration", f"{cost_info.get('estimated_duration_minutes', 0):.1f} minutes")
                table.add_row("Target URLs", str(len(cost_info.get('target_urls', []))))
                table.add_row("Scraping Type", cost_info.get('scraping_type', 'unknown'))
                
                console.print(table)
                
                if cost_info.get('validation_issues'):
                    console.print("[yellow]Issues:[/yellow]")
                    for issue in cost_info['validation_issues']:
                        console.print(f"  • {issue}")
                
                return
            
            # Actual scraping
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Processing request...", total=None)
                
                response = await engine.process_request(prompt)
                progress.remove_task(task)
            
            if response.success:
                console.print("[green]✓ Scraping completed successfully![/green]")
                
                # Display results
                results_table = Table(title="Scraping Results")
                results_table.add_column("Metric", style="cyan")
                results_table.add_column("Value", style="green")
                
                results_table.add_row("Records Extracted", str(response.total_records))
                results_table.add_row("Pages Processed", str(response.pages_processed))
                results_table.add_row("Processing Time", f"{response.processing_time:.2f} seconds")
                
                if response.export_url:
                    results_table.add_row("Export URL", response.export_url)
                
                if response.file_paths:
                    results_table.add_row("Files Created", ", ".join(response.file_paths))
                
                console.print(results_table)
                
                # Display quality metrics if available
                if (response.pipeline_result and 
                    response.pipeline_result.export_results and
                    response.pipeline_result.export_results[0].metadata):
                    
                    metadata = response.pipeline_result.export_results[0].metadata
                    if 'quality_assessment' in metadata:
                        quality = metadata['quality_assessment']
                        console.print(f"\n[bold]Quality Score:[/bold] {quality.get('quality_score', 'N/A')}")
            
            else:
                console.print(f"[red]✗ Scraping failed: {response.error}[/red]")
        
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            if ctx.obj.get('debug'):
                import traceback
                console.print(traceback.format_exc())
    
    asyncio.run(run_scraping())


@cli.command()
@click.pass_context
def health(ctx):
    """Check system health"""
    
    async def check_health():
        try:
            settings = Settings()
            engine = ScrapingEngine(settings)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Running health check...", total=None)
                
                health_status = await engine.health_check()
                progress.remove_task(task)
            
            # Display health status
            overall_health = health_status.get('overall_health', 'unknown')
            
            if overall_health == 'healthy':
                console.print("[green]✓ System is healthy[/green]")
            elif overall_health == 'degraded':
                console.print("[yellow]⚠ System is degraded[/yellow]")
            else:
                console.print("[red]✗ System is unhealthy[/red]")
            
            # Component status table
            table = Table(title="Component Health")
            table.add_column("Component", style="cyan")
            table.add_column("Status", style="green")
            
            for component, status in health_status.get('components', {}).items():
                if isinstance(status, dict):
                    component_status = status.get('overall_health', status.get('status', 'unknown'))
                else:
                    component_status = str(status)
                
                # Color code status
                if component_status == 'healthy':
                    status_text = "[green]✓ Healthy[/green]"
                elif component_status == 'degraded':
                    status_text = "[yellow]⚠ Degraded[/yellow]"
                else:
                    status_text = "[red]✗ Unhealthy[/red]"
                
                table.add_row(component.replace('_', ' ').title(), status_text)
            
            console.print(table)
            
            # Show issues if any
            if 'issues' in health_status:
                console.print("\n[yellow]Issues Found:[/yellow]")
                for issue in health_status['issues']:
                    console.print(f"  • {issue}")
        
        except Exception as e:
            console.print(f"[red]Health check failed: {str(e)}[/red]")
            if ctx.obj.get('debug'):
                import traceback
                console.print(traceback.format_exc())
    
    asyncio.run(check_health())


@cli.command()
@click.pass_context  
def stats(ctx):
    """Show system statistics"""
    
    async def show_stats():
        try:
            settings = Settings()
            engine = ScrapingEngine(settings)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Gathering statistics...", total=None)
                
                stats_data = await engine.get_system_stats()
                progress.remove_task(task)
            
            # Engine stats
            engine_stats = stats_data.get('engine', {})
            table = Table(title="Engine Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Active Requests", str(engine_stats.get('active_requests', 0)))
            table.add_row("Uptime", f"{engine_stats.get('uptime_seconds', 0):.0f} seconds")
            
            console.print(table)
            
            # LLM Provider stats
            llm_providers = stats_data.get('llm_providers', {})
            if llm_providers and 'error' not in llm_providers:
                provider_table = Table(title="LLM Providers")
                provider_table.add_column("Provider", style="cyan")
                provider_table.add_column("Status", style="green")
                provider_table.add_column("Type", style="blue")
                
                for provider, info in llm_providers.items():
                    status = "Available" if info.get('available') else "Unavailable"
                    provider_type = info.get('provider_type', 'unknown')
                    
                    status_color = "[green]" if info.get('available') else "[red]"
                    provider_table.add_row(
                        provider.title(), 
                        f"{status_color}{status}[/{status_color.strip('[')}", 
                        provider_type
                    )
                
                console.print(provider_table)
            
            # Data pipeline stats
            pipeline_stats = stats_data.get('data_pipeline', {})
            if pipeline_stats and 'error' not in pipeline_stats:
                storage_info = pipeline_stats.get('storage', {})
                if storage_info:
                    storage_table = Table(title="Storage Statistics")
                    storage_table.add_column("Metric", style="cyan")
                    storage_table.add_column("Value", style="green")
                    
                    storage_table.add_row("Connected", str(storage_info.get('connected', False)))
                    storage_table.add_row("Document Count", str(storage_info.get('document_count', 0)))
                    storage_table.add_row("Storage Size", f"{storage_info.get('storage_size_bytes', 0)} bytes")
                    
                    console.print(storage_table)
        
        except Exception as e:
            console.print(f"[red]Failed to get statistics: {str(e)}[/red]")
            if ctx.obj.get('debug'):
                import traceback
                console.print(traceback.format_exc())
    
    asyncio.run(show_stats())


@cli.command()
def version():
    """Show version information"""
    from . import __version__, __author__
    
    console.print(Panel.fit(
        f"[bold blue]IWSA - Intelligent Web Scraping Agent[/bold blue]\n"
        f"Version: {__version__}\n"
        f"Author: {__author__}",
        title="Version Information"
    ))


@cli.command()
@click.argument('prompt', required=True)
@click.option('--output', '-o', type=click.File('w'), default='-',
              help='Output file (default: stdout)')
@click.pass_context
def config(ctx, prompt, output):
    """Generate configuration for a scraping request"""
    
    async def generate_config():
        try:
            settings = Settings()
            engine = ScrapingEngine(settings)
            
            # Get cost estimation which includes configuration details
            cost_info = await engine.estimate_request_cost(prompt)
            
            if 'error' in cost_info:
                console.print(f"[red]Error: {cost_info['error']}[/red]")
                return
            
            config_data = {
                'prompt': prompt,
                'target_urls': cost_info.get('target_urls', []),
                'scraping_type': cost_info.get('scraping_type', 'general'),
                'estimated_volume': cost_info.get('volume_estimate', 0),
                'estimated_cost_usd': cost_info.get('estimated_cost_usd', 0),
                'estimated_pages': cost_info.get('estimated_pages', 0),
                'estimated_duration_minutes': cost_info.get('estimated_duration_minutes', 0),
                'validation_issues': cost_info.get('validation_issues', []),
                'validation_warnings': cost_info.get('validation_warnings', [])
            }
            
            json.dump(config_data, output, indent=2)
            
            if output != '-':
                console.print(f"[green]Configuration saved to {output.name}[/green]")
        
        except Exception as e:
            console.print(f"[red]Failed to generate configuration: {str(e)}[/red]")
            if ctx.obj.get('debug'):
                import traceback
                console.print(traceback.format_exc())
    
    asyncio.run(generate_config())


def main():
    """Main CLI entry point"""
    cli()


if __name__ == '__main__':
    main()