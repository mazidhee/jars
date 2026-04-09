# JARS: High-Throughput Market Data Ingestion Pipeline

> A robust, fault-tolerant infrastructure built to ingest high-frequency crypto market data stream (Bybit) and execute copy-trades with O(1) idempotency guarantees and zero-dropped-packet semantics.

## Pristine Data for Research

Quantitative researchers and econometricians need massive amounts of high-frequency market data to build accurate models (like predicting price movements based on order book imbalance). Standard REST APIs and web scrapers are too slow, and network connections drop. If a database records the same trade twice (a duplicate), the quant's mathematical model is ruined. 

Furthermore, when triggering automated secondary executions (Copy Trading), the system must fan out a single signal to hundreds of subscriber accounts simultaneously without blocking the ingestion cycle or double-spending subscriber funds due to concurrent signal glitches.

**JARS** models a solution. It is a fault-tolerant, event-driven data ingestion pipeline. It connects directly to exchange WebSockets, strips out the noise, mathematically guarantees no duplicates, and streams the data into a distributed time-series warehouse. It also processes parallel proportional trade sizing for followers utilizing a robust distributed locking mechanism.

---

![Bybit Exchange WebSocket-2026-04-09-121325.png](interface/src/app/Bybit%20Exchange%20WebSocket-2026-04-09-121325.png)

---

## Core Architecture 
The architecture decouples the high frequency ingestion layer from the storage worker using Apache Kafka. If the relational database struggles under peak market volatility the ingestion listener continues operating without blocking. Kafka acts as an immutable shock absorber that buffers incoming trades until the storage worker returns online. This specific design guarantees zero dropped packets and prevents out of memory failures during WebSocket disconnects.

Network partitions and WebSocket reconnections inevitably cause duplicate frames. Executing a trade takes roughly 10 to 20 milliseconds and a duplicate signal arriving during this execution window could easily trigger a double spend across hundreds of subscribers. To prevent this I implemented an idempotency lock using a Redis distributed mutex. Establishing a subscriber specific lock in constant time before executing the math guarantees exactly once processing semantics. This ensures the database is never corrupted with duplicate trades under heavy load.

For data storage standard PostgreSQL B Tree indexes degrade exponentially when querying millions of rows of time series data. I utilized TimescaleDB to partition the data into hypertables chunked by one day intervals. This architecture heavily optimizes the query planners for time based aggregations and ensures sequential disk IO. This allows the system to scale effortlessly to millions of rows while keeping the serving layer highly responsive.

Finally the execution engine completely avoids standard floating point mathematics. Standard floats introduce truncation artifacts that compound over thousands of trades leading to real financial discrepancies. The engine exclusively uses precise decimal arithmetic with strict predefined quantization and round down rules for all position sizing routines to guarantee absolute financial precision.

---


## Quick Start (Local Reproduction)

To spin up the entire cluster (Kafka, Sentinel, Worker, Redis, TimescaleDB, Web Service) on your local machine:

1. **Spin up the Docker Compose stack:**
   ```bash
   docker compose up -d
   ```

2. **Verify Container Health:**
   ```bash
   docker compose ps
   ```
   *(Ensure `jars_kafka`, `jars-redis-1`, `jars-db-1`, `jars-worker-1`, `jars-web-1`, and `jars-sentinel-1` are all listed as `Healthy` or `Up`).*

3. **Run the End-to-End Execution Pipeline Test:**
   ```bash
   docker compose exec web python scripts/test_pipeline.py
   ```
   This script bypasses the Sentinel (to simulate a trade trigger) and pushes a direct Event payload to Kafka. You can then watch the Worker successfully pull it, attempt to process it through the Copy-Trading engine, lock it via Redis, and save the execution result to the Postgres DB.

## Command Line Interface (CLI)
You can install the Python CLI to manage JARS locally:

```bash
# Ensure you have Poetry installed, or use standard pip
# From the root directory:
pip install -e .
# Or stringently isolated via pipx:
pipx install .

# Launch the REPL
jars
```
