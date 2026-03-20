# JARS Sentinel - Setup & Operations Guide

The Sentinel is a high-performance C++ WebSocket client that connects to Bybit 
and streams real-time trade data to your Python services via Redis.

## Architecture

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  Bybit Testnet  │──────▶│  C++ Sentinel   │──────▶│     Redis       │
│  WSS Stream     │       │  (simdjson)     │       │  (pub/sub)      │
└─────────────────┘       └─────────────────┘       └───────┬─────────┘
                                                           │
                                                           ▼
                                                   ┌─────────────────┐
                                                   │  Python Bridge  │
                                                   │  (struct unpack)│
                                                   └─────────────────┘
```

## Quick Start

### 1. Configure Bybit API Keys

Generate **Read-Only** API keys from [Bybit Testnet](https://testnet.bybit.com/):

1. Log in to Bybit Testnet
2. Go to **API Management**
3. Create new API key with **Read-Only** permissions
4. Add to your `.env` file:

```env
BYBIT_API_KEY=your_key_here
BYBIT_API_SECRET=your_secret_here
BYBIT_WS_URL=wss://stream-testnet.bybit.com/v5/public/linear
```

### 2. Start with Docker Compose

```bash
# Start Redis and Sentinel
docker-compose up -d redis sentinel

# Check logs
docker-compose logs -f sentinel
```

### 3. Verify with Python Bridge

```bash
# Install bridge dependencies
pip install -r sentinel/bridge/requirements.txt

# Run the bridge to see signals
python -m sentinel.bridge.redis_listener
```

## CLI Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| `jars sentinel start` | `snst` | Start the Sentinel container |
| `jars sentinel status` | `snss` | Check connection status |
| `jars sentinel stop` | `snsp` | Stop the Sentinel |
| `jars sentinel bridge` | `snbr` | Start Python listener |
| `jars sentinel logs` | `snlg` | View container logs |

## Building Locally (CLion)

### Prerequisites

1. **CLion** with C++ toolchain
2. **vcpkg** installed
3. **Docker Desktop** for Redis

### Setup vcpkg

```bash
# Clone vcpkg
git clone https://github.com/microsoft/vcpkg.git
cd vcpkg

# Bootstrap (Windows)
./bootstrap-vcpkg.bat

# Install dependencies
./vcpkg install boost-beast boost-asio simdjson hiredis spdlog fmt --triplet=x64-windows
```

### Configure CLion

1. Open `sentinel` folder in CLion
2. Go to **File > Settings > Build > CMake**
3. Add CMake option:
   ```
   -DCMAKE_TOOLCHAIN_FILE=C:/path/to/vcpkg/scripts/buildsystems/vcpkg.cmake
   ```
4. Reload CMake project

### Run

```bash
# Start Redis
docker-compose up -d redis

# Set environment variables
set REDIS_HOST=localhost
set BYBIT_WS_URL=wss://stream-testnet.bybit.com/v5/public/linear

# Run from CLion or command line
./build/sentinel
```

## Binary Protocol

The Sentinel sends 33-byte binary signals:

| Field | Type | Size | Description |
|-------|------|------|-------------|
| symbol | char[16] | 16 | Trading pair (e.g., "BTCUSDT") |
| price | double | 8 | Execution price |
| side | char | 1 | 'B' = Buy, 'S' = Sell |
| timestamp | uint64 | 8 | Microseconds since epoch |

Python unpacking:
```python
import struct
symbol, price, side, timestamp = struct.unpack('<16sdcQ', data)
```

## Testing

### 1. Build Verification
```bash
cd sentinel
docker build -t jars-sentinel .
```

### 2. Redis Connection Test
```bash
# Start Redis
docker-compose up -d redis

# Connect and subscribe
redis-cli SUBSCRIBE market_signals
```

### 3. Signal Flow Test
```bash
# Terminal 1: Start Sentinel
docker-compose up sentinel

# Terminal 2: Monitor signals
python -m sentinel.bridge.redis_listener
```

You should see trade data flowing within seconds during market hours.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Redis connection failed" | Ensure Redis is running: `docker-compose up -d redis` |
| "SSL handshake failed" | Check your firewall allows outbound 443 |
| "No signals received" | Bybit may be in maintenance; check status page |
| Build fails on Windows | Ensure vcpkg triplet is `x64-windows` |

## Code Archaeology Checklist

Use this while reviewing the C++ code:

- [ ] Trace the `std::shared_ptr<WebSocketClient>` lifecycle
- [ ] Find where the `std::strand` prevents race conditions  
- [ ] Locate the reconnection backoff logic
- [ ] Identify the zero-copy simdjson parsing
- [ ] Understand why we use `std::atomic` flags
