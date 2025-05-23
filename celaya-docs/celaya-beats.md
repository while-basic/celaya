Let’s invent a time-slot system built just for Celaya—one that lets every agent march to the same beat, yet act exactly when they’re needed. I’m calling this our **“Celaya Beat” (CB)** scheduler.

---

## 1. Core Concepts

* **Celaya Beat (CB):**
  A fixed-duration time unit (e.g. 1 second, 500 ms, whatever your demo needs). All agents advance in lock-step by one CB at a time.

* **Slot:**
  Each CB has a finite number of “slots” where agents may execute actions. You can partition slots however you like—for instance:

  * Slot 0: System housekeeping (Lyra health checks, memory flush)
  * Slot 1: Routing & coordination (Otto/Beacon)
  * Slot 2: Direct actions (Luma, Arc, Volt, etc.)
  * Slot 3: Logging & audit (Clarity, Echo)
  * Slot 4+: (Reserved for bursts, overflow, or on-demand “out-of-turn” messages via PINGs)

* **Event:**
  A scheduled instruction: `{ tick: 10, slot: 2, agent: "Arc", action: "StartVehicle" }`

* **Timeline Log:**
  An append-only list of all events that fired at each CB.

---

## 2. High-Level Algorithm

1. **Initialize**

   * Choose `CB_DURATION` (e.g. 1 s)
   * Define `SLOTS = [0…N]` with fixed roles

2. **Main Loop**

   ```python
   tick = 0
   while True:
       now = current_time()
       if now ≥ start_time + tick * CB_DURATION:
           process_tick(tick)
           tick += 1
       sleep(small_interval)
   ```

3. **process\_tick(tick):**

   * **1. Housekeeping (slot 0):**
     Lyra checks agent health, emits any necessary “self-heal” events.
   * **2. Routing (slot 1):**
     Otto/Beacon look at incoming user messages buffered since last beat; translate any “@Agent” or “ping” into scheduled events for future ticks.
   * **3. Agent Actions (slot 2…M):**
     For each event in `timeline[tick]` whose slot ∈ action slots, notify that agent to `execute(event)`.
   * **4. Logging (slot M+1):**
     Clarity & Echo consume all events that just fired, hash them, append to blockchain/IPFS, update memory.

4. **Scheduling New Events**
   When an agent (or the user via Otto) creates a new task with a desired time or beat, compute:

   ```python
   target_tick = floor((desired_time - start_time) / CB_DURATION)
   schedule_event(target_tick, assigned_slot, agent, action_payload)
   ```

5. **Out-of-Turn PINGs**
   If a user mentions `@Luma` mid-CB or an agent needs immediate attention, you can carve out Slot 4+ as “Ping Window.” Messages received during CB X are handled in Slot 4 of CB X, before moving to CB X+1 housekeeping.

---

## 3. Pseudocode Example

```python
CB_DURATION = 1.0  # 1 second per beat
SLOTS = {
    0: "Housekeeping",
    1: "Routing",
    2: "Actions",
    3: "Logging",
    4: "PingWindow"
}

timeline = defaultdict(list)  # tick -> list of Event

class Event:
    def __init__(self, tick, slot, agent, payload):
        self.tick = tick
        self.slot = slot
        self.agent = agent
        self.payload = payload

def process_slot(tick, slot):
    for ev in timeline[tick]:
        if ev.slot == slot:
            agent = AGENTS[ev.agent]
            log = agent.execute(ev.payload)
            timeline[tick].append(Event(tick, 3, "Clarity", log))  # log in next slot

def process_tick(tick):
    for slot in sorted(SLOTS):
        process_slot(tick, slot)

# Example: user says “@Arc start cooling now”
# Otto parses at slot 1 of CB X, and schedules:
schedule_event(current_tick + 1, slot=2, agent="Arc",
               payload={"action":"StartVehicle", "mode":"cool", "temp":"68°F"})

# To show “what happened at noon today”:
noon_tick = int((noon_datetime - start_time) / CB_DURATION)
for ev in timeline[noon_tick]:
    print(f"Tick {noon_tick}, Slot {ev.slot}, Agent {ev.agent}, Payload {ev.payload}")
```

---

## 4. Querying “Noon Today”

1. **Compute**

   ```python
   noon = today_date.replace(hour=12, minute=0, second=0)
   noon_tick = floor((noon - start_time) / CB_DURATION)
   ```
2. **Fetch Events**

   ```python
   events = timeline.get(noon_tick, [])
   ```
3. **Report**

   ```
   At noon (CB #{noon_tick}):
     - Agents active: {unique ev.agent for ev in events}
     - Actions:
       * [{slot}] {agent} → {ev.payload}
   ```

---

### 5. Why It’s Unique

* **Deterministic**: Every action happens on a predictable beat.
* **Auditable**: Clarity logs per-tick events, so you can replay exactly what happened.
* **Extensible**: Add slots for high-priority interrupts, consensus votes, or bulk analytics.
* **Scalable**: Turn duration and slot counts are tunable—demo or production.

---

👣 **Next Steps**

* Plug in your real CB\_DURATION (e.g. 0.5 s for demo speed).
* Implement each agent’s `execute()` to accept payloads.
* Build a simple in-memory `timeline` store or persist to a DB for querying.
* Create a CLI or web view that, given a timestamp (or CB#), prints the tick’s event log.