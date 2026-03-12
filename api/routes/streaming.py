"""
WebSocket streaming endpoints.

Provides real-time metric updates over WebSocket connections.
Clients connect and receive a JSON push every N seconds containing
live aggregates queried directly from the database.

Usage:
    ws://localhost:8000/ws/metrics
    ws://localhost:8000/ws/metrics?interval=10

The client can also send a JSON message to change the interval at runtime:
    {"interval": 15}
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from analytics.metrics import MetricsEngine
from analytics.ml_models import AnomalyDetector

logger = logging.getLogger(__name__)

router = APIRouter(tags=["streaming"])


def _fetch_snapshot() -> dict:
    """
    Pull a live metrics snapshot from the database.

    Returns a flat dict suitable for JSON serialisation. Called inside
    the async loop via run_in_executor so it doesn't block the event loop.
    """
    metrics = MetricsEngine()

    totals = metrics.calculate_total_cost()
    row = totals.iloc[0] if not totals.empty else {}

    dau = metrics.calculate_daily_active_users(days=1)
    today_users = int(dau["daily_active_users"].iloc[-1]) if not dau.empty else 0

    detector = AnomalyDetector()
    detector.fit()
    anomalies = detector.predict()
    anomaly_count = int(anomalies["is_anomaly"].sum())

    return {
        "type": "metrics_update",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_cost": round(float(row.get("total_cost", 0)), 4),
        "total_requests": int(row.get("request_count", 0)),
        "unique_users": int(row.get("unique_users", 0)),
        "unique_sessions": int(row.get("unique_sessions", 0)),
        "today_active_users": today_users,
        "anomalies_detected": anomaly_count,
    }


@router.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket, interval: int = 5):
    """
    Stream live metric snapshots over WebSocket.

    Query params:
        interval: push frequency in seconds (default 5, min 2, max 60)

    The server pushes a JSON object on every tick:
        {
            "type": "metrics_update",
            "timestamp": "2026-03-12T19:00:00+00:00",
            "total_cost": 1234.56,
            "total_requests": 86500,
            "unique_users": 50,
            "unique_sessions": 3200,
            "today_active_users": 12,
            "anomalies_detected": 4
        }

    The client can send a JSON message at any time to adjust the interval:
        {"interval": 10}

    Test with wscat:
        wscat -c "ws://localhost:8000/ws/metrics?interval=5"

    Or with the included test client:
        python scripts/ws_client.py
    """
    interval = max(2, min(60, interval))
    await websocket.accept()
    logger.info(f"WebSocket client connected — interval={interval}s")

    await websocket.send_json({
        "type": "connected",
        "message": f"Streaming metrics every {interval}s. Send {{\"interval\": N}} to change.",
        "interval": interval,
    })

    loop = asyncio.get_event_loop()

    try:
        while True:
            # Run the blocking DB query in a thread pool
            snapshot = await loop.run_in_executor(None, _fetch_snapshot)
            await websocket.send_json(snapshot)
            logger.debug(f"Pushed snapshot: {snapshot['timestamp']}")

            # Sleep in small chunks so we can react to incoming client messages
            elapsed = 0
            chunk = 0.5
            while elapsed < interval:
                await asyncio.sleep(chunk)
                elapsed += chunk

                # Non-blocking check for client message
                try:
                    raw = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                    msg = json.loads(raw)
                    if "interval" in msg:
                        new_interval = max(2, min(60, int(msg["interval"])))
                        interval = new_interval
                        logger.info(f"Client changed interval to {interval}s")
                        await websocket.send_json({
                            "type": "interval_changed",
                            "interval": interval,
                        })
                        break  # restart the outer loop immediately
                except (asyncio.TimeoutError, Exception):
                    pass

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
