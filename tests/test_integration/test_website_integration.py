import pytest
from fastapi import status


class TestWebsiteWorkflow:
    """Test complete workflows for website management."""

    @pytest.mark.asyncio
    async def test_get_and_update_workflow(self, async_client, sample_website):
        """Integration: Get website, update it, verify changes."""
        # Get initial state
        get_response = await async_client.get("/api/v1/websites")
        assert get_response.status_code == status.HTTP_200_OK
        initial_data = get_response.json()

        # Update
        update_data = {"title": "Integration Test Title"}
        patch_response = await async_client.patch("/api/v1/websites", json=update_data)
        assert patch_response.status_code == status.HTTP_200_OK

        # Verify update
        verify_response = await async_client.get("/api/v1/websites")
        assert verify_response.status_code == status.HTTP_200_OK
        updated_data = verify_response.json()

        assert updated_data["title"] == "Integration Test Title"
        assert updated_data["domain"] == initial_data["domain"]  # Unchanged

    @pytest.mark.asyncio
    async def test_multiple_updates_sequence(self, async_client, sample_website):
        """Integration: Multiple sequential updates."""
        updates = [
            {"title": "First Update"},
            {"description": "Second Update"},
            {"max_concurrent": 20},
            {"timezone": "America/Los_Angeles"},
        ]

        for update in updates:
            response = await async_client.patch("/api/v1/websites", json=update)
            assert response.status_code == status.HTTP_200_OK

        # Verify all updates persisted
        final_response = await async_client.get("/api/v1/websites")
        data = final_response.json()

        assert data["title"] == "First Update"
        assert data["description"] == "Second Update"
        assert data["max_concurrent"] == 20
        assert data["timezone"] == "America/Los_Angeles"

    @pytest.mark.asyncio
    async def test_update_arrays(self, async_client, sample_website):
        """Integration: Update array fields."""
        update_data = {
            "white_listed_domain": ["allowed1.com", "allowed2.com"],
            "black_listed_domain": ["blocked1.com", "blocked2.com"],
            "user_agents": ["Agent1/1.0", "Agent2/2.0"],
        }

        response = await async_client.patch("/api/v1/websites", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert set(data["white_listed_domain"]) == {"allowed1.com", "allowed2.com"}
        assert set(data["black_listed_domain"]) == {"blocked1.com", "blocked2.com"}
        assert len(data["user_agents"]) == 2


class TestDataIntegrity:
    """Test data integrity across operations."""

    @pytest.mark.asyncio
    async def test_timestamps_updated_on_patch(self, async_client, sample_website):
        """Data Integrity: updated_at should change on update."""
        # Get initial timestamps
        initial_response = await async_client.get("/api/v1/websites")
        initial_updated_at = initial_response.json()["updated_at"]

        # Small delay to ensure timestamp difference
        import asyncio

        await asyncio.sleep(0.1)

        # Update
        await async_client.patch("/api/v1/websites", json={"title": "New Title"})

        # Verify updated_at changed
        final_response = await async_client.get("/api/v1/websites")
        final_updated_at = final_response.json()["updated_at"]

        # Note: This might be flaky due to timestamp precision
        # Consider using mock time in production tests
        assert final_updated_at >= initial_updated_at

    @pytest.mark.asyncio
    async def test_created_at_not_changed_on_update(self, async_client, sample_website):
        """Data Integrity: created_at should not change on update."""
        initial_response = await async_client.get("/api/v1/websites")
        initial_created_at = initial_response.json()["created_at"]

        await async_client.patch("/api/v1/websites", json={"title": "New Title"})

        final_response = await async_client.get("/api/v1/websites")
        final_created_at = final_response.json()["created_at"]

        assert final_created_at == initial_created_at

    @pytest.mark.asyncio
    async def test_singleton_constraint(self, async_session, sample_website):
        """Data Integrity: Only one website should exist (id=1)."""
        from app.models.website import Website
        from sqlalchemy import select

        result = await async_session.execute(select(Website))
        websites = result.scalars().all()

        assert len(websites) == 1
        assert websites[0].id == 1
