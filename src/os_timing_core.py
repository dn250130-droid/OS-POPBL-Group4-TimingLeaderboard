import threading
import queue
import time
import random
from datetime import datetime

# ==============================================================================
# OS CONCEPT 1: I/O BUFFERING (Bounded Circular Buffer in RAM)
# Absorbs high-frequency QR scan bursts without dropping runner records.
# ==============================================================================
BUFFER_CAPACITY = 50
io_input_buffer = queue.Queue(maxsize=BUFFER_CAPACITY)

# ==============================================================================
# OS CONCEPT 2: DOUBLE BUFFERING FOR LIVE LEADERBOARD
# Back buffer is updated by the Spooler; Front buffer is read by the UI.
# ==============================================================================
front_buffer_leaderboard = {}
back_buffer_leaderboard = {}
buffer_lock = threading.Lock()

# System & Race Configurations
RACE_DURATION_SECONDS = 3600  # 1 Hour (3600 seconds)
DEBOUNCE_SECONDS = 10         # Minimum time between valid loop scans per runner
race_start_time = None
system_running = True

# OS Telemetry Counters (For Live Demo & Technical Report)
telemetry = {
    "interrupts_received": 0,
    "buffer_drops": 0,
    "records_spooled": 0,
    "duplicates_ignored": 0
}


# ==============================================================================
# OS CONCEPT 3: HARDWARE INTERRUPT SERVICE ROUTINE (ISR)
# Triggered asynchronously every time the QR Scanner reads a Runner ID.
# ==============================================================================
def trigger_qr_interrupt(runner_id: str, runner_name: str):
    """Simulates a hardware IRQ when a runner scans their QR code."""
    global telemetry
    scan_timestamp = time.time()
    telemetry["interrupts_received"] += 1

    irq_payload = {
        "runner_id": runner_id,
        "runner_name": runner_name,
        "timestamp": scan_timestamp
    }

    try:
        # Non-blocking write into the I/O Input Buffer
        io_input_buffer.put_nowait(irq_payload)
        print(f"[IRQ] Scan captured: {runner_id} | Buffer Load: {io_input_buffer.qsize()}/{BUFFER_CAPACITY}")
    except queue.Full:
        # Buffer overflow protection
        telemetry["buffer_drops"] += 1
        print(f"[IRQ WARNING] I/O Buffer Full! Dropped scan for {runner_id}")


# ==============================================================================
# OS CONCEPT 4: SPOOLING (Background Consumer Thread)
# Reads buffered scans in FIFO order, validates loops, and swaps UI buffers.
# ==============================================================================
def spooler_worker():
    """Background daemon thread acting as the OS I/O Spooler."""
    global front_buffer_leaderboard, back_buffer_leaderboard, telemetry

    while system_running or not io_input_buffer.empty():
        try:
            # Wait up to 0.5s for an item from the circular buffer
            record = io_input_buffer.get(timeout=0.5)
        except queue.Empty:
            continue

        # Simulate slight disk/processing latency to demonstrate why buffering is needed
        time.sleep(0.15)

        r_id = record["runner_id"]
        r_name = record["runner_name"]
        scan_time = record["timestamp"]
        elapsed_race_time = scan_time - race_start_time

        # 1. Check if scan occurred within the 1-hour race window
        if elapsed_race_time > RACE_DURATION_SECONDS:
            print(f"[SPOOLER] Overtime scan ignored for {r_id} ({elapsed_race_time:.1f}s)")
            io_input_buffer.task_done()
            continue

        # 2. Process runner record in the Back Buffer
        if r_id not in back_buffer_leaderboard:
            # First scan registers the runner at Loop 1
            back_buffer_leaderboard[r_id] = {
                "name": r_name,
                "loops": 1,
                "last_scan": scan_time,
                "total_time": elapsed_race_time
            }
            telemetry["records_spooled"] += 1
        else:
            time_since_last_loop = scan_time - back_buffer_leaderboard[r_id]["last_scan"]

            # Debounce check: prevent accidental double-scans at the checkpoint
            if time_since_last_loop < DEBOUNCE_SECONDS:
                telemetry["duplicates_ignored"] += 1
                print(f"[SPOOLER] Duplicate scan ignored for {r_id} ({time_since_last_loop:.2f}s)")
                io_input_buffer.task_done()
                continue

            # Valid loop completed
            back_buffer_leaderboard[r_id]["loops"] += 1
            back_buffer_leaderboard[r_id]["last_scan"] = scan_time
            back_buffer_leaderboard[r_id]["total_time"] = elapsed_race_time
            telemetry["records_spooled"] += 1

        # 3. Double Buffer Swap: Safely publish updated leaderboard to Front Buffer
        with buffer_lock:
            front_buffer_leaderboard = {
                k: v.copy() for k, v in back_buffer_leaderboard.items()
            }

        io_input_buffer.task_done()


def display_leaderboard():
    """Reads exclusively from the Front Buffer to render the Live Leaderboard."""
    with buffer_lock:
        # Sort by highest loops first, then lowest total time (tie-breaker)
        sorted_runners = sorted(
            front_buffer_leaderboard.items(),
            key=lambda item: (-item[1]["loops"], item[1]["total_time"])
        )

    print("\n" + "=" * 60)
    print(" LIVE LEADERBOARD (1-HOUR LOOP CHALLENGE) ")
    print("=" * 60)
    print(f"{'Rank':<6}{'ID':<10}{'Name':<18}{'Loops':<8}{'Time (s)':<10}")
    print("-" * 60)
    for rank, (r_id, data) in enumerate(sorted_runners, start=1):
        print(f"{rank:<6}{r_id:<10}{data['name']:<18}{data['loops']:<8}{data['total_time']:<10.2f}")
    print("=" * 60)
    print(f"OS Telemetry -> IRQs: {telemetry['interrupts_received']} | "
          f"Spooled: {telemetry['records_spooled']} | "
          f"Duplicates Ignored: {telemetry['duplicates_ignored']} | "
          f"Drops: {telemetry['buffer_drops']}\n")


# ==============================================================================
# SIMULATION RUNNER (Alpha Test: Concurrent Burst Scans)
# ==============================================================================
if __name__ == "__main__":
    print("Initializing OS Timing & Leaderboard Kernel...")
    race_start_time = time.time()

    # Start the background Spooler thread
    spooler = threading.Thread(target=spooler_worker, daemon=True)
    spooler.start()

    runners = [
        ("R001", "Aiman"), ("R002", "Siti"), ("R003", "Chong"),
        ("R004", "Priya"), ("R005", "Hafiz"), ("R006", "Nurul")
    ]

    # Simulate Loop 1: Burst traffic (all 6 runners scan almost simultaneously)
    print("\n--- Simulating Burst Scan Wave 1 (Loop 1) ---")
    for r_id, name in runners:
        trigger_qr_interrupt(r_id, name)
        time.sleep(0.05)  # 50ms apart (faster than spooler processing speed!)

    # Simulate an accidental duplicate scan by R001
    trigger_qr_interrupt("R001", "Aiman")

    # Wait for Spooler to drain the I/O Buffer
    io_input_buffer.join()
    display_leaderboard()

    # Wait past debounce threshold to simulate Loop 2
    print("Waiting 11 seconds to simulate Loop 2 completion...")
    time.sleep(11)

    print("\n--- Simulating Burst Scan Wave 2 (Loop 2) ---")
    for r_id, name in random.sample(runners, 4):
        trigger_qr_interrupt(r_id, name)
        time.sleep(0.05)

    io_input_buffer.join()
    system_running = False
    spooler.join()

    display_leaderboard()
