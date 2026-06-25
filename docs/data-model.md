# Data Model (Database Schema V1)

## 1. Overview

This document defines the core database schema for the Lead Generator App.

The system is designed around four core ideas:

* Businesses are the central entity
* Contacts belong to businesses
* Public contact collection adds contact information to businesses
* Sources provide traceability and trust

---

# 2. Core Entities

## 2.1 Users Table

Stores authenticated application users.

```sql
users
```

### Fields

* id (UUID, PK)
* email (TEXT, unique)
* password_hash (TEXT)
* role (TEXT) — admin, user, system_worker
* is_active (BOOLEAN)
* created_at (TIMESTAMP)
* updated_at (TIMESTAMP)

---

## 2.2 Refresh Tokens Table

Stores hashed opaque refresh tokens for session lifecycle management.

```sql
refresh_tokens
```

### Fields

* id (UUID, PK)
* user_id (FK -> users.id)
* token_hash (TEXT)
* issued_at (TIMESTAMP)
* expires_at (TIMESTAMP)
* revoked_at (TIMESTAMP, nullable)
* replaced_by_token_id (UUID, nullable)
* created_ip (VARCHAR)
* user_agent (TEXT)
* last_used_at (TIMESTAMP)

Raw refresh tokens must never be stored.

---

## 2.3 Businesses Table

Central entity of the system.

```sql
businesses
```

### Fields

* id (UUID, PK)
* name (TEXT)
* industry (TEXT)
* website (TEXT)
* phone (TEXT)
* email (TEXT, nullable)
* country (TEXT)
* state (TEXT)
* city (TEXT)
* address (TEXT)
* description (TEXT, nullable)
* source_type (TEXT) — e.g. "directory", "website", "manual"
* created_at (TIMESTAMP)
* updated_at (TIMESTAMP)

---

## 2.4 Contacts Table

Stores public contact information associated with a business.

```sql
contacts
```

### Fields

* id (UUID, PK)
* business_id (FK → businesses.id)
* source_id (UUID, FK -> data_sources.id)
* full_name (TEXT)
* role (TEXT, nullable)
* email (TEXT, nullable; encrypted at repository persistence boundary)
* phone (TEXT, nullable; encrypted at repository persistence boundary)
* linkedin_url (TEXT, nullable)
* is_decision_maker (BOOLEAN) - MVP default false; Phase 4 must not infer decision-maker status
* priority_score (INTEGER) - MVP default 0; Phase 4 must not calculate lead ranking
* source_url (TEXT)
* collection_timestamp (TIMESTAMP)
* created_at (TIMESTAMP)

---

## 2.5 Data Sources Table

Tracks where each piece of data came from.

```sql
data_sources
```

### Fields

* id (UUID, PK)

* business_id (FK)

* source_type (TEXT)

  * "website"
  * "directory"
  * "search_engine"
  * "manual"

* source_url (TEXT)

* trust_tier (TEXT)

  * A
  * B
  * C
  * D

* confidence_score (INTEGER) — 0–100

* collected_at (TIMESTAMP)

---

## 2.6 Social Profiles Table

Stores social media links separately for normalization.

```sql
social_profiles
```

### Fields

* id (UUID, PK)
* business_id (FK)
* platform (TEXT) — facebook, instagram, linkedin, youtube
* url (TEXT)

---

## 2.7 Search Logs Table

Tracks user searches for analytics and caching.

```sql
search_logs
```

### Fields

* id (UUID, PK)

* user_id (UUID, FK -> users.id)

* request_id (TEXT)

* industry (TEXT)

* country (TEXT)

* state (TEXT)

* city (TEXT)

* results_count (INTEGER)

* created_at (TIMESTAMP)

---

## 2.8 Exports Table

Tracks CSV export requests and generated files.

```sql
exports
```

### Fields

* id (UUID, PK)
* user_id (FK → users.id)
* format (TEXT) — csv
* filters (JSONB)
* status (TEXT) — pending, processing, completed, failed
* file_path (TEXT, nullable)
* created_at (TIMESTAMP)
* updated_at (TIMESTAMP)

---

## 2.9 Background Jobs Table

Supports the V1 database-backed polling worker system.

```sql
background_jobs
```

### Fields

