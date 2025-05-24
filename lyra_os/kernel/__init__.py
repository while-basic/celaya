# ----------------------------------------------------------------------------
#  File:        __init__.py
#  Project:     Celaya Solutions
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Lyra OS kernel and boot sequence
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

"""
Lyra OS kernel and boot sequence.

Provides the core functionality for booting and managing the Lyra OS.
"""

import asyncio
import logging
import os
import subprocess
import time
import yaml
from typing import Dict, List, Any, Optional, Set

from celaya_python.runtime.bus import Bus
from celaya_python.runtime.ticker import Ticker
from celaya_python.runtime.consensus import ConsensusManager, VoteType

# Import these later to avoid circular imports
# from lyra_os.kernel.keyring import Keyring
# from lyra_os.kernel.ledger import Ledger
# from lyra_os.kernel.animation import welcome

logger = logging.getLogger(__name__)

class KernelState:
    """Enum-like class for kernel states."""
    INITIALIZING = "initializing"
    BOOTING = "booting"
    CONSENSUS = "consensus"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"


class KernelService:
    """
    Lyra OS Kernel Service.
    
    Manages the lifecycle of the Lyra OS, including the boot sequence,
    agent management, and system services.
    """
    
    def __init__(self, config_path=None, tick_interval_ms=1000, debug=False):
        """
        Initialize a new kernel service.
        
        Args:
            config_path: Path to the configuration file
            tick_interval_ms: Tick interval in milliseconds
            debug: Enable debug logging
        """
        self.state = KernelState.INITIALIZING
        
        # Set up configuration
        if config_path is None:
            # Use the default configuration path relative to the installed package
            import os
            package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_path = os.path.join(package_dir, "conf", "bootstrap.yaml")
        else:
            self.config_path = config_path
        self.tick_interval = tick_interval_ms
        self.quorum_threshold = 0.66
        self.bootstrap = []
        self.bus = Bus()
        self.ticker = Ticker(tick_interval_ms, self.bus)
        self.consensus = ConsensusManager(self.bus, self.quorum_threshold)
        self.agent_processes = {}
        self.ready_agents: Set[str] = set()
        self.agent_pubkeys: Dict[str, str] = {}
        
        # The all_ready event is triggered when all required agents are ready
        self.all_ready = asyncio.Event()
        
        # Register handlers
        self.bus.subscribe("kernel", "global.bus")
        self.bus.register_handler("global.bus", self._handle_global_message)
        
        logger.info("Kernel service initialized")
    
    async def boot(self):
        """Boot the Lyra OS kernel."""
        logger.info("Booting Lyra OS kernel...")
        
        # Import here to avoid circular imports
        from lyra_os.kernel.animation import welcome
        
        # Change state to booting
        self.state = KernelState.BOOTING
        
        # Load configuration
        try:
            await self._load_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
            raise
        
        # Create queues for all agents
        for agent in self.bootstrap:
            agent_id = agent["id"]
            self.bus.create_private_queue(agent_id)
            self.bus.subscribe(agent_id, f"agent.{agent_id}.in")
        
        # Start the consensus manager
        await self.consensus.start()
        
        # Start the ticker
        await self.ticker.start()
        
        # Launch agents
        await self._launch_agents()
        
        # Wait for all agents to be ready
        await self.wait_for_all_ready()
        
        # Start boot consensus
        self.state = KernelState.CONSENSUS
        proposal_id = self.propose_boot_consensus()
        await self.await_consensus(proposal_id)
        
        # Display welcome animation
        await welcome()
        
        # Change state to running
        self.state = KernelState.RUNNING
        logger.info("Lyra OS kernel is now running")
    
    async def shutdown(self):
        """Shutdown the Lyra OS kernel."""
        self.state = KernelState.SHUTTING_DOWN
        
        # Stop the ticker
        await self.ticker.stop()
        
        # Stop the consensus manager
        await self.consensus.stop()
        
        # Terminate agent processes
        for agent_id, process in self.agent_processes.items():
            if process.returncode is None:
                try:
                    process.terminate()
                    logger.info(f"Terminated agent process: {agent_id}")
                except Exception as e:
                    logger.warning(f"Error terminating agent process {agent_id}: {e}")
        
        logger.info("Lyra OS kernel has been shut down")
    
    async def _load_config(self):
        """Load the bootstrap configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            if not config or not isinstance(config, dict):
                raise ValueError("Invalid configuration format")
                
            self.bootstrap = config.get("agents", [])
            
            # Validate agent configurations
            for i, agent in enumerate(self.bootstrap):
                if not isinstance(agent, dict):
                    raise ValueError(f"Invalid agent configuration at index {i}")
                    
                if "id" not in agent:
                    agent["id"] = f"agent_{i}"
                    
                if "model" not in agent:
                    raise ValueError(f"Missing 'model' for agent {agent['id']}")
            
            logger.info(f"Loaded configuration with {len(self.bootstrap)} agents")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
            raise
    
    async def _launch_agents(self):
        """Launch agent processes."""
        for agent in self.bootstrap:
            agent_id = agent["id"]
            model = agent["model"]
            
            try:
                # Launch the agent process
                process = await asyncio.create_subprocess_exec(
                    "celaya_python", "run", model,
                    "--agent-id", agent_id,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                self.agent_processes[agent_id] = process
                
                # Start a task to monitor the process output
                asyncio.create_task(self._monitor_agent_output(agent_id, process))
                
                logger.info(f"Launched agent {agent_id} with model {model}")
            except Exception as e:
                logger.error(f"Error launching agent {agent_id}: {e}", exc_info=True)
    
    async def _monitor_agent_output(self, agent_id: str, process: asyncio.subprocess.Process):
        """
        Monitor agent process output.
        
        Args:
            agent_id: The ID of the agent
            process: The agent process
        """
        try:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                    
                line_str = line.decode('utf-8').strip()
                logger.debug(f"Agent {agent_id} output: {line_str}")
                
                # Check if the agent is ready
                if "READY" in line_str:
                    # Extract public key if available
                    parts = line_str.split()
                    pubkey = None
                    for i, part in enumerate(parts):
                        if part == "READY" and i < len(parts) - 1:
                            pubkey = parts[i + 1]
                            break
                    
                    self._mark_agent_ready(agent_id, pubkey)
        except Exception as e:
            logger.error(f"Error monitoring agent {agent_id} output: {e}", exc_info=True)
        finally:
            # Check if the process has exited
            if process.returncode is None:
                try:
                    await process.wait()
                except Exception:
                    pass
                    
            logger.info(f"Agent {agent_id} process exited with code {process.returncode}")
    
    async def _handle_global_message(self, message):
        """
        Handle messages on the global bus.
        
        Args:
            message: The message to handle
        """
        try:
            if not hasattr(message, 'payload'):
                return
                
            payload = message.payload
            
            # Handle ready messages
            if isinstance(payload, dict) and payload.get("type") == "READY":
                agent_id = payload.get("agent_id") or message.sender_id
                pubkey = payload.get("pubkey")
                
                if agent_id:
                    self._mark_agent_ready(agent_id, pubkey)
        except Exception as e:
            logger.error(f"Error handling global message: {e}", exc_info=True)
    
    def _mark_agent_ready(self, agent_id: str, pubkey: Optional[str] = None):
        """
        Mark an agent as ready.
        
        Args:
            agent_id: The ID of the agent
            pubkey: Optional public key for the agent
        """
        if agent_id in self.ready_agents:
            return
            
        self.ready_agents.add(agent_id)
        
        if pubkey:
            self.agent_pubkeys[agent_id] = pubkey
            
        logger.info(f"Agent {agent_id} is ready" + (f" with pubkey: {pubkey}" if pubkey else ""))
        
        # Check if all required agents are ready
        self._check_all_agents_ready()
    
    def _check_all_agents_ready(self):
        """Check if all required agents are ready."""
        required_agents = {agent["id"] for agent in self.bootstrap if agent.get("required", True)}
        
        if required_agents.issubset(self.ready_agents):
            logger.info("All required agents are ready")
            self.all_ready.set()
    
    async def wait_for_all_ready(self):
        """Wait until all required agents are ready."""
        await self.all_ready.wait()
    
    def propose_boot_consensus(self) -> str:
        """
        Propose a boot consensus.
        
        Returns:
            str: The ID of the created proposal
        """
        logger.info("Proposing boot consensus")
        
        # Create a boot consensus proposal
        proposal_id = self.consensus.create_proposal(
            proposal_type="BOOT_CONSENSUS",
            content={
                "version": "1.0.0",
                "timestamp": time.time(),
                "agents": list(self.ready_agents)
            },
            proposer_id="kernel",
            metadata={
                "agent_pubkeys": self.agent_pubkeys
            }
        )
        
        return proposal_id
    
    async def await_consensus(self, proposal_id: str, timeout: float = 30.0) -> bool:
        """
        Wait for consensus on a proposal.
        
        Args:
            proposal_id: The ID of the proposal to wait for
            timeout: Timeout in seconds
            
        Returns:
            bool: True if consensus was reached, False if timed out
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check if the proposal exists and has a status
            if proposal_id in self.consensus.proposals:
                status = self.consensus.proposals[proposal_id].status
                
                if status.name in ("APPROVED", "REJECTED"):
                    return status.name == "APPROVED"
            
            # Wait a bit before checking again
            await asyncio.sleep(0.5)
        
        logger.warning(f"Timed out waiting for consensus on proposal {proposal_id}")
        return False 