# Compliance Policy (V1)

## Project

Lead Generator App

---

# 1. Purpose

This document defines data acquisition compliance rules for V1.

The platform must collect only publicly available business and contact information.

---

# 2. Allowed Sources

Allowed sources:

* official business websites
* public contact pages
* public about pages
* public business directories
* government or verified business registries
* public social profiles where contact information is explicitly shown

---

# 3. Prohibited Sources And Methods

V1 must not use:

* private data
* hidden email guessing at scale
* credentialed scraping
* LinkedIn scraping automation
* paid datasets
* bypassing access controls
* collecting data from pages that explicitly prohibit automated access

---

# 4. Crawling Rules

Workers must:

* use conservative request rates
* respect robots.txt where applicable
* stop when blocked
* avoid repeated failed requests
* store source URLs for traceability

---

# 5. Email Collection Rules

Emails may be stored only when:

* publicly listed on an allowed source
* associated with the business being collected
* traceable to a source URL

Private personal emails must not be collected unless they are explicitly published as business contact information by the business.

---

# 6. Source Traceability

Every collected business or contact record must be traceable to:

* source_type
* source_url
* trust_tier
* confidence_score

For contacts, these source attributes are stored on `data_sources` and linked from `contacts.source_id`. Contact records must store `business_id`, `source_id`, `source_url`, and `collection_timestamp`.

---

# 7. MVP Exclusions

MVP collection must not include:

* decision-maker identification
* opportunity scoring
* AI enrichment
* credentialed scraping
* paid datasets

Any later expansion requires a separate approved policy update before implementation.
