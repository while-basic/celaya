# ----------------------------------------------------------------------------
#  File:        csuite_integration.py
#  Project:     Celaya Solutions (Agent Orchestration)
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Integration of Celaya C-Suite agents with round-robin orchestration
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import asyncio
import json
import logging
import sys
from typing import List, Dict, Any, Optional, Tuple

# Import the orchestrator module 
import orchestrator
from orchestrator import Orchestrator, CelayaAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CelayaCSuite")

class CSuiteAgent(CelayaAgent):
    """Extended agent class for C-Suite specialized behaviors"""
    
    def __init__(self, name: str, url: str, model: str = "llama3", 
                 system_prompt: str = None, role: str = None, specialty: str = None,
                 interrupt_threshold: int = 80, interrupt_keywords: List[str] = None):
        super().__init__(name, url, model, system_prompt, role)
        self.specialty = specialty
        self.interrupt_threshold = interrupt_threshold
        self.interrupt_keywords = interrupt_keywords or []
        self.logger = logging.getLogger(f"CSuite:{name}")
    
    async def speak(self, prompt: str, include_history: bool = True, orchestrator = None) -> str:
        """Enhanced speak method with C-Suite specialized behaviors"""
        
        # Check for specialty-specific keywords that should trigger interrupts
        if orchestrator and self.should_interrupt(prompt):
            priority = self.calculate_interrupt_priority(prompt)
            await orchestrator.request_interrupt(self, priority, prompt)
        
        # Normal speak behavior from parent class
        return await super().speak(prompt, include_history, orchestrator)
    
    def should_interrupt(self, prompt: str) -> bool:
        """Determine if this agent should interrupt based on the prompt"""
        # Check for general interrupt keywords
        if any(keyword in prompt.lower() for keyword in orchestrator.INTERRUPT_KEYWORDS):
            return True
            
        # Check for specialty-specific keywords
        if any(keyword in prompt.lower() for keyword in self.interrupt_keywords):
            return True
            
        return False
    
    def calculate_interrupt_priority(self, prompt: str) -> int:
        """Calculate interrupt priority based on prompt content and agent specialty"""
        # Base priority from agent configuration
        priority = self.interrupt_threshold
        
        # Increase priority for urgent keywords
        if "urgent" in prompt.lower() or "emergency" in prompt.lower() or "critical" in prompt.lower():
            priority += 10
            
        # Special case for Sentinel security concerns
        if self.name == "Sentinel" and any(kw in prompt.lower() for kw in ["security", "breach", "vulnerability", "attack"]):
            priority += 15
            
        # Special case for Volt hardware/engineering emergencies
        if self.name == "Volt" and any(kw in prompt.lower() for kw in ["hardware", "failure", "temperature", "power"]):
            priority += 15
            
        # Cap at maximum priority 100
        return min(priority, 100)


