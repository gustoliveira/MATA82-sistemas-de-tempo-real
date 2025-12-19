import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# --- Domain Model ---

@dataclass(frozen=True)
class Task:
    """
    Represents a static task definition.
    Immutable as per requirements.
    """
    id: str
    period: int
    execution_time: int

    @property
    def priority(self) -> int:
        """Rate Monotonic priority: Shorter period = Higher priority (lower value)."""
        return self.period

    @property
    def utilization(self) -> float:
        return self.execution_time / self.period


@dataclass
class Job:
    """
    Represents a specific instance of a task.
    """
    task: Task
    id: int
    arrival_time: float
    remaining_time: float
    absolute_deadline: float
    completed: bool = False

    def __post_init__(self):
        # Ensure remaining_time is float for simulation precision
        self.remaining_time = float(self.remaining_time)


class Processor:
    """
    Represents a CPU core.
    """
    def __init__(self, pid: int):
        self.id = pid
        self.assigned_tasks: List[Task] = []
        self.active_job: Optional[Job] = None
        self.ready_queue: List[Job] = []
        # Log format: (start_time, end_time, task_id)
        self.execution_log: List[Tuple[float, float, str]] = []

    @property
    def utilization(self) -> float:
        return sum(t.utilization for t in self.assigned_tasks)

    def add_task(self, task: Task):
        self.assigned_tasks.append(task)

    def sort_ready_queue(self):
        """
        Sorts the ready queue based on Rate Monotonic policy (Period).
        Secondary sort key could be arrival time for FIFO within same priority, 
        but period is the primary RM key.
        """
        self.ready_queue.sort(key=lambda j: j.task.period)

# --- Algorithms ---

def liu_layland_bound(n: int) -> float:
    """
    Calculates the Liu & Layland utilization bound for n tasks.
    U <= n * (2^(1/n) - 1)
    """
    if n == 0:
        return 1.0
    return n * (math.pow(2, 1/n) - 1)

def partition_tasks_ff_rm(tasks: List[Task]) -> List[Processor]:
    """
    First-Fit Rate Monotonic Partitioning.
    """
    # 1. Sort global tasks by priority (RM: shortest period first)
    sorted_tasks = sorted(tasks, key=lambda t: t.period)
    
    processors: List[Processor] = [Processor(0)]

    for task in sorted_tasks:
        assigned = False
        for proc in processors:
            # Liu & Layland Test
            current_n = len(proc.assigned_tasks)
            new_n = current_n + 1
            current_u = proc.utilization
            
            # Check if adding this task keeps us under the bound
            if (current_u + task.utilization) <= liu_layland_bound(new_n):
                proc.add_task(task)
                assigned = True
                break
        
        if not assigned:
            # Create new processor
            new_proc = Processor(len(processors))
            new_proc.add_task(task)
            processors.append(new_proc)
            
    return processors

# --- Discrete Event Simulation Engine ---

def run_simulation(processors: List[Processor], max_time: int):
    """
    Executes the discrete event simulation.
    """
    current_time = 0.0
    
    # Track next arrival time for each task on each processor
    # Map: Processor -> Task -> Next Arrival Time
    task_next_arrival = {}
    for proc in processors:
        task_next_arrival[proc] = {task: 0.0 for task in proc.assigned_tasks}
        
    job_counters = {task.id: 1 for proc in processors for task in proc.assigned_tasks}

    while current_time < max_time:
        # --- Step A: Find Next Event ---
        next_arrival = float('inf')
        
        # Check potential arrivals
        for proc in processors:
            for task, arrival in task_next_arrival[proc].items():
                if arrival < next_arrival:
                    next_arrival = arrival
        
        # Check potential completions
        next_completion = float('inf')
        for proc in processors:
            if proc.active_job:
                # Time to finish current job
                completion_time = current_time + proc.active_job.remaining_time
                if completion_time < next_completion:
                    next_completion = completion_time
        
        next_event_time = min(next_arrival, next_completion)
        
        # Cap at max_time
        if next_event_time > max_time:
            next_event_time = max_time
            if next_event_time == current_time: # Avoid infinite loop at end
                break

        # --- Step B: Advance State (Delta Calculation) ---
        dt = next_event_time - current_time
        
        # Only advance if time actually passes
        if dt > 0:
            for proc in processors:
                if proc.active_job:
                    proc.active_job.remaining_time -= dt
                    # Log execution
                    # Append to last log if contiguous, else new entry
                    if proc.execution_log and proc.execution_log[-1][2] == proc.active_job.task.id and proc.execution_log[-1][1] == current_time:
                        # Update end time of existing entry
                        last_start, _, tid = proc.execution_log.pop()
                        proc.execution_log.append((last_start, next_event_time, tid))
                    else:
                        proc.execution_log.append((current_time, next_event_time, proc.active_job.task.id))
        
        current_time = next_event_time

        # --- Step C: Handle Events ---
        
        # 1. Handle Completions
        for proc in processors:
            if proc.active_job and proc.active_job.remaining_time <= 1e-9: # Epsilon for float comparison
                proc.active_job.completed = True
                proc.active_job = None

        # 2. Handle Arrivals
        for proc in processors:
            for task in list(task_next_arrival[proc].keys()):
                if abs(task_next_arrival[proc][task] - current_time) < 1e-9:
                    # Create new job
                    new_job = Job(
                        task=task,
                        id=job_counters[task.id],
                        arrival_time=current_time,
                        remaining_time=task.execution_time,
                        absolute_deadline=current_time + task.period
                    )
                    job_counters[task.id] += 1
                    proc.ready_queue.append(new_job)
                    
                    # Schedule next arrival
                    task_next_arrival[proc][task] += task.period

        # --- Step D: Dispatcher (Scheduling) ---
        for proc in processors:
            # Preemption Logic
            if proc.active_job:
                # Check if anyone in ready queue has STRICTLY higher priority (lower period)
                # Note: If periods are equal, RM usually favors the current one or FCFS. 
                # We adhere to "strictly smaller period" for preemption to avoid unnecessary context switches.
                better_candidate = False
                for job in proc.ready_queue:
                    if job.task.period < proc.active_job.task.period:
                        better_candidate = True
                        break
                
                if better_candidate:
                    proc.ready_queue.append(proc.active_job)
                    proc.active_job = None
            
            # Select Job
            proc.sort_ready_queue()
            
            if not proc.active_job and proc.ready_queue:
                proc.active_job = proc.ready_queue.pop(0)


