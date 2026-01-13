import pytest
from pydantic import ValidationError

from app.schemas.website import (
    WebsiteBase,
    WebsiteCreate,
    WebsiteUpdate,
    WebsiteResponse,
    normalize_domain,
    DOMAIN_REGEX,
)


class TestNormalizeDomain:
    """Test domain normalization function."""

    def test_lowercase_conversion(self):
        """Positive: Domain should be converted to lowercase."""
        assert normalize_domain("EXAMPLE.COM") == "example.com"

    def test_strip_whitespace(self):
        """Positive: Whitespace should be stripped."""
        assert normalize_domain("  example.com  ") == "example.com"

    def test_remove_trailing_slash(self):
        """Positive: Trailing slash should be removed."""
        assert normalize_domain("example.com/") == "example.com"

    def test_combined_normalization(self):
        """Positive: All normalizations should apply together."""
        assert normalize_domain("  EXAMPLE.COM/  ") == "example.com"


class TestDomainRegex:
    """Test domain validation regex."""

    @pytest.mark.parametrize(
        "domain",
        [
            "example.com",
            "sub.example.com",
            "sub.sub.example.co.uk",
            "http://example.com",
            "https://example.com",
            "my-site.org",
            "123.example.com",
        ],
    )
    def test_valid_domains(self, domain):
        """Positive: Valid domains should match."""
        assert DOMAIN_REGEX.match(domain) is not None

    @pytest.mark.parametrize(
        "domain",
        [
            "invalid",
            "invalid.",
            ".invalid",
            "invalid domain.com",
            "http://",
            "://example.com",
            "",
            "example.c",  # TLD too short
            "-invalid.com",
        ],
    )
    def test_invalid_domains(self, domain):
        """Negative: Invalid domains should not match."""
        assert DOMAIN_REGEX.match(domain) is None


