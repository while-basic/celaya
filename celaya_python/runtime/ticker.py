# ----------------------------------------------------------------------------
#  File:        ticker.py
#  Project:     Celaya Solutions
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Ticker that emits TickEvent(epoch) through Bus
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

"""
Ticker module for the Celaya runtime.

Provides a ticker that emits TickEvent through the Bus at regular intervals.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional

from celaya_python.runtime.bus import Bus

logger = logging.getLogger(__name__)

@dataclass
class TickEvent:
    """Event emitted by the ticker at regular intervals."""
    
    epoch: int
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class Ticker:
    """
    Ticker that emits TickEvent through the Bus at regular intervals.
    
    Used to synchronize agent activities and consensus rounds.
    """
    
    def __init__(self, interval_ms: int, bus: Bus, topic: str = "ticker"):
        """
        Initialize a new ticker.
        
        Args:
            interval_ms: The interval between ticks in milliseconds
            bus: The message bus to publish events to
            topic: The topic to publish tick events on
        """
        self.interval_ms = interval_ms
        self.interval_sec = interval_ms / 1000.0
        self.bus = bus
        self.topic = topic
        self.current_epoch = 0
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        logger.info(f"Ticker initialized with interval {interval_ms}ms")
    
    async def start(self):
        """Start the ticker."""
        if self._running:
            logger.warning("Ticker is already running")
            return
            
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Ticker started")
    
    async def stop(self):
        """Stop the ticker."""
        if not self._running:
            logger.warning("Ticker is not running")
            return
            
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            
        logger.info("Ticker stopped")
    
    async def _run(self):
        """Run the ticker loop."""
        try:
            while self._running:
                # Emit a tick event
                event = TickEvent(epoch=self.current_epoch)
                self.bus.publish(self.topic, event, sender_id="ticker")
                
                logger.debug(f"Emitted tick event: epoch={self.current_epoch}")
                
                # Increment the epoch
                self.current_epoch += 1
                
                # Wait for the next interval
                await asyncio.sleep(self.interval_sec)
        except asyncio.CancelledError:
            logger.debug("Ticker task cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in ticker loop: {e}", exc_info=True)
            self._running = False
            raise
    
    @property
    def is_running(self) -> bool:
        """Check if the ticker is running."""
        return self._running 