async def create_csuite_agents(api_url: str = "http://localhost:11434", model: str = "luma") -> List[CSuiteAgent]:
    """Create the 13 C-Suite agents with appropriate specialties and system prompts"""
    
    # Define agent configurations
    agent_configs = [
        {
            "name": "Lyra",
            "role": "operating_system",
            "specialty": "agent_orchestration",
            "system_prompt": "You are Lyra, the Operating System Meta-Agent that bootstraps and monitors the entire C-Suite. You handle memory management, updates, and repairs when agents fail.",
            "interrupt_threshold": 85,
            "interrupt_keywords": ["system failure", "agent malfunction", "memory issue", "update required"]
        },
        {
            "name": "Otto",
            "role": "orchestrator",
            "specialty": "task_routing",
            "system_prompt": "You are Otto, the Task Orchestrator that routes user requests to appropriate agents and manages turn-taking in multi-agent conversations.",
            "interrupt_threshold": 75,
            "interrupt_keywords": ["coordination", "routing", "organize"]
        },
        {
            "name": "Core",
            "role": "strategist",
            "specialty": "ideation",
            "system_prompt": "You are Core, the Ideation & Strategy Architect that generates breakthrough ideas, strategies, and next steps.",
            "interrupt_threshold": 70,
            "interrupt_keywords": ["strategy", "idea", "vision", "plan"]
        },
        {
            "name": "Verdict",
            "role": "legal",
            "specialty": "compliance",
            "system_prompt": "You are Verdict, the Legal & Compliance Specialist that ensures traceability, writes contracts, and checks compliance with regulations.",
            "interrupt_threshold": 80,
            "interrupt_keywords": ["legal", "compliance", "regulation", "contract", "liability"]
        },
        {
            "name": "Vitals",
            "role": "bioengineer",
            "specialty": "health_science",
            "system_prompt": "You are Vitals, the Health & Bioengineer AI that handles health data, biometrics, and medical information.",
            "interrupt_threshold": 85,
            "interrupt_keywords": ["health", "medical", "emergency", "biometric"]
        },
        {
            "name": "Beacon",
            "role": "researcher",
            "specialty": "information_retrieval",
            "system_prompt": "You are Beacon, the Search & Intel Gathering specialist that researches, verifies sources, and provides high-quality citations.",
            "interrupt_threshold": 65,
            "interrupt_keywords": ["research", "source", "citation", "fact check"]
        },
        {
            "name": "Sentinel",
            "role": "security",
            "specialty": "safety_protocols",
            "system_prompt": "You are Sentinel, the Safety & Security Watchdog that monitors for threats, prevents manipulation, and enforces safety protocols.",
            "interrupt_threshold": 95,
            "interrupt_keywords": ["security", "breach", "threat", "manipulation", "jailbreak"]
        },
        {
            "name": "Theory",
            "role": "scientist",
            "specialty": "technical_reasoning",
            "system_prompt": "You are Theory, the Technical & Scientific Thinker that handles abstract reasoning, hypotheses, and advanced models.",
            "interrupt_threshold": 70,
            "interrupt_keywords": ["scientific", "hypothesis", "theory", "mathematical"]
        },
        {
            "name": "Lens",
            "role": "analyst",
            "specialty": "pattern_recognition",
            "system_prompt": "You are Lens, the Insight Engine that analyzes conversation logs, extracts meaning, finds patterns, and scores memory for usefulness.",
            "interrupt_threshold": 65,
            "interrupt_keywords": ["pattern", "insight", "analysis", "trend"]
        },
        {
            "name": "Volt",
            "role": "engineer",
            "specialty": "hardware_integration",
            "system_prompt": "You are Volt, the Hardware-AI Integration Specialist that interfaces with physical systems, IoT devices, and industrial equipment.",
            "interrupt_threshold": 90,
            "interrupt_keywords": ["hardware", "system failure", "power", "device"]
        },
        {
            "name": "Echo",
            "role": "memory",
            "specialty": "self_improvement",
            "system_prompt": "You are Echo, the Reflection & Self-Improvement Agent that analyzes logs, summarizes events, and drives agent evolution through learning.",
            "interrupt_threshold": 60,
            "interrupt_keywords": ["remember", "historical", "previous", "improve"]
        },
        {
            "name": "Luma",
            "role": "companion",
            "specialty": "personalization",
            "system_prompt": "You are Luma, the Home AI Companion that handles ambient tasks, understands routines, and offers personal support.",
            "interrupt_threshold": 65,
            "interrupt_keywords": ["personal", "routine", "schedule", "preference"]
        },
        {
            "name": "Clarity",
            "role": "historian",
            "specialty": "record_keeping",
            "system_prompt": "You are Clarity, the Historian that keeps records of all agent interactions, creates audit trails, and preserves decision history.",
            "interrupt_threshold": 70,
            "interrupt_keywords": ["record", "document", "timeline", "audit"]
        }
    ]
    
    # Create the agents
    agents = []
    for config in agent_configs:
        agent = CSuiteAgent(
            name=config["name"],
            url=api_url,
            model=model,
            system_prompt=config["system_prompt"],
            role=config["role"],
            specialty=config["specialty"],
            interrupt_threshold=config["interrupt_threshold"],
            interrupt_keywords=config["interrupt_keywords"]
        )
        agents.append(agent)
        logger.info(f"Created C-Suite agent: {agent.name} with specialty: {agent.specialty}")
    
    return agents


