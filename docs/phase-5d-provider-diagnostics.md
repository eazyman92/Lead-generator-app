# Phase 5D Provider Diagnostics

## Purpose

Add provider-level diagnostics for the production Search -> Worker -> Provider
pipeline without replacing the provider, fabricating data, or changing dashboard
behavior.

## Current Root Cause Hypothesis

The pipeline now reaches the real provider and fails honestly. The remaining
failure is provider-side discovery returning zero accepted businesses.

Before this pass, logs did not include the exact OpenStreetMap request URL, raw
response body, parsed record count, or candidate-level decisions. Without those
fields, AWS validation could only show `Provider returned zero businesses`, not
whether the cause was:

* HTTP error
* timeout
* rate limiting
* empty provider response
* parser failure
* filtering rejecting every record

This pass adds those diagnostics. The exact provider root cause should be read
from AWS logs after deployment.

## Diagnostic Logs Added

Provider logs now include:

* `provider_selected`
* `provider_request`
  * provider
  * query
  * limit
  * exact request URL
* `provider_raw_response`
  * raw HTTP status
  * exact request URL
  * raw response body, truncated to 2000 characters
  * raw body length
* `provider_response`
  * raw HTTP status
  * records parsed
  * businesses returned
* `provider_candidate_decision`
  * candidate index
  * accepted true/false
  * accept/reject reason
  * OSM id/type when available
* `provider_response_failed`
  * HTTP status
  * normalized provider error code

## Failure Classification

The provider layer now distinguishes:

| Code | Meaning |
| --- | --- |
| `HTTP_429` | Provider rate limited the request. |
| `HTTP_5XX` | Provider server error. |
| `NETWORK_TIMEOUT` | Provider request timed out. |
| `DNS_FAILURE` | Provider host could not be resolved. |
| `INVALID_PROVIDER_RESPONSE` | Provider returned invalid JSON or unexpected response shape. |
| `EMPTY_PROVIDER_RESPONSE` | Provider returned a valid empty result list. |
| `FILTERED_ALL_RESULTS` | Provider returned candidates, but parser rejected all of them. |
| `NO_BUSINESSES_FOUND` | Composite provider chain returned no businesses without a provider-specific error. |

## How To Diagnose AWS Searches

For searches such as:

* Restaurants, Houston, Texas, United States
* Restaurants, London, England, United Kingdom
* Restaurants, Ikeja, Lagos, Nigeria

inspect worker logs:

```bash
docker compose logs worker --since 30m | grep -E "provider_request|provider_raw_response|provider_response|provider_candidate_decision|contact_collection_failed"
```

Confirm:

1. Which provider was selected.
2. The exact request URL.
3. HTTP status.
4. Whether the raw body is `[]`, an error payload, or an unexpected shape.
5. How many records were parsed.
6. Whether candidates were accepted or rejected.
7. The final job `failure_reason` in `background_jobs.payload.progress`.

## Validation

Added regression tests for:

* successful OpenStreetMap response parsing
* empty provider response classification
* parser rejecting all candidates
* worker-level provider failure propagation
* zero-result handling
