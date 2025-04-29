# scheduler.py
import copy
import sys


# Process with attributes
class Process:
    def __init__(self, pid, arrival_time, burst_time):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time

        # Performance metrics
        # Time execution first starts
        self.start_time = -1
        self.completion_time = -1
        self.waiting_time = 0
        self.turnaround_time = 0

        # Internal tracking for algorithms
        self.remaining_time = burst_time

        # Used for calculating intermittent waits
        self.last_execution_time = arrival_time

    def __repr__(self):
        return f"P{self.pid}(AT:{self.arrival_time}, BT:{self.burst_time})"


# Calculate the average metrics for a list of completed processes
def calculate_metrics(processes):
    num_processes = len(processes)
    if num_processes == 0:
        return {"AWT": 0, "ATT": 0, "CPU Utilization": 0, "Throughput": 0}

    total_waiting_time = sum(p.waiting_time for p in processes)
    total_turnaround_time = sum(p.turnaround_time for p in processes)

    # Find total time elapsed
    first_arrival = min(p.arrival_time for p in processes) if processes else 0
    last_completion = max(p.completion_time for p in processes) if processes else 0
    total_time_elapsed = last_completion - first_arrival

    # Avoid division by zero
    if total_time_elapsed <= 0:
        total_time_elapsed = 1

    # Find total busy time
    total_burst_time = sum(p.burst_time for p in processes)

    awt = total_waiting_time / num_processes
    att = total_turnaround_time / num_processes
    cpu_utilization = (total_burst_time / total_time_elapsed) * 100 if total_time_elapsed > 0 else 0
    effective_total_time = last_completion
    throughput = num_processes / effective_total_time if effective_total_time > 0 else 0

    return {
        "AWT": round(awt, 2),
        "ATT": round(att, 2),
        "CPU Utilization": round(cpu_utilization, 2),

        # Processes per time unit
        "Throughput": round(throughput, 4)
    }


# Shortest Remaining Time First (SRTF) algorithm
def run_srtf(process_list):
    processes = copy.deepcopy(process_list)
    num_processes = len(processes)
    completed_processes = []
    ready_queue = []
    current_time = 0
    current_process = None
    cpu_busy_time = 0

    print("\nSRTF Simulation")

    # (pid, start_time, end_time)
    gantt_chart = []

    processes.sort(key=lambda proc: proc.arrival_time)
    process_idx = 0

    while len(completed_processes) < num_processes:

        # Add newly arrived processes to ready queue
        while process_idx < num_processes and processes[process_idx].arrival_time <= current_time:
            ready_queue.append(processes[process_idx])
            process_idx += 1

        # Sort ready queue by remaining time (shortest first)
        ready_queue.sort(key=lambda item: item.remaining_time)

        # Check for preemption or selection of new process
        new_process = None
        if ready_queue:
            # Shortest remaining time process
            new_process = ready_queue[0]

        # Preemption check, check if a new shorter job arrived
        if current_process:
            if new_process and new_process.remaining_time < current_process.remaining_time:

                # Add current process back to ready queue if not finished
                if current_process.remaining_time > 0:
                    ready_queue.append(current_process)
                current_process = new_process

                # Remove the selected new process
                ready_queue.pop(0)
        elif new_process:

            # CPU was idle, start the shortest job
            current_process = new_process
            ready_queue.pop(0)

        # Execute the current process
        if current_process:

            # First time running
            if current_process.start_time == -1:
                current_process.start_time = current_time

            exec_start_time = current_time
            current_process.remaining_time -= 1
            current_time += 1
            cpu_busy_time += 1
            gantt_chart.append((current_process.pid, exec_start_time, current_time))

            if current_process.remaining_time == 0:
                current_process.completion_time = current_time
                current_process.turnaround_time = current_process.completion_time - current_process.arrival_time
                current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
                completed_processes.append(current_process)

                # CPU becomes free
                current_process = None

        # If no preemption occurred, current_process remains set for next cycle unless finished
        else:

            # No process ready or running, CPU is idle
            current_time += 1

            # -1 indicates Idle
            gantt_chart.append((-1, current_time - 1, current_time))

    # Clean up Gantt chart (merge consecutive entries)
    merged_gantt = []
    if gantt_chart:
        last_pid, start, end = gantt_chart[0]
        for i in range(1, len(gantt_chart)):
            pid, s, e = gantt_chart[i]
            if pid == last_pid:

                # Extend duration
                end = e
            else:
                merged_gantt.append((f"P{last_pid}" if last_pid != -1 else "Idle", start, end))
                last_pid, start, end = pid, s, e
        merged_gantt.append((f"P{last_pid}" if last_pid != -1 else "Idle", start, end))

    print("Gantt Chart (PID, Start, End):", merged_gantt)
    print("Process Metrics:")
    for p in sorted(completed_processes, key=lambda proc: proc.pid):
        print(f"  P{p.pid}: Completion={p.completion_time}, TAT={p.turnaround_time}, WT={p.waiting_time}")

    # Ensure calculation uses the final list of completed processes
    completed_processes.sort(key=lambda x: x.pid)
    metrics = calculate_metrics(completed_processes)
    print("Average Metrics:", metrics)
    return metrics, completed_processes


