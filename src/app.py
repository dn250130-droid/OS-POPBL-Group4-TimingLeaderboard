from flask import Flask, render_template, request, jsonify
import threading
import queue
import time

app = Flask(__name__)

# ==============================================================================
# OS CONCEPTS: I/O BUFFERING & DOUBLE BUFFERING
# ==============================================================================
BUFFER_CAPACITY = 50
io_input_buffer = queue.Queue(maxsize=BUFFER_CAPACITY)

front_buffer_leaderboard = {}
back_buffer_leaderboard = {}
buffer_lock = threading.Lock()

RACE_DURATION_SECONDS = 3600  # 1 Jam
DEBOUNCE_SECONDS = 10         # Elak double-scan dalam masa 10 saat
race_start_time = time.time()

telemetry = {
    "interrupts_received": 0,
    "records_spooled": 0,
    "duplicates_ignored": 0,
    "buffer_drops": 0
}

# ==============================================================================
# OS CONCEPT: BACKGROUND SPOOLER THREAD
# ==============================================================================
def spooler_worker():
    global front_buffer_leaderboard, back_buffer_leaderboard
    while True:
        try:
            record = io_input_buffer.get(timeout=0.5)
        except queue.Empty:
            continue

        time.sleep(0.1)  # Simulasi masa pemprosesan I/O
        r_id = record["runner_id"]
        scan_time = record["timestamp"]
        elapsed = scan_time - race_start_time

        if elapsed <= RACE_DURATION_SECONDS:
            if r_id not in back_buffer_leaderboard:
                back_buffer_leaderboard[r_id] = {
                    "id": r_id,
                    "loops": 1,
                    "last_scan": scan_time,
                    "total_time": round(elapsed, 2)
                }
                telemetry["records_spooled"] += 1
            else:
                if scan_time - back_buffer_leaderboard[r_id]["last_scan"] >= DEBOUNCE_SECONDS:
                    back_buffer_leaderboard[r_id]["loops"] += 1
                    back_buffer_leaderboard[r_id]["last_scan"] = scan_time
                    back_buffer_leaderboard[r_id]["total_time"] = round(elapsed, 2)
                    telemetry["records_spooled"] += 1
                else:
                    telemetry["duplicates_ignored"] += 1

            # Double Buffer Swap ke paparan website
            with buffer_lock:
                front_buffer_leaderboard = {k: v.copy() for k, v in back_buffer_leaderboard.items()}

        io_input_buffer.task_done()

# Jalankan Spooler di belakang tabir
threading.Thread(target=spooler_worker, daemon=True).start()

# ==============================================================================
# WEB ROUTES & INTERRUPT ENDPOINT
# ==============================================================================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scan", methods=["POST"])
def trigger_qr_interrupt():
    """Menerima signal QR dari website sebagai Hardware Interrupt (IRQ)."""
    data = request.json
    runner_id = data.get("runner_id", "").strip()
    if not runner_id:
        return jsonify({"status": "error", "message": "Invalid QR"}), 400

    telemetry["interrupts_received"] += 1
    try:
        io_input_buffer.put_nowait({"runner_id": runner_id, "timestamp": time.time()})
        return jsonify({"status": "queued", "runner_id": runner_id})
    except queue.Full:
        telemetry["buffer_drops"] += 1
        return jsonify({"status": "dropped", "message": "I/O Buffer Full!"}), 503

@app.route("/api/leaderboard")
def get_leaderboard():
    """Membaca data daripada Front Buffer untuk dipaparkan di website."""
    with buffer_lock:
        ranked = sorted(
            front_buffer_leaderboard.values(),
            key=lambda x: (-x["loops"], x["total_time"])
        )
    remaining = max(0, int(RACE_DURATION_SECONDS - (time.time() - race_start_time)))
    return jsonify({
        "leaderboard": ranked,
        "remaining_seconds": remaining,
        "buffer_usage": io_input_buffer.qsize(),
        "buffer_capacity": BUFFER_CAPACITY,
        "telemetry": telemetry
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
