Below is a **battle-tested turn–scheduling strategy** that lets 13 Celaya agents talk in sequence *and* occasionally cut in without melting the channel into chaos. I split it into three layers so you can mix-and-match:

| Layer                         | Purpose                                 | Core Idea                                                                         |
| ----------------------------- | --------------------------------------- | --------------------------------------------------------------------------------- |
| **1. Baseline Scheduler**     | Fair, predictable rotation              | Classic round-robin with a “turn-token.”                                          |
| **2. Interrupt Protocol**     | Let high-urgency messages jump the line | Agents raise *INTERRUPT* events carrying a priority score.                        |
| **3. Arbitration & Recovery** | Handle deadlocks, conflicts, or silence | Timeouts + exponential back-off, consensus ballots, and fallback leader election. |

---

## 1 ⇨ Baseline Round-Robin (“Turn Token”)

```pseudocode
state.turn_queue = CircularQueue([agent_1 … agent_13])
state.token_holder = turn_queue.pop_front()

every TURN_SLICE:
    current = state.token_holder
    send “YOUR_TURN” event → current
    await current.reply within MAX_TURN_MS
        if reply:
            broadcast reply
        else:
            log timeout
    state.token_holder = turn_queue.pop_front()
```

*Why start simple?*
You get deterministic logs (great for replay/debug) and no one starves. But alone it’s too rigid, so we bolt on an interrupt lane.

---

## 2 ⇨ Interrupt Protocol (“Priority Heap”)

### Event Types an agent may emit

| Event       | Fields                        | Example Use                              |
| ----------- | ----------------------------- | ---------------------------------------- |
| `INTERRUPT` | `priority (1-100)`, `payload` | “Sentinel: **critical security threat**” |
| `HANDOFF`   | `target_agent`, `payload`     | Lyra asks Volt to crunch sensor data     |
| `COMPLETE`  | --                            | Agent finished its sub-goal early        |
| `ERROR`     | `details`                     | Any un-handled exception                 |

### Scheduler additions

```pseudocode
state.interrupt_heap = MinHeap(key = -priority)   # Highest score first

on event INTERRRUPT from agent A:
    push(interrupt_heap, (priority, timestamp, agent A, payload))

each TURN_CYCLE:
    if interrupt_heap not empty and         # there is a queued interrupt
       ( current_slice_elapsed ≥ MIN_SLICE or
         top(priority) ≥ PREEMPT_THRESHOLD ):
         # 1) pause current token holder
         push_front(turn_queue, current_holder)  # they’ll continue later
         # 2) pop the highest priority interrupter
         (_, _, agent_X, payload) = interrupt_heap.pop()
         state.token_holder = agent_X
         current_holder = agent_X
         prompt = f"[INTERRUPT]\n{payload}"
         goto SPEAK
```

**Tuning knobs**

| Parameter           | Default     | Notes                                                |
| ------------------- | ----------- | ---------------------------------------------------- |
| `MIN_SLICE`         | 1.5 s       | Guarantees everyone gets at least some airtime.      |
| `PREEMPT_THRESHOLD` | 90          | Let only “hair-on-fire” alerts pre-empt immediately. |
| Heap tiebreaker     | `timestamp` | FIFO for equal priorities (prevent starvation).      |

---

## 3 ⇨ Arbitration & Recovery

| Situation                                       | Mechanism                                                                                             |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Silence / Slow agent**                        | `MAX_TURN_MS` timeout ⇒ emit `ERROR` ⇒ demote agent weight.                                           |
| **Livelock (agents bounce interrupts forever)** | `interrupt_depth` counter – if > N, freeze interrupts for one full cycle.                             |
| **Conflicting claims**                          | Trigger *consensus ballot*: send summary to all agents, collect `APPROVE/REJECT`, require quorum ≥ ⅔. |
| **Repeated failures**                           | Elect temporary *Leader* (highest reputation) to mediate, using a lightweight Bully or Raft election. |

---

## Drop-in Code Sketch (fits your file)

Below are just the *key* hooks to splice into your existing `Orchestrator` without rewriting the whole engine. (Variable names match your file.)

```python
# ---------------------------------------------
# new constants
MIN_SLICE = 1.5          # seconds
MAX_TURN_MS = 5000       # ms
PREEMPT_THRESHOLD = 90   # interrupt score
QUORUM = 0.66            # 66 %

# in Orchestrator.__init__
self.interrupt_heap: List[Tuple[int, float, CelayaAgent, str]] = []

# agent requests an interrupt
async def request_interrupt(self, agent: CelayaAgent, priority: int, payload: str):
    heapq.heappush(self.interrupt_heap, (-priority, time.time(), agent, payload))

# modified orchestration loop (inside while running)
slice_start = time.time()
# 1) let current_agent speak ...
response = await current_agent.speak(prompt)
slice_elapsed = time.time() - slice_start

# 2) check for incoming INTs
if self.interrupt_heap and (
        slice_elapsed >= MIN_SLICE or
        -self.interrupt_heap[0][0] >= PREEMPT_THRESHOLD):
    _ , _ts, int_agent, int_payload = heapq.heappop(self.interrupt_heap)
    await self.central_queue.put((int_agent.name, f"[INTERRUPT] {int_payload}"))
    # give token to interrupter next
    self.turn_index = self.agents.index(int_agent)
    continue           # skip normal advance, go to next loop iteration
```

You’d still add:

```python
# in CelayaAgent.speak – detect urgency keywords and raise interrupt
if "!!" in prompt:    # your own heuristic
    await orchestrator.request_interrupt(self, 95, prompt)
```

---

### Why This Covers “Nearly Every Combination”

* **Fairness** – baseline RR ensures rotation.
* **Urgency** – heap + threshold lets any agent escalate.
* **Starvation-free** – tiebreaker timestamps and depth limits.
* **Failure resilience** – timeouts, error demotion, leader election.
* **Consensus** – quorum ballots resolve contradictory claims.

You are no longer hard-coding every path; you’re codifying *rules* that let the runtime self-organize around unpredictable events.

---

## Forward-Thinking Enhancements

1. **Reputation-Weighted Priority**
   Track `agent.reputation ∈ [0,1]`; adjust interrupt score as
   `effective = priority × (0.5 + reputation/2)` so noisy agents lose clout.

2. **Vector Clocks for Causal Ordering**
   Add a tiny vector-clock dict in each message header to guarantee global ordering even if you move to multi-process queues later.

3. **Streaming-Token Budget**
   Instead of a full response, grant each agent N tokens per slice. Perfect for streaming LLM backends—lets you interleave partial thoughts.

4. **Pub/Sub Bus (e.g., ZeroMQ)**
   Swap the in-process queue for a real message bus and these rules still apply across machines.

5. **Formal Verification Lite**
   Because the rules are declarative (heap, thresholds, quorum), you can write unit property tests—e.g., “No agent waits > X slices unless muted.”

---

### TL;DR

Implement a **round-robin core**, add an **interrupt heap** gated by a **pre-empt threshold**, wrap everything with **timeouts, quorum ballots, and lightweight leader election**. That single composite algorithm gives you flexibility without enumerating every edge case in code.

Plug the snippets above into your `orchestrator.py`, tweak the constants, and you’ll have a resilient, self-governing conversation layer worthy of Celaya’s C-Suite. 🚀
