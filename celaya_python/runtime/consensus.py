# ----------------------------------------------------------------------------
#  File:        consensus.py
#  Project:     Celaya Solutions
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Consensus mechanism for multi-agent systems
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

"""
Consensus module for multi-agent systems.

Holds proposal table, vote table, weight calculations, and lock emitters.
"""

import asyncio
import enum
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Any, Callable, Awaitable

from celaya_python.runtime.bus import Bus, Message

logger = logging.getLogger(__name__)

class ProposalStatus(enum.Enum):
    """Status of a consensus proposal."""
    
    PENDING = "pending"
    VOTING = "voting"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class VoteType(enum.Enum):
    """Type of vote on a proposal."""
    
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


@dataclass
class Vote:
    """Vote on a consensus proposal."""
    
    id: str
    proposal_id: str
    agent_id: str
    vote_type: VoteType
    timestamp: float = field(default_factory=time.time)
    signature: Optional[str] = None
    rationale: Optional[str] = None


@dataclass
class Proposal:
    """Consensus proposal."""
    
    id: str
    type: str
    proposer_id: str
    content: Any
    status: ProposalStatus = ProposalStatus.PENDING
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the proposal to a dictionary."""
        result = asdict(self)
        result["status"] = self.status.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Proposal":
        """Create a proposal from a dictionary."""
        # Convert string status to enum
        if "status" in data and isinstance(data["status"], str):
            data["status"] = ProposalStatus(data["status"])
        return cls(**data)


@dataclass
class ConsensusEvent:
    """Base class for consensus events."""
    
    proposal_id: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class ProposalCreatedEvent:
    """Event emitted when a proposal is created."""
    
    proposal: Proposal
    proposal_id: str = field(init=False)
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        self.proposal_id = self.proposal.id


@dataclass
class VoteReceivedEvent:
    """Event emitted when a vote is received."""
    
    vote: Vote
    proposal_id: str = field(init=False)
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        self.proposal_id = self.vote.proposal_id


@dataclass
class ProposalStatusChangedEvent:
    """Event emitted when a proposal's status changes."""
    
    proposal_id: str
    old_status: ProposalStatus
    new_status: ProposalStatus
    timestamp: float = field(default_factory=time.time)


@dataclass
class QuorumReachedEvent:
    """Event emitted when quorum is reached for a proposal."""
    
    proposal_id: str
    result: VoteType
    votes: List[Vote]
    timestamp: float = field(default_factory=time.time)


@dataclass
class SoftLockEvent:
    """Event emitted when a soft lock is initiated."""
    
    proposal_id: str
    duration_sec: float
    reason: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class HardLockEvent:
    """Event emitted when a hard lock is initiated."""
    
    proposal_id: str
    reason: str
    shutdown_requested: bool = False
    timestamp: float = field(default_factory=time.time)


