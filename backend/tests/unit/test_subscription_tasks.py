import asyncio

import pytest

from app.tasks import subscription_tasks


@pytest.mark.asyncio
async def test_stop_subscription_reconciliation_job_reraises_cancellation(monkeypatch):
    async def wait_for_shutdown() -> None:
        await asyncio.sleep(60)

    task = asyncio.create_task(wait_for_shutdown())
    monkeypatch.setattr(subscription_tasks, "_subscription_reconciliation_task", task)
    with pytest.raises(asyncio.CancelledError):
        await subscription_tasks.stop_subscription_reconciliation_job()
