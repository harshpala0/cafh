# CA FirmHub — Product Specification & Module Catalogue

**Built by Harsh Pala**  
**Product name:** CA FirmHub  
**Live:** https://cafh.onrender.com  
**Repo:** github.com/harshpala0/cafh

> Every module below is tagged: **Designed & Built by Harsh Pala**

---

## 1. Product Overview

**Module: CA FirmHub Core Platform · Designed & Built by Harsh Pala**

CA FirmHub is a multi-tenant SaaS practice management suite for Chartered Accountant firms in India. It unifies clients, engagements, tasks, statutory compliance, billing, client document exchange, notifications, and mobile access.

| Attribute | Value |
|-----------|--------|
| Product Name | **CA FirmHub** |
| Builder | **Harsh Pala** |
| Stack | Flask · PostgreSQL · Vanilla JS SPA · PWA |
| Hosting | Render · Neon · optional Cloudflare R2 |
| Mobile | PWA + Play Store TWA |

---

## 2. Access Portals

**Module: CA FirmHub Access Layer · Designed & Built by Harsh Pala**

| Portal | URL | Designed for |
|--------|-----|----------------|
| **Staff Workbench** | `/` | Admin, Team Leader, Member |
| **Client Connect Portal** | `/portal` | Client |
| **Platform Control** | `/superadmin` | SuperAdmin (platform owner) |
| **Mobile Reach** | Same URLs (PWA / TWA) | All roles on mobile |

---

## 3. Named Sub-Modules

| # | Module name | Purpose | Primary users |
|---|-------------|---------|----------------|
| 1 | **Horizon Dashboard** | Firm command centre + ops shortcuts | Staff |
| 2 | **Client Ledger** | Client master (PAN, GSTIN, contacts) | Staff |
| 3 | **Engagement Studio** | Engagements & FY binding | Staff |
| 4 | **TaskForge** | Tasks, assignees, compliance→task | Staff |
| 5 | **Query Desk** | Query / response register | Staff (Client limited) |
| 6 | **FeeVault Billing** | Invoices, GST, payments | Admin, Team Leader |
| 7 | **Statute Calendar** | GST/TDS/ITR/ROC calendar + client packs | Staff |
| 8 | **DocTrail Register** | Inward/outward document register | Staff |
| 9 | **Client Connect Portal** | Client doc requests & uploads | Client |
| 10 | **Portal Inbox** | Staff view of portal uploads | Staff |
| 11 | **Pulse Reminders** | Compliance + docs + fees in one list | Staff |
| 12 | **Ageing Receivables** | Fee OS ageing buckets | Staff |
| 13 | **Signal Notify** | Email digest + WhatsApp webhook | Admin, Team Leader |
| 14 | **NightWatch Cron** | Secured scheduled digests | Platform / system |
| 15 | **Sentinel Health** | Module health endpoint | DevOps |
| 16 | **Mobile Reach** | PWA + Play Store TWA | All |
| 17 | **Platform Control** | SuperAdmin multi-tenant console | SuperAdmin |
| 18 | **Insight Reports** | Practice overview reports | Admin, Team Leader |

Each row: **Designed & Built by Harsh Pala**.

---

## 4. Builder Attribution

**Official tag:** Designed & Built by Harsh Pala  
**Product name (locked):** CA FirmHub  
**Author:** Harsh Pala

— End of specification —