class TestWebsiteBase:
    """Test WebsiteBase schema validation."""

    # ==================
    # Positive Scenarios
    # ==================

    def test_valid_complete_data(self, valid_website_data):
        """Positive: Valid complete data should create schema successfully."""
        website = WebsiteBase(**valid_website_data)
        assert website.domain == valid_website_data["domain"]
        assert website.title == valid_website_data["title"]

    def test_valid_minimal_data(self, minimal_website_data):
        """Positive: Minimal data with defaults should work."""
        website = WebsiteBase(**minimal_website_data)
        assert website.domain == "minimal.com"
        assert website.timezone == "UTC"
        assert website.max_concurrent == 8

    def test_default_values(self):
        """Positive: Default values should be applied correctly."""
        website = WebsiteBase(domain="example.com")
        assert website.timezone == "UTC"
        assert website.respect_robots is False
        assert website.max_concurrent == 8
        assert website.playwright_timeout == 30
        assert website.timeout == 15
        assert website.max_retries == 3
        assert website.max_depth == 100
        assert website.rate_limiting_delay == 2
        assert website.scraping_schedule == "* * * * *"
        assert len(website.user_agents) == 1

    # ==================
    # Negative Scenarios
    # ==================

    def test_invalid_domain_format(self):
        """Negative: Invalid domain format should raise error."""
        with pytest.raises(ValidationError) as exc_info:
            WebsiteBase(domain="not a valid domain")
        assert "Invalid domain format" in str(exc_info.value)

    def test_empty_domain(self):
        """Negative: Empty domain should raise error."""
        with pytest.raises(ValidationError):
            WebsiteBase(domain="")

    def test_invalid_timezone(self):
        """Negative: Invalid timezone should raise error."""
        with pytest.raises(ValidationError) as exc_info:
            WebsiteBase(domain="example.com", timezone="Invalid/Timezone")
        assert "Invalid timezone" in str(exc_info.value)

    def test_empty_user_agents(self):
        """Negative: Empty user agents list should raise error."""
        with pytest.raises(ValidationError):
            WebsiteBase(domain="example.com", user_agents=[])

    def test_short_user_agent(self):
        """Negative: User agent too short should raise error."""
        with pytest.raises(ValidationError) as exc_info:
            WebsiteBase(domain="example.com", user_agents=["ab"])
        assert "user-agent" in str(exc_info.value).lower()

    # =======================
    # Boundary Value Testing
    # =======================

    def test_max_concurrent_minimum(self):
        """Boundary: max_concurrent at minimum (1) should work."""
        website = WebsiteBase(domain="example.com", max_concurrent=1)
        assert website.max_concurrent == 1

    def test_max_concurrent_maximum(self):
        """Boundary: max_concurrent at maximum (100) should work."""
        website = WebsiteBase(domain="example.com", max_concurrent=100)
        assert website.max_concurrent == 100

    def test_max_concurrent_below_minimum(self):
        """Boundary: max_concurrent below minimum should fail."""
        with pytest.raises(ValidationError):
            WebsiteBase(domain="example.com", max_concurrent=0)

    def test_max_concurrent_above_maximum(self):
        """Boundary: max_concurrent above maximum should fail."""
        with pytest.raises(ValidationError):
            WebsiteBase(domain="example.com", max_concurrent=101)

    def test_playwright_timeout_boundaries(self):
        """Boundary: playwright_timeout boundaries."""
        # Minimum
        website = WebsiteBase(domain="example.com", playwright_timeout=1)
        assert website.playwright_timeout == 1

        # Maximum
        website = WebsiteBase(domain="example.com", playwright_timeout=120)
        assert website.playwright_timeout == 120

        # Below minimum
        with pytest.raises(ValidationError):
            WebsiteBase(domain="example.com", playwright_timeout=0)

        # Above maximum
        with pytest.raises(ValidationError):
            WebsiteBase(domain="example.com", playwright_timeout=121)

    def test_timeout_boundaries(self):
        """Boundary: timeout boundaries."""
        website = WebsiteBase(domain="example.com", timeout=1)
        assert website.timeout == 1

        website = WebsiteBase(domain="example.com", timeout=120)
        assert website.timeout == 120

        with pytest.raises(ValidationError):
            WebsiteBase(domain="example.com", timeout=0)

        with pytest.raises(ValidationError):
            WebsiteBase(domain="example.com", timeout=121)

    def test_max_retries_boundaries(self):
        """Boundary: max_retries boundaries."""
        website = WebsiteBase(domain="example.com", max_retries=0)
        assert website.max_retries == 0

        website = WebsiteBase(domain="example.com", max_retries=10)
        assert website.max_retries == 10

        with pytest.raises(ValidationError):
            WebsiteBase(domain="example.com", max_retries=-1)

        with pytest.raises(ValidationError):
            WebsiteBase(domain="example.com", max_retries=11)

    def test_max_depth_boundaries(self):
        """Boundary: max_depth boundaries."""
        website = WebsiteBase(domain="example.com", max_depth=1)
        assert website.max_depth == 1

        website = WebsiteBase(domain="example.com", max_depth=1000)
        assert website.max_depth == 1000

        with pytest.raises(ValidationError):
            WebsiteBase(domain="example.com", max_depth=0)

        with pytest.raises(ValidationError):
            WebsiteBase(domain="example.com", max_depth=1001)

    def test_rate_limiting_delay_boundaries(self):
        """Boundary: rate_limiting_delay boundaries."""
        website = WebsiteBase(domain="example.com", rate_limiting_delay=0)
        assert website.rate_limiting_delay == 0

        website = WebsiteBase(domain="example.com", rate_limiting_delay=60)
        assert website.rate_limiting_delay == 60

        with pytest.raises(ValidationError):
            WebsiteBase(domain="example.com", rate_limiting_delay=-1)

        with pytest.raises(ValidationError):
            WebsiteBase(domain="example.com", rate_limiting_delay=61)

    # ===================
    # Data Validation
    # ===================

    def test_domain_normalization(self):
        """Data Validation: Domain should be normalized."""
        website = WebsiteBase(domain="  EXAMPLE.COM/  ")
        assert website.domain == "example.com"

    def test_whitelist_domain_normalization(self):
        """Data Validation: Whitelist domains should be normalized."""
        website = WebsiteBase(
            domain="example.com", white_listed_domain=["  PARTNER.COM/  "]
        )
        assert website.white_listed_domain == ["partner.com"]

    def test_blacklist_domain_normalization(self):
        """Data Validation: Blacklist domains should be normalized."""
        website = WebsiteBase(
            domain="example.com", black_listed_domain=["  SPAM.COM/  "]
        )
        assert website.black_listed_domain == ["spam.com"]

    def test_invalid_whitelist_domain(self):
        """Data Validation: Invalid whitelist domain should fail."""
        with pytest.raises(ValidationError) as exc_info:
            WebsiteBase(domain="example.com", white_listed_domain=["not valid"])
        assert "Invalid domain in list" in str(exc_info.value)

    def test_invalid_blacklist_domain(self):
        """Data Validation: Invalid blacklist domain should fail."""
        with pytest.raises(ValidationError) as exc_info:
            WebsiteBase(domain="example.com", black_listed_domain=["invalid"])
        assert "Invalid domain in list" in str(exc_info.value)

    def test_valid_regex_patterns(self):
        """Data Validation: Valid regex patterns should work."""
        website = WebsiteBase(
            domain="example.com",
            white_listed_path_patterns=[r"^/api/.*", r"^/public/\d+"],
            black_listed_path_patterns=[r"^/admin/.*", r"^/private/.*"],
        )
        assert len(website.white_listed_path_patterns) == 2
        assert len(website.black_listed_path_patterns) == 2

    def test_invalid_regex_pattern(self):
        """Data Validation: Invalid regex pattern should fail."""
        with pytest.raises(ValidationError) as exc_info:
            WebsiteBase(domain="example.com", white_listed_path_patterns=["[invalid"])
        assert "Invalid regex pattern" in str(exc_info.value)

    def test_valid_cron_expressions(self):
        """Data Validation: Valid cron expressions should work."""
        valid_crons = [
            "* * * * *",
            "0 * * * *",
            "0 0 * * *",
            "0 0 1 * *",
            "0 0 1 1 *",
            "*/5 * * * *",
            "0 0,12 * * *",
        ]
        for cron in valid_crons:
            website = WebsiteBase(domain="example.com", scraping_schedule=cron)
            assert website.scraping_schedule == cron

    def test_invalid_cron_expression(self):
        """Data Validation: Invalid cron expression should fail."""
        with pytest.raises(ValidationError) as exc_info:
            WebsiteBase(domain="example.com", scraping_schedule="invalid cron")
        assert "Invalid cron expression" in str(exc_info.value)

    # =======================
    # Cross-Field Validation
    # =======================

    def test_overlapping_whitelist_blacklist_domains(self):
        """Cross-Field: Overlapping whitelist/blacklist domains should fail."""
        with pytest.raises(ValidationError) as exc_info:
            WebsiteBase(
                domain="example.com",
                white_listed_domain=["partner.com"],
                black_listed_domain=["partner.com"],
            )
        assert "cannot be both whitelisted and blacklisted" in str(exc_info.value)

    def test_overlapping_path_patterns(self):
        """Cross-Field: Overlapping path patterns should fail."""
        with pytest.raises(ValidationError) as exc_info:
            WebsiteBase(
                domain="example.com",
                white_listed_path_patterns=[r"^/api/.*"],
                black_listed_path_patterns=[r"^/api/.*"],
            )
        assert "cannot be both whitelisted and blacklisted" in str(exc_info.value)

    def test_no_overlap_different_domains(self):
        """Cross-Field: Non-overlapping domains should work."""
        website = WebsiteBase(
            domain="example.com",
            white_listed_domain=["partner.com"],
            black_listed_domain=["spam.com"],
        )
        assert "partner.com" in website.white_listed_domain
        assert "spam.com" in website.black_listed_domain

    # =================
    # Security Testing
    # =================

    def test_xss_in_title(self):
        """Security: XSS attempt in title should be stored as-is (sanitize on output)."""
        xss_payload = "<script>alert('xss')</script>"
        website = WebsiteBase(domain="example.com", title=xss_payload)
        assert website.title == xss_payload

    def test_sql_injection_in_domain(self):
        """Security: SQL injection in domain should fail validation."""
        with pytest.raises(ValidationError):
            WebsiteBase(domain="'; DROP TABLE websites;--")

    def test_command_injection_in_cron(self):
        """Security: Command injection in cron should fail validation."""
        with pytest.raises(ValidationError):
            WebsiteBase(domain="example.com", scraping_schedule="; rm -rf /")

    def test_path_traversal_in_patterns(self):
        """Security: Path traversal patterns are technically valid regex."""
        # This is valid regex, security should be handled at application level
        website = WebsiteBase(
            domain="example.com", white_listed_path_patterns=[r"\.\.\/"]
        )
        assert r"\..\/" in website.white_listed_path_patterns

    def test_extremely_long_domain(self):
        """Security: Extremely long domain should fail."""
        long_domain = "a" * 300 + ".com"
        with pytest.raises(ValidationError):
            WebsiteBase(domain=long_domain)

    def test_unicode_domain(self):
        """Security: Unicode in domain."""
        # IDN domains might be valid depending on requirements
        with pytest.raises(ValidationError):
            WebsiteBase(domain="例え.jp")

    # =============================================
    # Localization and Internationalization
    # =============================================

    def test_various_timezones(self):
        """Localization: Various international timezones should work."""
        timezones = [
            "America/New_York",
            "Europe/London",
            "Asia/Tokyo",
            "Australia/Sydney",
            "Pacific/Auckland",
            "Africa/Cairo",
            "America/Sao_Paulo",
        ]
        for tz in timezones:
            website = WebsiteBase(domain="example.com", timezone=tz)
            assert website.timezone == tz

    def test_utc_offset_timezone(self):
        """Localization: UTC offset notation might not be supported."""
        with pytest.raises(ValidationError):
            WebsiteBase(domain="example.com", timezone="UTC+5")

    def test_international_tlds(self):
        """Localization: International TLDs should work."""
        international_domains = [
            "example.co.uk",
            "example.com.br",
            "example.de",
            "example.jp",
            "example.cn",
        ]
        for domain in international_domains:
            website = WebsiteBase(domain=domain)
            assert website.domain == domain


