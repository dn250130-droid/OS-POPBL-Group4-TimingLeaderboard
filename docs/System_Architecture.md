# System Architecture & OS I/O Flow (Week 5)

## 1. High-Level System Architecture
This diagram illustrates how physical QR scan events are processed as OS Hardware Interrupts, queued in an in-memory Circular Buffer, and processed asynchronously by a background Spooler thread to update the Live Leaderboard.

```mermaid
flowchart LR
    subgraph Hardware_IO [1. Input Hardware Layer]
        A[Runner QR Code] -->|Camera / Scanner| B(QR Input Device)
    end

    subgraph Kernel_OS [2. OS I/O Management Layer]
        B -->|Triggers IRQ| C{Interrupt Handler / ISR}
        C -->|Push Payload: ID + Time| D[(Circular Input Buffer\nRAM Queue)]
        D -->|FIFO Pop| E[Background Spooler Thread]
    end

    subgraph Storage_UI [3. Storage & Output Layer]
        E -->|Validate & Save| F[(Persistent Log / DB)]
        E -->|Write New Rank| G[Back Buffer\nLeaderboard State]
        G -.->|Buffer Swap| H[Front Buffer\nLive Web UI]
    end
```

## 2. Spooler & Loop Validation Flowchart
To prevent accidental double-scans (e.g., a runner holding their QR code in front of the scanner for 3 seconds), the Spooler thread enforces a debounce threshold before incrementing the loop count.

```mermaid
flowchart TD
    Start([Spooler Thread Active]) --> CheckBuf{Is Input Buffer Empty?}
    CheckBuf -- Yes --> Wait[Sleep / Wait for Interrupt]
    Wait --> CheckBuf
    CheckBuf -- No --> Pop[Pop Oldest Scan Record]
    Pop --> CheckTimer{Is 1-Hour Race Active?}
    CheckTimer -- No --> Discard1[Log as Overtime / Ignore]
    Discard1 --> CheckBuf
    CheckTimer -- Yes --> Debounce{Time Since Last Scan > 30s?}
    Debounce -- No --> Discard2[Ignore Duplicate Scan]
    Discard2 --> CheckBuf
    Debounce -- Yes --> Update[Increment Runner Loop Count & Total Time]
    Update --> Swap[Update Back Buffer & Swap to Live Leaderboard]
    Swap --> CheckBuf
```

## 3. Selected Development Tools
* **Core Engine:** Python 3.10+ (`threading`, `queue.Queue`, `time`)
* **I/O Input Simulation & Capture:** OpenCV + `pyzbar` (Webcam QR Reader) & Multi-threaded Stress Tester
* **Live Leaderboard Interface:** Flask Web Server + HTML/JavaScript (Auto-refreshing Front Buffer)
