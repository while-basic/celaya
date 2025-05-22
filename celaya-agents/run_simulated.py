# ----------------------------------------------------------------------------
#  File:        run_simulated.py
#  Project:     Celaya Solutions (Agent Orchestration)
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Simulated version of the agent system with all 11 agents
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SimulatedOrchestrator")

class SimulatedAgent:
    """Simulated agent for demonstration without Celaya API"""
    
    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.conversation_history = []
        self.private_queue = asyncio.Queue()
        self.logger = logging.getLogger(f"Agent:{name}")
        self.personality_traits = self._generate_personality_traits()
    
    def _generate_personality_traits(self) -> Dict[str, float]:
        """Generate random personality traits to shape responses"""
        return {
            "conciseness": random.uniform(0.3, 1.0),
            "formality": random.uniform(0.3, 1.0),
            "enthusiasm": random.uniform(0.3, 1.0),
            "analytical": random.uniform(0.3, 1.0),
            "creativity": random.uniform(0.3, 1.0),
        }
    
    async def speak(self, prompt: str) -> str:
        """Generate a response based on the agent's role and personality"""
        # Extract the query from the prompt
        query = prompt
        if "Previous message from" in prompt:
            query = prompt.split(": ", 1)[1] if ": " in prompt else prompt

        # Get response based on agent role
        response_parts = []
        
        # Add role-specific content
        if self.role == "communicator":
            response_parts.append(f"I've analyzed this communication and want to clarify that")
            response_parts.append(self._generate_communication_insight(query))
            
        elif self.role == "decision_maker":
            response_parts.append("Based on the available information, I've reached a decision.")
            response_parts.append(self._generate_decision(query))
            
        elif self.role == "health_monitor":
            response_parts.append("My assessment of the current situation is:")
            response_parts.append(self._generate_health_assessment(query))
            
        elif self.role == "foundation_builder":
            response_parts.append("To build a strong foundation, we need to consider:")
            response_parts.append(self._generate_foundation_principle(query))
            
        elif self.role == "conceptual_thinker":
            response_parts.append("Let me explore this concept from a theoretical perspective:")
            response_parts.append(self._generate_theoretical_insight(query))
            
        elif self.role == "guardian":
            response_parts.append("I've identified some important considerations regarding integrity and security:")
            response_parts.append(self._generate_security_insight(query))
            
        elif self.role == "guide":
            response_parts.append("I can see a path forward. Here's my guidance:")
            response_parts.append(self._generate_guidance(query))
            
        elif self.role == "perspective_shifter":
            response_parts.append("Let's look at this from a different angle:")
            response_parts.append(self._generate_alternative_perspective(query))
            
        elif self.role == "energizer":
            response_parts.append("I'm excited about where this is heading! Let's push forward:")
            response_parts.append(self._generate_motivational_message(query))
            
        elif self.role == "simplifier":
            response_parts.append("To simplify what we're discussing:")
            response_parts.append(self._generate_simplified_explanation(query))
            
        elif self.role == "historian":
            response_parts.append("Let me provide some context based on our previous discussions:")
            response_parts.append(self._generate_historical_context(query))
        
        # Apply personality traits
        response = " ".join(response_parts)
        
        # Adjust response based on conciseness trait
        if self.personality_traits["conciseness"] > 0.7:
            response = self._make_concise(response)
        
        # Adjust formality based on trait
        if self.personality_traits["formality"] > 0.7:
            response = self._make_formal(response)
        
        # Add enthusiasm if trait is high
        if self.personality_traits["enthusiasm"] > 0.7:
            response = self._add_enthusiasm(response)

        # Update conversation history
        self.conversation_history.append({"role": "user", "content": prompt})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Simulate processing time
        await asyncio.sleep(0.2)
        
        return response

    def _make_concise(self, text: str) -> str:
        """Make the response more concise"""
        # Simple simulation of making text more concise
        if len(text) > 100:
            sentences = text.split('.')
            if len(sentences) > 2:
                return '.'.join(sentences[:2]) + '.'
        return text
    
    def _make_formal(self, text: str) -> str:
        """Make the response more formal"""
        # Simple simulation of making text more formal
        text = text.replace("Let's", "Let us")
        text = text.replace("I'm", "I am")
        text = text.replace("can't", "cannot")
        text = text.replace("don't", "do not")
        return text
    
    def _add_enthusiasm(self, text: str) -> str:
        """Add enthusiasm to the response"""
        if not text.endswith('!'):
            if random.random() > 0.5:
                text += '!'
        return text

    # Role-specific response generators
    def _generate_communication_insight(self, query: str) -> str:
        insights = [
            "we need to establish clearer channels for information flow.",
            "there seems to be a misunderstanding about the core objective.",
            "we should focus on the key message and eliminate noise.",
            "using more precise terminology would help everyone stay aligned.",
            "summarizing the main points periodically will keep everyone on track."
        ]
        return random.choice(insights)
    
    def _generate_decision(self, query: str) -> str:
        decisions = [
            "we should proceed with approach A, as it balances both short and long-term considerations.",
            "the most effective path forward is to pause and gather more information before continuing.",
            "we need to pivot our strategy based on the new information presented.",
            "the optimal decision is to divide our resources between these two promising avenues.",
            "we should commit fully to this direction given the evidence presented."
        ]
        return random.choice(decisions)
    
    def _generate_health_assessment(self, query: str) -> str:
        assessments = [
            "our current approach seems sustainable, but we should monitor for signs of strain.",
            "there are early warning signs that we may be overextending in some areas.",
            "the balance of workload and resources appears healthy at this time.",
            "we should be cautious about potential burnout if we continue at this pace.",
            "the system is showing remarkable resilience despite challenging conditions."
        ]
        return random.choice(assessments)
    
    def _generate_foundation_principle(self, query: str) -> str:
        principles = [
            "establishing clear definitions that everyone agrees on.",
            "creating a framework that can adapt to changing conditions.",
            "identifying the core values that will guide all decisions.",
            "ensuring we have robust mechanisms for feedback and correction.",
            "building redundancy into critical systems to prevent single points of failure."
        ]
        return random.choice(principles)
    
    def _generate_theoretical_insight(self, query: str) -> str:
        insights = [
            "this resembles a classic problem in systems theory, where emergent properties can't be predicted from individual components.",
            "we might apply the concept of antifragility here - designing a system that gets stronger when exposed to volatility.",
            "this appears to be a manifestation of the explore-exploit dilemma in decision theory.",
            "there's an interesting parallel to how complex adaptive systems maintain equilibrium while evolving.",
            "this challenge reflects the tension between optimization for known conditions versus flexibility for unknown futures."
        ]
        return random.choice(insights)
    
    def _generate_security_insight(self, query: str) -> str:
        insights = [
            "we should verify our assumptions before proceeding to avoid hidden vulnerabilities.",
            "there's a potential ethical consideration here we haven't fully addressed.",
            "we should establish guardrails to prevent unintended consequences.",
            "maintaining integrity requires consistent standards across all aspects of implementation.",
            "we need to consider not just success scenarios but also failure modes and recovery plans."
        ]
        return random.choice(insights)
    
    def _generate_guidance(self, query: str) -> str:
        guidance = [
            "first identify the highest leverage points, then focus our initial efforts there.",
            "break this down into smaller milestones that provide clear feedback on our progress.",
            "consider alternative routes to our objective that may offer less resistance.",
            "align our approach with our strengths while acknowledging and addressing our limitations.",
            "seek balance between immediate results and long-term sustainability."
        ]
        return random.choice(guidance)
    
    def _generate_alternative_perspective(self, query: str) -> str:
        perspectives = [
            "what if we viewed this as an opportunity rather than a challenge?",
            "from the perspective of a newcomer without our assumptions, how would this situation appear?",
            "if we invert our thinking and consider what we should avoid, we might gain clarity on what to pursue.",
            "considering this from a completely different domain or industry might yield fresh insights.",
            "what if the constraints we're facing are actually advantages in disguise?"
        ]
        return random.choice(perspectives)
    
    def _generate_motivational_message(self, query: str) -> str:
        messages = [
            "we've already overcome bigger challenges, and this one is well within our capabilities!",
            "each step forward creates momentum that will make the next steps easier!",
            "imagine the impact we'll have once we solve this - it's worth the effort!",
            "let's harness our collective energy and creativity to breakthrough this barrier!",
            "this is precisely the kind of challenge that leads to our greatest innovations!"
        ]
        return random.choice(messages)
    
    def _generate_simplified_explanation(self, query: str) -> str:
        explanations = [
            "at its core, this is about finding the balance between opposing but valuable forces.",
            "the key insight is that small, consistent improvements compound over time.",
            "we're essentially trying to create a system that makes the right choice the easiest choice.",
            "this all comes down to matching our resources with our highest priorities.",
            "the fundamental question we're addressing is how to create sustainable value."
        ]
        return random.choice(explanations)
    
    def _generate_historical_context(self, query: str) -> str:
        contexts = [
            "we faced a similar situation previously and found success by focusing on incremental improvements.",
            "our past attempts in this area taught us the importance of cross-functional collaboration.",
            "historical patterns suggest that persistence through the initial difficulties yields breakthroughs.",
            "we've built a foundation of trust and capability that positions us better for this challenge than ever before.",
            "previous iterations revealed that user feedback early in the process saves resources in the long run."
        ]
        return random.choice(contexts)

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


