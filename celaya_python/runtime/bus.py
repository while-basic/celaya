# ----------------------------------------------------------------------------
#  File:        bus.py
#  Project:     Celaya Solutions
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Async pub-sub wrapper around asyncio.Queue
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

"""
Bus module for inter-agent communication.

Provides an async pub-sub wrapper around asyncio.Queue with 1 global topic
and N private queues.
"""

import asyncio
import logging
from typing import Any, Dict, List, Set, Callable, Awaitable, Optional
import uuid

logger = logging.getLogger(__name__)

class Message:
    """Message class for the bus system."""
    
    def __init__(self, topic: str, payload: Any, sender_id: str = None):
        """
        Initialize a new message.
        
        Args:
            topic: The topic this message is published on
            payload: The message payload
            sender_id: Optional identifier for the sender
        """
        self.id = str(uuid.uuid4())
        self.topic = topic
        self.payload = payload
        self.sender_id = sender_id
        self.timestamp = asyncio.get_event_loop().time()
    
    def __repr__(self):
        return f"Message(id={self.id}, topic={self.topic}, sender={self.sender_id})"


class Bus:
    """
    Async pub-sub message bus.
    
    Provides a global topic and private queues for inter-agent communication.
    """
    
    def __init__(self):
        """Initialize the message bus."""
        self._queues: Dict[str, asyncio.Queue] = {}
        self._subscriptions: Dict[str, Set[str]] = {}
        self._handlers: Dict[str, List[Callable[[Message], Awaitable[None]]]] = {}
        
        # Create the global topic
        self._subscriptions["global.bus"] = set()
        
        logger.info("Message bus initialized")
    
    def create_private_queue(self, queue_id: str) -> None:
        """
        Create a private queue for an agent or component.
        
        Args:
            queue_id: Unique identifier for the queue
        """
        if queue_id in self._queues:
            logger.warning(f"Queue '{queue_id}' already exists. Ignoring request.")
            return
            
        self._queues[queue_id] = asyncio.Queue()
        logger.debug(f"Created private queue '{queue_id}'")
    
    def subscribe(self, subscriber_id: str, topic: str) -> None:
        """
        Subscribe to a topic.
        
        Args:
            subscriber_id: Unique identifier for the subscriber
            topic: The topic to subscribe to
        """
        if topic not in self._subscriptions:
            self._subscriptions[topic] = set()
            
        self._subscriptions[topic].add(subscriber_id)
        
        # Create queue if it doesn't exist
        if subscriber_id not in self._queues:
            self.create_private_queue(subscriber_id)
            
        logger.debug(f"'{subscriber_id}' subscribed to topic '{topic}'")
    
    def unsubscribe(self, subscriber_id: str, topic: str) -> None:
        """
        Unsubscribe from a topic.
        
        Args:
            subscriber_id: Unique identifier for the subscriber
            topic: The topic to unsubscribe from
        """
        if topic in self._subscriptions and subscriber_id in self._subscriptions[topic]:
            self._subscriptions[topic].remove(subscriber_id)
            logger.debug(f"'{subscriber_id}' unsubscribed from topic '{topic}'")
    
    def register_handler(self, topic: str, handler: Callable[[Message], Awaitable[None]]) -> None:
        """
        Register a handler function for a topic.
        
        Args:
            topic: The topic to handle messages for
            handler: Async function that handles messages for this topic
        """
        if topic not in self._handlers:
            self._handlers[topic] = []
            
        self._handlers[topic].append(handler)
        logger.debug(f"Registered handler for topic '{topic}'")
    
    def publish(self, topic: str, payload: Any, sender_id: Optional[str] = None) -> None:
        """
        Publish a message to a topic.
        
        Args:
            topic: The topic to publish to
            payload: The message payload
            sender_id: Optional identifier for the sender
        """
        message = Message(topic, payload, sender_id)
        
        # Handle direct subscribers
        if topic in self._subscriptions:
            for subscriber_id in self._subscriptions[topic]:
                if subscriber_id in self._queues:
                    self._queues[subscriber_id].put_nowait(message)
        
        # Handle registered handlers
        if topic in self._handlers:
            for handler in self._handlers[topic]:
                asyncio.create_task(handler(message))
                
        logger.debug(f"Published message to '{topic}': {message}")
    
    async def subscribe_and_consume(self, subscriber_id: str, topic: str) -> asyncio.Queue:
        """
        Subscribe to a topic and return a queue for consuming messages.
        
        Args:
            subscriber_id: Unique identifier for the subscriber
            topic: The topic to subscribe to
            
        Returns:
            asyncio.Queue: A queue that will receive messages from the topic
        """
        self.subscribe(subscriber_id, topic)
        return self._queues[subscriber_id]
    
    async def get_message(self, subscriber_id: str) -> Message:
        """
        Get the next message for a subscriber.
        
        Args:
            subscriber_id: Unique identifier for the subscriber
            
        Returns:
            Message: The next message in the queue
            
        Raises:
            KeyError: If the subscriber doesn't have a queue
        """
        if subscriber_id not in self._queues:
            raise KeyError(f"No queue exists for subscriber '{subscriber_id}'")
            
        return await self._queues[subscriber_id].get()
    
    def get_queue(self, subscriber_id: str) -> asyncio.Queue:
        """
        Get the queue for a subscriber.
        
        Args:
            subscriber_id: Unique identifier for the subscriber
            
        Returns:
            asyncio.Queue: The subscriber's queue
            
        Raises:
            KeyError: If the subscriber doesn't have a queue
        """
        if subscriber_id not in self._queues:
            raise KeyError(f"No queue exists for subscriber '{subscriber_id}'")
            
        return self._queues[subscriber_id] 