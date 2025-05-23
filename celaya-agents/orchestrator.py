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
import heapq
from collections import deque
from typing import List, Dict, Tuple, Any, Optional, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CelayaOrchestrator")

# Round-Robin constants
MIN_SLICE = 1.5          # seconds
MAX_TURN_MS = 5000       # ms
PREEMPT_THRESHOLD = 90   # interrupt score
QUORUM = 0.66            # 66% for consensus
MAX_INTERRUPT_DEPTH = 3  # maximum depth of interrupts before freezing
INTERRUPT_KEYWORDS = ["urgent", "critical", "emergency", "important", "!!"]

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
        self.reputation = 1.0  # Agent's reputation score (0.0 to 1.0)
        self.response_times: List[float] = []  # Track response times
    
    async def speak(self, prompt: str, include_history: bool = True, orchestrator = None) -> str:
        """Generate a response from the agent using the Celaya API"""
        try:
            start_time = time.time()
            
            # Check for urgent keywords and raise interrupt if found
            if orchestrator and any(keyword in prompt.lower() for keyword in INTERRUPT_KEYWORDS):
                priority = 95  # High priority for detected urgent keywords
                await orchestrator.request_interrupt(self, priority, prompt)
            
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
                if orchestrator:
                    orchestrator.adjust_reputation(self, -0.1)  # Decrease reputation on error
                return f"[Error communicating with {self.name}]"
            
            result = response.json().get('response', '')
            
            # Update conversation history
            if include_history:
                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "assistant", "content": result})
            
            # Track response time and update reputation
            response_time = time.time() - start_time
            self.response_times.append(response_time)
            
            # Adjust reputation based on response time
            if orchestrator and response_time > (MAX_TURN_MS / 1000):
                orchestrator.adjust_reputation(self, -0.05)  # Slight decrease for slow responses
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in speak: {str(e)}")
            if orchestrator:
                orchestrator.adjust_reputation(self, -0.1)  # Decrease reputation on error
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
        
    async def request_handoff(self, target_agent_name: str, payload: str, orchestrator) -> bool:
        """Request to hand off the turn to another agent"""
        return await orchestrator.request_handoff(self, target_agent_name, payload)
        
    async def emit_complete(self, orchestrator) -> None:
        """Signal that the agent has completed its work for this turn"""
        await orchestrator.handle_complete(self)
        
    async def emit_error(self, details: str, orchestrator) -> None:
        """Signal that the agent has encountered an error"""
        await orchestrator.handle_error(self, details)


