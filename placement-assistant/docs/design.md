# Sprint — design notes

Answer each in a short paragraph. Point to the code.

1. Why is the unit of retry the tool call, and not the whole request?
   The tool call is the smallest operation with a durable boundary: `runner.call_tool` and `PlacementDb.once` can replay a missing record without asking the model to repeat already-completed work. Retrying the whole request could repeat read steps and produce different model decisions, while idempotency protects each side effect independently.
2. The idempotency key is stored in placement.db, not agent.db. Why there, and why in the same transaction as the side effect?
   The key protects placement data, so it belongs beside the application, booking, or notification it describes. `PlacementDb.once` runs the effect and inserts the key inside one `BEGIN IMMEDIATE` transaction; a crash before commit rolls back both, and a replay sees either both or neither.
3. What happens if the lease is shorter than one model call? What would you change?
   The lease can expire while the model is still generating, allowing another worker to reclaim the run; the first worker then loses ownership at its next heartbeat or write. I would use a lease comfortably longer than the provider timeout and heartbeat from a watchdog during long calls, or use a provider timeout below the lease duration.
4. Why do both databases open transactions with BEGIN IMMEDIATE instead of plain BEGIN?
   `BEGIN IMMEDIATE` acquires SQLite's write reservation before reads and updates. That serializes competing claimers and slot/idempotency writers early, avoiding two workers both believing they won and reducing the chance of a late lock failure after work has been performed.
5. Name one thing in this system that is still not exactly-once, and what it would take to fix it.
   The model call is not exactly-once: a worker can crash after the provider accepts a request but before `run_step` is recorded, so a retry can spend another request and receive another answer. Fixing that requires provider-supported request idempotency keys or a durable model gateway that records and replays responses before calling the provider again.