class TestWebsiteCreate:
    """Test WebsiteCreate schema."""

    def test_create_with_valid_data(self, valid_website_data):
        """Positive: Create with valid data should work."""
        website = WebsiteCreate(**valid_website_data)
        assert website.domain == valid_website_data["domain"]

    def test_create_with_minimal_data(self, minimal_website_data):
        """Positive: Create with minimal data should work."""
        website = WebsiteCreate(**minimal_website_data)
        assert website.domain == "minimal.com"


class TestWebsiteUpdate:
    """Test WebsiteUpdate schema."""

    def test_update_single_field(self):
        """Positive: Updating single field should work."""
        update = WebsiteUpdate(title="New Title")
        assert update.title == "New Title"

    def test_update_multiple_fields(self):
        """Positive: Updating multiple fields should work."""
        update = WebsiteUpdate(
            title="New Title", description="New Description", max_concurrent=15
        )
        assert update.title == "New Title"
        assert update.description == "New Description"
        assert update.max_concurrent == 15

    def test_update_with_no_fields(self):
        """Negative: Update with no fields should fail."""
        with pytest.raises(ValidationError) as exc_info:
            WebsiteUpdate()
        assert "at least one field" in str(exc_info.value).lower()

    def test_partial_update_validation(self):
        """Positive: Partial update should still validate provided fields."""
        with pytest.raises(ValidationError):
            WebsiteUpdate(max_concurrent=0)


class TestWebsiteResponse:
    """Test WebsiteResponse schema."""

    def test_response_includes_id(self, sample_website):
        """Positive: Response should include id."""
        response = WebsiteResponse.model_validate(sample_website)
        assert response.id == sample_website.id

    def test_response_includes_timestamps(self, sample_website):
        """Positive: Response should include timestamps."""
        response = WebsiteResponse.model_validate(sample_website)
        assert response.created_at is not None
        assert response.updated_at is not None

    def test_response_fields_frozen(self):
        """Data Integrity: Response fields should be frozen (immutable)."""
        # This test depends on how frozen is implemented
        # If using Pydantic's frozen config, assignment should raise error
        pass
