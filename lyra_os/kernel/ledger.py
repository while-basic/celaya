# ----------------------------------------------------------------------------
#  File:        ledger.py
#  Project:     Celaya Solutions
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Trust weights and CID cache for Lyra OS
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

"""
Ledger module for Lyra OS.

Manages trust weights and CID cache for agent consensus.
"""

import hashlib
import json
import logging
import os
import time
from typing import Dict, List, Any, Optional, Set, Tuple

logger = logging.getLogger(__name__)

class Ledger:
    """
    Ledger for managing trust weights and CID cache.
    
    Stores and manages trust weights for agents and maintains a cache of
    content identifiers (CIDs) for consensus records.
    """
    
    def __init__(self, ledger_path: str = None):
        """
        Initialize the ledger.
        
        Args:
            ledger_path: Path to the ledger directory
        """
        self.ledger_path = ledger_path or os.path.expanduser("~/.lyra/ledger")
        self.trust_weights: Dict[str, float] = {}
        self.cid_cache: Dict[str, Dict[str, Any]] = {}
        self.trust_history: Dict[str, List[Tuple[float, float]]] = {}  # agent_id -> [(timestamp, weight)]
        
        # Ensure the ledger directory exists
        os.makedirs(self.ledger_path, exist_ok=True)
        
        # Load existing data
        self._load_ledger()
        
        logger.info(f"Ledger initialized with path {self.ledger_path}")
    
    def _load_ledger(self):
        """Load the ledger data from disk."""
        trust_path = os.path.join(self.ledger_path, "trust_weights.json")
        cid_path = os.path.join(self.ledger_path, "cid_cache.json")
        
        # Load trust weights
        if os.path.exists(trust_path):
            try:
                with open(trust_path, 'r') as f:
                    data = json.load(f)
                    self.trust_weights = data.get("weights", {})
                    self.trust_history = data.get("history", {})
                    
                logger.info(f"Loaded trust weights for {len(self.trust_weights)} agents")
            except Exception as e:
                logger.error(f"Error loading trust weights: {e}", exc_info=True)
        
        # Load CID cache
        if os.path.exists(cid_path):
            try:
                with open(cid_path, 'r') as f:
                    self.cid_cache = json.load(f)
                    
                logger.info(f"Loaded {len(self.cid_cache)} CIDs from cache")
            except Exception as e:
                logger.error(f"Error loading CID cache: {e}", exc_info=True)
    
    def _save_trust_weights(self):
        """Save trust weights to disk."""
        trust_path = os.path.join(self.ledger_path, "trust_weights.json")
        
        try:
            data = {
                "weights": self.trust_weights,
                "history": self.trust_history,
                "updated_at": time.time()
            }
            
            with open(trust_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug("Saved trust weights to disk")
        except Exception as e:
            logger.error(f"Error saving trust weights: {e}", exc_info=True)
    
    def _save_cid_cache(self):
        """Save CID cache to disk."""
        cid_path = os.path.join(self.ledger_path, "cid_cache.json")
        
        try:
            with open(cid_path, 'w') as f:
                json.dump(self.cid_cache, f, indent=2)
                
            logger.debug("Saved CID cache to disk")
        except Exception as e:
            logger.error(f"Error saving CID cache: {e}", exc_info=True)
    
    def get_trust_weight(self, agent_id: str) -> float:
        """
        Get the trust weight for an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            The trust weight (0.0-1.0) or 0.5 if not found
        """
        return self.trust_weights.get(agent_id, 0.5)
    
    def set_trust_weight(self, agent_id: str, weight: float):
        """
        Set the trust weight for an agent.
        
        Args:
            agent_id: The ID of the agent
            weight: The trust weight (0.0-1.0)
        """
        # Normalize weight to be between 0 and 1
        weight = max(0.0, min(1.0, weight))
        
        # Update weight
        self.trust_weights[agent_id] = weight
        
        # Update history
        if agent_id not in self.trust_history:
            self.trust_history[agent_id] = []
            
        self.trust_history[agent_id].append((time.time(), weight))
        
        # Prune history if it gets too long
        if len(self.trust_history[agent_id]) > 100:
            self.trust_history[agent_id] = self.trust_history[agent_id][-100:]
        
        # Save to disk
        self._save_trust_weights()
        
        logger.info(f"Set trust weight for agent {agent_id} to {weight}")
    
    def update_trust_weight(self, agent_id: str, delta: float, min_weight: float = 0.1, max_weight: float = 1.0):
        """
        Update the trust weight for an agent by a delta.
        
        Args:
            agent_id: The ID of the agent
            delta: The change in trust weight (-1.0 to 1.0)
            min_weight: Minimum allowable weight
            max_weight: Maximum allowable weight
        """
        current = self.get_trust_weight(agent_id)
        new_weight = current + delta
        
        # Clamp to allowed range
        new_weight = max(min_weight, min(max_weight, new_weight))
        
        self.set_trust_weight(agent_id, new_weight)
        
        logger.info(f"Updated trust weight for agent {agent_id}: {current} -> {new_weight} (delta: {delta})")
    
    def compute_consensus_cid(self, pubkeys: List[str]) -> str:
        """
        Compute a consensus CID from a list of public keys.
        
        Args:
            pubkeys: List of agent public keys
            
        Returns:
            Content identifier (CID) for the consensus
        """
        # Sort pubkeys for deterministic ordering
        sorted_keys = sorted(pubkeys)
        
        # Concatenate keys
        keys_concat = "".join(sorted_keys)
        
        # Compute SHA-256 hash
        hash_obj = hashlib.sha256(keys_concat.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Generate a trust score from the hash (0.0-1.0)
        trust_score = int(hash_hex, 16) % 100 / 100.0
        
        # Create a CID-like string
        cid = f"lyra1{hash_hex}"
        
        logger.debug(f"Computed consensus CID: {cid} (trust score: {trust_score})")
        
        return cid
    
    def store_cid_data(self, cid: str, data: Any):
        """
        Store data associated with a CID.
        
        Args:
            cid: Content identifier
            data: Data to store
        """
        self.cid_cache[cid] = {
            "data": data,
            "timestamp": time.time()
        }
        
        self._save_cid_cache()
        
        logger.info(f"Stored data for CID: {cid}")
    
    def get_cid_data(self, cid: str) -> Optional[Any]:
        """
        Get data associated with a CID.
        
        Args:
            cid: Content identifier
            
        Returns:
            The associated data or None if not found
        """
        if cid not in self.cid_cache:
            return None
            
        return self.cid_cache[cid].get("data")
    
    def pin_to_ipfs(self, data: Any, save_locally: bool = True) -> str:
        """
        Pin data to IPFS and optionally save locally.
        
        This is a placeholder for actual IPFS integration.
        
        Args:
            data: Data to pin
            save_locally: Whether to save the data locally
            
        Returns:
            Content identifier (CID) for the pinned data
        """
        # Convert data to JSON string for hashing
        json_str = json.dumps(data, sort_keys=True)
        
        # Compute SHA-256 hash
        hash_obj = hashlib.sha256(json_str.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Create a CID-like string
        cid = f"lyra1{hash_hex}"
        
        if save_locally:
            self.store_cid_data(cid, data)
            
            # Also save to a file for persistence beyond the cache
            data_dir = os.path.join(self.ledger_path, "data")
            os.makedirs(data_dir, exist_ok=True)
            
            data_path = os.path.join(data_dir, f"{cid}.json")
            
            try:
                with open(data_path, 'w') as f:
                    json.dump(data, f, indent=2)
                    
                logger.debug(f"Saved data for CID {cid} to {data_path}")
            except Exception as e:
                logger.error(f"Error saving data for CID {cid}: {e}", exc_info=True)
        
        logger.info(f"Pinned data to IPFS with CID: {cid}")
        
        return cid
    
    def get_agent_history(self, agent_id: str) -> List[Tuple[float, float]]:
        """
        Get the trust weight history for an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            List of (timestamp, weight) tuples
        """
        return self.trust_history.get(agent_id, []) 