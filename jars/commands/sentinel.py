import os
import asyncio
import logging
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from jars.config import Theme

# Setup in-memory logger for `snlg` to access
import io
log_stream = io.StringIO()
log_handler = logging.StreamHandler(log_stream)
log_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s', datefmt='%H:%M:%S'))

# Apply to the sentinel logger
sentinel_logger = logging.getLogger("sentinel")
sentinel_logger.setLevel(logging.INFO)
# Remove all old handlers and add our StreamHandler
if sentinel_logger.hasHandlers():
    sentinel_logger.handlers.clear()
sentinel_logger.addHandler(log_handler)

log_handler_ws = logging.StreamHandler(log_stream)
log_handler_ws.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s', datefmt='%H:%M:%S'))

# Note: We configure root logger to capture sentinel.ws and sentinel.broker 
# but specifically target their names so we don't spam other logs
for name in ["sentinel.ws", "sentinel.broker"]:
    l = logging.getLogger(name)
    l.setLevel(logging.INFO)
    if l.hasHandlers():
         l.handlers.clear()
    l.addHandler(log_handler_ws)


app = typer.Typer(
    name="sentinel",
    help="Sentinel market data listener commands",
    no_args_is_help=True,
)

console = Console()

SIGNAL_CHANNEL = os.getenv("SIGNAL_CHANNEL", "jars:signals")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Global state to track our background task
_sentinel_task: Optional[asyncio.Task] = None
_broker = None
_client = None


async def _run_sentinel_bg():
    """The background worker that runs the Sentinel logic."""
    global _broker, _client
    
    # Needs to be imported here so it doesn't fail if dependencies are missing during CLI startup
    try:
        from sentinel.broker import Broker
        from sentinel.bybit_ws import BybitWSClient
    except ImportError as e:
        sentinel_logger.error(f"Cannot start sentinel: missing dependency {e}")
        return

    _broker = Broker()
    _client = BybitWSClient(_broker)

    sentinel_logger.info("Sentinel native service starting...")
    
    try:
        await _broker.connect()
        await _client.run_forever()
    except asyncio.CancelledError:
        sentinel_logger.info("Sentinel background task cancelled.")
    except Exception as e:
        sentinel_logger.error(f"Sentinel crashed: {e}")
    finally:
        await _client.shutdown()
        await _broker.disconnect()
        sentinel_logger.info("Sentinel shutdown complete.")


@app.command(name="start")
def start():
    """
    Start the Sentinel as a background process inside the CLI.
    Shortcut: snst
    """
    global _sentinel_task
    console.print()
    
    if _sentinel_task and not _sentinel_task.done():
        console.print(f"[{Theme.MUTED}]Sentinel is already running in the background.[/]")
        return
        
    try:
        import websockets
        import orjson
    except ImportError:
        console.print(f"[{Theme.ERROR}]✗[/] Missing dependencies. Run: pip install websockets orjson")
        raise typer.Exit(1)

    console.print(Panel(
        f"[{Theme.PRIMARY}]🛰️  Starting In-Process Sentinel[/]",
        border_style=Theme.BORDER
    ))

    # Clear previous logs
    log_stream.seek(0)
    log_stream.truncate(0)

    # Launch it natively as an asyncio background task
    loop = asyncio.get_event_loop()
    _sentinel_task = loop.create_task(_run_sentinel_bg())

    console.print(f"[{Theme.ONLINE}]✓[/] Sentinel has been launched in the background!")
    console.print(f"  Publishing to: [bold]{SIGNAL_CHANNEL}[/] channel")
    console.print()
    console.print(f"[{Theme.MUTED}]Type 'snlg' to see its logs, or 'snmo' to monitor signals.[/]")
    console.print()


