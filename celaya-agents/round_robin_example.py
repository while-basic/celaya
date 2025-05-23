# ----------------------------------------------------------------------------
#  File:        round_robin_example.py
#  Project:     Celaya Solutions (Agent Orchestration)
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Example demonstrating the round-robin orchestration system
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import asyncio
import json
import logging
import sys
from typing import List, Dict, Any, Optional, Tuple

# Import the orchestrator module but don't use its CelayaAgent class directly
import orchestrator
from orchestrator import Orchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("RoundRobinExample")

# Define a mock agent class that inherits from orchestrator.CelayaAgent
class MockCelayaAgent(orchestrator.CelayaAgent):
    """A mock version of CelayaAgent that doesn't make actual API calls"""
    
    async def speak(self, prompt: str, include_history: bool = True, orchestrator = None) -> str:
        """Generate a simulated response without making API calls"""
        # Check for urgency keywords and raise interrupt if found
        if orchestrator and any(kw in prompt.lower() for kw in ["urgent", "critical", "emergency", "!!"]):
            priority = 95  # High priority for detected urgent keywords
            await orchestrator.request_interrupt(self, priority, prompt)
            
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Update conversation history
        if include_history:
            self.conversation_history.append({"role": "user", "content": prompt})
        
        # Generate different responses based on agent role
        response = ""
        if self.role == "coordinator":
            response = f"As the project manager, I'll coordinate our efforts on this task. Let me analyze what we need for the {prompt[-50:].strip()}..."
        elif self.role == "security":
            response = f"From a security perspective, we need to ensure data protection. For the {prompt[-50:].strip()}, we should implement proper authentication."
        elif self.role == "analyst":
            response = f"Looking at the data patterns, I can provide insights on this. The {prompt[-50:].strip()} should include key metrics and trends."
        elif self.role == "designer":
            response = f"From a UX perspective, we should consider user workflow. The {prompt[-50:].strip()} needs an intuitive interface."
        elif self.role == "developer":
            response = f"I can implement the backend services needed for this. The {prompt[-50:].strip()} will require secure APIs."
        else:
            response = f"{self.name}'s response to: {prompt[:30]}..."
        
        # Update conversation history
        if include_history:
            self.conversation_history.append({"role": "assistant", "content": response})
            
        return response


async def simulate_agent_behaviors(orchestrator, agents):
    """Simulate various agent behaviors to demonstrate orchestration features"""
    
    # Let agents have a few normal turns first
    await asyncio.sleep(5)
    
    # 1. Simulate an interrupt from the security agent
    security_agent = next((a for a in agents if a.name == "SecurityExpert"), agents[0])
    logger.info("Simulating urgent interrupt from security agent")
    await orchestrator.request_interrupt(
        security_agent, 
        95, 
        "URGENT: Potential security breach detected in database access logs!"
    )
    
    # Wait a bit for the interrupt to process
    await asyncio.sleep(3)
    
    # 2. Simulate a handoff to a specialist
    if len(agents) >= 3:
        sender = agents[0]
        target = agents[2]
        logger.info(f"Simulating handoff from {sender.name} to {target.name}")
        await orchestrator.request_handoff(
            sender,
            target.name,
            f"You have expertise I need. Can you analyze this data pattern?"
        )
    
    # Wait a bit for normal processing
    await asyncio.sleep(5)
    
    # 3. Simulate a consensus ballot
    logger.info("Starting a consensus ballot")
    await orchestrator.start_consensus_ballot(
        "Should we implement the new feature suggested by the user?"
    )
    
    # Simulate some votes
    await asyncio.sleep(2)
    for i, agent in enumerate(agents):
        vote = "APPROVE" if i % 3 != 0 else "REJECT"  # 2/3 approve
        await orchestrator.register_vote(
            agent, 
            "Should we implement the new feature suggested by the user?",
            vote
        )
        await asyncio.sleep(0.5)

async def main():
    """Run a demonstration of the round-robin orchestration"""
    try:
        # Create mock agent configuration
        agent_config = [
            {
                "name": "ProjectManager",
                "url": "http://localhost:11434",
                "model": "llama3",
                "system_prompt": "You are a project manager agent focused on coordination and planning.",
                "role": "coordinator"
            },
            {
                "name": "SecurityExpert",
                "url": "http://localhost:11434",
                "model": "llama3", 
                "system_prompt": "You are a security expert agent that identifies and responds to security concerns.",
                "role": "security"
            },
            {
                "name": "DataAnalyst",
                "url": "http://localhost:11434",
                "model": "llama3",
                "system_prompt": "You are a data analyst agent that specializes in processing and interpreting data.",
                "role": "analyst"
            },
            {
                "name": "UXDesigner",
                "url": "http://localhost:11434", 
                "model": "llama3",
                "system_prompt": "You are a UX designer agent with expertise in user experience and interface design.",
                "role": "designer"
            },
            {
                "name": "BackendDeveloper",
                "url": "http://localhost:11434",
                "model": "llama3",
                "system_prompt": "You are a backend developer agent specializing in server-side architecture and APIs.",
                "role": "developer"
            }
        ]
        
        # Create mock agents
        agents = []
        for config in agent_config:
            agent = MockCelayaAgent(
                name=config["name"],
                url=config["url"],
                model=config.get("model", "llama3"),
                system_prompt=config.get("system_prompt"),
                role=config.get("role")
            )
            agents.append(agent)
            logger.info(f"Created agent: {agent.name}")
        
        # Create orchestrator with round-robin capability
        orchestrator = Orchestrator(agents, max_turns=30)
        
        # Start simulation task
        simulation_task = asyncio.create_task(simulate_agent_behaviors(orchestrator, agents))
        
        # Run orchestration with initial prompt
        initial_prompt = """
        Welcome to the Celaya agent orchestration test. Let's collaborate on designing a new 
        feature for our product. Each agent should contribute based on their expertise.
        
        The feature is a secure data visualization dashboard for user analytics.
        """
        await orchestrator.orchestrate(initial_prompt)
        
        # Wait for simulation to complete
        await simulation_task
        
        # Save conversation log
        orchestrator.save_conversation_log("round_robin_conversation.json")
        logger.info("Demonstration completed. Check round_robin_conversation.json for the conversation log.")
        
    except KeyboardInterrupt:
        logger.info("Demonstration interrupted by user")
    except Exception as e:
        logger.error(f"Error in demonstration: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 