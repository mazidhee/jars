"""
===========================================================
JARS CLI - Sentinel Commands
===========================================================
Commands to control the C++ Sentinel WebSocket listener.

Available commands:
- sentinel start (st) - Start the Sentinel
- sentinel status (ss) - Check Sentinel status
- sentinel stop (sp) - Stop the Sentinel
- sentinel bridge (sb) - Start the Python bridge

The Sentinel connects to Bybit and publishes trade data to Redis.
Python services can subscribe to receive real-time signals.
"""

import os
import subprocess
import signal
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import the config for styling
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from jars.config import Theme

# Create the Typer app for sentinel commands
app = typer.Typer(
    name="sentinel",
    help="Sentinel market data listener commands",
    no_args_is_help=True,
)

console = Console()

# Path to the sentinel directory
SENTINEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sentinel")
BRIDGE_MODULE = "sentinel.bridge.redis_listener"


@app.command(name="start")
def start(
    symbol: str = typer.Option("BTCUSDT", "--symbol", "-s", help="Trading symbol to subscribe"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging"),
):
    """
    Start the Sentinel WebSocket listener.
    
    Shortcut: st
    
    This starts the C++ Sentinel which connects to Bybit Testnet
    and publishes trade data to Redis.
    """
    console.print()
    console.print(Panel(
        f"[{Theme.PRIMARY}]🛰️  Starting Sentinel[/]",
        border_style=Theme.BORDER
    ))
    
    # Check if Docker is running
    try:
        subprocess.run(
            ["docker", "info"],
            capture_output=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print(f"[{Theme.ERROR}]✗[/] Docker is not running. Please start Docker first.")
        raise typer.Exit(1)
    
    # Build and run the sentinel container
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Step 1: Ensure Redis is running
            progress.add_task("Starting Redis...", total=None)
            subprocess.run(
                ["docker-compose", "up", "-d", "redis"],
                cwd=os.path.dirname(SENTINEL_DIR),
                capture_output=True,
                check=True
            )
            
            # Step 2: Build the sentinel image
            task = progress.add_task("Building Sentinel image (this may take a few minutes)...", total=None)
            result = subprocess.run(
                ["docker", "build", "-t", "jars-sentinel", "."],
                cwd=SENTINEL_DIR,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                console.print(f"[{Theme.ERROR}]✗[/] Build failed:")
                console.print(result.stderr)
                raise typer.Exit(1)
            
            progress.remove_task(task)
            
            # Step 3: Run the sentinel
            progress.add_task("Starting Sentinel...", total=None)
            
            env_vars = {
                "REDIS_HOST": "host.docker.internal",  # Docker-to-host networking
                "BYBIT_WS_URL": os.getenv("BYBIT_WS_URL", "wss://stream-testnet.bybit.com/v5/public/linear"),
                "LOG_LEVEL": "debug" if debug else "info"
            }
            
            env_args = [f"-e={k}={v}" for k, v in env_vars.items()]
            
            # Run in background
            subprocess.Popen(
                ["docker", "run", "-d", "--name", "jars-sentinel", "--network", "host"] + env_args + ["jars-sentinel"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        console.print(f"[{Theme.ONLINE}]✓[/] Sentinel started successfully!")
        console.print(f"  Subscribing to: [bold]{symbol}[/]")
        console.print(f"  Publishing to: [bold]market_signals[/] channel")
        console.print()
        console.print(f"[{Theme.MUTED}]Run 'jars sentinel status' to check the connection[/]")
        
    except subprocess.CalledProcessError as e:
        console.print(f"[{Theme.ERROR}]✗[/] Failed to start Sentinel: {e}")
        raise typer.Exit(1)
    
    console.print()


# Shortcut aliases
st = start


@app.command(name="status")
def status():
    """
    Check Sentinel connection status.
    
    Shortcut: ss
    
    Shows whether the Sentinel is running, connected to Bybit,
    and publishing to Redis.
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
    
    # Check Docker container
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=jars-sentinel", "--format", "{{.Status}}"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            table.add_row(
                "Sentinel Container",
                f"[{Theme.ONLINE}]● Running[/]",
                result.stdout.strip()
            )
        else:
            table.add_row(
                "Sentinel Container",
                f"[{Theme.OFFLINE}]● Stopped[/]",
                "Not running"
            )
    except FileNotFoundError:
        table.add_row(
            "Sentinel Container",
            f"[{Theme.ERROR}]● Error[/]",
            "Docker not found"
        )
    
    # Check Redis
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379)
        r.ping()
        
        # Check subscribers on market_signals channel
        pubsub_channels = r.pubsub_numsub("market_signals")
        subscriber_count = pubsub_channels[0][1] if pubsub_channels else 0
        
        table.add_row(
            "Redis",
            f"[{Theme.ONLINE}]● Connected[/]",
            f"{subscriber_count} subscriber(s)"
        )
    except Exception as e:
        table.add_row(
            "Redis",
            f"[{Theme.OFFLINE}]● Disconnected[/]",
            str(e)
        )
    
    # Check environment variables
    bybit_ws = os.getenv("BYBIT_WS_URL", "Not set")
    bybit_key = os.getenv("BYBIT_API_KEY", "Not set")
    
    table.add_row(
        "BYBIT_WS_URL",
        f"[{Theme.MUTED}]◦ Config[/]",
        bybit_ws[:60] + "..." if len(bybit_ws) > 60 else bybit_ws
    )
    table.add_row(
        "BYBIT_API_KEY",
        f"[{Theme.MUTED}]◦ Config[/]",
        "********" if bybit_key != "Not set" else "[yellow]Not configured[/]"
    )
    
    console.print(table)
    console.print()


# Shortcut aliases
ss = status


@app.command(name="stop")
def stop():
    """
    Stop the Sentinel.
    
    Shortcut: sp
    
    Gracefully stops the Sentinel container.
    """
    console.print()
    
    try:
        with console.status(f"[{Theme.MUTED}]Stopping Sentinel...[/]"):
            # Stop the container
            subprocess.run(
                ["docker", "stop", "jars-sentinel"],
                capture_output=True,
                check=True
            )
            # Remove the container
            subprocess.run(
                ["docker", "rm", "jars-sentinel"],
                capture_output=True,
                check=True
            )
        
        console.print(f"[{Theme.ONLINE}]✓[/] Sentinel stopped")
        
    except subprocess.CalledProcessError:
        console.print(f"[{Theme.MUTED}]Sentinel is not running[/]")
    except FileNotFoundError:
        console.print(f"[{Theme.ERROR}]✗[/] Docker not found")
        raise typer.Exit(1)
    
    console.print()


# Shortcut aliases
sp = stop


@app.command(name="bridge")
def bridge(
    redis_host: str = typer.Option("localhost", "--redis-host", "-r", help="Redis host"),
    redis_port: int = typer.Option(6379, "--redis-port", "-p", help="Redis port"),
):
    """
    Start the Python bridge (Redis listener).
    
    Shortcut: sb
    
    Listens for market signals from Redis and displays them.
    This is useful for verifying the Sentinel is publishing data.
    """
    console.print()
    console.print(Panel(
        f"[{Theme.PRIMARY}]🌉 Starting Python Bridge[/]\n"
        f"[{Theme.MUTED}]Listening on redis://{redis_host}:{redis_port}/market_signals[/]",
        border_style=Theme.BORDER
    ))
    console.print()
    
    # Import and run the bridge
    try:
        # Add sentinel to path
        sentinel_path = os.path.dirname(SENTINEL_DIR)
        if sentinel_path not in sys.path:
            sys.path.insert(0, sentinel_path)
        
        from sentinel.bridge.redis_listener import RedisListener, MarketSignal
        
        listener = RedisListener(host=redis_host, port=redis_port)
        
        if listener.connect():
            def on_signal(signal: MarketSignal):
                side_style = Theme.ONLINE if signal.side == 'B' else Theme.ERROR
                console.print(
                    f"[{Theme.MUTED}]{signal.timestamp_datetime.strftime('%H:%M:%S.%f')[:-3]}[/] "
                    f"[{Theme.PRIMARY}]{signal.symbol}[/] "
                    f"[{side_style}]{signal.side_name}[/] @ "
                    f"[bold]{signal.price:.2f}[/]"
                )
            
            console.print(f"[{Theme.ONLINE}]✓[/] Connected! Waiting for signals...")
            console.print(f"[{Theme.MUTED}]Press Ctrl+C to stop[/]")
            console.print()
            
            listener.run(callback=on_signal)
        else:
            console.print(f"[{Theme.ERROR}]✗[/] Failed to connect to Redis")
            raise typer.Exit(1)
            
    except ImportError as e:
        console.print(f"[{Theme.ERROR}]✗[/] Failed to import bridge: {e}")
        console.print(f"[{Theme.MUTED}]Install dependencies: pip install -r sentinel/bridge/requirements.txt[/]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print(f"\n[{Theme.MUTED}]Bridge stopped[/]")


# Shortcut aliases
sb = bridge


@app.command(name="logs")
def logs(
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    tail: int = typer.Option(50, "--tail", "-n", help="Number of lines to show"),
):
    """
    View Sentinel container logs.
    
    Shortcut: sl
    
    Shows logs from the Sentinel container.
    """
    console.print()
    
    try:
        cmd = ["docker", "logs", "jars-sentinel", "--tail", str(tail)]
        if follow:
            cmd.append("-f")
        
        subprocess.run(cmd)
        
    except FileNotFoundError:
        console.print(f"[{Theme.ERROR}]✗[/] Docker not found")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        pass
    
    console.print()


# Shortcut aliases
sl = logs
