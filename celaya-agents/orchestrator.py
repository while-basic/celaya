# ----------------------------------------------------------------------------
#  File:        orchestrator.py
#  Project:     Celaya Solutions (Agent Orchestration)
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Main orchestrator for managing agent communication via Celaya API
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import asyncio
from asyncio import Queue
import requests
import json
import time
import logging
import sys
import argparse
from typing import List, Dict, Tuple, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CelayaOrchestrator")

class CelayaAgent:
    """Represents an individual agent powered by Celaya API"""
    
    def __init__(self, name: str, url: str, model: str = "llama3", system_prompt: str = None, role: str = None):
        self.name = name
        self.url = url
        self.model = model
        self.system_prompt = system_prompt
        self.role = role
        self.conversation_history: List[Dict[str, Any]] = []
        self.private_queue: Queue = Queue()
        self.logger = logging.getLogger(f"Agent:{name}")
    
    async def speak(self, prompt: str, include_history: bool = True) -> str:
        """Generate a response from the agent using the Celaya API"""
        try:
            # Create effective prompt with system prompt and role
            effective_prompt = prompt
            
            if self.system_prompt and not include_history:
                effective_prompt = f"{self.system_prompt}\n\n{prompt}"
            
            # Create message payload
            payload = {
                "model": self.model,
                "prompt": effective_prompt,
                "system": self.system_prompt if include_history else None,
                "stream": False,
                "context": self._prepare_context() if include_history else []
            }
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            self.logger.debug(f"Sending request to {self.url}/api/generate")
            response = requests.post(f"{self.url}/api/generate", json=payload, timeout=60)
            
            if response.status_code != 200:
                self.logger.error(f"Error from API: {response.status_code} - {response.text}")
                return f"[Error communicating with {self.name}]"
            
            result = response.json().get('response', '')
            
            # Update conversation history
            if include_history:
                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "assistant", "content": result})
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in speak: {str(e)}")
            return f"[Error: {self.name} encountered an issue: {str(e)}]"
    
    def _prepare_context(self) -> List[int]:
        """Prepare conversation context for the API call"""
        # This is a placeholder for the actual context preparation
        # In a real implementation, this would convert conversation history to token IDs
        return []

    async def receive_message(self, sender: str, message: str) -> None:
        """Receive a message from another agent into the private queue"""
        await self.private_queue.put((sender, message))
        self.logger.debug(f"Received private message from {sender}")

    async def check_messages(self) -> List[Tuple[str, str]]:
        """Check for any pending messages in the private queue"""
        messages = []
        while not self.private_queue.empty():
            sender, message = await self.private_queue.get()
            messages.append((sender, message))
        return messages


class Orchestrator:
    """Central orchestrator for managing agent communication"""
    
    def __init__(self, agents: List[CelayaAgent], max_turns: int = 20):
        self.agents = agents
        self.turn_index = 0
        self.max_turns = max_turns
        self.central_queue = Queue()
        self.conversation_log: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("Orchestrator")
        self.running = False
        
        # Agent lookup by name
        self.agent_map = {agent.name: agent for agent in agents}
    
    async def orchestrate(self, initial_prompt: str) -> None:
        """Run the orchestration process with an initial prompt"""
        prompt = initial_prompt
        self.running = True
        turn_count = 0
        
        # Log the initial prompt
        self.conversation_log.append({
            "turn": turn_count,
            "agent": "User",
            "message": initial_prompt,
            "timestamp": time.time()
        })
        
        self.logger.info(f"Starting orchestration with initial prompt: {initial_prompt}")
        
        try:
            while self.running and turn_count < self.max_turns:
                current_agent = self.agents[self.turn_index % len(self.agents)]
                turn_count += 1
                
                self.logger.info(f"Turn {turn_count}/{self.max_turns}: {current_agent.name}'s turn")
                
                # First, check for any private messages
                private_messages = await current_agent.check_messages()
                if private_messages:
                    context = "\n".join([f"{sender}: {message}" for sender, message in private_messages])
                    prompt = f"{prompt}\n\nMessages from other agents:\n{context}"
                
                # Generate response
                response = await current_agent.speak(prompt)
                
                # Log the response
                self.logger.info(f"{current_agent.name} says: {response}")
                self.conversation_log.append({
                    "turn": turn_count,
                    "agent": current_agent.name,
                    "message": response,
                    "timestamp": time.time()
                })
                
                # Broadcast response to central queue for all agents to hear
                await self.central_queue.put((current_agent.name, response))
                
                # Process the central queue and deliver messages to all agents except the sender
                await self._process_central_queue()
                
                # Update prompt for next agent
                prompt = f"Previous message from {current_agent.name}: {response}\nYour turn to respond."
                
                # Move to next agent
                self.turn_index += 1
                
                # Short delay between turns
                await asyncio.sleep(0.5)
                
        except KeyboardInterrupt:
            self.logger.info("Orchestration interrupted by user")
        except Exception as e:
            self.logger.error(f"Error in orchestration: {str(e)}")
        finally:
            self.running = False
            self.save_conversation_log()
    
    async def _process_central_queue(self) -> None:
        """Process the central queue and deliver messages to agents"""
        if self.central_queue.empty():
            return
            
        sender, message = await self.central_queue.get()
        
        # Distribute the message to all agents except the sender
        for agent in self.agents:
            if agent.name != sender:
                await agent.receive_message(sender, message)
    
    def save_conversation_log(self, filename: str = "conversation_log.json") -> None:
        """Save the conversation log to a file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.conversation_log, f, indent=2)
            self.logger.info(f"Conversation log saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving conversation log: {str(e)}")

    def stop(self) -> None:
        """Stop the orchestration process"""
        self.running = False
        self.logger.info("Stopping orchestration")


async def direct_message(sender: CelayaAgent, recipient_name: str, message: str, orchestrator: Orchestrator) -> bool:
    """Send a direct message from one agent to another"""
    if recipient_name not in orchestrator.agent_map:
        return False
        
    recipient = orchestrator.agent_map[recipient_name]
    await recipient.receive_message(sender.name, message)
    return True


async def main():
    """Main entry point for the orchestrator"""
    parser = argparse.ArgumentParser(description="Celaya Agent Orchestrator")
    parser.add_argument("--config", default="agent_config.json", help="Path to agent configuration file")
    parser.add_argument("--prompt", default="Begin by introducing yourself.", help="Initial prompt to start the conversation")
    parser.add_argument("--max-turns", type=int, default=20, help="Maximum number of turns before stopping")
    args = parser.parse_args()
    
    try:
        # Load agent configuration
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        # Create agents
        agents = []
        for agent_config in config["agents"]:
            agent = CelayaAgent(
                name=agent_config["name"],
                url=agent_config["url"],
                model=agent_config.get("model", "llama3"),
                system_prompt=agent_config.get("system_prompt"),
                role=agent_config.get("role")
            )
            agents.append(agent)
            logger.info(f"Created agent: {agent.name} at {agent.url}")
        
        # Create orchestrator
        orchestrator = Orchestrator(agents, max_turns=args.max_turns)
        
        # Run orchestration
        await orchestrator.orchestrate(args.prompt)
        
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 