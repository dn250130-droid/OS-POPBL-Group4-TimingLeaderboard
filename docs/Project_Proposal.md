# Project Proposal: Automated QR Loop Timing & Live Leaderboard System

## 1. Event Scenario
The Community Running Event features a **1-Hour Loop Challenge**, where participants aim to complete as many loops as possible within a 60-minute timeframe. At the end of each loop, runners scan their unique QR code at the checkpoint. The system records the exact timestamp, validates the loop, and updates a public Live Leaderboard in real time.

## 2. Mapping to Operating System Concepts (I/O Management & Buffering)
To handle high-frequency scans without system lag or dropped records, the software mimics core OS I/O management mechanisms:
* **I/O Device & Interrupt Handling:** The QR scanner acts as an external input device. Every valid QR scan generates an Interrupt Request (IRQ), immediately capturing the Runner ID and system timestamp without blocking the main user interface.
* **I/O Buffering (Circular Queue):** Raw interrupt payloads are placed into an in-memory Circular Buffer (Bounded Queue). This absorbs burst traffic when groups of runners scan their QR codes within the same second.
* **Spooling (Background Consumer):** A dedicated background Spooler thread continuously reads data from the buffer in First-In-First-Out (FIFO) order, checks for duplicate scans (debounce threshold), updates the runner's total loop count, and writes to persistent storage.
* **Double Buffering (Display Output):** The Live Leaderboard alternates between a front buffer (displayed to spectators) and a back buffer (updated by the spooler) to ensure smooth, flicker-free screen refreshes.

## 3. Proposed Tech Stack
* **Programming Language:** Python 3
* **OS Concurrency & I/O Libraries:** `threading`, `queue` (for buffering), `time`
* **QR Input Module:** OpenCV & `pyzbar` (Webcam scanner) + CLI Stress-Test Simulator (to simulate 50+ simultaneous scans)
* **Frontend / Live Dashboard:** Flask + HTML/CSS/JavaScript

## 4. Team Role Distribution
* **Member 1:** Core OS Architecture (Interrupt Handler, Circular Buffer & Spooler Thread)
* **Member 2:** QR Scanner I/O Module & Concurrent Load Simulator
* **Member 3:** 1-Hour Race Timer, Loop Validation & Ranking Logic
* **Member 4:** Live Leaderboard Web UI & Real-Time Buffer Monitor Dashboard
* **Member 5:** System Architecture Diagrams, Testing Analysis & Presentation Assets