class Orchestrator:
    """Central orchestrator for managing agent communication"""
    
    def __init__(self, agents: List[CelayaAgent], max_turns: int = 20):
        self.agents = agents
        self.max_turns = max_turns
        self.central_queue = Queue()
        self.conversation_log: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("Orchestrator")
        self.running = False
        
        # Agent lookup by name
        self.agent_map = {agent.name: agent for agent in agents}
        
        # Round-Robin Scheduler (Layer 1)
        self.turn_queue = deque(agents)
        self.token_holder = None
        
        # Interrupt Protocol (Layer 2)
        self.interrupt_heap: List[Tuple[int, float, CelayaAgent, str]] = []
        self.interrupt_depth = 0
        self.paused_agents: deque = deque()
        
        # Arbitration & Recovery (Layer 3)
        self.timeout_count: Dict[str, int] = {agent.name: 0 for agent in agents}
        self.recent_errors: Dict[str, int] = {agent.name: 0 for agent in agents}
        self.consensus_in_progress = False
        self.consensus_votes: Dict[str, Set[str]] = {}  # proposal -> set of agent names
        self.leader = None
    
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
        
        # Initialize the token holder
        if self.turn_queue:
            self.token_holder = self.turn_queue.popleft()
            self.turn_queue.append(self.token_holder)  # Add back to end of queue
        
        try:
            while self.running and turn_count < self.max_turns:
                turn_count += 1
                current_agent = self.token_holder
                slice_start = time.time()
                
                self.logger.info(f"Turn {turn_count}/{self.max_turns}: {current_agent.name}'s turn")
                
                # Check for interrupts that qualify for preemption
                interrupt_handler = await self._check_interrupts(slice_start)
                if interrupt_handler:
                    # Handle the interrupt
                    self.logger.info(f"Interrupt from {interrupt_handler.name} being processed")
                    current_agent = interrupt_handler  # Set the interrupter as current agent
                
                # First, check for any private messages
                private_messages = await current_agent.check_messages()
                if private_messages:
                    context = "\n".join([f"{sender}: {message}" for sender, message in private_messages])
                    prompt = f"{prompt}\n\nMessages from other agents:\n{context}"
                
                # Generate response with timeout protection
                try:
                    response_task = asyncio.create_task(current_agent.speak(prompt, orchestrator=self))
                    response = await asyncio.wait_for(response_task, timeout=MAX_TURN_MS/1000)
                    
                    # Reset timeout count on successful response
                    self.timeout_count[current_agent.name] = 0
                    
                except asyncio.TimeoutError:
                    self.logger.warning(f"{current_agent.name} timed out")
                    self.timeout_count[current_agent.name] += 1
                    self.adjust_reputation(current_agent, -0.2)  # More significant reputation hit for timeout
                    
                    # Use a placeholder response
                    response = f"[{current_agent.name} timed out and did not respond in time]"
                    
                    # Check if we should elect a leader due to repeated timeouts
                    if self.timeout_count[current_agent.name] >= 3:
                        await self._elect_leader()
                
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
                
                # Advance the token to the next agent
                await self._advance_token()
                
                # Short delay between turns
                await asyncio.sleep(0.5)
                
                # Check for livelock (too many interrupts)
                if self.interrupt_depth > MAX_INTERRUPT_DEPTH:
                    self.logger.warning("Interrupt depth exceeds maximum, freezing interrupts for one cycle")
                    # Clear the interrupt heap for one full cycle
                    self.interrupt_heap = []
                    self.interrupt_depth = 0
                
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
    
    async def _check_interrupts(self, slice_start: float) -> Optional[CelayaAgent]:
        """Check for interrupts and determine if we should handle one"""
        if not self.interrupt_heap:
            return None
            
        slice_elapsed = time.time() - slice_start
        top_priority = -self.interrupt_heap[0][0]  # Highest priority (negated for min-heap)
        
        if (slice_elapsed >= MIN_SLICE or top_priority >= PREEMPT_THRESHOLD):
            # Conditions met for handling an interrupt
            self.interrupt_depth += 1
            
            # Save current token holder to be resumed later
            if self.token_holder:
                self.paused_agents.appendleft(self.token_holder)
                
            # Get the highest priority interrupt
            _, _, agent, _ = heapq.heappop(self.interrupt_heap)
            self.token_holder = agent
            
            return agent
            
        return None
        
    async def _advance_token(self) -> None:
        """Advance the token to the next agent"""
        # First check if we have paused agents to resume
        if self.paused_agents:
            self.token_holder = self.paused_agents.popleft()
            self.interrupt_depth -= 1
        else:
            # Normal round-robin advancement
            if self.turn_queue:
                self.token_holder = self.turn_queue.popleft()
                self.turn_queue.append(self.token_holder)  # Add back to end for next rotation
    
    async def request_interrupt(self, agent: CelayaAgent, priority: int, payload: str) -> None:
        """Request an interrupt with priority"""
        # Adjust priority based on agent reputation
        effective_priority = priority * (0.5 + agent.reputation/2)
        self.logger.info(f"{agent.name} requested interrupt with priority {priority} (effective: {effective_priority:.2f})")
        
        # Add to interrupt heap (negate priority for min-heap)
        heapq.heappush(self.interrupt_heap, (-effective_priority, time.time(), agent, payload))
    
    async def request_handoff(self, sender: CelayaAgent, target_agent_name: str, payload: str) -> bool:
        """Handle a handoff request from one agent to another"""
        if target_agent_name not in self.agent_map:
            return False
            
        target_agent = self.agent_map[target_agent_name]
        self.logger.info(f"{sender.name} is handing off to {target_agent_name}")
        
        # If sender is current token holder, transfer token
        if self.token_holder == sender:
            self.token_holder = target_agent
            
            # Update the turn queue
            if target_agent in self.turn_queue:
                self.turn_queue.remove(target_agent)
            self.turn_queue.appendleft(target_agent)
            
        # Deliver the handoff message
        await target_agent.receive_message(sender.name, f"[HANDOFF] {payload}")
        return True
        
    async def handle_complete(self, agent: CelayaAgent) -> None:
        """Handle an agent signaling completion of its work"""
        self.logger.info(f"{agent.name} signaled completion")
        
        # If this agent is the token holder, advance the token
        if self.token_holder == agent:
            await self._advance_token()
            
    async def handle_error(self, agent: CelayaAgent, details: str) -> None:
        """Handle an agent signaling an error"""
        self.logger.warning(f"{agent.name} reported error: {details}")
        self.recent_errors[agent.name] += 1
        self.adjust_reputation(agent, -0.1)  # Decrease reputation on reported error
        
        # If we're seeing many errors, consider electing a leader
        if self.recent_errors[agent.name] >= 3:
            await self._elect_leader()
            
    async def _elect_leader(self) -> None:
        """Elect a leader agent to handle recovery"""
        if self.leader:
            return  # Already have a leader
            
        # Find agent with highest reputation
        best_agent = max(self.agents, key=lambda a: a.reputation)
        self.leader = best_agent
        self.logger.info(f"Elected {best_agent.name} as leader with reputation {best_agent.reputation:.2f}")
        
        # Notify all agents about the new leader
        for agent in self.agents:
            if agent != best_agent:
                await agent.receive_message("Orchestrator", 
                                          f"Due to system issues, {best_agent.name} has been elected as leader. " +
                                          f"Please follow their coordination instructions.")
    
    async def start_consensus_ballot(self, proposal: str) -> None:
        """Start a consensus ballot among agents"""
        if self.consensus_in_progress:
            return  # Already have a consensus process running
            
        self.consensus_in_progress = True
        self.consensus_votes[proposal] = set()
        
        # Send ballot to all agents
        for agent in self.agents:
            await agent.receive_message("Orchestrator", 
                                      f"[CONSENSUS] Please vote APPROVE or REJECT on: {proposal}")
            
    async def register_vote(self, agent: CelayaAgent, proposal: str, vote: str) -> None:
        """Register an agent's vote in a consensus ballot"""
        if proposal not in self.consensus_votes:
            return
            
        if vote.upper() == "APPROVE":
            self.consensus_votes[proposal].add(agent.name)
            
        # Check if we have a quorum
        if len(self.consensus_votes[proposal]) >= len(self.agents) * QUORUM:
            self.logger.info(f"Consensus reached on: {proposal}")
            self.consensus_in_progress = False
            
            # Notify all agents about the consensus result
            for agent in self.agents:
                await agent.receive_message("Orchestrator", 
                                          f"[CONSENSUS RESULT] Proposal approved: {proposal}")
    
    def adjust_reputation(self, agent: CelayaAgent, change: float) -> None:
        """Adjust an agent's reputation score"""
        agent.reputation = max(0.0, min(1.0, agent.reputation + change))
        self.logger.debug(f"Adjusted {agent.name}'s reputation to {agent.reputation:.2f}")
    
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