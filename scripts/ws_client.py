"""
WebSocket test client for the metrics streaming endpoint.

Usage:
    python scripts/ws_client.py                  # default 5s interval
    python scripts/ws_client.py --interval 10    # 10s interval
    python scripts/ws_client.py --url ws://localhost:8000/ws/metrics

Requires: websockets (pip install websockets)
"""

import asyncio
import json
import argparse
from datetime import datetime

try:
    import websockets
except ImportError:
    print("Install websockets first:  pip install websockets")
    raise SystemExit(1)


async def stream(url: str):
    print(f"Connecting to {url} ...\n")

    async with websockets.connect(url) as ws:
        async for raw in ws:
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "connected":
                print(f"[connected]  {msg['message']}\n")

            elif msg_type == "metrics_update":
                ts = msg.get("timestamp", "")
                print(
                    f"[{ts}]\n"
                    f"  cost:             ${msg['total_cost']:,.4f}\n"
                    f"  requests:         {msg['total_requests']:,}\n"
                    f"  unique users:     {msg['unique_users']}\n"
                    f"  today active:     {msg['today_active_users']}\n"
                    f"  anomalies:        {msg['anomalies_detected']}\n"
                )

            elif msg_type == "interval_changed":
                print(f"[interval]   changed to {msg['interval']}s\n")

            elif msg_type == "error":
                print(f"[error]      {msg['message']}\n")

            else:
                print(f"[unknown]    {raw}\n")


def main():
    parser = argparse.ArgumentParser(description="WebSocket metrics stream client")
    parser.add_argument("--url", default="ws://localhost:8000/ws/metrics")
    parser.add_argument("--interval", type=int, default=5)
    args = parser.parse_args()

    url = f"{args.url}?interval={args.interval}"

    try:
        asyncio.run(stream(url))
    except KeyboardInterrupt:
        print("\nDisconnected.")


if __name__ == "__main__":
    main()
