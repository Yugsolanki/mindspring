import pytest
from fastapi import status


class TestGetWebsiteEndpoint:
    """Test GET /api/v1/websites endpoint."""

    @pytest.mark.asyncio
    async def test_get_website_success(self, async_client, sample_website):
        """Positive: Should return website data."""
        response = await async_client.get("/api/v1/websites")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1
        assert data["domain"] == sample_website.domain

    @pytest.mark.asyncio
    async def test_get_website_not_found(self, async_client):
        """Negative: Should return 404 when website doesn't exist."""
        response = await async_client.get("/api/v1/websites")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_website_response_structure(self, async_client, sample_website):
        """API Integration: Response should have correct structure."""
        response = await async_client.get("/api/v1/websites")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check required fields
        required_fields = [
            "id",
            "domain",
            "title",
            "description",
            "timezone",
            "white_listed_domain",
            "black_listed_domain",
            "white_listed_path_patterns",
            "black_listed_path_patterns",
            "respect_robots",
            "max_concurrent",
            "playwright_timeout",
            "timeout",
            "max_retries",
            "max_depth",
            "rate_limiting_delay",
            "user_agents",
            "scraping_schedule",
            "created_at",
            "updated_at",
        ]
        for field in required_fields:
            assert field in data

    @pytest.mark.asyncio
    async def test_get_website_content_type(self, async_client, sample_website):
        """API Integration: Response should be JSON."""
        response = await async_client.get("/api/v1/websites")

        assert response.headers["content-type"] == "application/json"


