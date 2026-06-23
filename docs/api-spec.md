# API Specification (V1)

## 1. Overview

This document defines secure API endpoints for the Lead Intelligence Platform.

All endpoints are:

* HTTPS only
* Authenticated via JWT
* Rate limited
* Logged for audit purposes

---

# 2. Authentication

## 2.1 Login

### Endpoint

```
POST /auth/login
```

### Request

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

### Response

```json
{
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here"
}
```

---

## 2.2 Refresh Token

```
POST /auth/refresh
```

Returns new access token.

---

## 2.3 Logout

```
POST /auth/logout
```

Invalidates refresh token.

---

# 3. Security Middleware (Applied to ALL endpoints)

Every request must pass:

* JWT validation
* Rate limit check
* Role validation
* Request logging
* Input sanitization

---

# 4. Business Search API

## 4.1 Search Businesses

```
POST /api/search
```

### Auth Required: YES

### Request

```json
{
  "industry": "gym",
  "country": "United States",
  "state": "Texas",
  "city": "Houston"
}
```

### Response

```json
{
  "results": [
    {
      "business_id": "uuid",
      "name": "ABC Fitness",
      "website": "https://abcfitness.com",
      "phone": "+123456789",
      "city": "Houston",
      "opportunity_score": 85
    }
  ]
}
```

---

# 5. Business Detail API

## 5.1 Get Business

```
GET /api/business/{id}
```

### Auth Required: YES

Returns:

* business info
* contacts
* enrichment
* opportunity score
* social profiles

---

# 6. Enrichment API

## 6.1 Trigger Enrichment

```
POST /api/enrich/{business_id}
```

### Auth Required: ADMIN / SYSTEM

Triggers:

* website scraping
* tech detection
* contact extraction
* social profile discovery

---

# 7. Opportunity Scoring API

## 7.1 Generate Score

```
POST /api/score/{business_id}
```

### Auth Required: SYSTEM

Returns:

```json
{
  "score": 92,
  "factors": {
    "no_chatbot": 20,
    "no_booking": 15,
    "high_reviews": 10
  }
}
```

---

# 8. Export API

## 8.1 Export Leads

```
POST /api/export
```

### Auth Required: YES

### Request

```json
{
  "format": "csv",
  "filters": {
    "industry": "gym",
    "country": "UK",
    "min_score": 80
  }
}
```

### Response

```json
{
  "download_url": "signed_url_here"
}
```

---

# 9. Contact API

## 9.1 Get Contacts

```
GET /api/business/{id}/contacts
```

Returns:

* decision makers
* roles
* emails (if available)
* source URLs

---

# 10. Data Source Tracking API

## 10.1 View Sources

```
GET /api/business/{id}/sources
```

Returns:

* where data came from
* trust tier
* confidence score

---

# 11. Internal System APIs (Locked Down)

These endpoints are NOT public.

## 11.1 Crawl Worker

```
POST /internal/crawl
```

## 11.2 Enrichment Worker

```
POST /internal/enrich
```

## 11.3 Scoring Worker

```
POST /internal/score
```

---

# 12. Security Controls

## 12.1 Rate Limiting

* 60 requests/min per user
* 1000 requests/day per user

---

## 12.2 IP Monitoring

* Block suspicious IPs
* Detect scraping patterns
* Auto-throttle abusive behavior

---

## 12.3 Audit Logging

Every request logs:

* user_id
* endpoint
* timestamp
* IP address
* response status

---

## 12.4 Data Protection

* No raw database exposure
* No direct SQL access from API layer
* Sanitized outputs only

---

## 12.5 Encryption

* TLS 1.2+ required
* Sensitive fields encrypted at rest (emails, contacts)

---

# 13. Role-Based Access Control (RBAC)

| Role          | Permissions                |
| ------------- | -------------------------- |
| user          | search, view, export       |
| admin         | enrich, score, manage data |
| system_worker | internal pipelines only    |

---

# 14. API Design Principles

* No endpoint without authentication
* No unbounded queries
* No raw scraping exposure
* No public access to internal pipelines
* All outputs must be structured JSON

---

# 15. V1 Security Summary

This API is designed to:

* prevent abuse
* protect data integrity
* ensure traceability
* limit scraping attacks
* enforce controlled enrichment
* support future scaling

---

# 16. Future Enhancements (NOT V1)

* API gateway (Kong / AWS API Gateway)
* OAuth2 login (Google / GitHub)
* Webhooks system
* API usage billing
* Multi-tenant workspace isolation
* Advanced anomaly detection