class SimulatedOrchestrator:
    """Orchestrates communication between simulated agents"""
    
    def __init__(self, agents: List[SimulatedAgent], max_turns: int = 20):
        self.agents = agents
        self.turn_index = 0
        self.max_turns = max_turns
        self.central_queue = asyncio.Queue()
        self.conversation_log: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("SimulatedOrchestrator")
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
                
                self.logger.info(f"Turn {turn_count}/{self.max_turns}: {current_agent.name}'s turn ({current_agent.role})")
                
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
    
    def save_conversation_log(self, filename: str = "simulated_conversation_log.json") -> None:
        """Save the conversation log to a file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.conversation_log, f, indent=2)
            self.logger.info(f"Conversation log saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving conversation log: {str(e)}")

    def print_conversation_summary(self) -> None:
        """Print a summary of the conversation"""
        print("\nConversation Summary:")
        for entry in self.conversation_log:
            print(f"[Turn {entry['turn']}] {entry['agent']}: {entry['message'][:80]}{'...' if len(entry['message']) > 80 else ''}")


async def direct_message(sender: SimulatedAgent, recipient_name: str, message: str, orchestrator: SimulatedOrchestrator) -> bool:
    """Send a direct message from one agent to another"""
    if recipient_name not in orchestrator.agent_map:
        return False
        
    recipient = orchestrator.agent_map[recipient_name]
    await recipient.receive_message(sender.name, message)
    return True


async def main():
    """Main entry point for the simulated orchestrator"""
    parser = argparse.ArgumentParser(description="Simulated Celaya Agent Orchestrator")
    parser.add_argument("--config", default="agent_config.json", help="Path to agent configuration file")
    parser.add_argument("--prompt", default="Let's discuss the future of artificial intelligence and its impact on society.", 
                      help="Initial prompt to start the conversation")
    parser.add_argument("--max-turns", type=int, default=22, help="Maximum number of turns before stopping (2 for each agent)")
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
        
        # Create orchestrator
        orchestrator = SimulatedOrchestrator(agents, max_turns=args.max_turns)
        
        # Print agent information
        print("\n===== SIMULATED AGENT SYSTEM =====")
        print(f"Running with {len(agents)} agents for up to {args.max_turns} turns")
        print("Agents participating:")
        for agent in agents:
            print(f"  - {agent.name}: {agent.role}")
        print(f"Initial prompt: {args.prompt}")
        print("==================================\n")
        
        # Run orchestration
        await orchestrator.orchestrate(args.prompt)
        
        # Print summary
        orchestrator.print_conversation_summary()
        
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 