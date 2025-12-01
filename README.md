# VibeCoding Hosting Backend (FastAPI)

## Getting started
1. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
2. Run the API
   ```bash
   uvicorn app.main:app --reload
   ```
3. Visit the docs at [`/docs`](http://localhost:8000/docs) for interactive testing.

## Available endpoints (happy-path flow)
> All `/admin/*` endpoints require the `X-Admin-Key` header to match `ADMIN_API_KEY` in your environment.

- `POST /admin/plans`, `DELETE /admin/plans/{name}`, `GET /admin/plans` – admin CRUD for plan presets (vcpu, memory, disk, clone mode full/linked, price, default expire days, Proxmox mapping, optional template + storage).
- `POST /admin/upgrades`, `DELETE /admin/upgrades/{name}`, `GET /admin/upgrades` – define reusable upgrade bundles (add vCPU/RAM/disk + optional price) and list them.
- `POST /admin/proxmox/hosts`, `DELETE /admin/proxmox/hosts/{id}`, `GET /admin/proxmox/hosts` – admin registers/list/removes Proxmox API endpoints (api_url, username/password/realm, node, location tag).
- `GET /admin/servers` – admin view of all servers with optional filters (`owner_id`, `status`, `plan`, `location`).
- `POST /users` – register a customer with `email`, `phone_number`, and optional `external_auth_id` (to link your auth provider).
- `GET /users` – list registered customers.
- `GET /servers/metadata/allowed` – discover configured plan specs, upgrade bundles, and available locations before provisioning.
- `POST /servers` – provision a server for the authenticated user; if `expire_in_days` is omitted, the plan's `default_expire_days` is applied. Returns the generated VM password (not stored) and later attaches the primary IP once Proxmox reports it. Body example:
  ```json
  {
    "plan": "basic",
    "location": "kr-central",
    "expire_in_days": 30
  }
  ```
- `GET /servers/user/{user_id}` – list servers created for a specific user (refreshes status and IP from Proxmox on read). Requires the caller to either be that user or present `X-Admin-Key`.
- `GET /servers/{server_id}` – fetch a single server for the owner (refreshes status/resources/IP). Admins may supply only the admin key.
- `POST /servers/{server_id}/extend` – add more days for the owner; admins can override with `X-Admin-Key`.
- Power controls: `POST /servers/{id}/start|stop|shutdown|reboot|reset|suspend|resume` – owner auth required (or admin key override).
- `POST /servers/{id}/upgrade` – apply a named upgrade bundle (owner auth required; server must be stopped; admin key allowed for overrides).
- `POST /servers/{id}/password/reset` – regenerates a random VM password (not persisted) and pushes it to Proxmox for the owner; returns the password once.
- Automatic expiry guard: nightly scheduler stops expired servers and sends SOLAPI reminders `EXPIRY_WARNING_DAYS` (default 3) before `expire_at`.
- `GET /healthz` – simple health check.

## How the Proxmox & SOLAPI adapters work
- `app/infrastructure/clients/proxmox.py` – logs in with username/password (realm defaults to `pam`) to fetch a ticket/CSRF token, then hits the Proxmox API to create VMs on the configured node. It supports cloning from a template VMID defined on the plan (with optional storage target) or creating a fresh VM. The host/node credentials come from the admin-managed catalog (or the fallback `PROXMOX_*` env values if provided).
- `app/infrastructure/clients/solapi.py` – place to call the official SOLAPI SDK. It reads `SOLAPI_KEY`, `SOLAPI_SECRET`, and `SOLAPI_FROM`. Implement SMS sending in `send_provisioning_sms`.

Both clients are injected into the saga orchestrator (`app/application/services/server_orchestrator.py`), which sets the server status, calls Proxmox, and sends an SMS. If an exception occurs, the orchestrator rolls back by calling `destroy_server` and marking the server as `ROLLED_BACK`.

## Configuration
- Defaults live in `app/infrastructure/config/settings.py` and are overrideable via environment variables or a local `.env` file.
- Proxmox defaults (used only if no admin hosts are registered):
  - `PROXMOX_HOST` (e.g., `https://proxmox.local`)
  - `PROXMOX_USERNAME`
  - `PROXMOX_PASSWORD`
  - `PROXMOX_REALM` (defaults to `pam`)
- Persistence: set `DATABASE_PATH` to control where the SQLite file is written (defaults to `data/vibecoding.db`).
- Provisioning policy uses the admin-managed plan catalog and Proxmox host catalog; the metadata endpoint exposes what is currently configured.
- Auth: set `JWT_SECRET`, `JWT_ISSUER`, and `JWT_AUDIENCE` to validate bearer tokens. Use `X-Admin-Key: <ADMIN_API_KEY>` for admin routes or local testing; optional `X-Impersonate-User` can be supplied with a UUID to act on behalf of a user when the admin key is present.

## Example cURL
Bootstrap one host/plan via admin APIs (optional if you rely on `.env` defaults):
```bash
# Register a Proxmox endpoint with username/password auth
curl -X POST http://localhost:8000/admin/proxmox/hosts \
  -H "Content-Type: application/json" \
  -d '{"id":"pve1","api_url":"https://proxmox.local","username":"root","password":"changeme","realm":"pam","node":"pve","location":"kr-central"}'

# Register a plan bound to that host
curl -X POST http://localhost:8000/admin/plans \
  -H "Content-Type: application/json" \
  -d '{"name":"basic","vcpu":1,"memory_mb":1024,"disk_gb":20,"location":"kr-central","proxmox_host_id":"pve1","proxmox_node":"pve"}'
```

```bash
# 1) Register a user
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","phone_number":"01012345678"}'

# 2) Check allowed plans/locations
curl http://localhost:8000/servers/metadata/allowed

# 3) Provision a server (with optional expiry window)
curl -X POST http://localhost:8000/servers \
  -H "Content-Type: application/json" \
  -d '{"user_id":"<uuid>","plan":"basic","location":"kr-central","expire_in_days":14}'
```

## End-to-end walkthrough (expected responses)
Assuming the app is running locally on port `8000`:

```bash
# 1) Register a user
curl -s -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","phone_number":"01099998888"}' | jq
```
Expected response:
```json
{
  "id": "0e9a8db2-4c03-4c5d-9a22-5601d2e4d4f1",
  "email": "demo@example.com",
  "phone_number": "01099998888",
  "external_auth_id": null
}
```

```bash
# 2) See allowed plans/locations before provisioning
curl -s http://localhost:8000/servers/metadata/allowed | jq
```
Expected response:
```json
{
  "plans": [
    {
      "name": "basic",
      "location": "kr-central",
      "vcpu": 1,
      "memory_mb": 1024,
      "disk_gb": 20,
      "proxmox_host_id": "default",
      "proxmox_node": null,
      "template_vmid": null,
      "disk_storage": "local-lvm",
      "clone_mode": "full",
      "description": "Default starter plan"
    }
  ],
  "locations": ["kr-central"]
}
```

```bash
# 3) Provision a server for the user
curl -s -X POST http://localhost:8000/servers \
  -H "Content-Type: application/json" \
  -d '{"user_id":"0e9a8db2-4c03-4c5d-9a22-5601d2e4d4f1","plan":"basic","location":"kr-central"}' | jq
```
Expected response (IDs will differ):
```json
{
  "id": "8c04a4df-1fae-4b43-8d45-b69d49fe4f57",
  "owner_id": "0e9a8db2-4c03-4c5d-9a22-5601d2e4d4f1",
  "plan": "basic",
  "location": "kr-central",
  "proxmox_host_id": "default",
  "proxmox_node": null,
  "vcpu": 1,
  "memory_mb": 1024,
  "disk_gb": 20,
  "expire_in_days": 14,
  "expire_at": "2024-01-15T12:00:00.000000",
  "created_at": "2023-12-31T12:00:00.000000",
  "status": "active",
  "external_id": "vm-8c04a4df-1fae-4b43-8d45-b69d49fe4f57"
}
```

```bash
# 4) Fetch the server directly (or list all servers for the user)
curl -s http://localhost:8000/servers/8c04a4df-1fae-4b43-8d45-b69d49fe4f57 | jq
curl -s http://localhost:8000/servers/user/0e9a8db2-4c03-4c5d-9a22-5601d2e4d4f1 | jq

# 5) Power controls using the backend-issued server ID (owner user_id is required)
curl -s -X POST http://localhost:8000/servers/8c04a4df-1fae-4b43-8d45-b69d49fe4f57/stop \
  -H "Content-Type: application/json" \
  -d '{"user_id":"0e9a8db2-4c03-4c5d-9a22-5601d2e4d4f1"}' | jq
curl -s -X POST http://localhost:8000/servers/8c04a4df-1fae-4b43-8d45-b69d49fe4f57/start \
  -H "Content-Type: application/json" \
  -d '{"user_id":"0e9a8db2-4c03-4c5d-9a22-5601d2e4d4f1"}' | jq
curl -s -X POST http://localhost:8000/servers/8c04a4df-1fae-4b43-8d45-b69d49fe4f57/reboot \
  -H "Content-Type: application/json" \
  -d '{"user_id":"0e9a8db2-4c03-4c5d-9a22-5601d2e4d4f1"}' | jq
curl -s -X POST http://localhost:8000/servers/8c04a4df-1fae-4b43-8d45-b69d49fe4f57/shutdown \
  -H "Content-Type: application/json" \
  -d '{"user_id":"0e9a8db2-4c03-4c5d-9a22-5601d2e4d4f1"}' | jq

# 6) Extend lifetime by 7 days (owner user_id required)
curl -s -X POST http://localhost:8000/servers/8c04a4df-1fae-4b43-8d45-b69d49fe4f57/extend \
  -H "Content-Type: application/json" \
  -d '{"user_id":"0e9a8db2-4c03-4c5d-9a22-5601d2e4d4f1","additional_days":7}' | jq
```
Both `GET /servers/{id}` and `GET /servers/user/{user_id}` refresh each server's runtime status from Proxmox (running/stopped/etc.) before returning and persist the latest state.
Each server will show its persisted state, created/expiry times, and Proxmox mapping:
```json
[
  {
    "id": "8c04a4df-1fae-4b43-8d45-b69d49fe4f57",
    "owner_id": "0e9a8db2-4c03-4c5d-9a22-5601d2e4d4f1",
    "plan": "basic",
    "location": "kr-central",
    "proxmox_host_id": "default",
    "proxmox_node": null,
    "vcpu": 1,
    "memory_mb": 1024,
    "disk_gb": 20,
    "expire_in_days": 21,
    "expire_at": "2024-01-22T12:00:00.000000",
    "created_at": "2023-12-31T12:00:00.000000",
    "status": "active",
    "external_id": "vm-8c04a4df-1fae-4b43-8d45-b69d49fe4f57"
  }
]
```

```bash
# 5) Confirm the health endpoint if needed
curl -s http://localhost:8000/healthz
```
```json
{"status":"ok"}
```

## Notes
- Persistence now uses SQLite via lightweight repositories; set `DATABASE_PATH` to move the DB file.
- Validation/rollback is handled in the `ProvisionServer` use case and the `ServerProvisionOrchestrator`.