# Round Robin (RR) algorithm
def run_rr(process_list, quantum):
    processes = copy.deepcopy(process_list)
    num_processes = len(processes)
    completed_processes = []

    # FIFO queue
    ready_queue = []
    current_time = 0
    time_slice_left = 0
    current_process = None
    cpu_busy_time = 0

    print(f"\nRound Robin Simulation (Quantum={quantum})")
    gantt_chart = []

    processes.sort(key=lambda proc2: proc2.arrival_time)
    process_idx = 0

    # Track processes that have arrived
    processes_in_system = []

    while len(completed_processes) < num_processes:

        # Add newly arrived processes to the end of the ready queue
        newly_arrived = []
        while process_idx < num_processes and processes[process_idx].arrival_time <= current_time:
            proc = processes[process_idx]
            processes_in_system.append(proc)
            ready_queue.append(proc)
            newly_arrived.append(proc.pid)
            process_idx += 1

        # Select next process if current one finished or quantum expired or CPU idle
        if current_process is None or time_slice_left == 0:
            if current_process is not None and current_process.remaining_time > 0:
                # Add back to queue if quantum is expired and not finished
                ready_queue.append(current_process)

            if ready_queue:

                # Get front of queue
                current_process = ready_queue.pop(0)
                time_slice_left = quantum

                # First time running
                if current_process.start_time == -1:
                    current_process.start_time = current_time
            else:

                # If queue is empty but not all processes are done, CPU is idle
                current_process = None
                if len(completed_processes) < num_processes and process_idx < num_processes:

                    # Advance time to next arrival if needed
                    next_arrival_time = processes[process_idx].arrival_time
                    idle_start = current_time
                    current_time = next_arrival_time

                    # Idle time
                    gantt_chart.append((-1, idle_start, current_time))

                    # Re-check arrivals at new time
                    continue

                elif len(completed_processes) < num_processes:

                    # Idle because processes are in I/O or future arrival, just tick time
                    gantt_chart.append((-1, current_time, current_time + 1))
                    current_time += 1
                    continue
                else:
                    break

        # Execute the current process
        if current_process:
            exec_start_time = current_time
            run_time = min(time_slice_left, current_process.remaining_time)

            current_process.remaining_time -= run_time
            time_slice_left -= run_time
            current_time += run_time
            cpu_busy_time += run_time
            gantt_chart.append((current_process.pid, exec_start_time, current_time))

            if current_process.remaining_time == 0:
                current_process.completion_time = current_time
                current_process.turnaround_time = current_process.completion_time - current_process.arrival_time
                current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
                completed_processes.append(current_process)

                # Free the CPU for next selection cycle
                current_process = None

                # Ensure new process is selected next cycle
                time_slice_left = 0
        else:

            # Handles idle cases
            if len(completed_processes) < num_processes:
                gantt_chart.append((-1, current_time, current_time + 1))
                current_time += 1
            else:
                break

    # Clean up Gantt chart
    merged_gantt = []
    if gantt_chart:
        last_pid, start, end = gantt_chart[0]
        for i in range(1, len(gantt_chart)):
            pid, s, e = gantt_chart[i]

            # Check continuity
            if pid == last_pid and s == end:

                # Extend duration
                end = e
            else:
                merged_gantt.append((f"P{last_pid}" if last_pid != -1 else "Idle", start, end))
                last_pid, start, end = pid, s, e
        merged_gantt.append((f"P{last_pid}" if last_pid != -1 else "Idle", start, end))

    print("Gantt Chart (PID, Start, End):", merged_gantt)
    print("Process Metrics:")

    # Sort completed processes by PID
    completed_processes.sort(key=lambda x: x.pid)
    for p in completed_processes:
        print(f"  P{p.pid}: Completion={p.completion_time}, TAT={p.turnaround_time}, WT={p.waiting_time}")

    metrics = calculate_metrics(completed_processes)
    print("Average Metrics:", metrics)
    return metrics, completed_processes


