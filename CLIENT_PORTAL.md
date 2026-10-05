# Client Portal

URL: **https://your-domain/portal**

## How to enable for a client

1. Open **Users** (Admin).
2. Create or edit a user:
   - **Role** = `Client`
   - **Linked Client** = the client record
   - Set username + password; share with the client.
3. Client opens `/portal` (or logs in on main site and is redirected).

## What clients can do

- View engagement status
- View & **respond** to open queries
- See document requests from the firm and **upload files**
- View document register entries for their client
- View invoices (read-only)

## Staff: request documents from a client

`POST /api/portal/admin/doc-requests` (Bearer staff token)

```json
{
  "client_id": 12,
  "title": "Bank statements FY 2025-26",
  "description": "Please upload Apr–Mar statements for all accounts.",
  "due_date": "2026-10-20"
}
```

List: `GET /api/portal/admin/doc-requests?client_id=12`  
Close: `PUT /api/portal/admin/doc-requests/<id>` body `{"status":"Closed"}`

## Safety

- Additive only — existing firm features unchanged.
- Client APIs are scoped to `g.user.client_id`; no cross-client data.
