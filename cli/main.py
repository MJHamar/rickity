import click
from datetime import datetime
from client import HabitClient
from typing import Optional
import sys
from pathlib import Path

@click.group()
@click.option('--config', type=click.Path(exists=True), help='Path to config file')
@click.pass_context
def cli(ctx, config: Optional[str]):
    """Habit tracking CLI"""
    ctx.ensure_object(dict)
    ctx.obj['client'] = HabitClient(config)

@cli.command()
@click.pass_context
def list(ctx):
    """List all habits"""
    client = ctx.obj['client']
    habits = client.list_habits()
    
    if not habits:
        click.echo("No habits found")
        return
    
    for habit in habits:
        click.echo(f"{habit['id']}: {habit['name']} (every {habit['recurrence']})")

@cli.command()
@click.argument('name')
@click.argument('recurrence')
@click.pass_context
def create(ctx, name: str, recurrence: str):
    """Create a new habit
    
    NAME: Name of the habit
    RECURRENCE: Frequency (e.g., '24h' for daily, '7d' for weekly)
    """
    client = ctx.obj['client']
    habit = client.create_habit(name, recurrence)
    click.echo(f"Created habit: {habit['name']} (ID: {habit['id']})")

@cli.command()
@click.option('--date', help='Check habits due for specific date (YYYY-MM-DD)')
@click.pass_context
def due(ctx, date: Optional[str]):
    """Show habits due today or on a specific date"""
    client = ctx.obj['client']
    habits = client.get_due_habits(date)
    
    if not habits:
        click.echo("No habits due")
        return
    
    for habit_with_log in habits:
        habit = habit_with_log['habit']
        log = habit_with_log['latest_log']
        status = "✓" if log and log['completed'] else "⨯"
        click.echo(f"{status} {habit['name']} (ID: {habit['id']})")
        if log:
            click.echo(f"  Log ID: {log['id']}")

@cli.command()
@click.argument('log_id')
@click.pass_context
def complete(ctx, log_id: str):
    """Mark a habit as completed"""
    client = ctx.obj['client']
    if client.complete_habit(log_id):
        click.echo("Habit marked as completed")
    else:
        click.echo("Failed to mark habit as completed", err=True)

def main():
    cli(obj={})

if __name__ == '__main__':
    main() 