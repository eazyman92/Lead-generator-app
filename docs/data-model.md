# Data Model (Database Schema V1)

## 1. Overview

This document defines the core database schema for the Lead Intelligence Platform.

The system is designed around four core ideas:

* Businesses are the central entity
* Contacts belong to businesses
* Enrichment adds intelligence to businesses
* Sources provide traceability and trust

---

# 2. Core Entities

## 2.1 Businesses Table

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

## 2.2 Contacts Table

Stores people associated with a business.

```sql
contacts
```

### Fields

* id (UUID, PK)
* business_id (FK → businesses.id)
* full_name (TEXT)
* role (TEXT) — CEO, Founder, Manager, etc.
* email (TEXT, nullable)
* phone (TEXT, nullable)
* linkedin_url (TEXT, nullable)
* is_decision_maker (BOOLEAN)
* priority_score (INTEGER) — 0–100
* source_url (TEXT)
* created_at (TIMESTAMP)

---

## 2.3 Decision Makers View (Logical Layer)

Not necessarily a separate table — derived from `contacts`.

Definition:

* role IN (CEO, Founder, Owner, Managing Director, COO)
  OR
* priority_score >= 80

---

## 2.4 Business Enrichment Table

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

## 2.5 Opportunity Scores Table

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

## 2.6 Data Sources Table

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

## 2.7 Social Profiles Table

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

## 2.8 Search Queries Table

Tracks user searches for analytics and caching.

```sql
search_queries
```

### Fields

* id (UUID, PK)

* industry (TEXT)

* country (TEXT)

* state (TEXT)

* city (TEXT)

* results_count (INTEGER)

* created_at (TIMESTAMP)

---

# 3. Relationships

```
businesses
   │
   ├── contacts
   ├── business_enrichment
   ├── opportunity_scores
   ├── data_sources
   └── social_profiles
```

---

# 4. Key Design Principles

## 4.1 Business-Centric Model

Everything revolves around a business entity.

---

## 4.2 Separation of Concerns

* Contacts ≠ Businesses
* Enrichment ≠ Core Data
* Scores ≠ Raw Data
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

## opportunity_scores

* (total_score)

---

# 6. Data Integrity Rules

* A business cannot exist without at least one source entry
* Contacts must belong to a business
* Enrichment must be tied to a business
* Scores must always be derived, not manually entered
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
* Decision-maker identification
* Website enrichment
* AI opportunity scoring
* Source validation
* CSV export

It is optimized for:

* simplicity
* scalability
* AI augmentation
* fast querying
