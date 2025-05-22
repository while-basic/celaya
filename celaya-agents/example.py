# ----------------------------------------------------------------------------
#  File:        example.py
#  Project:     Celaya Solutions (Agent Orchestration)
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Example script to demonstrate the agent orchestration system
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import asyncio
import argparse
import json
import logging
import sys
from orchestrator import CelayaAgent, Orchestrator, direct_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CelayaExample")

async def setup_example():
    """Set up a simple example with mock agents for testing without Celaya"""
    
    # Create mock agents (these won't actually call Celaya API)
    echo = MockAgent("Echo", "http://localhost:5001", "I'm Echo, the communicator.")
    verdict = MockAgent("Verdict", "http://localhost:5002", "I'm Verdict, the decision maker.")
    vitals = MockAgent("Vitals", "http://localhost:5003", "I'm Vitals, the health monitor.")
    
    # Create orchestrator with only 3 agents for simplicity
    orchestrator = Orchestrator([echo, verdict, vitals], max_turns=6)
    
    # Run orchestration
    await orchestrator.orchestrate("Let's discuss how to improve team communication.")
    
    # Print conversation log
    print("\nConversation Summary:")
    for entry in orchestrator.conversation_log:
        print(f"[Turn {entry['turn']}] {entry['agent']}: {entry['message']}")

class MockAgent(CelayaAgent):
    """Mock agent for testing without actual Celaya API calls"""
    
    def __init__(self, name, url, response_prefix):
        super().__init__(name, url)
        self.response_prefix = response_prefix
    
    async def speak(self, prompt, include_history=True):
        """Generate a mock response without calling the API"""
        # Create a simple mock response based on the prompt
        response = f"{self.response_prefix} Responding to: {prompt[:50]}..."
        
        # Update conversation history
        if include_history:
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": response})
        
        return response

async def sample_priority_orchestration():
    """Example of how to implement priority-based orchestration"""
    
    # Load configuration
    with open("agent_config.json", 'r') as f:
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
    
    class PriorityOrchestrator(Orchestrator):
        """Example of priority-based orchestration"""
        
        def __init__(self, agents, max_turns=20):
            super().__init__(agents, max_turns)
            self.priorities = {
                "Echo": 10,      # High priority
                "Verdict": 9,
                "Vitals": 8,
                "Core": 7,
                "Theory": 6,
                "Sentinel": 5,
                "Beacon": 4,
                "Lens": 3,
                "Volt": 2,
                "Clarity": 1,
                "Arkive": 0      # Low priority
            }
        
        def get_next_agent(self, current_turn):
            """Get the next agent based on priority"""
            if current_turn < 3:
                # For first few turns, just go in order of priority
                sorted_agents = sorted(self.agents, key=lambda a: -self.priorities[a.name])
                return sorted_agents[current_turn % len(sorted_agents)]
            else:
                # After a few turns, randomize with weighting toward higher priorities
                import random
                weights = [self.priorities[agent.name] + 1 for agent in self.agents]
                return random.choices(self.agents, weights=weights, k=1)[0]
    
    # Create priority orchestrator
    orchestrator = PriorityOrchestrator(agents, max_turns=10)
    
    # Override the original orchestrate method to use our priority-based scheduling
    original_orchestrate = orchestrator.orchestrate
    
    async def priority_orchestrate(initial_prompt):
        """Modified orchestration using priority-based scheduling"""
        prompt = initial_prompt
        orchestrator.running = True
        turn_count = 0
        
        # Log the initial prompt
        orchestrator.conversation_log.append({
            "turn": turn_count,
            "agent": "User",
            "message": initial_prompt
        })
        
        logger.info(f"Starting priority-based orchestration with prompt: {initial_prompt}")
        
        try:
            while orchestrator.running and turn_count < orchestrator.max_turns:
                # Get next agent based on priority
                current_agent = orchestrator.get_next_agent(turn_count)
                turn_count += 1
                
                logger.info(f"Turn {turn_count}/{orchestrator.max_turns}: {current_agent.name}'s turn (priority: {orchestrator.priorities[current_agent.name]})")
                
                # Rest of the orchestration logic remains the same...
                # This is just a demonstration of how to modify the agent selection
                
                # For this mock example, we'll just stop after a few turns
                if turn_count >= 3:
                    break
                
        except Exception as e:
            logger.error(f"Error in priority orchestration: {str(e)}")
        finally:
            orchestrator.running = False
    
    # Not actually running this to avoid API calls in the example
    logger.info("This is just an example of how to implement priority-based orchestration")

async def main():
    """Main entry point for the example"""
    parser = argparse.ArgumentParser(description="Celaya Agent Example")
    parser.add_argument("--mock", action="store_true", help="Run with mock agents (no actual API calls)")
    args = parser.parse_args()
    
    if args.mock:
        await setup_example()
    else:
        logger.info("To run with real agents, use the orchestrator.py script directly")
        logger.info("This example is mainly to demonstrate concepts")
        
        # Just show the priority orchestration example
        await sample_priority_orchestration()

if __name__ == "__main__":
    asyncio.run(main()) 