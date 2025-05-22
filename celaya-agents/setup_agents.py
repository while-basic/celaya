# ----------------------------------------------------------------------------
#  File:        setup_agents.py
#  Project:     Celaya Solutions (Agent Orchestration)
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Utility script to set up and manage Celaya instances for each agent
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import os
import json
import argparse
import subprocess
import time
import signal
import logging
import sys
import shutil
import psutil
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CelayaSetup")

# Default paths
DEFAULT_CONFIG_PATH = "agent_config.json"
DEFAULT_CELAYA_PATH = "../celaya"  # Assuming Celaya is in the parent directory
DEFAULT_MODELS_DIR = "./models"
DEFAULT_LOGS_DIR = "./logs"


def check_celaya_exists(celaya_path: str) -> bool:
    """Check if the Celaya binary exists at the specified path"""
    return os.path.isfile(celaya_path) and os.access(celaya_path, os.X_OK)


def create_directory(dir_path: str) -> None:
    """Create directory if it doesn't exist"""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")


def load_config(config_path: str) -> Dict:
    """Load agent configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        sys.exit(1)


def start_celaya_instance(
    celaya_path: str,
    agent_name: str,
    port: int,
    models_dir: str,
    log_path: str
) -> subprocess.Popen:
    """Start a Celaya instance for an agent"""
    env = os.environ.copy()
    env["CELAYA_HOST"] = f"0.0.0.0:{port}"
    
    # Create full models directory path for this agent
    agent_models_dir = os.path.join(models_dir, agent_name.lower())
    create_directory(agent_models_dir)
    
    # Set Celaya environment variables
    env["CELAYA_MODELS"] = agent_models_dir
    
    # Open log file
    log_file = open(log_path, 'w')
    
    # Start Celaya process
    process = subprocess.Popen(
        [celaya_path, "serve"],
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True  # Detach from parent process
    )
    
    logger.info(f"Started Celaya for {agent_name} on port {port}, PID: {process.pid}")
    return process


def stop_celaya_instance(process: subprocess.Popen) -> None:
    """Stop a Celaya instance gracefully"""
    if process and process.poll() is None:
        try:
            # Try to terminate process gracefully
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't terminate
            process.kill()
            process.wait()


def check_port_availability(ports: List[int]) -> List[int]:
    """Check if ports are available"""
    unavailable_ports = []
    
    for port in ports:
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                unavailable_ports.append(port)
                break
    
    return unavailable_ports


def start_all_agents(
    config: Dict,
    celaya_path: str,
    models_dir: str,
    logs_dir: str
) -> Dict[str, subprocess.Popen]:
    """Start all agent instances based on configuration"""
    processes = {}
    
    # Extract all ports from agent URLs
    ports = []
    for agent in config["agents"]:
        url = agent["url"]
        if ":" in url:
            port = int(url.split(":")[-1])
            ports.append(port)
    
    # Check port availability
    unavailable_ports = check_port_availability(ports)
    if unavailable_ports:
        logger.error(f"Ports already in use: {unavailable_ports}")
        sys.exit(1)
    
    # Start each agent
    for agent in config["agents"]:
        agent_name = agent["name"]
        url = agent["url"]
        
        # Extract port from URL
        if ":" in url:
            port = int(url.split(":")[-1])
        else:
            logger.error(f"Invalid URL format for agent {agent_name}: {url}")
            continue
        
        # Create log file path
        log_path = os.path.join(logs_dir, f"{agent_name.lower()}.log")
        
        # Start Celaya instance
        process = start_celaya_instance(
            celaya_path=celaya_path,
            agent_name=agent_name,
            port=port,
            models_dir=models_dir,
            log_path=log_path
        )
        
        processes[agent_name] = process
        
        # Short delay to prevent resource contention
        time.sleep(1)
    
    return processes


def stop_all_agents(processes: Dict[str, subprocess.Popen]) -> None:
    """Stop all running agent instances"""
    for agent_name, process in processes.items():
        logger.info(f"Stopping {agent_name}...")
        stop_celaya_instance(process)
    
    logger.info("All agents stopped")


def pull_models(config: Dict, celaya_path: str) -> None:
    """Pull required models for agents"""
    models = set()
    
    # Collect all required models
    for agent in config["agents"]:
        model = agent.get("model", config["settings"].get("default_model", "llama3"))
        models.add(model)
    
    # Pull each model
    for model in models:
        logger.info(f"Pulling model: {model}")
        try:
            subprocess.run(
                [celaya_path, "pull", model],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"Successfully pulled {model}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to pull {model}: {e.stderr.decode()}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Celaya Agent Setup Utility")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to agent configuration file")
    parser.add_argument("--celaya", default=DEFAULT_CELAYA_PATH, help="Path to Celaya binary")
    parser.add_argument("--models-dir", default=DEFAULT_MODELS_DIR, help="Directory for agent models")
    parser.add_argument("--logs-dir", default=DEFAULT_LOGS_DIR, help="Directory for agent logs")
    parser.add_argument("--pull-models", action="store_true", help="Pull required models before starting")
    parser.add_argument("--stop", action="store_true", help="Stop all running agents")
    
    args = parser.parse_args()
    
    # Check if Celaya exists
    if not check_celaya_exists(args.celaya):
        logger.error(f"Celaya binary not found at {args.celaya}")
        sys.exit(1)
    
    # Create necessary directories
    create_directory(args.models_dir)
    create_directory(args.logs_dir)
    
    # Load configuration
    config = load_config(args.config)
    
    if args.pull_models:
        pull_models(config, args.celaya)
    
    if args.stop:
        # This is a limited implementation since we don't have access to the PIDs
        # of previously started processes. In a real implementation, you'd want to
        # save PIDs to a file or use a more robust process management approach.
        logger.warning("Can only stop processes started in this session")
        return
    
    try:
        # Start all agents
        processes = start_all_agents(
            config=config,
            celaya_path=args.celaya,
            models_dir=args.models_dir,
            logs_dir=args.logs_dir
        )
        
        logger.info(f"Started {len(processes)} agent instances")
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Interrupt received, shutting down...")
        finally:
            stop_all_agents(processes)
    
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 