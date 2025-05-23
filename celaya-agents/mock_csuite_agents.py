# ----------------------------------------------------------------------------
#  File:        mock_csuite_agents.py
#  Project:     Celaya Solutions (Agent Orchestration)
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Mock implementation of C-Suite agents for demonstration purposes
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import asyncio
import logging
from typing import List, Dict, Any, Optional

# Import the C-Suite agent class to extend
from csuite_integration import CSuiteAgent

# Configure logging
logger = logging.getLogger("MockCSuite")

class MockCSuiteAgent(CSuiteAgent):
    """A mock version of CSuiteAgent that doesn't make actual API calls"""
    
    async def speak(self, prompt: str, include_history: bool = True, orchestrator = None) -> str:
        """Generate a simulated response based on agent specialty without making API calls"""
        
        # Check for specialty-specific keywords that should trigger interrupts
        if orchestrator and self.should_interrupt(prompt):
            priority = self.calculate_interrupt_priority(prompt)
            await orchestrator.request_interrupt(self, priority, prompt)
        
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Update conversation history
        if include_history:
            self.conversation_history.append({"role": "user", "content": prompt})
        
        # Generate response based on agent specialty
        response = self._generate_themed_response(prompt)
        
        # Update conversation history
        if include_history:
            self.conversation_history.append({"role": "assistant", "content": response})
            
        return response
    
    def _generate_themed_response(self, prompt: str) -> str:
        """Generate a response based on the agent's specialty"""
        
        # Extract a relevant part of the prompt to reference in the response
        prompt_extract = prompt.split()[-10:] if len(prompt.split()) > 10 else prompt.split()
        prompt_ref = " ".join(prompt_extract)
        
        # Generic starting phrase based on agent's role
        role_phrase = self._get_role_phrase()
        
        # Agent-specific responses based on specialty
        if self.name == "Lyra":
            return f"{role_phrase} I'm monitoring system resources and ensuring all agents are functioning optimally. For the task related to {prompt_ref}, I'll ensure continued operation."
            
        elif self.name == "Otto":
            return f"{role_phrase} I'll coordinate our approach to {prompt_ref}. Let me bring in the appropriate specialists to address different aspects of this challenge."
            
        elif self.name == "Core":
            return f"{role_phrase} After analyzing {prompt_ref}, I've developed a strategic approach with three key components. First, we should focus on the underlying patterns..."
            
        elif self.name == "Verdict":
            return f"{role_phrase} I've reviewed the legal implications of {prompt_ref}. There are several compliance considerations we need to address, particularly regarding data handling."
            
        elif self.name == "Vitals":
            return f"{role_phrase} From a health perspective, {prompt_ref} requires careful consideration of biological factors. Let me analyze the key biomarkers and physiological patterns."
            
        elif self.name == "Beacon":
            return f"{role_phrase} I've researched the latest information about {prompt_ref}. According to recent studies from Stanford and MIT, there are three relevant approaches we should consider."
            
        elif self.name == "Sentinel":
            return f"{role_phrase} I've identified potential security concerns related to {prompt_ref}. We need to implement proper safeguards to protect sensitive information."
            
        elif self.name == "Theory":
            return f"{role_phrase} The scientific principles behind {prompt_ref} are fascinating. Let me formulate a theoretical model that explains the underlying mechanisms."
            
        elif self.name == "Lens":
            return f"{role_phrase} Analyzing the patterns in {prompt_ref}, I can identify three key insights that might not be immediately obvious. First, there's a correlation between..."
            
        elif self.name == "Volt":
            return f"{role_phrase} From an engineering perspective, {prompt_ref} requires careful consideration of system architecture and technical constraints."
            
        elif self.name == "Echo":
            return f"{role_phrase} Looking at our historical data related to {prompt_ref}, I notice we've encountered similar situations in the past. We can learn from those experiences."
            
        elif self.name == "Luma":
            return f"{role_phrase} I can help personalize the approach to {prompt_ref} based on your preferences and routines. Would you like me to create a customized schedule?"
            
        elif self.name == "Clarity":
            return f"{role_phrase} I've documented all the key information about {prompt_ref} for future reference. This will ensure we have a complete audit trail of decisions and actions."
            
        else:
            return f"As {self.name}, I'm analyzing {prompt_ref} and will provide my specialized insights shortly."
    
    def _get_role_phrase(self) -> str:
        """Return a role-appropriate starting phrase"""
        
        if self.role == "operating_system":
            return f"As the Operating System, I'm managing our collective resources."
            
        elif self.role == "orchestrator":
            return f"I'll coordinate our team's approach."
            
        elif self.role == "strategist":
            return f"From a strategic perspective,"
            
        elif self.role == "legal":
            return f"From a legal standpoint,"
            
        elif self.role == "bioengineer":
            return f"Based on biometric analysis,"
            
        elif self.role == "researcher":
            return f"My research indicates that"
            
        elif self.role == "security":
            return f"After a security assessment,"
            
        elif self.role == "scientist":
            return f"The scientific analysis shows"
            
        elif self.role == "analyst":
            return f"My pattern analysis reveals"
            
        elif self.role == "engineer":
            return f"From an engineering perspective,"
            
        elif self.role == "memory":
            return f"Reflecting on past interactions,"
            
        elif self.role == "companion":
            return f"To personalize this for you,"
            
        elif self.role == "historian":
            return f"For the historical record,"
            
        else:
            return f"As {self.name},"
            

