# ----------------------------------------------------------------------------
#  File:        demo.py
#  Project:     Celaya Solutions (Agent Orchestration)
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Demo script for running various agent demonstrations
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import argparse
import subprocess
import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("AgentDemo")

DEMO_TYPES = [
    "mock",
    "simulated",
    "directmsg",
    "full"
]

DEMO_DESCRIPTIONS = {
    "mock": "Run a basic mock test with simulated agent responses",
    "simulated": "Run a complete simulation of all 11 agents with customizable prompts",
    "directmsg": "Run a demonstration of direct/private messaging between agents",
    "full": "Run the full Celaya implementation with actual instances (requires Celaya binary)"
}

DEFAULT_PROMPTS = {
    "mock": "Let's discuss how to improve team communication.",
    "simulated": "Let's discuss the future of artificial intelligence and its impact on society.",
    "directmsg": "Let's discuss how to handle sensitive user data in AI systems.",
    "full": "What are the most important considerations for developing ethical AI systems?"
}

def show_demos():
    print("\n===== CELAYA AGENT DEMOS =====")
    print("Available demos:")
    for demo in DEMO_TYPES:
        print(f"  - {demo}: {DEMO_DESCRIPTIONS[demo]}")
    print("\nRun a demo by using: python demo.py --type <demo_type>")
    print("Example: python demo.py --type simulated")
    print("==========================\n")

def run_demo(demo_type, prompt=None, max_turns=None):
    """Run the specified demo type with optional customizations"""
    if demo_type not in DEMO_TYPES:
        logger.error(f"Unknown demo type: {demo_type}")
        show_demos()
        return False
    
    # Use default prompt if none provided
    if not prompt:
        prompt = DEFAULT_PROMPTS[demo_type]
    
    # Determine max turns if not specified
    if not max_turns:
        max_turns = 6 if demo_type == "mock" else 15
    
    logger.info(f"Running {demo_type} demo with prompt: {prompt}")
    
    # Prepare the command based on demo type
    cmd = []
    if demo_type == "mock":
        cmd = ["python", "example.py", "--mock"]
    elif demo_type == "simulated":
        cmd = ["python", "run_simulated.py", "--prompt", prompt, "--max-turns", str(max_turns)]
    elif demo_type == "directmsg":
        cmd = ["python", "direct_message_example.py", "--prompt", prompt, "--max-turns", str(max_turns)]
    elif demo_type == "full":
        # For the full implementation, we need to first check if Celaya binary exists
        import os
        celaya_path = os.path.join("..", "celaya")
        if not os.path.exists(celaya_path):
            logger.error("Celaya binary not found at '../celaya', cannot run full demo")
            logger.info("You can still run other demos that don't require the Celaya binary")
            return False
        
        # First set up the agents
        logger.info("Setting up Celaya instances for all agents...")
        setup_cmd = ["python", "setup_agents.py", "--celaya", celaya_path]
        subprocess.run(setup_cmd)
        
        # Then run the example with actual API
        cmd = ["python", "example.py", "--prompt", prompt, "--max-turns", str(max_turns)]
    
    # Run the chosen demo
    logger.info(f"Starting {demo_type} demo...")
    try:
        subprocess.run(cmd)
        logger.info(f"{demo_type} demo completed")
        return True
    except Exception as e:
        logger.error(f"Error running {demo_type} demo: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Celaya Agent Demo Runner")
    parser.add_argument("--type", choices=DEMO_TYPES, help="Type of demo to run")
    parser.add_argument("--prompt", help="Custom prompt to use for the demo")
    parser.add_argument("--max-turns", type=int, help="Maximum number of turns in the conversation")
    args = parser.parse_args()
    
    if not args.type:
        show_demos()
        return
    
    run_demo(args.type, args.prompt, args.max_turns)

if __name__ == "__main__":
    main() 