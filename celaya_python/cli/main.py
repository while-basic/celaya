# ----------------------------------------------------------------------------
#  File:        main.py
#  Project:     Celaya Solutions
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: CLI entry point for the Celaya runtime
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

"""
Command-line interface for the Celaya runtime.

Provides commands for interacting with the Celaya runtime, including
booting the Lyra OS kernel and managing agents.
"""

import argparse
import asyncio
import importlib.metadata
import logging
import os
import sys
from typing import List, Dict, Any, Optional

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def parse_args(args: List[str]) -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Celaya CLI - Multi-agent consensus runtime"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Boot command
    boot_parser = subparsers.add_parser("boot", help="Boot the Lyra OS kernel")
    boot_parser.add_argument(
        "--config", "-c",
        help="Path to configuration file",
        default=os.environ.get("LYRA_CONFIG", "lyra_os/conf/bootstrap.yaml")
    )
    boot_parser.add_argument(
        "--interval", "-i",
        help="Tick interval in milliseconds",
        type=int,
        default=os.environ.get("LYRA_TICK_INTERVAL", "1000")
    )
    boot_parser.add_argument(
        "--quorum", "-q",
        help="Quorum threshold (0.0-1.0)",
        type=float,
        default=os.environ.get("LYRA_QUORUM_THRESHOLD", "0.66")
    )
    boot_parser.add_argument(
        "--debug", "-d",
        help="Enable debug logging",
        action="store_true"
    )
    
    # Run command (existing Celaya command)
    run_parser = subparsers.add_parser("run", help="Run a model")
    run_parser.add_argument(
        "model",
        help="Model to run"
    )
    run_parser.add_argument(
        "--agent-id",
        help="Agent identifier",
        default=None
    )
    
    # Add other existing Celaya commands here
    # ...
    
    return parser.parse_args(args)

async def boot_lyra_os(config_path=None, tick_interval=1000, quorum_threshold=0.66, debug=False):
    """
    Boot the Lyra OS kernel.
    
    Args:
        config_path: Path to the configuration file
        tick_interval: Tick interval in milliseconds
        quorum_threshold: Quorum threshold (0.0-1.0)
        debug: Enable debug logging
    """
    # Set up logging
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    
    logger.info("Booting Lyra OS kernel...")
    
    try:
        # Import the kernel service
        from lyra_os.kernel import KernelService
        
        # Initialize the kernel
        kernel = KernelService(
            config_path=config_path,
            tick_interval_ms=tick_interval,
            debug=debug
        )
        
        # Boot the kernel
        await kernel.boot()
        
        # Keep the kernel running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Lyra OS kernel stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Error booting Lyra OS kernel: {e}")
        raise
        
    return 0

def discover_agents() -> Dict[str, Any]:
    """
    Discover agents via entry points.
    
    Returns:
        Dictionary mapping agent names to agent classes
    """
    agents = {}
    
    try:
        # Look for entry points in the 'celaya.agents' group
        for entry_point in importlib.metadata.entry_points(group='celaya.agents'):
            try:
                agent_class = entry_point.load()
                agents[entry_point.name] = agent_class
                logger.debug(f"Discovered agent: {entry_point.name}")
            except Exception as e:
                logger.warning(f"Failed to load agent {entry_point.name}: {e}")
    except Exception as e:
        logger.warning(f"Error discovering agents: {e}")
    
    return agents

def main(args: Optional[List[str]] = None):
    """
    Main entry point for the CLI.
    
    Args:
        args: Command-line arguments
    """
    if args is None:
        args = sys.argv[1:]
        
    parsed_args = parse_args(args)
    
    # Set logging level
    if getattr(parsed_args, 'debug', False):
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle commands
    if parsed_args.command == "boot":
        # Boot the Lyra OS kernel
        asyncio.run(boot_lyra_os(
            config_path=parsed_args.config,
            tick_interval=int(parsed_args.interval),
            quorum_threshold=float(parsed_args.quorum),
            debug=parsed_args.debug
        ))
    elif parsed_args.command == "run":
        # This would call the existing Celaya runtime to run a model
        # For now, we'll just print a message
        print(f"Running model: {parsed_args.model}")
        if parsed_args.agent_id:
            print(f"Agent ID: {parsed_args.agent_id}")
    else:
        # No command specified, show help
        parse_args(["--help"])

if __name__ == "__main__":
    main() 