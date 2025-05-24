# ----------------------------------------------------------------------------
#  File:        __init__.py
#  Project:     Celaya Solutions
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Agent registration functionality for Celaya
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

"""
Celaya agent registration module.

This module provides functionality for registering agents with the Celaya runtime.
"""

import functools
import inspect
import logging
from typing import Callable, Dict, List, Type, Any

# Registry to store all registered agent classes
_agent_registry: Dict[str, Type] = {}
logger = logging.getLogger(__name__)

def register_agent(cls=None, *, name: str = None):
    """
    Decorator to register an agent class with the Celaya runtime.
    
    This allows external modules to register agents without modifying core code.
    
    Args:
        cls: The class to register
        name: Optional name for the agent. If not provided, uses the class name
        
    Returns:
        The decorated class
    """
    def decorator(cls):
        agent_name = name or cls.__name__
        if agent_name in _agent_registry:
            logger.warning(f"Agent '{agent_name}' is already registered. Overwriting previous registration.")
        _agent_registry[agent_name] = cls
        logger.info(f"Agent '{agent_name}' registered successfully")
        return cls
        
    if cls is None:
        return decorator
    return decorator(cls)

def get_registered_agents() -> Dict[str, Type]:
    """
    Returns a dictionary of all registered agents.
    
    Returns:
        Dict[str, Type]: Dictionary mapping agent names to agent classes
    """
    return _agent_registry.copy()

def get_agent(name: str) -> Type:
    """
    Get a registered agent class by name.
    
    Args:
        name: The name of the agent to retrieve
        
    Returns:
        The agent class
        
    Raises:
        KeyError: If no agent with the given name is registered
    """
    if name not in _agent_registry:
        raise KeyError(f"No agent registered with name '{name}'")
    return _agent_registry[name]
