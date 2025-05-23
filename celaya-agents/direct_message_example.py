# ----------------------------------------------------------------------------
#  File:        direct_message_example.py
#  Project:     Celaya Solutions (Agent Orchestration)
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Example of direct messaging between agents
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import asyncio
import json
import logging
import sys
import time
import argparse
import random
from typing import List, Dict, Tuple, Any, Optional
from run_simulated import SimulatedAgent, SimulatedOrchestrator, direct_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("DirectMessageExample")

class DirectMessageOrchestrator(SimulatedOrchestrator):
    """Extended orchestrator that demonstrates direct messaging between agents"""
    
    async def orchestrate_with_direct_messages(self, initial_prompt: str) -> None:
        """Run orchestration with some direct messages between agents"""
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
            # First few turns - normal orchestration
            for i in range(min(5, self.max_turns)):
                if not self.running:
                    break
                    
                current_agent = self.agents[self.turn_index % len(self.agents)]
                turn_count += 1
                
                self.logger.info(f"Turn {turn_count}/{self.max_turns}: {current_agent.name}'s turn ({current_agent.role})")
                
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
                
                # Broadcast response to central queue
                await self.central_queue.put((current_agent.name, response))
                
                # Process the central queue
                await self._process_central_queue()
                
                # Update prompt for next agent
                prompt = f"Previous message from {current_agent.name}: {response}\nYour turn to respond."
                
                # Move to next agent
                self.turn_index += 1
                
                # Short delay between turns
                await asyncio.sleep(0.5)
            
            # Now let's add some direct messages
            if self.running:
                # Find specific agents for direct messaging
                sentinel = None
                clarity = None
                volt = None
                verdict = None
                
                for agent in self.agents:
                    if agent.name == "Sentinel":
                        sentinel = agent
                    elif agent.name == "Clarity":
                        clarity = agent
                    elif agent.name == "Volt":
                        volt = agent
                    elif agent.name == "Verdict":
                        verdict = agent
                
                # Sentinel privately asks Clarity for simplification
                if sentinel and clarity:
                    self.logger.info("Demonstrating direct messaging between agents:")
                    private_message = "I'm noticing some complexity in this discussion. Could you help simplify the key points?"
                    self.logger.info(f"🔒 Sentinel privately to Clarity: {private_message}")
                    
                    # Record in conversation log with special marker
                    self.conversation_log.append({
                        "turn": turn_count + 0.1,
                        "agent": "Sentinel [private to Clarity]",
                        "message": private_message,
                        "timestamp": time.time()
                    })
                    
                    # Send the direct message
                    await direct_message(sentinel, "Clarity", private_message, self)
                    
                    # Allow Clarity to respond privately
                    clarity_response = await clarity.speak(f"Private message from Sentinel: {private_message}")
                    self.logger.info(f"🔒 Clarity privately to Sentinel: {clarity_response}")
                    
                    # Record in conversation log
                    self.conversation_log.append({
                        "turn": turn_count + 0.2,
                        "agent": "Clarity [private to Sentinel]",
                        "message": clarity_response,
                        "timestamp": time.time()
                    })
                    
                    # Send response back to Sentinel
                    await direct_message(clarity, "Sentinel", clarity_response, self)
                
                # Volt privately encourages Verdict
                if volt and verdict:
                    private_message = "I sense hesitation in your decision-making. Remember, bold action with careful consideration can lead to breakthrough progress!"
                    self.logger.info(f"🔒 Volt privately to Verdict: {private_message}")
                    
                    # Record in conversation log
                    self.conversation_log.append({
                        "turn": turn_count + 0.3,
                        "agent": "Volt [private to Verdict]",
                        "message": private_message,
                        "timestamp": time.time()
                    })
                    
                    # Send the direct message
                    await direct_message(volt, "Verdict", private_message, self)
                    
                    # Allow Verdict to respond privately
                    verdict_response = await verdict.speak(f"Private message from Volt: {private_message}")
                    self.logger.info(f"🔒 Verdict privately to Volt: {verdict_response}")
                    
                    # Record in conversation log
                    self.conversation_log.append({
                        "turn": turn_count + 0.4,
                        "agent": "Verdict [private to Volt]",
                        "message": verdict_response,
                        "timestamp": time.time()
                    })
                    
                    # Send response back to Volt
                    await direct_message(verdict, "Volt", verdict_response, self)
            
            # Continue with normal orchestration but with the private context now available
            while self.running and turn_count < self.max_turns:
                current_agent = self.agents[self.turn_index % len(self.agents)]
                turn_count += 1
                
                self.logger.info(f"Turn {turn_count}/{self.max_turns}: {current_agent.name}'s turn ({current_agent.role})")
                
                # Check for any private messages
                private_messages = await current_agent.check_messages()
                if private_messages:
                    context = "\n".join([f"{sender}: {message}" for sender, message in private_messages])
                    prompt = f"{prompt}\n\nMessages from other agents:\n{context}"
                    self.logger.info(f"  👀 {current_agent.name} has received private messages and will incorporate them")
                
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
                
                # Broadcast response to central queue
                await self.central_queue.put((current_agent.name, response))
                
                # Process the central queue
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
            self.save_conversation_log("direct_message_conversation.json")


async def main():
    """Main entry point for the direct message example"""
    parser = argparse.ArgumentParser(description="Celaya Agent Direct Message Example")
    parser.add_argument("--config", default="agent_config.json", help="Path to agent configuration file")
    parser.add_argument("--prompt", default="Let's discuss how to handle sensitive user data in AI systems.", 
                      help="Initial prompt to start the conversation")
    parser.add_argument("--max-turns", type=int, default=11, help="Maximum number of turns before stopping")
    args = parser.parse_args()
    
    try:
        # Load agent configuration
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        # Create simulated agents
        agents = []
        for agent_config in config["agents"]:
            agent = SimulatedAgent(
                name=agent_config["name"],
                role=agent_config.get("role"),
                system_prompt=agent_config.get("system_prompt")
            )
            agents.append(agent)
            logger.info(f"Created simulated agent: {agent.name} ({agent.role})")
        
        # Create orchestrator with direct messaging
        orchestrator = DirectMessageOrchestrator(agents, max_turns=args.max_turns)
        
        # Print agent information
        print("\n===== DIRECT MESSAGE EXAMPLE =====")
        print(f"Running with {len(agents)} agents for up to {args.max_turns} turns")
        print("This example will demonstrate private messages between agents")
        print(f"Initial prompt: {args.prompt}")
        print("=================================\n")
        
        # Run orchestration with direct messages
        await orchestrator.orchestrate_with_direct_messages(args.prompt)
        
        # Print summary
        orchestrator.print_conversation_summary()
        
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 