class ConsensusManager:
    """
    Consensus manager for multi-agent systems.
    
    Manages proposals, votes, and consensus decisions.
    """
    
    def __init__(self, bus: Bus, quorum_threshold: float = 0.66):
        """
        Initialize a new consensus manager.
        
        Args:
            bus: The message bus to publish events to
            quorum_threshold: The threshold (0.0-1.0) of weighted votes needed for consensus
        """
        self.bus = bus
        self.quorum_threshold = quorum_threshold
        self.proposals: Dict[str, Proposal] = {}
        self.votes: Dict[str, Dict[str, Vote]] = {}  # proposal_id -> agent_id -> vote
        self.agent_weights: Dict[str, float] = {}  # agent_id -> weight
        self.topic_prefix = "consensus"
        
        # Subscribe to relevant events
        bus.subscribe("consensus_manager", f"{self.topic_prefix}.proposal")
        bus.subscribe("consensus_manager", f"{self.topic_prefix}.vote")
        
        # Register handlers
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        logger.info(f"Consensus manager initialized with quorum threshold {quorum_threshold}")
    
    async def start(self):
        """Start the consensus manager."""
        if self._running:
            logger.warning("Consensus manager is already running")
            return
            
        self._running = True
        self._task = asyncio.create_task(self._process_messages())
        logger.info("Consensus manager started")
    
    async def stop(self):
        """Stop the consensus manager."""
        if not self._running:
            logger.warning("Consensus manager is not running")
            return
            
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            
        logger.info("Consensus manager stopped")
    
    async def _process_messages(self):
        """Process messages from the bus."""
        queue = self.bus.get_queue("consensus_manager")
        
        try:
            while self._running:
                # Get the next message
                message = await queue.get()
                
                # Process the message based on its topic
                if message.topic == f"{self.topic_prefix}.proposal":
                    await self._handle_proposal(message)
                elif message.topic == f"{self.topic_prefix}.vote":
                    await self._handle_vote(message)
        except asyncio.CancelledError:
            logger.debug("Consensus manager task cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in consensus manager loop: {e}", exc_info=True)
            self._running = False
            raise
    
    async def _handle_proposal(self, message: Message):
        """Handle a proposal message."""
        try:
            if not isinstance(message.payload, dict):
                logger.warning(f"Invalid proposal format: {message.payload}")
                return
                
            # Create a proposal from the message
            proposal = Proposal.from_dict(message.payload)
            
            # Store the proposal
            self.proposals[proposal.id] = proposal
            
            # Initialize vote tracking for this proposal
            self.votes[proposal.id] = {}
            
            # Emit a proposal created event
            event = ProposalCreatedEvent(proposal_id=proposal.id, proposal=proposal)
            self.bus.publish(f"{self.topic_prefix}.event.proposal_created", event)
            
            # Update proposal status
            await self._update_proposal_status(proposal.id, ProposalStatus.VOTING)
            
            logger.info(f"New proposal created: {proposal.id} ({proposal.type})")
        except Exception as e:
            logger.error(f"Error handling proposal: {e}", exc_info=True)
    
    async def _handle_vote(self, message: Message):
        """Handle a vote message."""
        try:
            if not isinstance(message.payload, dict):
                logger.warning(f"Invalid vote format: {message.payload}")
                return
                
            # Extract vote data
            vote_data = message.payload
            proposal_id = vote_data.get("proposal_id")
            agent_id = vote_data.get("agent_id") or message.sender_id
            vote_type_str = vote_data.get("vote_type")
            
            # Validate required fields
            if not all([proposal_id, agent_id, vote_type_str]):
                logger.warning(f"Missing required vote fields: {vote_data}")
                return
                
            # Check if the proposal exists
            if proposal_id not in self.proposals:
                logger.warning(f"Vote for unknown proposal: {proposal_id}")
                return
                
            # Check if the proposal is still accepting votes
            proposal = self.proposals[proposal_id]
            if proposal.status != ProposalStatus.VOTING:
                logger.warning(f"Vote for non-voting proposal: {proposal_id} (status: {proposal.status})")
                return
            
            # Convert vote type string to enum
            try:
                vote_type = VoteType(vote_type_str)
            except ValueError:
                logger.warning(f"Invalid vote type: {vote_type_str}")
                return
            
            # Create and store the vote
            vote_id = str(uuid.uuid4())
            vote = Vote(
                id=vote_id,
                proposal_id=proposal_id,
                agent_id=agent_id,
                vote_type=vote_type,
                rationale=vote_data.get("rationale"),
                signature=vote_data.get("signature")
            )
            
            # Store the vote
            self.votes[proposal_id][agent_id] = vote
            
            # Emit a vote received event
            event = VoteReceivedEvent(vote=vote)
            self.bus.publish(f"{self.topic_prefix}.event.vote_received", event)
            
            logger.info(f"Vote received from {agent_id} on {proposal_id}: {vote_type.value}")
            
            # Check if we have reached consensus
            await self._check_consensus(proposal_id)
        except Exception as e:
            logger.error(f"Error handling vote: {e}", exc_info=True)
    
    async def _check_consensus(self, proposal_id: str):
        """
        Check if consensus has been reached for a proposal.
        
        Args:
            proposal_id: The ID of the proposal to check
        """
        if proposal_id not in self.proposals or proposal_id not in self.votes:
            return
            
        proposal = self.proposals[proposal_id]
        votes = list(self.votes[proposal_id].values())
        
        # Skip if no votes
        if not votes:
            return
            
        # Calculate weighted votes
        approve_weight = 0.0
        reject_weight = 0.0
        total_weight = 0.0
        
        for vote in votes:
            agent_id = vote.agent_id
            weight = self.agent_weights.get(agent_id, 1.0)  # Default weight of 1.0
            total_weight += weight
            
            if vote.vote_type == VoteType.APPROVE:
                approve_weight += weight
            elif vote.vote_type == VoteType.REJECT:
                reject_weight += weight
        
        # Skip if no weighted votes
        if total_weight == 0:
            return
            
        # Calculate approval and rejection ratios
        approve_ratio = approve_weight / total_weight
        reject_ratio = reject_weight / total_weight
        
        # Check if we've reached consensus
        if approve_ratio >= self.quorum_threshold:
            # Consensus reached - proposal approved
            await self._update_proposal_status(proposal_id, ProposalStatus.APPROVED)
            
            # Emit a quorum reached event
            event = QuorumReachedEvent(
                proposal_id=proposal_id,
                result=VoteType.APPROVE,
                votes=votes
            )
            self.bus.publish(f"{self.topic_prefix}.event.quorum_reached", event)
            
            logger.info(f"Proposal {proposal_id} approved with {approve_ratio:.2f} weighted approval")
        elif reject_ratio >= self.quorum_threshold:
            # Consensus reached - proposal rejected
            await self._update_proposal_status(proposal_id, ProposalStatus.REJECTED)
            
            # Emit a quorum reached event
            event = QuorumReachedEvent(
                proposal_id=proposal_id,
                result=VoteType.REJECT,
                votes=votes
            )
            self.bus.publish(f"{self.topic_prefix}.event.quorum_reached", event)
            
            logger.info(f"Proposal {proposal_id} rejected with {reject_ratio:.2f} weighted rejection")
    
    async def _update_proposal_status(self, proposal_id: str, new_status: ProposalStatus):
        """
        Update the status of a proposal.
        
        Args:
            proposal_id: The ID of the proposal to update
            new_status: The new status
        """
        if proposal_id not in self.proposals:
            return
            
        proposal = self.proposals[proposal_id]
        old_status = proposal.status
        
        # Skip if status hasn't changed
        if old_status == new_status:
            return
            
        # Update the status
        proposal.status = new_status
        
        # Emit a status changed event
        event = ProposalStatusChangedEvent(
            proposal_id=proposal_id,
            old_status=old_status,
            new_status=new_status
        )
        self.bus.publish(f"{self.topic_prefix}.event.status_changed", event)
        
        logger.info(f"Proposal {proposal_id} status changed: {old_status.value} -> {new_status.value}")
    
    def set_agent_weight(self, agent_id: str, weight: float):
        """
        Set the weight for an agent's votes.
        
        Args:
            agent_id: The ID of the agent
            weight: The weight to assign (0.0-1.0)
        """
        # Normalize weight to be between 0 and 1
        weight = max(0.0, min(1.0, weight))
        self.agent_weights[agent_id] = weight
        logger.debug(f"Set weight for agent {agent_id} to {weight}")
    
    def create_proposal(self, proposal_type: str, content: Any, proposer_id: str, 
                       expires_in_sec: Optional[float] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Create a new consensus proposal.
        
        Args:
            proposal_type: The type of proposal
            content: The proposal content
            proposer_id: The ID of the proposing agent
            expires_in_sec: Optional expiration time in seconds
            metadata: Optional metadata for the proposal
            
        Returns:
            str: The ID of the created proposal
        """
        proposal_id = str(uuid.uuid4())
        expires_at = None if expires_in_sec is None else time.time() + expires_in_sec
        
        proposal = Proposal(
            id=proposal_id,
            type=proposal_type,
            proposer_id=proposer_id,
            content=content,
            status=ProposalStatus.PENDING,
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        # Publish the proposal
        self.bus.publish(f"{self.topic_prefix}.proposal", proposal.to_dict(), sender_id=proposer_id)
        
        return proposal_id
    
    def cast_vote(self, proposal_id: str, agent_id: str, vote_type: VoteType, 
                 rationale: Optional[str] = None, signature: Optional[str] = None):
        """
        Cast a vote on a proposal.
        
        Args:
            proposal_id: The ID of the proposal
            agent_id: The ID of the voting agent
            vote_type: The type of vote
            rationale: Optional rationale for the vote
            signature: Optional signature for the vote
        """
        vote_data = {
            "proposal_id": proposal_id,
            "agent_id": agent_id,
            "vote_type": vote_type.value,
            "rationale": rationale,
            "signature": signature
        }
        
        # Publish the vote
        self.bus.publish(f"{self.topic_prefix}.vote", vote_data, sender_id=agent_id)
    
    def emit_soft_lock(self, proposal_id: str, duration_sec: float, reason: str):
        """
        Emit a soft lock event.
        
        Args:
            proposal_id: The ID of the triggering proposal
            duration_sec: The duration of the soft lock in seconds
            reason: The reason for the soft lock
        """
        event = SoftLockEvent(
            proposal_id=proposal_id,
            duration_sec=duration_sec,
            reason=reason
        )
        
        self.bus.publish(f"{self.topic_prefix}.event.soft_lock", event)
        logger.warning(f"Soft lock initiated for {duration_sec}s: {reason}")
    
    def emit_hard_lock(self, proposal_id: str, reason: str, shutdown_requested: bool = False):
        """
        Emit a hard lock event.
        
        Args:
            proposal_id: The ID of the triggering proposal
            reason: The reason for the hard lock
            shutdown_requested: Whether a system shutdown is requested
        """
        event = HardLockEvent(
            proposal_id=proposal_id,
            reason=reason,
            shutdown_requested=shutdown_requested
        )
        
        self.bus.publish(f"{self.topic_prefix}.event.hard_lock", event)
        logger.critical(f"Hard lock initiated: {reason} (shutdown requested: {shutdown_requested})")
    
    @property
    def is_running(self) -> bool:
        """Check if the consensus manager is running."""
        return self._running 