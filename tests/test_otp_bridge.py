import asyncio

import pytest

from app.monitor import otp_bridge


class FakePubSub:
    def __init__(self, messages: list[dict]):
        self.messages = messages
        self.subscribed: list[str] = []

    async def subscribe(self, channel: str) -> None:
        self.subscribed.append(channel)

    async def unsubscribe(self, channel: str) -> None:
        pass

    async def close(self) -> None:
        pass

    async def get_message(self, ignore_subscribe_messages: bool = True, timeout: float = 5.0):
        if not self.messages:
            await asyncio.sleep(timeout)
            return None
        return self.messages.pop(0)


class FakeRedis:
    def __init__(self, messages: list[dict]):
        self._messages = messages
        self.store: dict[str, str] = {}

    def pubsub(self) -> FakePubSub:
        return FakePubSub(self._messages)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value

    async def delete(self, key: str) -> int:
        return int(self.store.pop(key, None) is not None)

    async def get(self, key: str):
        return self.store.get(key)

    async def publish(self, channel: str, message: str) -> int:
        return 1


@pytest.mark.asyncio
async def test_wait_for_otp_returns_code() -> None:
    fake = FakeRedis([{"type": "message", "data": b"123456"}])
    code = await otp_bridge.wait_for_otp(fake, task_id=1, timeout=2.0)
    assert code == "123456"


@pytest.mark.asyncio
async def test_wait_for_otp_times_out() -> None:
    fake = FakeRedis([])
    code = await otp_bridge.wait_for_otp(fake, task_id=2, timeout=0.2)
    assert code is None


@pytest.mark.asyncio
async def test_open_close_request_keys() -> None:
    fake = FakeRedis([])
    await otp_bridge.open_otp_request(fake, task_id=7)
    assert fake.store["otp:request:7"] == "1"
    await otp_bridge.close_otp_request(fake, task_id=7)
    assert "otp:request:7" not in fake.store