def create_mock_csuite_responses() -> Dict[str, List[str]]:
    """Create a dictionary of sample responses for each C-Suite agent"""
    
    responses = {
        "Lyra": [
            "I'm monitoring all system resources and ensuring optimal agent performance. All systems are operating within expected parameters.",
            "I've detected a potential resource contention issue. I'm reallocating memory to ensure continued smooth operation.",
            "I've initialized a backup of our conversation state to ensure continuity in case of any interruptions."
        ],
        "Otto": [
            "I'll coordinate our approach to this task. Let me bring in Core for strategy, Beacon for research, and Verdict for legal assessment.",
            "This situation requires specialized expertise. I'm routing this to Volt for technical analysis and Sentinel for security assessment.",
            "Let me organize our collective response. I'll sequence our agents for maximum efficiency based on task dependencies."
        ],
        "Core": [
            "I've analyzed the situation and developed a three-part strategy. First, we should address the immediate concerns, then develop a medium-term plan, and finally establish preventative measures.",
            "This presents an opportunity for innovation. By combining approaches from different domains, we can create a novel solution.",
            "Let me reframe this challenge. Instead of seeing it as a problem to solve, we can view it as an opportunity to redesign the entire process."
        ],
        "Verdict": [
            "From a legal perspective, there are several compliance issues to consider. We need to ensure we're adhering to GDPR, CCPA, and industry-specific regulations.",
            "I've reviewed the contract language and identified three clauses that present potential liability. We should revise these to limit our exposure.",
            "For proper documentation and compliance, I'll prepare the necessary audit trail with timestamps and decision justifications."
        ],
        "Vitals": [
            "Based on the biometric data available, I recommend a personalized approach that accounts for circadian rhythms and individual metabolic factors.",
            "The health implications of this situation involve complex interactions between multiple physiological systems. Let me analyze the key markers.",
            "From a bioengineering perspective, we can optimize this process by working with natural biological mechanisms rather than against them."
        ],
        "Beacon": [
            "I've researched the latest studies on this topic. Research from Stanford, MIT, and Oxford all point to an emerging consensus around three key principles.",
            "Let me verify that information against reliable sources. According to the latest peer-reviewed literature and industry reports, the situation is more nuanced.",
            "I've compiled a comprehensive set of references on this topic, including academic papers, industry whitepapers, and regulatory guidelines."
        ],
        "Sentinel": [
            "I've detected a potential security vulnerability that requires immediate attention. We should implement additional authentication measures.",
            "From a safety perspective, we need to establish clear boundaries around data usage and implement strict access controls.",
            "I'm monitoring for any attempt to manipulate or misuse this conversation. All activities are being logged for security audit purposes."
        ],
        "Theory": [
            "Let me formulate a theoretical model that explains these observations. If we represent the system as a dynamic network with feedback loops...",
            "This phenomenon can be explained by applying principles from quantum mechanics and information theory to create a unified mathematical framework.",
            "I've developed a testable hypothesis that accounts for the observed data anomalies. We can validate this through a series of controlled experiments."
        ],
        "Lens": [
            "Analyzing the patterns in the data, I can identify three non-obvious correlations that suggest a hidden causal relationship.",
            "When we visualize this information as a network graph rather than a linear sequence, a clear pattern emerges that wasn't previously visible.",
            "I've calculated the statistical significance of these trends. The p-value of 0.003 suggests this is highly unlikely to be random chance."
        ],
        "Volt": [
            "From an engineering perspective, we can interface with the hardware systems using a secure API that provides real-time monitoring and control capabilities.",
            "I've analyzed the system architecture and identified a potential bottleneck in the data processing pipeline that's causing the observed latency.",
            "Let me design a technical solution that balances performance, security, and scalability while working within the existing infrastructure constraints."
        ],
        "Echo": [
            "Looking at our historical interactions, I notice we've encountered similar situations three times before. Each time, the most successful approach was...",
            "I've analyzed our learning trajectory over time and identified areas where we've made significant progress and others where we continue to face challenges.",
            "Reflecting on past outcomes, I can see a pattern in how we approach these problems. Let's incorporate those lessons into our current strategy."
        ],
        "Luma": [
            "Based on your personal preferences and daily routine, I've created a customized approach that will integrate seamlessly into your schedule.",
            "I notice this aligns with your interest in efficiency and minimal disruption. Would you like me to prioritize those aspects in our solution?",
            "To make this more comfortable for you, I've adjusted the tone and complexity to match your preferred communication style."
        ],
        "Clarity": [
            "I've documented this entire process with timestamped records of all decisions and their justifications for future reference.",
            "For the official record, I'm capturing the key points of this interaction, including the problem statement, proposed solutions, and final decisions.",
            "I've created a complete audit trail of this conversation that can be referenced in the future if questions arise about the reasoning behind these decisions."
        ]
    }
    
    return responses 