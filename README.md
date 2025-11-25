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
- `POST /users` – register a customer with `email` and `phone_number`.
- `GET /users` – list registered customers.
- `GET /servers/metadata/allowed` – discover the allowed `plans` and `locations` enforced by the provisioning policy.
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
- `app/infrastructure/clients/proxmox.py` – wraps calls to the Proxmox HTTP API. Replace the placeholder logic in `provision_server` / `destroy_server` with real requests (e.g., using `proxmoxer` or `requests`). The client already pulls auth/token values from environment variables (`PROXMOX_HOST`, `PROXMOX_TOKEN_ID`, `PROXMOX_TOKEN_SECRET`).
- `app/infrastructure/clients/solapi.py` – place to call the official SOLAPI SDK. It reads `SOLAPI_KEY`, `SOLAPI_SECRET`, and `SOLAPI_FROM`. Implement SMS sending in `send_provisioning_sms`.

Both clients are injected into the saga orchestrator (`app/application/services/server_orchestrator.py`), which sets the server status, calls Proxmox, and sends an SMS. If an exception occurs, the orchestrator rolls back by calling `destroy_server` and marking the server as `ROLLED_BACK`.

## Configuration
- Defaults live in `app/infrastructure/config/settings.py` and are overrideable via environment variables or a local `.env` file.
- Provisioning policy allows `basic`/`pro` plans and `kr-central`/`jp-east` locations by default; adjust in `app/api/dependencies.py` or `app/domain/services/provisioning_policy.py` as needed.

## Example cURL
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

## Notes
- Persistence is in-memory only; swap `UserRepository`/`ServerRepository` with real adapters to persist data.
- Validation/rollback is handled in the `ProvisionServer` use case and the `ServerProvisionOrchestrator`.
