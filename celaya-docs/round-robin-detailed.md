Below is a **“builder’s walkthrough.”**  Treat it like a lab manual: you can follow it line-by-line, run the snippets, and watch the orchestration layer come to life.

---

## 0  Prerequisites (15 min)

| Task                                                | Why                                           |
| --------------------------------------------------- | --------------------------------------------- |
| `python -m venv .venv && source .venv/bin/activate` | Keep deps isolated.                           |
| `pip install aiohttp more-itertools rich`           | Non-blocking HTTP, heap helpers, pretty logs. |
| Clone / open your **orchestrator.py** in VS Code.   | Faster reload/debug.                          |
| `export CELAYA_API=http://localhost:11434`          | Point to your local Ollama fork.              |

*(All snippets assume Python 3.10+ and your existing file structure.)*

---

## 1  Lay the Groundwork: Event Objects & Enums (10 min)

Create a tiny “protocol” module so every part of the system speaks the same dialect.

```python
# file: protocol.py
from enum import Enum, auto
from dataclasses import dataclass
from typing import Any

class EventType(Enum):
    TURN       = auto()
    INTERRUPT  = auto()
    HANDOFF    = auto()
    COMPLETE   = auto()
    ERROR      = auto()

@dataclass
class Event:
    etype: EventType
    sender: str
    payload: Any
    priority: int = 0      # 1-100, only used for INTERRUPT
    timestamp: float = 0.0
```

Why bother? Because *structured* events are easier to log, unit-test, and (later) serialize to IPFS / blockchain.

---

## 2  Round-Robin Token Loop (20 min)

**Goal:** every agent gets airtime in a fair cycle.

1. Import `deque` and store agents inside it.
2. Pop left → that agent owns the **turn-token**.
3. Wait `MAX_TURN_MS` for their reply.
4. Append the agent back to the right of the deque.

```python
from collections import deque
MAX_TURN_MS = 5000

class Orchestrator:
    def __init__(..., agents):
        self.turn_queue = deque(agents)
        self.token_holder: CelayaAgent | None = None
    ...
    async def _next_turn(self, prompt: str):
        self.token_holder = self.turn_queue.popleft()
        reply = await asyncio.wait_for(
            self.token_holder.speak(prompt), timeout=MAX_TURN_MS/1000
        )
        self.turn_queue.append(self.token_holder)
        return reply
```

*🧠 Mental model:* a conch shell in “Lord of the Flies.” Whoever holds it may talk.

---

## 3  Interrupt Lane – Priority Heap (30 min)

### 3.1 Add a Min-Heap

```python
import heapq, time
self.interrupt_heap: list[tuple[int,float,CelayaAgent,str]] = []
```

### 3.2 Agents Request an Interrupt

Modify **CelayaAgent.speak** so the model can self-escalate:

```python
if "!!" in prompt:                 # your heuristic, replace as needed
    await orchestrator.request_interrupt(self, 95, prompt)
```

…and add the orchestrator helper:

```python
async def request_interrupt(self, agent, priority: int, payload: str):
    heapq.heappush(self.interrupt_heap, (-priority, time.time(), agent, payload))
```

### 3.3 Scheduler Check

Inside the main loop **after** you process the current reply:

```python
slice_elapsed = time.time() - slice_start
if ( self.interrupt_heap and
     (slice_elapsed >= MIN_SLICE or -self.interrupt_heap[0][0] >= PREEMPT_THRESHOLD)
):
    _, _, int_agent, int_payload = heapq.heappop(self.interrupt_heap)
    await self.central_queue.put((int_agent.name, f"[INTERRUPT] {int_payload}"))
    # Give the token to interrupter next
    self.turn_index = self.agents.index(int_agent)
    continue   # restart loop → int_agent now speaks
```

Tweak **MIN\_SLICE** (fairness) and **PREEMPT\_THRESHOLD** (urgency) till you like the vibe.

---

## 4  Arbitration & Fault Tolerance (25 min)

| Feature               | How to implement                                                                                                           |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **Timeouts**          | `asyncio.wait_for` on `speak`. If it raises `TimeoutError`, log an `EventType.ERROR`, reduce agent’s “reliability” score.  |
| **Livelock breaker**  | Keep `interrupt_depth` counter. If > N consecutive interrupts, *freeze* the heap for one full rotation.                    |
| **Consensus ballots** | Broadcast a “BALLOT: xyz” message. Each agent replies APPROVE/REJECT. Count. If `approve/(approve+reject) ≥ 0.66`, commit. |
| **Leader election**   | On 3+ consecutive failures, pick agent with highest `reputation`; give it exclusive right to mediate for 1 rotation.       |

All four mechanisms are parameterized knobs – no hard-coded branches per scenario.

---

## 5  Unit Test Harness (20 min)

Spin fake agents that return canned replies immediately, so you can hammer the scheduler without burning GPU cycles:

```python
class Dummy(CelayaAgent):
    async def speak(self, prompt, include_history=True):
        await asyncio.sleep(0.01)
        if "force-int" in prompt:
            await orchestrator.request_interrupt(self, 99, "🔥 critical")
        return f"{self.name} heard → {prompt[:20]}..."
```

Then:

```python
import pytest, anyio
@pytest.mark.anyio
async def test_interrupt_trumps_round_robin():
    agents = [Dummy("A",""), Dummy("B",""), Dummy("C","")]
    orch = Orchestrator(agents, max_turns=5)
    await orch.orchestrate("force-int")   # B will interrupt
    assert orch.conversation_log[1]["agent"] == "B"
```

Crank out more edge-case tests (timeout, multiple interrupts, quorum).

---

## 6  Observability Hooks (10 min)

* Use the **rich** library for colorized console logs.
* Emit `Event` objects to a `/logs` WebSocket so your dashboard’s “Live Stream” panel lights up.
* Histogram the *interrupt delay* metric: `(interrupt_granted_at – interrupt_requested_at)`.

---

## 7  Gradual Roll-Out Plan

| Day   | Milestone                                                                |
| ----- | ------------------------------------------------------------------------ |
| **1** | Baseline round-robin passes unit tests.                                  |
| **2** | Interrupt heap integrated; add CLI flags `--min-slice` & `--threshold`.  |
| **3** | Timeouts + error demotion; log to JSON → manual playback tool.           |
| **4** | Consensus ballot helper + simulation script with 500 random events.      |
| **5** | Swap `asyncio.Queue` for ZeroMQ PUB/SUB; prove works across 2 processes. |

---

## 8  Mindset Tips While Coding

1. **Test in isolation first.** A single bad LLM call will mask scheduler bugs.
2. **Keep constants in .toml** (`scheduler.toml`) → hot-reload without redeploy.
3. **Embrace randomness.** Seeded fuzz tests surface deadlocks you’d never type by hand.

---

### TL;DR for Builders

1. Start with a **simple deque** (round-robin).
2. Layer on a **priority heap** for interrupts.
3. Surround with **timeouts, ballots, and back-off** → self-healing loop.
4. Unit-test with dummy agents before plugging real LLMs.
5. Expose every hard number as a config knob so you can tune live.

Follow the steps above and you’ll have a robust, extensible scheduler that keeps 13 Celaya agents chatting in harmony—yet lets Sentinel shout “🔥 breach!” the instant it matters. Happy hacking!
