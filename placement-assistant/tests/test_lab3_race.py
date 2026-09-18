"""Lab 3 — two runs booking the same slot; one wins cleanly."""
import threading

from app.memory import RunStore
from app.placement_db import PlacementDb
from app.providers import ModelTurn, PositionalMock, ToolCall
from app.worker import Worker


def booking_turns(student_id):
   return [
      ModelTurn(text=None, tool_calls=[ToolCall("apply_to_drive", {"student_id": student_id, "drive_id": 2})]),
      ModelTurn(text=None, tool_calls=[ToolCall("book_interview_slot", {"student_id": student_id, "slot_id": 3})]),
      ModelTurn(text="done"),
   ]


def test_two_workers_two_runs_one_slot(db_files):
   agent_path, placement_path = db_files
   stores = [RunStore(agent_path), RunStore(agent_path)]
   placements = [PlacementDb(placement_path), PlacementDb(placement_path)]
   students = ["22IT017", "22CS045"]
   run_ids = [store.enqueue(store.create_thread(student), "apply and book", "mock")
            for store, student in zip(stores, students)]
   workers = [Worker(store, placement, PositionalMock(booking_turns(student)), worker_id=f"w{i}")
            for i, (store, placement, student) in enumerate(zip(stores, placements, students))]

   outcomes = [worker.run_once() for worker in workers]

   assert [result[1] for result in outcomes] == ["succeeded", "succeeded"]
   tool_results = [step["result"] for store, run_id in zip(stores, run_ids)
               for step in store.get_run(run_id)["steps"] if step["kind"] == "tool"]
   assert sum(result.get("status") == "booked" for result in tool_results) == 1
   assert sum(result.get("error") == "slot_taken" for result in tool_results) == 1
   assert placements[0].get_slot(3).student_id in (2, 1)


def test_truly_concurrent_claims_have_one_winner(db_files):
   _, placement_path = db_files
   seed = PlacementDb(placement_path)
   version = seed.slot_version(3)
   barrier = threading.Barrier(8)
   results = []
   lock = threading.Lock()

   def attempt(student_id):
      placement = PlacementDb(placement_path)
      barrier.wait()
      won = placement.claim_slot(3, student_id, version)
      with lock:
         results.append(won)

   threads = [threading.Thread(target=attempt, args=(1 if index % 2 else 2,)) for index in range(8)]
   for thread in threads:
      thread.start()
   for thread in threads:
      thread.join()

   assert results.count(True) == 1
   assert results.count(False) == 7
   assert seed.slot_version(3) == version + 1