# Test Scenarios
# Scenario 1: Small scale test
processes_small = [
    Process(pid=1, arrival_time=0, burst_time=8),
    Process(pid=2, arrival_time=1, burst_time=4),
    Process(pid=3, arrival_time=2, burst_time=9),
    Process(pid=4, arrival_time=3, burst_time=5),
]

# Scenario 2: Large scale test
processes_large = [
    Process(pid=1, arrival_time=0, burst_time=5),
    Process(pid=2, arrival_time=2, burst_time=5),
    Process(pid=3, arrival_time=4, burst_time=5),
    Process(pid=4, arrival_time=5, burst_time=5),
    Process(pid=5, arrival_time=6, burst_time=5),
    Process(pid=6, arrival_time=8, burst_time=5),
    Process(pid=7, arrival_time=9, burst_time=5),
    Process(pid=8, arrival_time=11, burst_time=5),
    Process(pid=9, arrival_time=12, burst_time=5),
    Process(pid=10, arrival_time=15, burst_time=5),
]

# Scenario 3: Edge case
# All arrive at 0 with varying bursts
processes_edge1 = [
    Process(pid=1, arrival_time=0, burst_time=10),
    Process(pid=2, arrival_time=0, burst_time=1),
    Process(pid=3, arrival_time=0, burst_time=2),
    Process(pid=4, arrival_time=0, burst_time=1),
    Process(pid=5, arrival_time=0, burst_time=5),
]

# Scenario 4: Edge case
# Long and short bursts with mixed arrivals
processes_edge2 = [
    Process(pid=1, arrival_time=0, burst_time=20),
    Process(pid=2, arrival_time=1, burst_time=2),
    Process(pid=3, arrival_time=2, burst_time=3),
    Process(pid=4, arrival_time=3, burst_time=1),
    Process(pid=5, arrival_time=30, burst_time=2),
]

if __name__ == "__main__":
    # Map names to the process lists
    scenarios = {
        "small": processes_small,
        "large": processes_large,
        "edge1": processes_edge1,
        "edge2": processes_edge2
    }

    # Scenario Selection
    if len(sys.argv) != 2 or sys.argv[1] not in scenarios:
        print("Usage: python scheduler.py <scenario_name>")
        print("Available scenarios:", ", ".join(scenarios.keys()))
        # Exit if incorrect arguments
        sys.exit(1)

    choice = sys.argv[1]
    test_scenario = scenarios[choice]
    print(f"Selected scenario via command line: {choice}")

    print(f"Simulating scenario: {[str(p) for p in test_scenario]}")

    # Run SRTF
    srtf_metrics, srtf_results = run_srtf(test_scenario)

    # Run Round Robin with time quantum of 4
    rr_quantum = 4
    rr_metrics, rr_results = run_rr(test_scenario, rr_quantum)

    # Performance Summary
    print("\nPerformance Summary")
    print("\nAlgorithm: SRTF\nAWT: " + str(srtf_metrics['AWT'])
          + "\nATT: " + str(srtf_metrics['ATT'])
          + "\nCPU Util (%): " + str(srtf_metrics['CPU Utilization'])
          + "\nThroughput: " + str(srtf_metrics['Throughput']))

    print(f"\nAlgorithm: RR (Q={rr_quantum})\nAWT: {rr_metrics['AWT']}"
          + f"\nATT: {rr_metrics['ATT']}"
          + f"\nCPU Util (%): {rr_metrics['CPU Utilization']}"
          + f"\nThroughput: {rr_metrics['Throughput']}")
