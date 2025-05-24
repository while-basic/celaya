# ----------------------------------------------------------------------------
#  File:        keyring.py
#  Project:     Celaya Solutions
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: ED25519 key management for Lyra OS
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

"""
Keyring module for Lyra OS.

Handles the generation and loading of ED25519 keys for agent authentication.
"""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Dict, Tuple, Optional, Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

logger = logging.getLogger(__name__)

class Keyring:
    """
    Keyring for managing ED25519 keys.
    
    Handles the generation and loading of ED25519 keys for agent authentication.
    """
    
    def __init__(self, keystore_path: str = None):
        """
        Initialize the keyring.
        
        Args:
            keystore_path: Path to the keystore directory
        """
        self.keystore_path = keystore_path or os.path.expanduser("~/.lyra/keys")
        self.private_keys: Dict[str, ed25519.Ed25519PrivateKey] = {}
        self.public_keys: Dict[str, ed25519.Ed25519PublicKey] = {}
        
        # Ensure the keystore directory exists
        os.makedirs(self.keystore_path, exist_ok=True)
        
        logger.info(f"Keyring initialized with keystore at {self.keystore_path}")
    
    def generate_keypair(self, entity_id: str) -> Tuple[str, str]:
        """
        Generate a new ED25519 keypair.
        
        Args:
            entity_id: Identifier for the entity
            
        Returns:
            Tuple of (public_key_b64, private_key_b64)
        """
        # Generate a new keypair
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        # Store the keys
        self.private_keys[entity_id] = private_key
        self.public_keys[entity_id] = public_key
        
        # Serialize the keys to bytes
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        # Convert to base64 for storage/transmission
        private_b64 = base64.b64encode(private_bytes).decode('utf-8')
        public_b64 = base64.b64encode(public_bytes).decode('utf-8')
        
        # Save to keystore
        self._save_keys(entity_id, public_b64, private_b64)
        
        logger.info(f"Generated new keypair for {entity_id}")
        
        return (public_b64, private_b64)
    
    def load_keypair(self, entity_id: str) -> Optional[Tuple[str, str]]:
        """
        Load an ED25519 keypair from the keystore.
        
        Args:
            entity_id: Identifier for the entity
            
        Returns:
            Tuple of (public_key_b64, private_key_b64) or None if not found
        """
        key_path = os.path.join(self.keystore_path, f"{entity_id}.json")
        
        if not os.path.exists(key_path):
            logger.warning(f"No keypair found for {entity_id}")
            return None
        
        try:
            with open(key_path, 'r') as f:
                key_data = json.load(f)
                
            public_b64 = key_data.get("public_key")
            private_b64 = key_data.get("private_key")
            
            if not public_b64 or not private_b64:
                logger.error(f"Invalid key data for {entity_id}")
                return None
                
            # Deserialize the keys
            private_bytes = base64.b64decode(private_b64)
            public_bytes = base64.b64decode(public_b64)
            
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)
            
            # Store the keys
            self.private_keys[entity_id] = private_key
            self.public_keys[entity_id] = public_key
            
            logger.info(f"Loaded keypair for {entity_id}")
            
            return (public_b64, private_b64)
        except Exception as e:
            logger.error(f"Error loading keypair for {entity_id}: {e}", exc_info=True)
            return None
    
    def get_or_create_keypair(self, entity_id: str) -> Tuple[str, str]:
        """
        Get an existing keypair or create a new one if it doesn't exist.
        
        Args:
            entity_id: Identifier for the entity
            
        Returns:
            Tuple of (public_key_b64, private_key_b64)
        """
        result = self.load_keypair(entity_id)
        
        if result is None:
            return self.generate_keypair(entity_id)
            
        return result
    
    def sign(self, entity_id: str, data: bytes) -> Optional[str]:
        """
        Sign data with an entity's private key.
        
        Args:
            entity_id: Identifier for the entity
            data: Data to sign
            
        Returns:
            Base64-encoded signature or None if the key doesn't exist
        """
        if entity_id not in self.private_keys:
            if not self.load_keypair(entity_id):
                logger.warning(f"No private key available for {entity_id}")
                return None
        
        private_key = self.private_keys[entity_id]
        signature = private_key.sign(data)
        
        return base64.b64encode(signature).decode('utf-8')
    
    def verify(self, entity_id: str, data: bytes, signature_b64: str) -> bool:
        """
        Verify a signature with an entity's public key.
        
        Args:
            entity_id: Identifier for the entity
            data: Data that was signed
            signature_b64: Base64-encoded signature
            
        Returns:
            True if the signature is valid, False otherwise
        """
        if entity_id not in self.public_keys:
            if not self.load_keypair(entity_id):
                logger.warning(f"No public key available for {entity_id}")
                return False
        
        public_key = self.public_keys[entity_id]
        signature = base64.b64decode(signature_b64)
        
        try:
            public_key.verify(signature, data)
            return True
        except Exception:
            return False
    
    def _save_keys(self, entity_id: str, public_b64: str, private_b64: str):
        """
        Save keys to the keystore.
        
        Args:
            entity_id: Identifier for the entity
            public_b64: Base64-encoded public key
            private_b64: Base64-encoded private key
        """
        key_path = os.path.join(self.keystore_path, f"{entity_id}.json")
        
        key_data = {
            "entity_id": entity_id,
            "public_key": public_b64,
            "private_key": private_b64,
            "type": "ed25519"
        }
        
        with open(key_path, 'w') as f:
            json.dump(key_data, f, indent=2)
            
        logger.debug(f"Saved keys for {entity_id} to {key_path}")
    
    def get_public_key(self, entity_id: str) -> Optional[str]:
        """
        Get an entity's public key.
        
        Args:
            entity_id: Identifier for the entity
            
        Returns:
            Base64-encoded public key or None if not found
        """
        if entity_id in self.public_keys:
            public_key = self.public_keys[entity_id]
            public_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            return base64.b64encode(public_bytes).decode('utf-8')
        
        # Try to load from keystore
        result = self.load_keypair(entity_id)
        
        if result:
            return result[0]
            
        return None 