@app.command(name="status")
def status():
    """
    Check Sentinel connection status.
    Shortcut: snss
    """
    console.print()

    table = Table(
        title="Sentinel Status",
        title_style=Theme.HEADER,
        border_style=Theme.BORDER,
    )
    table.add_column("Component", style=Theme.PRIMARY)
    table.add_column("Status")
    table.add_column("Details")

    # --- Container / Task Check ---
    global _sentinel_task
    if _sentinel_task and not _sentinel_task.done():
        table.add_row(
            "Native Process",
            f"[{Theme.ONLINE}]● Running[/]",
            "Active in background",
        )
    else:
        table.add_row(
            "Native Process",
            f"[{Theme.OFFLINE}]● Stopped[/]",
            "Not active",
        )

    # --- Redis ---
    try:
        import redis
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        r.ping()
        subs = r.pubsub_numsub(SIGNAL_CHANNEL)
        sub_count = subs[0][1] if subs else 0

        table.add_row(
            "Redis Broker",
            f"[{Theme.ONLINE}]● Connected[/]",
            f"{sub_count} subscriber(s) on {SIGNAL_CHANNEL}",
        )
    except Exception as e:
        table.add_row(
            "Redis Broker",
            f"[{Theme.OFFLINE}]● Disconnected[/]",
            str(e)[:60],
        )

    # --- Config ---
    bybit_ws = os.getenv("BYBIT_WS_URL", "wss://stream.bybit.com/v5/private")
    bybit_key = os.getenv("BYBIT_API_KEY", "")

    table.add_row(
        "WebSocket URL",
        f"[{Theme.MUTED}]◦ Config[/]",
        bybit_ws[:60] + "..." if len(bybit_ws) > 60 else bybit_ws,
    )
    table.add_row(
        "API Key",
        f"[{Theme.MUTED}]◦ Config[/]",
        "********" + bybit_key[-4:] if bybit_key else "[yellow]Not configured[/]",
    )

    console.print(table)
    console.print()


@app.command(name="stop")
def stop():
    """
    Stop the in-process Sentinel.
    Shortcut: snsp
    """
    global _sentinel_task
    console.print()
    
    if not _sentinel_task or _sentinel_task.done():
        console.print(f"[{Theme.MUTED}]Native Sentinel is not running.[/]")
        return
        
    with console.status(f"[{Theme.MUTED}]Stopping Native Sentinel...[/]"):
        _sentinel_task.cancel()
        
    console.print(f"[{Theme.ONLINE}]✓[/] Native Sentinel stopped gracefully")
    console.print()


@app.command(name="logs")
def logs(
    tail: int = typer.Option(20, "--tail", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f"),  # Ignored for in-process, kept for compat
):
    """
    View logs from the in-process Sentinel.
    Shortcut: snlg
    """
    console.print()
    
    logs_output = log_stream.getvalue()
    if not logs_output.strip():
        console.print(f"[{Theme.MUTED}]No logs available. Is the sentinel started? (snst)[/]")
        return
        
    lines = [line for line in logs_output.split("\n") if line.strip()]
    lines_to_show = lines[-tail:] if tail > 0 else lines
    
    console.print(Panel(
        "\n".join(lines_to_show),
        title="[bold]Native Sentinel Logs[/]",
        border_style=Theme.BORDER,
    ))
    console.print()


@app.command(name="monitor")
def monitor(
    redis_host: str = typer.Option(REDIS_HOST, "--redis-host", "-r", help="Redis host"),
    redis_port: int = typer.Option(REDIS_PORT, "--redis-port", "-p", help="Redis port"),
):
    """
    Live-stream signals from the jars:signals channel.
    Shortcut: snmo
    """
    console.print()
    console.print(Panel(
        f"[{Theme.PRIMARY}]📡 Signal Monitor[/]\n"
        f"[{Theme.MUTED}]Listening on redis://{redis_host}:{redis_port}/{SIGNAL_CHANNEL}[/]",
        border_style=Theme.BORDER,
    ))
    console.print()

    try:
        import redis
        import json
    except ImportError:
        console.print(f"[{Theme.ERROR}]✗[/] redis package not installed")
        raise typer.Exit(1)

    try:
        r = redis.Redis(host=redis_host, port=redis_port)
        r.ping()
        console.print(f"[{Theme.ONLINE}]✓[/] Connected to Redis. Waiting for signals...")
        console.print(f"[{Theme.MUTED}]Press Ctrl+C to stop[/]")
        console.print()

        pubsub = r.pubsub()
        pubsub.subscribe(SIGNAL_CHANNEL)

        for message in pubsub.listen():
            if message["type"] != "message":
                continue

            try:
                data = json.loads(message["data"])
                symbol = data.get("symbol", "???")
                side = data.get("side", "?")
                qty = data.get("qty", 0)
                price = data.get("price", 0)

                side_style = Theme.ONLINE if side == "Buy" else Theme.ERROR
                console.print(
                    f"[{Theme.MUTED}]SIGNAL[/] "
                    f"[{Theme.PRIMARY}]{symbol}[/] "
                    f"[{side_style}]{side}[/] "
                    f"[bold]{qty}[/] @ [bold]{price}[/]"
                )
            except (json.JSONDecodeError, KeyError):
                console.print(f"[{Theme.MUTED}]RAW: {message['data']}[/]")

    except redis.ConnectionError:
        console.print(f"[{Theme.ERROR}]✗[/] Cannot connect to Redis at {redis_host}:{redis_port}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print(f"\n[{Theme.MUTED}]Monitor stopped[/]")

    console.print()
