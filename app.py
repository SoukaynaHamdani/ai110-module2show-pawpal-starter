"""
PawPal+ Streamlit UI
Connects the Scheduler backend to an interactive web interface.
Run: streamlit run app.py
"""

import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling — powered by Python OOP & algorithmic logic.")

# ── Session state initialisation ─────────────────────────────────────────────
# Persist the Owner object across Streamlit reruns using session_state
if "owner" not in st.session_state:
    st.session_state.owner = None

if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# ── Sidebar: Owner & Pet Setup ───────────────────────────────────────────────
with st.sidebar:
    st.header("1. Owner & Pet Setup")
    owner_name = st.text_input("Owner name", value="Jordan")
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])

    if st.button("Create / Reset Owner & Pet", type="primary"):
        pet = Pet(name=pet_name, species=species)
        owner = Owner(name=owner_name)
        owner.add_pet(pet)
        st.session_state.owner = owner
        st.session_state.scheduler = Scheduler(owner)
        st.success(f"Owner '{owner_name}' created with pet '{pet_name}'!")

    if st.session_state.owner:
        st.divider()
        st.header("2. Add Another Pet")
        new_pet_name = st.text_input("New pet name", key="new_pet")
        new_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"], key="new_species")
        if st.button("Add Pet"):
            new_pet = Pet(name=new_pet_name, species=new_species)
            st.session_state.owner.add_pet(new_pet)
            st.success(f"Added pet '{new_pet_name}'!")

# ── Main area ────────────────────────────────────────────────────────────────
if st.session_state.owner is None:
    st.info("Use the sidebar to set up an owner and pet to get started.")
    st.stop()

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

# Show current pets
pet_names = [p.name for p in owner.pets]
st.subheader(f"Owner: {owner.name}  |  Pets: {', '.join(pet_names)}")
st.divider()

# ── Add Task ─────────────────────────────────────────────────────────────────
st.subheader("Add a Care Task")

col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    task_time = st.text_input("Time (HH:MM)", value="07:00")
with col3:
    duration = st.number_input("Duration (min)", min_value=1, max_value=480, value=20)
with col4:
    priority = st.selectbox("Priority", ["high", "medium", "low"])
with col5:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])

target_pet = st.selectbox("Assign to pet", pet_names)

if st.button("Add Task", type="primary"):
    # Validate time format
    try:
        h, m = task_time.split(":")
        assert 0 <= int(h) <= 23 and 0 <= int(m) <= 59
    except Exception:
        st.error("Time must be in HH:MM format (e.g. 07:30)")
    else:
        new_task = Task(
            title=task_title,
            time=task_time,
            duration_minutes=int(duration),
            priority=priority,
            frequency=frequency,
            pet_name=target_pet,
            due_date=date.today(),
        )
        for pet in owner.pets:
            if pet.name == target_pet:
                pet.add_task(new_task)
                break
        st.success(f"Task '{task_title}' added to {target_pet}!")

st.divider()

# ── Generate & Display Schedule ───────────────────────────────────────────────
st.subheader("Today's Schedule")

col_gen, col_filter = st.columns([2, 1])
with col_filter:
    filter_pet = st.selectbox("Filter by pet", ["All"] + pet_names)

schedule = scheduler.generate_schedule()
if filter_pet != "All":
    schedule = [t for t in schedule if t.pet_name == filter_pet]

# Conflict detection
conflicts = scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        st.warning(warning)

if not schedule:
    st.info("No pending tasks for today. Add some tasks above!")
else:
    for task in schedule:
        cols = st.columns([3, 1, 1, 1, 1, 1])
        with cols[0]:
            label = f"**{task.title}** — {task.pet_name}"
            st.markdown(label)
        with cols[1]:
            st.markdown(f"`{task.time}`")
        with cols[2]:
            st.markdown(f"{task.duration_minutes} min")
        with cols[3]:
            color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task.priority, "")
            st.markdown(f"{color} {task.priority}")
        with cols[4]:
            st.markdown(f"*{task.frequency}*")
        with cols[5]:
            btn_key = f"complete_{task.title}_{task.pet_name}_{task.time}"
            if st.button("Done", key=btn_key):
                scheduler.mark_task_complete(task)
                st.success(f"'{task.title}' marked complete!")
                st.rerun()

st.divider()

# ── All tasks table ───────────────────────────────────────────────────────────
st.subheader("All Tasks")
all_tasks = scheduler.sort_by_time()

if filter_pet != "All":
    all_tasks = [t for t in all_tasks if t.pet_name == filter_pet]

if all_tasks:
    rows = [
        {
            "Time": t.time,
            "Task": t.title,
            "Pet": t.pet_name,
            "Duration (min)": t.duration_minutes,
            "Priority": t.priority,
            "Frequency": t.frequency,
            "Status": "Done" if t.completed else "Pending",
        }
        for t in all_tasks
    ]
    st.table(rows)
else:
    st.info("No tasks yet.")

# ── Stats sidebar ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.divider()
    st.header("Stats")
    total = len(scheduler.get_all_tasks())
    done = len(scheduler.filter_by_status(completed=True))
    pending = len(scheduler.filter_by_status(completed=False))
    st.metric("Total tasks", total)
    st.metric("Completed", done)
    st.metric("Pending", pending)
    if total:
        st.progress(done / total)
