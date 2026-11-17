# OS-POPBL-Group4-TimingLeaderboard

## Team Members (Group 4)
1- DN250130	 AZIEM HAKIMIE BIN ZU @ ZULKIFLE
2- DN250092	MUHAMMAD HAZIQ BIN AHMAD ZULKAFLI
3- CN250404	MUHAMMAD ADAM FARHAN BIN MOHD TARMIZI
4- DN250027	MUHAMMAD SYAFIQ BIN JA'AFAR
5- CN250124	AMMARUL DANISH BIN ABU BAKAR

## Assigned Theme & Core OS Concepts
* **Theme:** Timing & Live Leaderboard (1-Hour Community Loop Run)
* **Core OS Concepts:** I/O Management, Hardware Interrupts, I/O Buffering, and Spooling
* **Problem & Solution:** During a 1-hour loop run, multiple runners cross the checkpoint simultaneously and scan their QR codes. Direct database writes during peak traffic can cause I/O bottlenecks and data loss. Our system treats the QR scanner as an I/O input device that triggers interrupts, stores incoming scan timestamps in a RAM-based Circular Buffer, and uses a background Spooler thread to process loop counts and update the Live Leaderboard asynchronously.

## Installation & Run Instructions
*(To be updated in Week 6 during Alpha release)*