class CSuiteOrchestrator(Orchestrator):
    """Extended orchestrator for C-Suite specific behaviors"""
    
    def __init__(self, agents: List[CSuiteAgent], max_turns: int = 40):
        super().__init__(agents, max_turns)
        
        # Special C-Suite configurations
        self.agent_specialties = {agent.name: agent.specialty for agent in agents}
        self.scenario_state = {}
    
    async def run_scenario(self, scenario_name: str, initial_prompt: str, max_turns: int = None) -> Dict:
        """Run a specific C-Suite scenario"""
        
        # Initialize scenario state
        self.scenario_state = {
            "name": scenario_name,
            "start_time": asyncio.get_event_loop().time(),
            "events": [],
            "decisions": [],
            "current_phase": "initialization"
        }
        
        # Adjust max turns if specified
        original_max_turns = self.max_turns
        if max_turns:
            self.max_turns = max_turns
        
        try:
            # Run the orchestration
            await self.orchestrate(initial_prompt)
            
            # Finalize scenario
            self.scenario_state["end_time"] = asyncio.get_event_loop().time()
            self.scenario_state["duration"] = self.scenario_state["end_time"] - self.scenario_state["start_time"]
            self.scenario_state["current_phase"] = "completed"
            
            # Save scenario log
            scenario_filename = f"{scenario_name.lower().replace(' ', '_')}_log.json"
            self.save_conversation_log(scenario_filename)
            
            # Generate scenario summary
            summary = await self._generate_scenario_summary()
            
            return {
                "scenario": scenario_name,
                "duration": self.scenario_state["duration"],
                "turn_count": len(self.conversation_log) - 1,  # Subtract initial prompt
                "summary": summary,
                "log_file": scenario_filename
            }
            
        finally:
            # Restore original max turns
            self.max_turns = original_max_turns
    
    async def _generate_scenario_summary(self) -> Dict:
        """Generate a summary of the scenario execution"""
        
        # Find agents with relevant specialties
        summary_agent = next((a for a in self.agents if a.specialty == "pattern_recognition"), None)
        if not summary_agent:
            summary_agent = self.agents[0]
            
        # Create a prompt for the summary
        conversation_extract = "\n".join([
            f"{entry['agent']}: {entry['message'][:100]}..." 
            for entry in self.conversation_log[:10]
        ])
        
        summary_prompt = f"""
        Please summarize this conversation scenario:
        
        Scenario: {self.scenario_state['name']}
        Duration: {self.scenario_state['duration']:.2f} seconds
        Turns: {len(self.conversation_log) - 1}
        
        Conversation extract:
        {conversation_extract}
        
        Please provide:
        1. Key events and decisions
        2. Top contributions by agent
        3. Overall effectiveness
        """
        
        # Generate the summary
        summary = await summary_agent.speak(summary_prompt, include_history=False)
        
        return {
            "text": summary,
            "agent": summary_agent.name,
            "key_metrics": {
                "turns": len(self.conversation_log) - 1,
                "duration": self.scenario_state["duration"],
                "unique_agents": len(set(entry["agent"] for entry in self.conversation_log if entry["agent"] != "User"))
            }
        }


async def run_demo_scenario(scenario_name: str, scenario_prompt: str):
    """Run a demonstration scenario with the C-Suite agents"""
    
    try:
        # Create the C-Suite agents
        agents = await create_csuite_agents()
        
        # Create the C-Suite orchestrator
        orchestrator = CSuiteOrchestrator(agents, max_turns=40)
        
        # Run the scenario
        logger.info(f"Starting demo scenario: {scenario_name}")
        result = await orchestrator.run_scenario(scenario_name, scenario_prompt)
        
        # Log the results
        logger.info(f"Completed scenario: {scenario_name}")
        logger.info(f"Duration: {result['duration']:.2f} seconds")
        logger.info(f"Turns: {result['turn_count']}")
        logger.info(f"Log file: {result['log_file']}")
        logger.info(f"Summary: {result['summary']['text'][:100]}...")
        
        return result
        
    except Exception as e:
        logger.error(f"Error running scenario {scenario_name}: {str(e)}")
        raise


async def main():
    """Run the C-Suite demo scenarios"""
    
    # Define the demo scenarios
    scenarios = [
        {
            "name": "Product Launch Preparation",
            "prompt": """
            I need help preparing for our product launch next week. We need to finalize messaging, 
            ensure legal compliance of our claims, and conduct competitive analysis. Our product 
            is an AI-powered analytics platform for enterprise customers.
            """
        },
        {
            "name": "Datacenter Crisis",
            "prompt": """
            URGENT: We have a critical issue at our data center. The temperature is rising 
            rapidly (84°F and increasing) and our monitoring system shows unusual activity. 
            Help me diagnose and resolve this situation immediately.
            """
        },
        {
            "name": "Quantum Computing Optimization",
            "prompt": """
            Our research team is working on quantum circuit optimization for error mitigation. 
            We're currently using a surface code variant but seeing high qubit overhead. 
            Can you help us improve our approach?
            """
        },
        {
            "name": "Health Improvement Plan",
            "prompt": """
            I want to improve my physical fitness and energy levels. I have a sedentary job, 
            occasionally jog on weekends, and often feel tired by mid-afternoon. Can you 
            create a personalized health improvement plan for me?
            """
        },
        {
            "name": "Contract Review Deadline",
            "prompt": """
            I just received a 47-page vendor contract for software licensing that needs review 
            and revisions by Monday morning. It's Friday afternoon now. Can you help me analyze 
            the contract, identify concerning clauses, and prepare revisions?
            """
        }
    ]
    
    # Run each scenario in sequence
    results = []
    for scenario in scenarios:
        result = await run_demo_scenario(scenario["name"], scenario["prompt"])
        results.append(result)
        await asyncio.sleep(1)  # Brief pause between scenarios
    
    # Print overall summary
    logger.info("C-Suite Demo Scenarios Completed")
    logger.info(f"Total scenarios: {len(results)}")
    for result in results:
        logger.info(f"- {result['scenario']}: {result['turn_count']} turns in {result['duration']:.2f} seconds")
    
    return results


# This script can be run independently or imported
if __name__ == "__main__":
    asyncio.run(main()) 