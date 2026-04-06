"""
PawPal+ CLI Demo Script
Verifies backend logic without the Streamlit UI.
Run: python main.py
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler


def main():
    # ── Setup owner ──────────────────────────────────────────────
    owner = Owner("Jordan")

    # ── Setup pets ───────────────────────────────────────────────
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # ── Add tasks (intentionally out of order to test sorting) ───
    mochi.add_task(Task("Evening walk",    "18:00", 30, "medium", "daily",  "Mochi"))
    mochi.add_task(Task("Morning walk",    "07:00", 20, "high",   "daily",  "Mochi"))
    mochi.add_task(Task("Flea medication", "09:00", 5,  "high",   "weekly", "Mochi"))
    mochi.add_task(Task("Dinner feeding",  "18:00", 10, "high",   "daily",  "Mochi"))  # conflict!

    luna.add_task(Task("Breakfast feeding", "08:00", 10, "high",   "daily",  "Luna"))
    luna.add_task(Task("Playtime",          "15:00", 20, "medium", "daily",  "Luna"))
    luna.add_task(Task("Vet appointment",   "11:00", 60, "high",   "once",   "Luna"))

    scheduler = Scheduler(owner)

    # ── Print full schedule ──────────────────────────────────────
    scheduler.print_schedule()

    # ── Demo: sorted task list ───────────────────────────────────
    print("All tasks sorted by time:")
    for task in scheduler.sort_by_time():
        print(f"  {task}")

    # ── Demo: filter by pet ──────────────────────────────────────
    print("\nMochi's tasks only:")
    for task in scheduler.filter_by_pet("Mochi"):
        print(f"  {task}")

    # ── Demo: mark a daily task complete (tests recurrence) ──────
    print("\n--- Marking 'Morning walk' complete ---")
    morning_walk = mochi.tasks[1]  # "Morning walk"
    scheduler.mark_task_complete(morning_walk)
    print(f"  '{morning_walk.title}' completed: {morning_walk.completed}")
    print(f"  Mochi now has {len(mochi.tasks)} tasks (next walk auto-scheduled)")

    # ── Demo: pending tasks only ─────────────────────────────────
    print("\nPending tasks after completion:")
    for task in scheduler.filter_by_status(completed=False):
        print(f"  {task}")


if __name__ == "__main__":
    main()
