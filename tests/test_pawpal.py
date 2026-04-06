"""
Automated test suite for PawPal+ system.
Run: python -m pytest
"""

from datetime import date, timedelta
import pytest
from pawpal_system import Task, Pet, Owner, Scheduler


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_task():
    return Task(
        title="Morning walk",
        time="07:00",
        duration_minutes=20,
        priority="high",
        frequency="daily",
        pet_name="Mochi",
    )


@pytest.fixture
def sample_pet():
    return Pet(name="Mochi", species="dog")


@pytest.fixture
def scheduler_with_tasks():
    owner = Owner("Jordan")
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")

    mochi.add_task(Task("Evening walk",    "18:00", 30, "medium", "daily",  "Mochi"))
    mochi.add_task(Task("Morning walk",    "07:00", 20, "high",   "daily",  "Mochi"))
    mochi.add_task(Task("Flea medication", "09:00", 5,  "high",   "weekly", "Mochi"))

    luna.add_task(Task("Breakfast",   "08:00", 10, "high",   "daily",  "Luna"))
    luna.add_task(Task("Playtime",    "15:00", 20, "medium", "daily",  "Luna"))
    luna.add_task(Task("Vet visit",   "11:00", 60, "high",   "once",   "Luna"))

    owner.add_pet(mochi)
    owner.add_pet(luna)
    return Scheduler(owner), mochi, luna


# ── Task tests ────────────────────────────────────────────────────────────────

def test_task_initial_not_completed(sample_task):
    """A new task should start as not completed."""
    assert sample_task.completed is False


def test_mark_complete_sets_completed(sample_task):
    """Calling mark_complete() should set completed to True."""
    sample_task.mark_complete()
    assert sample_task.completed is True


def test_daily_task_returns_next_occurrence(sample_task):
    """A daily task should return a new task scheduled for tomorrow."""
    today = sample_task.due_date
    next_task = sample_task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False
    assert next_task.title == sample_task.title


def test_weekly_task_returns_next_occurrence():
    """A weekly task should return a new task scheduled one week later."""
    task = Task("Bath time", "10:00", 30, "medium", "weekly", "Mochi")
    today = task.due_date
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


def test_once_task_returns_no_next_occurrence():
    """A one-time task should not generate a next occurrence."""
    task = Task("Vet visit", "11:00", 60, "high", "once", "Luna")
    next_task = task.mark_complete()
    assert next_task is None


# ── Pet tests ─────────────────────────────────────────────────────────────────

def test_add_task_increases_count(sample_pet, sample_task):
    """Adding a task to a pet should increase its task count by 1."""
    initial_count = len(sample_pet.tasks)
    sample_pet.add_task(sample_task)
    assert len(sample_pet.tasks) == initial_count + 1


def test_get_tasks_returns_all_added(sample_pet):
    """get_tasks() should return every task that was added."""
    t1 = Task("Walk",    "07:00", 20, "high",   "daily", "Mochi")
    t2 = Task("Feeding", "08:00", 10, "medium", "daily", "Mochi")
    sample_pet.add_task(t1)
    sample_pet.add_task(t2)
    assert len(sample_pet.get_tasks()) == 2


# ── Sorting tests ─────────────────────────────────────────────────────────────

def test_sort_by_time_returns_chronological_order(scheduler_with_tasks):
    """sort_by_time() must return tasks in HH:MM ascending order."""
    scheduler, _, _ = scheduler_with_tasks
    sorted_tasks = scheduler.sort_by_time()
    times = [t.time for t in sorted_tasks]
    assert times == sorted(times)


def test_sort_by_time_handles_empty():
    """sort_by_time() on an owner with no pets should return empty list."""
    scheduler = Scheduler(Owner("Empty"))
    assert scheduler.sort_by_time() == []


# ── Filter tests ──────────────────────────────────────────────────────────────

def test_filter_by_pet_returns_correct_tasks(scheduler_with_tasks):
    """filter_by_pet() should only return tasks for the specified pet."""
    scheduler, mochi, _ = scheduler_with_tasks
    mochi_tasks = scheduler.filter_by_pet("Mochi")
    assert all(t.pet_name == "Mochi" for t in mochi_tasks)
    assert len(mochi_tasks) == len(mochi.tasks)


def test_filter_by_pet_case_insensitive(scheduler_with_tasks):
    """filter_by_pet() should be case-insensitive."""
    scheduler, _, _ = scheduler_with_tasks
    assert len(scheduler.filter_by_pet("mochi")) == len(scheduler.filter_by_pet("Mochi"))


def test_filter_by_status_pending(scheduler_with_tasks):
    """filter_by_status(False) should return only incomplete tasks."""
    scheduler, _, _ = scheduler_with_tasks
    pending = scheduler.filter_by_status(completed=False)
    assert all(not t.completed for t in pending)


def test_filter_by_status_completed(scheduler_with_tasks):
    """filter_by_status(True) should return only completed tasks."""
    scheduler, mochi, _ = scheduler_with_tasks
    scheduler.mark_task_complete(mochi.tasks[0])
    done = scheduler.filter_by_status(completed=True)
    assert len(done) >= 1
    assert all(t.completed for t in done)


# ── Conflict detection tests ──────────────────────────────────────────────────

def test_no_conflicts_when_times_are_unique(scheduler_with_tasks):
    """Scheduler should report no conflicts when all times are distinct."""
    scheduler, _, _ = scheduler_with_tasks
    assert scheduler.detect_conflicts() == []


def test_conflict_detected_when_same_time():
    """Scheduler must flag a conflict when two tasks share the same time."""
    owner = Owner("Test")
    pet = Pet("Rex", "dog")
    pet.add_task(Task("Walk",    "09:00", 20, "high", "daily", "Rex"))
    pet.add_task(Task("Feeding", "09:00", 10, "high", "daily", "Rex"))
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1
    assert "09:00" in conflicts[0]


# ── Recurrence via Scheduler.mark_task_complete ───────────────────────────────

def test_mark_task_complete_adds_next_daily_task(scheduler_with_tasks):
    """Completing a daily task via Scheduler should add the next occurrence to the pet."""
    scheduler, mochi, _ = scheduler_with_tasks
    original_count = len(mochi.tasks)
    daily_task = next(t for t in mochi.tasks if t.frequency == "daily")
    scheduler.mark_task_complete(daily_task)
    assert len(mochi.tasks) == original_count + 1


def test_mark_task_complete_once_does_not_add(scheduler_with_tasks):
    """Completing a one-time task should NOT add a new task to the pet."""
    scheduler, _, luna = scheduler_with_tasks
    original_count = len(luna.tasks)
    once_task = next(t for t in luna.tasks if t.frequency == "once")
    scheduler.mark_task_complete(once_task)
    assert len(luna.tasks) == original_count


# ── Generate schedule tests ───────────────────────────────────────────────────

def test_generate_schedule_excludes_completed(scheduler_with_tasks):
    """generate_schedule() should not include completed tasks."""
    scheduler, mochi, _ = scheduler_with_tasks
    scheduler.mark_task_complete(mochi.tasks[0])
    schedule = scheduler.generate_schedule()
    assert all(not t.completed for t in schedule)


def test_generate_schedule_priority_order(scheduler_with_tasks):
    """High-priority tasks should appear before low-priority tasks in the schedule."""
    scheduler, _, _ = scheduler_with_tasks
    schedule = scheduler.generate_schedule()
    priorities = [t.priority for t in schedule]
    priority_vals = [Scheduler.PRIORITY_ORDER.get(p, 2) for p in priorities]
    assert priority_vals == sorted(priority_vals)
