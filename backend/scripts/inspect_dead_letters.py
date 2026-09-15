"""Print bounded, redacted Redis dead-letter metadata for operators."""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

from app.services.queue_service import QueueService, queue_service


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stream", choices=("stripe", "vision"), required=True)
    parser.add_argument("--count", type=int, default=100)
    return parser.parse_args()


async def _run() -> None:
    args = _arguments()
    source_stream = QueueService.STRIPE_STREAM if args.stream == "stripe" else QueueService.VISION_STREAM
    try:
        messages = await queue_service.read_dead_letters(source_stream, args.count)
        records: list[dict[str, Any]] = []
        for message in messages:
            record = QueueService._deserialize(message.fields.get("message")) or {}
            records.append(
                {
                    "message_id": message.message_id,
                    "source_stream": record.get("source_stream"),
                    "source_message_id": record.get("source_message_id"),
                    "reason": record.get("reason"),
                    "fields": record.get("fields", {}),
                    "fields_redacted": record.get("fields_redacted", False),
                    "failed_at": record.get("failed_at"),
                }
            )
        print(json.dumps(records, ensure_ascii=False, separators=(",", ":")))
    finally:
        await queue_service.close()


if __name__ == "__main__":
    asyncio.run(_run())
