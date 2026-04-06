"""
PawPal+ System Logic
Core classes: Task, Pet, Owner, Scheduler
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional


@dataclass
class Task:
    """Represents a single pet care activity."""

    title: str
    time: str  # "HH:MM" 24-hour format
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    frequency: str  # "once", "daily", "weekly"
    pet_name: str
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def mark_complete(self) -> Optional["Task"]:
        """Mark task complete and return the next occurrence for recurring tasks."""
        self.completed = True
        if self.frequency == "daily":
            return Task(
                title=self.title,
                time=self.time,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                frequency=self.frequency,
                pet_name=self.pet_name,
                due_date=self.due_date + timedelta(days=1),
            )
        if self.frequency == "weekly":
            return Task(
                title=self.title,
                time=self.time,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                frequency=self.frequency,
                pet_name=self.pet_name,
                due_date=self.due_date + timedelta(weeks=1),
            )
        return None

    def __str__(self) -> str:
        status = "Done" if self.completed else "Pending"
        return (
            f"[{self.time}] {self.title} ({self.pet_name}) | "
            f"{self.duration_minutes}min | {self.priority} priority | "
            f"{self.frequency} | {status}"
        )


@dataclass
class Pet:
    """Stores pet details and their associated tasks."""

    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def get_tasks(self) -> List[Task]:
        """Return all tasks assigned to this pet."""
        return self.tasks

    def __str__(self) -> str:
        return f"{self.name} ({self.species}) — {len(self.tasks)} task(s)"


class Owner:
    """Manages multiple pets and provides access to all their tasks."""

    def __init__(self, name: str) -> None:
        """Initialize an owner with a name and empty pet list."""
        self.name = name
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's care."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return all tasks across every pet this owner manages."""
        tasks: List[Task] = []
        for pet in self.pets:
            tasks.extend(pet.get_tasks())
        return tasks

    def __str__(self) -> str:
        return f"Owner: {self.name} | Pets: {[p.name for p in self.pets]}"


class Scheduler:
    """The brain of PawPal+: retrieves, sorts, filters, and manages tasks."""

    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, owner: Owner) -> None:
        """Initialize the scheduler with an owner whose pets' tasks it manages."""
        self.owner = owner

    def get_all_tasks(self) -> List[Task]:
        """Retrieve all tasks from all pets belonging to the owner."""
        return self.owner.get_all_tasks()

    def sort_by_time(self) -> List[Task]:
        """Return all tasks sorted chronologically by their scheduled time (HH:MM)."""
        return sorted(self.get_all_tasks(), key=lambda t: t.time)

    def filter_by_pet(self, pet_name: str) -> List[Task]:
        """Return tasks filtered to a specific pet by name (case-insensitive)."""
        return [t for t in self.get_all_tasks() if t.pet_name.lower() == pet_name.lower()]

    def filter_by_status(self, completed: bool) -> List[Task]:
        """Return tasks filtered by completion status."""
        return [t for t in self.get_all_tasks() if t.completed == completed]

    def detect_conflicts(self) -> List[str]:
        """
        Detect tasks scheduled at the exact same time.
        Returns a list of warning strings; empty list means no conflicts.
        """
        warnings: List[str] = []
        seen: dict = {}
        for task in self.get_all_tasks():
            if task.time in seen:
                other = seen[task.time]
                warnings.append(
                    f"WARNING: Conflict at {task.time}: '{other.title}' ({other.pet_name}) "
                    f"clashes with '{task.title}' ({task.pet_name})"
                )
            else:
                seen[task.time] = task
        return warnings

    def mark_task_complete(self, task: Task) -> None:
        """
        Mark a task complete. For recurring tasks, automatically schedules
        the next occurrence on the appropriate pet.
        """
        next_task = task.mark_complete()
        if next_task:
            for pet in self.owner.pets:
                if pet.name == task.pet_name:
                    pet.add_task(next_task)
                    break

    def generate_schedule(self) -> List[Task]:
        """
        Generate today's schedule: pending tasks due today or earlier,
        sorted by priority (high first) then by scheduled time.
        """
        today = date.today()
        pending = [
            t for t in self.get_all_tasks()
            if not t.completed and t.due_date <= today
        ]
        return sorted(
            pending,
            key=lambda t: (self.PRIORITY_ORDER.get(t.priority, 2), t.time),
        )

    def print_schedule(self) -> None:
        """Print a formatted today's schedule to the terminal."""
        schedule = self.generate_schedule()
        conflicts = self.detect_conflicts()

        print("\n" + "=" * 55)
        print(f"  PawPal+ Daily Schedule for {self.owner.name}")
        print("=" * 55)

        if not schedule:
            print("  No tasks scheduled for today!")
        else:
            for i, task in enumerate(schedule, 1):
                print(f"  {i}. {task}")

        if conflicts:
            print("\n" + "-" * 55)
            print("  CONFLICT WARNINGS:")
            for warning in conflicts:
                print(f"  {warning}")

        print("=" * 55 + "\n")
