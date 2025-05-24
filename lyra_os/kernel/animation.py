# ----------------------------------------------------------------------------
#  File:        animation.py
#  Project:     Celaya Solutions
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Terminal animations for Lyra OS using Rich
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

"""
Animation module for Lyra OS.

Provides terminal animations and visual effects using the Rich library.
"""

import asyncio
import logging
import random
import time
from itertools import cycle
from typing import List, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.align import Align
    from rich.text import Text
    from rich.live import Live
    from rich import box
except ImportError:
    logging.warning("Rich library not found. Animations will be disabled.")
    
    # Create dummy classes for compatibility
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
    
    class Panel:
        def __init__(self, *args, **kwargs):
            self.content = args[0] if args else ""
            
    class Align:
        def __init__(self, *args, **kwargs):
            self.content = args[0] if args else ""
            
    class Text:
        def __init__(self, *args, **kwargs):
            self.content = args[0] if args else ""
            
    class Live:
        def __init__(self, *args, **kwargs):
            pass
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args, **kwargs):
            pass
            
        def update(self, *args, **kwargs):
            pass
            
    class box:
        SQUARE = None

logger = logging.getLogger(__name__)

async def welcome(console: Optional[Console] = None) -> None:
    """
    Display the welcome animation.
    
    Args:
        console: Rich console instance or None to create a new one
    """
    if console is None:
        console = Console()
    
    try:
        await _orb_convergence(console)
        await _welcome_text(console)
    except Exception as e:
        logger.error(f"Error in welcome animation: {e}", exc_info=True)
        console.print("[bold cyan]Welcome to Lyra OS[/]")

async def _orb_convergence(console: Console) -> None:
    """
    Display the orb convergence animation.
    
    Args:
        console: Rich console instance
    """
    swirl = cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
    
    def _make_panel(char: str, iteration: int) -> Panel:
        width = min(30, max(10, iteration))
        padding = max(0, 15 - iteration // 2)
        content = char * width
        
        # Add some colors based on the iteration
        if iteration < 12:
            style = "bold blue"
        elif iteration < 24:
            style = "bold cyan"
        else:
            style = "bold magenta"
            
        text = Text(content, style=style)
        aligned = Align.center(text)
        
        return Panel(
            aligned,
            box=box.SQUARE,
            padding=(1, padding),
            border_style=style
        )
    
    with Live(refresh_per_second=12, console=console) as live:
        for i in range(36):
            live.update(_make_panel(next(swirl), i))
            await asyncio.sleep(0.08)

async def _welcome_text(console: Console) -> None:
    """
    Display the welcome text animation.
    
    Args:
        console: Rich console instance
    """
    text = "[bold magenta]★  Welcome to C-Suite  ★[/]"
    
    # Fade in effect
    for i in range(1, 11):
        opacity = i / 10
        color_val = int(255 * opacity)
        styled_text = f"[bold rgb({color_val},0,{color_val})]★  Welcome to C-Suite  ★[/]"
        console.print("\n" + styled_text + "\n", justify="center")
        await asyncio.sleep(0.05)
        console.clear()
    
    # Final text with blinking effect
    console.print("\n[bold magenta blink]★  Welcome to C-Suite  ★[/]\n", justify="center")

async def boot_sequence(console: Optional[Console] = None) -> None:
    """
    Display the boot sequence animation.
    
    Args:
        console: Rich console instance or None to create a new one
    """
    if console is None:
        console = Console()
    
    boot_steps = [
        ("Initializing Lyra OS kernel", 0.5),
        ("Loading system components", 0.7),
        ("Establishing agent connections", 1.0),
        ("Verifying cryptographic signatures", 0.8),
        ("Synchronizing consensus mechanisms", 1.2),
        ("Preparing global message bus", 0.6),
        ("Starting ticker service", 0.4),
        ("Launching agent runtimes", 1.5)
    ]
    
    for step, duration in boot_steps:
        with console.status(f"[bold blue]{step}[/]", spinner="dots"):
            await asyncio.sleep(duration)
        console.print(f"[bold green]✓[/] {step}")
        
    console.print("\n[bold cyan]Boot sequence complete[/]\n")

async def display_consensus_animation(console: Optional[Console] = None) -> None:
    """
    Display the consensus animation.
    
    Args:
        console: Rich console instance or None to create a new one
    """
    if console is None:
        console = Console()
    
    console.print("[bold cyan]Initiating consensus protocol[/]")
    
    # Simulate agents voting
    agents = ["Strategist", "Analyst", "Engineer", "Operator", "Coordinator"]
    votes = []
    
    with Live(console=console, refresh_per_second=4) as live:
        for i, agent in enumerate(agents):
            votes.append(agent)
            percentage = int((i + 1) / len(agents) * 100)
            
            panel = Panel(
                f"Consensus: {percentage}% complete\nVotes received from: {', '.join(votes)}",
                title="Consensus Status",
                border_style="green",
                padding=(1, 2)
            )
            
            live.update(panel)
            await asyncio.sleep(random.uniform(0.5, 1.5))
    
    console.print("[bold green]Consensus achieved![/]")

if __name__ == "__main__":
    # Test the animations
    async def test():
        console = Console()
        await boot_sequence(console)
        await welcome(console)
        await display_consensus_animation(console)
    
    asyncio.run(test()) 