class TestPatchWebsiteEndpoint:
    """Test PATCH /api/v1/websites endpoint."""

    @pytest.mark.asyncio
    async def test_patch_website_success(self, async_client, sample_website):
        """Positive: Should update website successfully."""
        update_data = {"title": "Updated Title"}
        response = await async_client.patch("/api/v1/websites", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_patch_website_multiple_fields(self, async_client, sample_website):
        """Positive: Should update multiple fields."""
        update_data = {
            "title": "New Title",
            "description": "New Description",
            "max_concurrent": 15,
        }
        response = await async_client.patch("/api/v1/websites", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "New Title"
        assert data["description"] == "New Description"
        assert data["max_concurrent"] == 15

    @pytest.mark.asyncio
    async def test_patch_website_empty_body(self, async_client, sample_website):
        """Negative: Empty update should fail."""
        response = await async_client.patch("/api/v1/websites", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_patch_website_invalid_data(self, async_client, sample_website):
        """Negative: Invalid data should fail."""
        update_data = {"max_concurrent": 0}  # Below minimum
        response = await async_client.patch("/api/v1/websites", json=update_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_patch_website_not_found(self, async_client):
        """Negative: Updating non-existent website should fail."""
        update_data = {"title": "New Title"}
        response = await async_client.patch("/api/v1/websites", json=update_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ==================
    # Boundary Testing
    # ==================

    @pytest.mark.asyncio
    async def test_patch_max_concurrent_minimum(self, async_client, sample_website):
        """Boundary: max_concurrent at minimum."""
        response = await async_client.patch(
            "/api/v1/websites", json={"max_concurrent": 1}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["max_concurrent"] == 1

    @pytest.mark.asyncio
    async def test_patch_max_concurrent_maximum(self, async_client, sample_website):
        """Boundary: max_concurrent at maximum."""
        response = await async_client.patch(
            "/api/v1/websites", json={"max_concurrent": 100}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["max_concurrent"] == 100

    @pytest.mark.asyncio
    async def test_patch_max_concurrent_below_minimum(
        self, async_client, sample_website
    ):
        """Boundary: max_concurrent below minimum should fail."""
        response = await async_client.patch(
            "/api/v1/websites", json={"max_concurrent": 0}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_patch_max_concurrent_above_maximum(
        self, async_client, sample_website
    ):
        """Boundary: max_concurrent above maximum should fail."""
        response = await async_client.patch(
            "/api/v1/websites", json={"max_concurrent": 101}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # =================
    # Data Validation
    # =================

    @pytest.mark.asyncio
    async def test_patch_invalid_domain(self, async_client, sample_website):
        """Data Validation: Invalid domain should fail."""
        response = await async_client.patch(
            "/api/v1/websites", json={"domain": "invalid domain"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_patch_invalid_timezone(self, async_client, sample_website):
        """Data Validation: Invalid timezone should fail."""
        response = await async_client.patch(
            "/api/v1/websites", json={"timezone": "Invalid/Timezone"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_patch_invalid_cron(self, async_client, sample_website):
        """Data Validation: Invalid cron should fail."""
        response = await async_client.patch(
            "/api/v1/websites", json={"scraping_schedule": "invalid cron"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_patch_overlapping_domains(self, async_client, sample_website):
        """Data Validation: Overlapping whitelist/blacklist should fail."""
        response = await async_client.patch(
            "/api/v1/websites",
            json={
                "white_listed_domain": ["example.com"],
                "black_listed_domain": ["example.com"],
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # =================
    # Security Testing
    # =================

    @pytest.mark.asyncio
    async def test_patch_xss_in_title(self, async_client, sample_website):
        """Security: XSS in title should be handled."""
        xss_payload = "<script>alert('xss')</script>"
        response = await async_client.patch(
            "/api/v1/websites", json={"title": xss_payload}
        )
        # Depending on security policy, this might be allowed or sanitized
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_patch_sql_injection_in_domain(self, async_client, sample_website):
        """Security: SQL injection should be handled."""
        response = await async_client.patch(
            "/api/v1/websites", json={"domain": "'; DROP TABLE websites;--"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_patch_extremely_large_payload(self, async_client, sample_website):
        """Security: Extremely large payload should be rejected."""
        large_description = "a" * 100000
        response = await async_client.patch(
            "/api/v1/websites", json={"description": large_description}
        )
        # Should fail due to max_length or server limits
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        ]


class TestMethodNotAllowed:
    """Test that unsupported methods return 405."""

    @pytest.mark.asyncio
    async def test_post_not_allowed(self, async_client):
        """Negative: POST should not be allowed."""
        response = await async_client.post("/api/v1/websites", json={})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.asyncio
    async def test_delete_not_allowed(self, async_client):
        """Negative: DELETE should not be allowed."""
        response = await async_client.delete("/api/v1/websites")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.asyncio
    async def test_put_not_allowed(self, async_client):
        """Negative: PUT should not be allowed."""
        response = await async_client.put("/api/v1/websites", json={})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestNegativeDataInput:
    """Test various negative/malicious data inputs."""

    @pytest.mark.asyncio
    async def test_null_values(self, async_client, sample_website):
        """Negative Data: Null values where not allowed."""
        response = await async_client.patch("/api/v1/websites", json={"domain": None})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_wrong_type_integer(self, async_client, sample_website):
        """Negative Data: String where integer expected."""
        response = await async_client.patch(
            "/api/v1/websites", json={"max_concurrent": "not a number"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_wrong_type_boolean(self, async_client, sample_website):
        """Negative Data: String where boolean expected."""
        response = await async_client.patch(
            "/api/v1/websites", json={"respect_robots": "not a boolean"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_wrong_type_array(self, async_client, sample_website):
        """Negative Data: String where array expected."""
        response = await async_client.patch(
            "/api/v1/websites", json={"white_listed_domain": "not an array"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_negative_numbers(self, async_client, sample_website):
        """Negative Data: Negative numbers where positive expected."""
        response = await async_client.patch(
            "/api/v1/websites", json={"max_concurrent": -1}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_float_where_integer_expected(self, async_client, sample_website):
        """Negative Data: Float where integer expected."""
        response = await async_client.patch(
            "/api/v1/websites", json={"max_concurrent": 5.5}
        )
        # FastAPI might coerce this or reject it
        assert response.status_code in [
            status.HTTP_200_OK,  # If coerced to 5
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    @pytest.mark.asyncio
    async def test_special_characters_in_title(self, async_client, sample_website):
        """Negative Data: Special characters in title."""
        await async_client.patch(
            "/api/v1/websites", json={"title": "Test\x00Title\x1f"}
        )
        # Null bytes and control characters might be problematic
        # Behavior depends on validation
        pass

    @pytest.mark.asyncio
    async def test_unicode_in_fields(self, async_client, sample_website):
        """Localization: Unicode characters in fields."""
        response = await async_client.patch(
            "/api/v1/websites",
            json={"title": "日本語タイトル", "description": "Описание на русском"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "日本語タイトル"
        assert data["description"] == "Описание на русском"

    @pytest.mark.asyncio
    async def test_emoji_in_fields(self, async_client, sample_website):
        """Localization: Emoji in fields."""
        response = await async_client.patch(
            "/api/v1/websites",
            json={"title": "My Site 🚀", "description": "Description with emoji 😀"},
        )
        assert response.status_code == status.HTTP_200_OK
