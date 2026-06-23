# UI / UX Specification (V1)

## Project

Lead Intelligence Platform

---

# 1. Design Philosophy

The platform should feel like:

* Apollo.io
* HubSpot
* Notion
* Airtable
* Linear

Combined into a simple lead intelligence dashboard.

Primary goals:

* Discover leads quickly
* Analyze opportunities easily
* Export leads efficiently

---

# 2. Design System

## Frontend Stack

### Framework

* Next.js

### Language

* TypeScript

### Styling

* Tailwind CSS

### Component Library

* shadcn/ui

### State Management

* React Query
* React Context

---

# 3. Navigation Structure

## Sidebar Navigation

```text
Dashboard

Lead Search

Results

Opportunity Center

Exports

Settings
```

---

# 4. Main Pages

## Page 1 — Dashboard

Purpose:

Provide platform overview.

---

### Dashboard Widgets

#### Total Businesses

```text
145,220
```

---

#### Decision Makers Found

```text
18,450
```

---

#### Emails Collected

```text
97,800
```

---

#### High Opportunity Leads

```text
5,200
```

---

### Recent Searches

Table:

| Industry   | Location | Results |
| ---------- | -------- | ------- |
| Gym        | Houston  | 1,245   |
| Restaurant | Lagos    | 2,014   |

---

# 5. Lead Search Page

This is the core page.

---

## Search Filters

### Industry

Dropdown

Examples:

* Gym
* Restaurant
* Hotel
* Dentist
* Law Firm

---

### Country

Dropdown

Examples:

* United States
* United Kingdom
* Nigeria
* Ghana
* South Africa

---

### State / Region

Dynamic dropdown

Example:

Country = USA

Shows:

* Texas
* California
* Florida

---

### City

Dynamic dropdown

Example:

State = Texas

Shows:

* Houston
* Dallas
* Austin

---

### Search Button

Large CTA:

```text
Search Leads
```

---

# 6. Search Results Page

Purpose:

Display discovered businesses.

---

## Results Table

Columns:

| Business | Website | Phone | Email | City | Score |
| -------- | ------- | ----- | ----- | ---- | ----- |

---

### Actions

Per Row:

* View
* Enrich
* Export

---

### Bulk Actions

* Select All
* Export Selected
* Run Enrichment

---

# 7. Lead Detail Page

Purpose:

Display complete business intelligence.

---

## Section A

Business Information

```text
Business Name

Industry

Country

State

City

Address
```

---

## Section B

Contact Information

```text
Website

Phone

Public Email

Contact URL
```

---

## Section C

Decision Makers

Table:

| Name | Role | Email | Priority |
| ---- | ---- | ----- | -------- |

---

## Section D

Social Profiles

Cards:

* Facebook
* Instagram
* LinkedIn
* YouTube

---

## Section E

Website Intelligence

Display:

```text
Has Chatbot

Has Booking

Has WhatsApp

Has Contact Form
```

---

## Section F

Technology Stack

Badges:

* WordPress
* Shopify
* React
* Google Analytics

---

# 8. Opportunity Center

Purpose:

Show best leads first.

---

## Filters

Minimum Score

Industry

Country

City

---

## Opportunity Table

Columns:

| Business | Score | Opportunity |
| -------- | ----- | ----------- |

---

Examples:

```text
92
AI Chatbot Opportunity
```

```text
88
Booking Automation Opportunity
```

---

# 9. Export Center

Purpose:

Manage exports.

---

## Export Formats

* CSV

Future:

* Excel
* JSON

---

## Export Options

Fields Selection

Checkboxes:

☑ Business Name

☑ Email

☑ Phone

☑ Website

☑ Score

---

# 10. Settings Page

---

## Profile Settings

* Name
* Email

---

## Security Settings

* Change Password
* Active Sessions

---

## API Settings (Future)

* API Key Management

---

# 11. User Experience Principles

## Fast Search

Search results should begin rendering within seconds.

---

## Progressive Loading

Show:

```text
Loading Leads...
```

while enrichment continues.

---

## Empty State Design

Example:

```text
No businesses found.

Try another city or industry.
```

---

## Error Handling

Example:

```text
Unable to fetch results.

Please try again.
```

---

# 12. Visual Design Guidelines

## Style

Modern SaaS

Minimalistic

Professional

Data-focused

---

## Layout

Desktop First

Responsive Mobile

Tablet Support

---

## Cards

Rounded corners

Soft shadows

Consistent spacing

---

## Tables

Sticky headers

Pagination

Sorting

Filtering

---

# 13. Dark Mode Support

Required:

* Light Mode
* Dark Mode

User preference saved.

---

# 14. Accessibility

Support:

* Keyboard navigation
* Screen readers
* High contrast mode

---

# 15. Performance Requirements

Search Results:

< 3 seconds

Dashboard Load:

< 2 seconds

Page Navigation:

Instant client-side transitions

---

# 16. V1 Screens

### Screen 1

Dashboard

---

### Screen 2

Lead Search

---

### Screen 3

Results Table

---

### Screen 4

Lead Detail

---

### Screen 5

Opportunity Center

---

### Screen 6

Export Center

---

### Screen 7

Settings

---

# 17. Success Criteria

Users can:

✓ Search businesses

✓ View enriched business data

✓ View decision makers

✓ Identify opportunities

✓ Export leads

✓ Navigate efficiently

The UI should feel modern, responsive, and professional while prioritizing business intelligence over visual complexity.
