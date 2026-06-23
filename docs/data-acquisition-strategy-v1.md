# Data Acquisition Strategy V1 (Updated)

## Project Name

Lead Intelligence Platform (Working Name = Shark)

---

# 1. Purpose

This document defines how the platform discovers, collects, enriches, validates, and ranks business and decision-maker data.

It introduces an enhanced focus on:

* Decision Maker Identification
* Contact Hierarchy Modeling
* Email Sourcing Rules
* Source Trust Ranking System

---

# 2. Core Principles

* Data must be sourced from publicly available information only.
* Decision-makers are higher priority than generic contacts.
* Enrichment is more valuable than raw collection.
* Data must be traceable to a source.
* Multiple sources increase confidence score.
* Simplicity and reliability over aggressive scraping.

---

# 3. Data Acquisition Pipeline

## Stage 1: Business Discovery

Identify businesses using:

* Industry
* Country
* State / Region
* City

Output:

* Business name
* Website (if available)
* Basic listing information

---

## Stage 2: Base Data Collection

Collect foundational business data:

* Business name
* Website
* Phone number
* Address
* Industry category
* Location hierarchy

---

## Stage 3: Website Discovery

Locate official company web presence:

* Primary website
* Contact page
* About page
* Team or leadership page

---

## Stage 4: Contact & Decision Maker Extraction

### 4.1 Contact Hierarchy Model

Contacts are categorized into tiers:

#### Tier 1 — Decision Makers (Highest Priority)

* CEO
* Founder
* Owner
* Managing Director
* COO

#### Tier 2 — Senior Management

* CMO
* CTO
* Head of Operations
* Head of Marketing

#### Tier 3 — Functional Contacts

* Sales Manager
* Support Manager
* HR Manager

#### Tier 4 — Generic Contacts

* info@
* contact@
* sales@
* support@

---

### 4.2 Decision Maker Identification Layer

The system must attempt to identify decision makers using:

* Company About pages
* Team pages
* Leadership pages
* Press releases
* Public company profiles
* Verified public directories

Output:

* Full name
* Role / title
* Company association
* Source URL

---

# 5. Email Sourcing Rules

Email collection must follow strict hierarchy:

## 5.1 Primary Sources (Highest Trust)

* Official company website
* Contact page
* About page
* Footer contact sections

Collected emails:

* info@
* contact@
* sales@
* support@

---

## 5.2 Secondary Sources

* Public leadership pages
* Press releases
* Public business directories
* Official social media profiles (only where email is explicitly shown)

---

## 5.3 Decision Maker Emails

Decision maker emails are collected only when:

* Explicitly published on official websites OR
* Clearly associated with named contacts on public pages

Examples:

* [john.smith@company.com](mailto:john.smith@company.com)
* [ceo@company.com](mailto:ceo@company.com) (role-based but high intent)
* [firstname.lastname@company.com](mailto:firstname.lastname@company.com) (only if publicly confirmed pattern)

---

## 5.4 Prohibited in V1

* No hidden email guessing without domain confirmation
* No private email harvesting
* No LinkedIn scraping for emails

---

# 6. Source Trust Ranking System

Each data source is assigned a trust level:

## Tier A — Highest Trust

* Official company website
* Contact pages
* About pages
* Leadership pages

Confidence: 90–100%

---

## Tier B — High Trust

* Press releases
* Verified business registries
* Government business directories

Confidence: 75–90%

---

## Tier C — Medium Trust

* Industry directories
* Public listings
* Aggregated business databases

Confidence: 50–75%

---

## Tier D — Low Trust

* Unverified third-party sources
* User-generated listings
* Outdated directories

Confidence: 0–50%

---

# 7. Data Enrichment Layer

Each business is enriched with:

## 7.1 Communication Intelligence

* Phone number
* Public email
* Contact page URL
* Contact form presence
* WhatsApp availability

---

## 7.2 Social Intelligence

* Facebook
* Instagram
* LinkedIn
* YouTube

---

## 7.3 Website Intelligence

* CMS detection
* Chatbot presence
* Booking system detection
* Technology stack
* Analytics tools

---

# 8. Opportunity Detection Layer

The system identifies business needs:

## Indicators:

* No chatbot → AI support opportunity
* No booking system → automation opportunity
* Weak online presence → digital transformation opportunity
* High reviews but poor response → automation opportunity

Output:

* Opportunity type
* Score (0–100)
* Suggested service angle

---

# 9. Data Quality Rules

* Remove duplicates across sources
* Normalize phone formats
* Normalize URLs
* Validate location hierarchy consistency
* Assign confidence score per business
* Require minimum 2 sources for high-confidence leads

---

# 10. Data Refresh Strategy

* Active businesses: refresh every 30 days
* Inactive businesses: refresh every 90 days
* High-value leads: refresh every 14 days

---

# 11. Version 1 Scope

## Included:

* Business discovery
* Website discovery
* Contact extraction
* Decision maker identification
* Email sourcing (public only)
* Social profile collection
* Website enrichment
* Opportunity scoring
* CSV export

## Not Included:

* LinkedIn scraping automation
* Email guessing at scale
* Paid datasets
* Outreach automation
* CRM system
* Email verification services

---

# 12. Success Criteria

Version 1 is successful if:

* Users can find businesses by industry + location
* Decision makers are correctly identified when available
* Public emails are accurately extracted
* Businesses are enriched with useful intelligence
* Opportunity scoring improves lead quality vs basic directories
