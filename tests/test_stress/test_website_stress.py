import pytest
import asyncio
from fastapi import status


class TestStress:
    """Stress testing for the website API."""

    @pytest.mark.asyncio
    async def test_concurrent_reads(self, async_client, sample_website):
        """Stress: Handle many concurrent read requests."""

        async def make_request():
            response = await async_client.get("/api/v1/websites")
            return response.status_code

        # Execute 50 concurrent reads
        tasks = [make_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)

        assert all(status == 200 for status in results)

    @pytest.mark.asyncio
    async def test_concurrent_updates(self, async_client, sample_website):
        """Stress: Handle concurrent update requests."""

        async def make_update(i):
            response = await async_client.patch(
                "/api/v1/websites", json={"title": f"Concurrent Update {i}"}
            )
            return response.status_code

        # Execute 20 concurrent updates
        tasks = [make_update(i) for i in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed (last one wins)
        successful = [r for r in results if isinstance(r, int) and r == 200]
        assert len(successful) >= 15  # Allow some failures under high load

    @pytest.mark.asyncio
    async def test_mixed_concurrent_operations(self, async_client, sample_website):
        """Stress: Handle mixed read/write operations."""

        async def read_op():
            return await async_client.get("/api/v1/websites")

        async def write_op(i):
            return await async_client.patch(
                "/api/v1/websites", json={"title": f"Mixed Op {i}"}
            )

        # Mix of reads and writes
        tasks = []
        for i in range(30):
            if i % 3 == 0:
                tasks.append(write_op(i))
            else:
                tasks.append(read_op())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful operations
        successful = [
            r for r in results if hasattr(r, "status_code") and r.status_code == 200
        ]
        assert len(successful) >= 25

    @pytest.mark.asyncio
    async def test_rapid_sequential_updates(self, async_client, sample_website):
        """Stress: Rapid sequential updates."""
        for i in range(50):
            response = await async_client.patch(
                "/api/v1/websites", json={"title": f"Rapid Update {i}"}
            )
            assert response.status_code == status.HTTP_200_OK

        # Verify final state
        final_response = await async_client.get("/api/v1/websites")
        assert final_response.json()["title"] == "Rapid Update 49"

    @pytest.mark.asyncio
    async def test_large_array_updates(self, async_client, sample_website):
        """Stress: Update with large arrays."""
        large_domains = [f"domain{i}.com" for i in range(50)]
        large_patterns = [f"^/path{i}/.*" for i in range(50)]
        large_agents = [f"Agent{i}/1.0 (Compatible)" for i in range(50)]

        response = await async_client.patch(
            "/api/v1/websites",
            json={
                "white_listed_domain": large_domains[:25],
                "black_listed_domain": large_domains[25:],
                "white_listed_path_patterns": large_patterns[:25],
                "black_listed_path_patterns": large_patterns[25:],
                "user_agents": large_agents,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["white_listed_domain"]) == 25
        assert len(data["user_agents"]) == 50


class TestConcurrency:
    """Test concurrency handling."""

    @pytest.mark.asyncio
    async def test_optimistic_locking_scenario(self, async_client, sample_website):
        """Concurrency: Simulate optimistic locking scenario."""
        # Get initial version
        await async_client.get("/api/v1/websites")
        # initial_updated_at = initial.json()["updated_at"]

        # Simulate two concurrent updates
        async def update_a():
            await asyncio.sleep(0.01)
            return await async_client.patch(
                "/api/v1/websites", json={"title": "Update A"}
            )

        async def update_b():
            return await async_client.patch(
                "/api/v1/websites", json={"title": "Update B"}
            )

        results = await asyncio.gather(update_a(), update_b())

        # Both should succeed (last write wins without optimistic locking)
        assert all(r.status_code == 200 for r in results)

    @pytest.mark.asyncio
    async def test_read_during_write(self, async_client, sample_website):
        """Concurrency: Read during write operation."""

        async def write_op():
            await asyncio.sleep(0.01)
            return await async_client.patch(
                "/api/v1/websites", json={"title": "Written During Read"}
            )

        async def read_op():
            return await async_client.get("/api/v1/websites")

        # Start write, then read immediately
        write_task = asyncio.create_task(write_op())
        read_task = asyncio.create_task(read_op())

        results = await asyncio.gather(write_task, read_task)

        # Both operations should complete successfully
        assert results[0].status_code == 200  # Write
        assert results[1].status_code == 200  # Read
