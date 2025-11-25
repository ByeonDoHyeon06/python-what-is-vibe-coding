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
- `POST /admin/plans` – admin creates/updates plan presets (vcpu, memory, disk, location, proxmox host/node mapping, optional template clone info).
- `GET /admin/plans` – list all configured plans.
- `POST /admin/proxmox/hosts` – admin registers a Proxmox API endpoint (api_url, username/password/realm, node, location tag).
- `GET /admin/proxmox/hosts` – list configured Proxmox endpoints.
- `POST /users` – register a customer with `email`, `phone_number`, and optional `external_auth_id` (to link your auth provider).
- `GET /users` – list registered customers.
- `GET /servers/metadata/allowed` – discover configured plan specs and available locations before provisioning.
- `POST /servers` – provision a server for a user. Body example:
  ```json
  {
    "user_id": "<user uuid from /users>",
    "plan": "basic",
    "location": "kr-central"
  }
  ```
- `GET /servers/user/{user_id}` – list servers created for a specific user.
- `GET /servers/{server_id}` – fetch a single server.
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

# 3) Provision a server
curl -X POST http://localhost:8000/servers \
  -H "Content-Type: application/json" \
  -d '{"user_id":"<uuid>","plan":"basic","location":"kr-central"}'
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
  "status": "active",
  "external_id": "vm-8c04a4df-1fae-4b43-8d45-b69d49fe4f57"
}
```

```bash
# 4) Fetch the server directly (or list all servers for the user)
curl -s http://localhost:8000/servers/8c04a4df-1fae-4b43-8d45-b69d49fe4f57 | jq
curl -s http://localhost:8000/servers/user/0e9a8db2-4c03-4c5d-9a22-5601d2e4d4f1 | jq
```
Each server will show its persisted state:
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
