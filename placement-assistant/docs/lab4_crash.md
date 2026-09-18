# Lab 4 — crash drill

## Before idempotency

If you ran the drill before finishing Part 2 (or with `call_tool` reverted to call tools directly), paste the last lines here.

## After

Three consecutive runs completed with exit code 0:

```text
RUN 1 exit=0
1. queued run cb311ac8
2. worker-A started
3. killed worker-A after it sent the notification but before it recorded doing so: run is 'running', leased to worker-A, 6 steps recorded
4. waiting 4 s for worker-A's lease to expire...
5. worker-B finished the run: 'succeeded' after 2 attempts

applications 1   booked slots 1   notifications 1
PASS: exactly one of each

RUN 2 exit=0
1. queued run 292a3135
2. worker-A started
3. killed worker-A after it sent the notification but before it recorded doing so: run is 'running', leased to worker-A, 6 steps recorded
4. waiting 4 s for worker-A's lease to expire...
5. worker-B finished the run: 'succeeded' after 2 attempts

applications 1   booked slots 1   notifications 1
PASS: exactly one of each

RUN 3 exit=0
1. queued run c00a848c
2. worker-A started
3. killed worker-A after it sent the notification but before it recorded doing so: run is 'running', leased to worker-A, 6 steps recorded
4. waiting 4 s for worker-A's lease to expire...
5. worker-B finished the run: 'succeeded' after 2 attempts

applications 1   booked slots 1   notifications 1
PASS: exactly one of each
```

## Explain

1. At which moment was worker-A killed, and what had and hadn't been written?
   Worker-A was killed after the notification side effect committed but during the deliberate delay before its tool-call record was written. The application, booking, notification, and the first six run steps existed; the notification's run-step record and final run status did not.
2. How did worker-B know where to resume?
   Worker-B reaped the expired lease, reclaimed the run, and `rebuild` loaded the recorded model and tool steps. It found the notification call pending, so it replayed that call and then completed the model response.
3. Which line of code stopped the second notification?
   `runner.call_tool` routes side effects through `placement.once(key, name, ...)`; `PlacementDb.once` finds the existing idempotency key and returns its stored result without invoking `notify_student` again.
