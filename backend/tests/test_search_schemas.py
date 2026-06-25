import pytest

from app.schemas.search import BusinessSearchRequest, PaginationResponse


def test_search_request_normalizes_filters() -> None:
    payload = BusinessSearchRequest(
        filters={
            "industry": "  gym   studio ",
            "country": " United   States ",
            "state": " Texas ",
            "city": " Houston ",
        }
    )

    assert payload.filters.industry == "gym studio"
    assert payload.filters.country == "United States"
    assert payload.filters.state == "Texas"
    assert payload.filters.city == "Houston"
    assert payload.pagination.page == 1
    assert payload.pagination.per_page == 25


def test_search_request_rejects_unknown_fields() -> None:
    with pytest.raises(ValueError):
        BusinessSearchRequest(
            filters={
                "industry": "gym",
                "country": "United States",
                "state": "Texas",
                "city": "Houston",
                "score": 90,
            }
        )


def test_search_pagination_response_calculates_flags() -> None:
    pagination = PaginationResponse.from_counts(page=2, per_page=25, total=80)

    assert pagination.total_pages == 4
    assert pagination.has_next is True
    assert pagination.has_previous is True
