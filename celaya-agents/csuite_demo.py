# ----------------------------------------------------------------------------
#  File:        csuite_demo.py
#  Project:     Celaya Solutions (Agent Orchestration)
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Demonstration of C-Suite agents collaboration with mock agents
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import asyncio
import json
import logging
import sys
import os
from typing import List, Dict, Any

# Import the orchestration components
from csuite_integration import CSuiteOrchestrator, create_csuite_agents
from mock_csuite_agents import MockCSuiteAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CSuiteDemo")

# Define the demo scenarios from the csuite_demo_scenarios.md
DEMO_SCENARIOS = [
    {
        "name": "One Thousand Brains in Perfect Harmony",
        "prompt": """
        I need help preparing for our product launch next week. We need to finalize messaging, 
        ensure legal compliance of our claims, and conduct competitive analysis. Our product 
        is an AI-powered analytics platform for enterprise customers.
        """
    },
    {
        "name": "The Datacenter Crisis",
        "prompt": """
        URGENT: We have a critical issue at our data center. The temperature is rising 
        rapidly (84°F and increasing) and our monitoring system shows unusual activity. 
        Help me diagnose and resolve this situation immediately.
        """
    },
    {
        "name": "The Quantum Breakthrough",
        "prompt": """
        Our research team is working on quantum circuit optimization for error mitigation. 
        We're currently using a surface code variant but seeing high qubit overhead. 
        Can you help us improve our approach?
        """
    },
    {
        "name": "The Health Coach",
        "prompt": """
        I want to improve my physical fitness and energy levels. I have a sedentary job, 
        occasionally jog on weekends, and often feel tired by mid-afternoon. Can you 
        create a personalized health improvement plan for me?
        """
    },
    {
        "name": "The Legal Deadline",
        "prompt": """
        I just received a 47-page vendor contract for software licensing that needs review 
        and revisions by Monday morning. It's Friday afternoon now. Can you help me analyze 
        the contract, identify concerning clauses, and prepare revisions?
        """
    }
]


async def create_mock_csuite_agents() -> List[MockCSuiteAgent]:
    """Create mock C-Suite agents for demonstration"""
    
    # Define agent configurations (same as in csuite_integration.py)
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
    
    # Create the mock agents
    agents = []
    for config in agent_configs:
        agent = MockCSuiteAgent(
            name=config["name"],
            url="http://localhost:11434",  # Dummy URL, won't be used
            model="llama3",                # Dummy model, won't be used
            system_prompt=config["system_prompt"],
            role=config["role"],
            specialty=config["specialty"],
            interrupt_threshold=config["interrupt_threshold"],
            interrupt_keywords=config["interrupt_keywords"]
        )
        agents.append(agent)
        logger.info(f"Created mock C-Suite agent: {agent.name}")
    
    return agents


async def run_mock_scenario(scenario_name: str, scenario_prompt: str, max_turns: int = 15):
    """Run a demonstration scenario with the mock C-Suite agents"""
    
    try:
        # Create the mock C-Suite agents
        agents = await create_mock_csuite_agents()
        
        # Create the C-Suite orchestrator
        orchestrator = CSuiteOrchestrator(agents, max_turns=max_turns)
        
        # Create output directory if it doesn't exist
        os.makedirs("scenario_logs", exist_ok=True)
        
        # Run the scenario
        logger.info(f"Starting demo scenario: {scenario_name}")
        logger.info(f"Initial prompt: {scenario_prompt.strip()}")
        
        # Run the orchestration
        await orchestrator.orchestrate(scenario_prompt)
        
        # Save conversation log
        scenario_filename = f"scenario_logs/{scenario_name.lower().replace(' ', '_')}_log.json"
        orchestrator.save_conversation_log(scenario_filename)
        
        # Log completion
        logger.info(f"Completed scenario: {scenario_name}")
        logger.info(f"Log file: {scenario_filename}")
        
        # Pretty print the conversation for the console
        print("\n" + "="*80)
        print(f"SCENARIO: {scenario_name}")
        print("="*80)
        
        for i, entry in enumerate(orchestrator.conversation_log):
            if i == 0:
                print(f"\nUSER: {entry['message'].strip()}\n")
            else:
                print(f"{entry['agent']}: {entry['message'].strip()}")
                if i < len(orchestrator.conversation_log) - 1:
                    print("-"*40)
        
        print("\n" + "="*80 + "\n")
        
        return scenario_filename
        
    except Exception as e:
        logger.error(f"Error running scenario {scenario_name}: {str(e)}")
        raise


async def run_all_scenarios():
    """Run all demonstration scenarios"""
    
    results = []
    
    for scenario in DEMO_SCENARIOS:
        log_file = await run_mock_scenario(
            scenario["name"], 
            scenario["prompt"],
            max_turns=15  # Limit turns for demonstration
        )
        results.append({
            "scenario": scenario["name"],
            "log_file": log_file
        })
        
        # Brief pause between scenarios
        await asyncio.sleep(1)
    
    # Generate HTML summary report
    generate_html_report(results)
    
    return results


def generate_html_report(results: List[Dict[str, str]]):
    """Generate an HTML report of all scenario runs"""
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Celaya C-Suite Demo Results</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #2c3e50; }
            h2 { color: #3498db; margin-top: 30px; }
            .scenario { border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px; }
            .message { margin: 10px 0; padding: 10px; border-radius: 3px; }
            .user { background-color: #f8f9fa; }
            .agent { background-color: #e9f7fe; margin-left: 20px; }
            .agent-name { font-weight: bold; color: #2980b9; }
            hr { border: 0; border-top: 1px solid #eee; margin: 15px 0; }
        </style>
    </head>
    <body>
        <h1>Celaya C-Suite Demo Results</h1>
        <p>This report shows the results of the C-Suite agent orchestration demo scenarios.</p>
    """
    
    for result in results:
        scenario_name = result["scenario"]
        log_file = result["log_file"]
        
        html_content += f"<h2>{scenario_name}</h2>\n<div class='scenario'>\n"
        
        # Read the log file
        try:
            with open(log_file, 'r') as f:
                log_data = json.load(f)
                
            for i, entry in enumerate(log_data):
                if i == 0:
                    html_content += f"<div class='message user'><strong>USER:</strong> {entry['message']}</div>\n"
                else:
                    html_content += f"<div class='message agent'><span class='agent-name'>{entry['agent']}:</span> {entry['message']}</div>\n"
                    
        except Exception as e:
            html_content += f"<p>Error loading log file: {str(e)}</p>\n"
            
        html_content += "</div>\n"
    
    html_content += """
    </body>
    </html>
    """
    
    # Write the HTML report
    with open("csuite_demo_report.html", "w") as f:
        f.write(html_content)
    
    logger.info("Generated HTML report: csuite_demo_report.html")


async def main():
    """Main entry point for the C-Suite demo"""
    
    logger.info("Starting Celaya C-Suite Demo")
    
    # Run all scenarios
    results = await run_all_scenarios()
    
    logger.info("Demo completed.")
    logger.info(f"Total scenarios: {len(results)}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main()) 