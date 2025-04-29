# project-2: CPU Scheduling Simulator

This project implements and evaluates CPU scheduling algorithms and was built from scratch in Python.

## Project Goal

To simulate different CPU scheduling algorithms, measure their performance using standard metrics, and analyze their behavior under various workloads.

## Algorithms Implemented

This simulator implements the following algorithms:

1.  **Shortest Remaining Time First (SRTF):** A preemptive scheduling algorithm where the process with the smallest remaining execution time is chosen to run.
2.  **Round Robin (RR):** A preemptive scheduling algorithm where each process is assigned a fixed time unit (quantum) to execute. If the process doesn't complete within the quantum, it's moved to the back of the ready queue.

## Performance Metrics Calculated

The simulator calculates the following metrics for each algorithm:

*   **Average Waiting Time (AWT):** The average time processes spend waiting in the ready queue.
*   **Average Turnaround Time (ATT):** The average time from process arrival to process completion.
*   **CPU Utilization (%):** The percentage of time the CPU is busy executing processes.
*   **Throughput:** The number of processes completed per unit of time.

## How to Run

1.  **Prerequisites:** Ensure you have Python 3.x installed.
2.  **Clone the repository:**
    ```bash
    git clone <this-repo-url>
    cd <repository-directory>
    ```
3.  **Execute the script:**
    ```bash
    python scheduler.py
    ```
4.  **Modify Test Scenario:** To run different test workloads, edit the `test_scenario` variable near the end of the `scheduler.py` file to select one of the predefined `processes_small`, `processes_large`, `processes_edge1`, or `processes_edge2` lists, or define your own list of `Process` objects.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Notes

*   The Round Robin quantum is currently hardcoded in the `main` block (`rr_quantum = 4`).
*   The output includes a simple text-based Gantt chart representation and a summary table of performance metrics.