* id (UUID, PK)
* job_type (TEXT)
* status (TEXT) — pending, running, completed, failed
* payload (JSONB)
* attempts (INTEGER)
* max_attempts (INTEGER)
* locked_at (TIMESTAMP, nullable)
* locked_by (TEXT, nullable)
* error_message (TEXT, nullable)
* created_at (TIMESTAMP)
* updated_at (TIMESTAMP)

---

## 2.10 Audit Logs Table

Tracks security and user activity events.

```sql
audit_logs
```

### Fields

* id (UUID, PK)
* user_id (FK → users.id, nullable)
* event_type (TEXT)
* ip_address (TEXT, nullable)
* request_id (TEXT)
* metadata (JSONB)
* created_at (TIMESTAMP)

---

# 3. Relationships

```
businesses
   │
   ├── contacts
   ├── data_sources
   └── social_profiles

data_sources
   │
   └── contacts

users
   │
   ├── refresh_tokens
   ├── exports
   ├── search_logs
   └── audit_logs
```

---

# 4. Key Design Principles

## 4.1 Business-Centric Model

Everything revolves around a business entity.

---

## 4.2 Separation of Concerns

* Contacts ≠ Businesses
* Sources ≠ Business Entity

---

## 4.3 Source Traceability

Every piece of data must be traceable via:

* data_sources table
* source_id when a collected contact is stored
* source_url
* trust_tier

---

## 4.4 Contact Source Traceability

Every collected contact must be traceable to:

* `contacts.business_id`
* `contacts.source_id`
* `contacts.collection_timestamp`

`contacts.source_id` references `data_sources.id`. `contacts.source_url` is retained for readable attribution and must match the referenced source record.

Phase 4 must not infer decision-maker status or calculate lead ranking.

---

# 5. Indexing Strategy (Important for performance)

Phase 4A may add schema changes required for documented source traceability, deduplication, and job idempotency. These changes are part of Phase 4A implementation scope and do not change the approved technology stack.

## businesses

* (country, state, city)
* (industry)
* (name)

## contacts

* (business_id)
* (source_id)
* (collection_timestamp)
* (role)
* (is_decision_maker)

Partial unique indexes required for retry-safe public contact collection:

* `ux_contacts_business_source_email` on `(business_id, source_id, lower(email))` where `email IS NOT NULL`
* `ux_contacts_business_source_phone` on `(business_id, source_id, phone)` where `email IS NULL AND phone IS NOT NULL`
* `ux_contacts_business_source_name_url` on `(business_id, source_id, lower(full_name), source_url)` where `email IS NULL AND phone IS NULL`

These indexes enforce the documented deduplication order without requiring new columns.

## data_sources

* (business_id)
* unique `(business_id, source_url)`

## refresh_tokens

* (user_id)
* (token_hash)
* (expires_at)
* (revoked_at)

## background_jobs

* (status)
* (job_type)
* (locked_at)
* partial unique `(job_type, payload->>'idempotency_key')` where `status IN ('pending', 'running')`

## exports

* (user_id)
* (status)

---

# 6. Data Integrity Rules

* A business cannot exist without at least one source entry
* Contacts must belong to a business
* Contacts collected by Phase 4 must reference a `data_sources.id` through `contacts.source_id`
* Contacts collected by Phase 4 must store `collection_timestamp`
* Contact email and phone values must be encrypted before insert/update according to `security-standards.md`
* `data_sources` must be unique by `(business_id, source_url)` for Phase 4 collected sources
* Active background jobs must be unique by `(job_type, payload.idempotency_key)`
* Phase 4 must not infer decision-maker status
* Phase 4 must not calculate lead ranking
* Duplicate businesses must be merged based on:

  * website OR
  * phone OR
  * name + location

---

# 7. Future Extensions (NOT V1)

These are intentionally excluded for now:

* Email verification system
* Outreach campaign tracking
* CRM pipeline stages
* Payment / SaaS billing system
* LinkedIn API integration
* Multi-tenant workspace system

---

# 8. V1 Summary

This database supports:

* Business discovery
* Contact extraction
* Public contact collection
* CSV export
* Source validation

It is optimized for:

* simplicity
* scalability
* traceable public data collection
* fast querying
