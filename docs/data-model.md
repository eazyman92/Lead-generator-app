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
* full_name (TEXT)
* role (TEXT, nullable)
* email (TEXT, nullable)
* phone (TEXT, nullable)
* linkedin_url (TEXT, nullable)
* is_decision_maker (BOOLEAN)
* priority_score (INTEGER) — 0–100
* source_url (TEXT)
* created_at (TIMESTAMP)

---

## 2.5 Future Decision Makers View (Logical Layer)

Not necessarily a separate table — derived from `contacts`.

Definition:

* role IN (CEO, Founder, Owner, Managing Director, COO)
  OR
* priority_score >= 80

---

## 2.6 Future Business Enrichment Table

Stores AI + scraping intelligence.

```sql
business_enrichment
```

### Fields

* id (UUID, PK)

* business_id (FK)

* has_website (BOOLEAN)

* has_chatbot (BOOLEAN)

* has_booking_system (BOOLEAN)

* has_whatsapp (BOOLEAN)

* has_contact_form (BOOLEAN)

* tech_stack (JSONB)

* facebook_url (TEXT)

* instagram_url (TEXT)

* linkedin_url (TEXT)

* youtube_url (TEXT)

* seo_score (INTEGER)

* website_speed_score (INTEGER)

* mobile_friendly (BOOLEAN)

* ai_opportunity_score (INTEGER)

* last_scanned (TIMESTAMP)

---

## 2.7 Future Opportunity Scores Table

Stores AI-generated lead value scoring.

```sql
opportunity_scores
```

### Fields

* id (UUID, PK)

* business_id (FK)

* total_score (INTEGER) — 0–100

* has_chatbot_gap_score (INTEGER)

* has_booking_gap_score (INTEGER)

* automation_potential_score (INTEGER)

* digital_presence_score (INTEGER)

* recommendation (TEXT) — AI-generated insight

* created_at (TIMESTAMP)

---

## 2.8 Data Sources Table

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

## 2.9 Social Profiles Table

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

## 2.10 Search Logs Table

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

## 2.11 Exports Table

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

## 2.12 Background Jobs Table

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

## 2.13 Audit Logs Table

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
   ├── business_enrichment (future)
   ├── opportunity_scores (future)
   ├── data_sources
   └── social_profiles

users
   │
   ├── refresh_tokens
   ├── exports
   └── audit_logs
```

---

# 4. Key Design Principles

## 4.1 Business-Centric Model

Everything revolves around a business entity.

---

## 4.2 Separation of Concerns

* Contacts ≠ Businesses
* Future enrichment ≠ Core Data
* Future scores ≠ Raw Data
* Sources ≠ Business Entity

---

## 4.3 AI-Ready Structure

Fields like:

* ai_opportunity_score
* recommendation
* tech_stack (JSONB)

are designed for future AI expansion.

---

## 4.4 Source Traceability

Every piece of data must be traceable via:

* data_sources table
* source_url
* trust_tier

---

## 4.5 Decision Maker Logic

Decision makers are NOT stored separately.

They are derived from:

* contacts.role
* contacts.priority_score

---

# 5. Indexing Strategy (Important for performance)

## businesses

* (country, state, city)
* (industry)
* (name)

## contacts

* (business_id)
* (role)
* (is_decision_maker)

## refresh_tokens

* (user_id)
* (token_hash)
* (expires_at)
* (revoked_at)

## opportunity_scores

* (total_score)

## background_jobs

* (status)
* (job_type)
* (locked_at)

## exports

* (user_id)
* (status)

---

# 6. Data Integrity Rules

* A business cannot exist without at least one source entry
* Contacts must belong to a business
* Future enrichment must be tied to a business
* Future scores must always be derived, not manually entered
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
* AI augmentation
* fast querying
