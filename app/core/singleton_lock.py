# singleton_lock.py
import redis
import time
import uuid
import threading
from app.core.config import settings


redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

# Lua scripts for atomic operations
ACQUIRE_SCRIPT = """
local lock_key = KEYS[1]
local heartbeat_key = KEYS[2]
local owner_id = ARGV[1]
local current_time = ARGV[2]

if redis.call('GET', lock_key) == false then
    redis.call('SET', lock_key, owner_id)
    redis.call('SET', heartbeat_key, current_time)
    return 1
end
return 0
"""

STEAL_IF_STALE_SCRIPT = """
local lock_key = KEYS[1]
local heartbeat_key = KEYS[2]
local new_owner_id = ARGV[1]
local current_time = tonumber(ARGV[2])
local stale_after = tonumber(ARGV[3])

local current_owner = redis.call('GET', lock_key)
if not current_owner then
    return 0  -- Lock gone, let caller retry acquire
end

local last_heartbeat = redis.call('GET', heartbeat_key)
local is_stale = false

if not last_heartbeat then
    is_stale = true
else
    is_stale = (current_time - tonumber(last_heartbeat)) > stale_after
end

if is_stale then
    redis.call('SET', lock_key, new_owner_id)
    redis.call('SET', heartbeat_key, current_time)
    return 1
end
return 0
"""

HEARTBEAT_SCRIPT = """
local lock_key = KEYS[1]
local heartbeat_key = KEYS[2]
local owner_id = ARGV[1]
local current_time = ARGV[2]

if redis.call('GET', lock_key) == owner_id then
    redis.call('SET', heartbeat_key, current_time)
    return 1
end
return 0
"""

RELEASE_SCRIPT = """
local lock_key = KEYS[1]
local heartbeat_key = KEYS[2]
local owner_id = ARGV[1]

if redis.call('GET', lock_key) == owner_id then
    redis.call('DEL', lock_key, heartbeat_key)
    return 1
end
return 0
"""


class SingletonLock:
    def __init__(self, name: str, heartbeat_interval: int = 10, stale_after: int = 60):
        if stale_after <= heartbeat_interval * 2:
            raise ValueError("stale_after should be at least 2x heartbeat_interval")

        self.name = name
        self.owner_id = str(uuid.uuid4())
        self.heartbeat_key = f"{name}:heartbeat"
        self.heartbeat_interval = heartbeat_interval
        self.stale_after = stale_after

        self._state_lock = threading.Lock()
        self._running = False

        # Register scripts for better performance (SHA caching)
        self._acquire = redis_client.register_script(ACQUIRE_SCRIPT)
        self._steal = redis_client.register_script(STEAL_IF_STALE_SCRIPT)
        self._heartbeat = redis_client.register_script(HEARTBEAT_SCRIPT)
        self._release = redis_client.register_script(RELEASE_SCRIPT)

    @property
    def is_running(self) -> bool:
        with self._state_lock:
            return self._running

    def acquire(self, max_steal_attempts: int = 3) -> bool:
        """Atomically acquire lock or steal if stale."""
        current_time = str(time.time())

        # Try direct acquisition
        acquired = self._acquire(
            keys=[self.name, self.heartbeat_key], args=[self.owner_id, current_time]
        )

        if acquired:
            with self._state_lock:
                self._running = True
            return True

        # Lock exists - attempt to steal if stale
        for _ in range(max_steal_attempts):
            current_time = str(time.time())
            stolen = self._steal(
                keys=[self.name, self.heartbeat_key],
                args=[self.owner_id, current_time, str(self.stale_after)],
            )

            if stolen:
                with self._state_lock:
                    self._running = True
                return True

            # Small delay before retry
            time.sleep(0.1)

        return False

    def heartbeat(self) -> bool:
        """Update heartbeat only if we still own the lock."""
        if not self.is_running:
            return False

        current_time = str(time.time())
        still_owner = self._heartbeat(
            keys=[self.name, self.heartbeat_key], args=[self.owner_id, current_time]
        )

        if not still_owner:
            with self._state_lock:
                self._running = False
            return False

        return True

    def release(self):
        """Release lock only if we own it."""
        try:
            self._release(keys=[self.name, self.heartbeat_key], args=[self.owner_id])
        finally:
            with self._state_lock:
                self._running = False