# --- Visualization ---

def print_gantt(processors: List[Processor], max_time: int):
    """
    Generates ASCII Gantt Chart.
    """
    print("\n" + "="*50)
    print("SIMULATION RESULTS (ASCII Gantt)")
    print("="*50 + "\n")

    # Time header
    header = "Time: "
    for t in range(max_time + 1):
        header += f"{t:<5}"
    print(header)
    
    # Separator
    separator = "      " + "|----" * max_time + "|"
    print(separator)

    for proc in processors:
        row = f"CPU {proc.id}: "
        
        # We need to fill the timeline slot by slot
        # This is a discrete visualization of continuous data, simplified for the requirement.
        # We check execution log to see what was running between t and t+1.
        
        for t in range(max_time):
            # Find if any task executed significantly in interval [t, t+1]
            # A task counts if it executed for the majority of the slot or was the main occupant?
            # For simplicity in this int-based visualization, we look for an entry covering this start time.
            
            task_id = "   " # Default idle
            
            # Naive search in log for coverage
            # We look for a segment that covers the midpoint of the interval (t + 0.5)
            # or simply starts at t.
            midpoint = t + 0.5
            found = False
            
            for start, end, tid in proc.execution_log:
                if start <= midpoint < end:
                    task_id = f"{tid:<3}"
                    found = True
                    break
            
            # Simple conflict/deadline check could be added here if we tracked history of jobs better.
            
            row += f"[{task_id}]"
        
        print(row)
    print("\n")


# --- Main Execution ---

if __name__ == "__main__":
    # Test Case from Specification
    # T1 (C=1, T=2) - U=0.5
    # T2 (C=2, T=5) - U=0.4
    # T3 (C=2, T=4) - U=0.5
    
    tasks = [
        Task("T1", 2, 1),
        Task("T2", 5, 2),
        Task("T3", 4, 2)
    ]

    # Calculate Hyperperiod (LCM)
    def lcm(a, b):
        return abs(a*b) // math.gcd(a, b)
    
    hyperperiod = 1
    for t in tasks:
        hyperperiod = lcm(hyperperiod, t.period)

    # --- SCENARIO 1: Uniprocessor Rate Monotonic (Pure RM) ---
    print("\n" + "#"*60)
    print("SCENARIO 1: Uniprocessor Rate Monotonic (All tasks on CPU 0)")
    print("#"*60)
    
    # Force all tasks onto one processor
    cpu0 = Processor(0)
    for t in tasks:
        cpu0.add_task(t)
    
    print(f"Processor 0 Tasks: {[t.id for t in cpu0.assigned_tasks]}")
    print(f"Total Utilization: {cpu0.utilization:.2f} (Overload expected if > 1.0 or > LL bound)")

    run_simulation([cpu0], hyperperiod)
    print_gantt([cpu0], hyperperiod)


    # --- SCENARIO 2: Multiprocessor First-Fit Rate Monotonic (FF-RM) ---
    print("\n" + "#"*60)
    print("SCENARIO 2: Multiprocessor First-Fit Rate Monotonic (FF-RM)")
    print("#"*60)
    
    # Use Partitioning Logic
    print("Partitioning tasks...")
    processors_ff = partition_tasks_ff_rm(tasks)
    
    for proc in processors_ff:
        t_ids = [t.id for t in proc.assigned_tasks]
        print(f"Processor {proc.id}: {t_ids} (Utilization: {proc.utilization:.2f})")
    
    print(f"Hyperperiod: {hyperperiod}")
    
    run_simulation(processors_ff, hyperperiod)
    print_gantt(processors_ff, hyperperiod)
