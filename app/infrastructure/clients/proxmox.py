from __future__ import annotations

from typing import Any

import requests
from requests import Response

from app.domain.models.server import Server
from app.infrastructure.config.settings import settings


class ProxmoxClient:
    """Thin wrapper around Proxmox HTTP API (see https://pve.proxmox.com/pve-docs/api-viewer/)."""

    def __init__(self):
        self.base_url = settings.proxmox_host.rstrip("/")
        self.user = settings.proxmox_user
        self.password = settings.proxmox_password
        self.realm = settings.proxmox_realm or "pam"
        self.default_node = settings.proxmox_default_node
        self.node_map = settings.proxmox_node_map
        self.plan_templates = settings.proxmox_plan_templates

        self.session = requests.Session()
        self.csrf_token: str | None = None
        self.ticket: str | None = None

    def provision_server(self, server: Server, node: str, plan_template: dict[str, Any]) -> str:
        """Provision a server via Proxmox HTTP API and return the external identifier."""

        self._ensure_authenticated()

        vm_type = plan_template.get("type", "qemu")
        template_vmid = plan_template.get("template_vmid")
        if not template_vmid:
            raise ValueError(f"No template_vmid configured for plan: {server.plan}")

        vmid = self._get_next_vmid()
        name_prefix = plan_template.get("name_prefix", "vc")
        name = f"{name_prefix}-{server.id}"

        payload: dict[str, Any] = {"newid": vmid}
        if vm_type == "qemu":
            payload["name"] = name
            api_path = f"/nodes/{node}/qemu/{template_vmid}/clone"
        else:
            payload["hostname"] = name
            api_path = f"/nodes/{node}/lxc/{template_vmid}/clone"

        for optional_key in ("pool", "storage"):
            if optional_key in plan_template:
                payload[optional_key] = plan_template[optional_key]

        self._api_post(api_path, payload)
        return f"{vm_type}:{node}:{vmid}"

    def destroy_server(self, external_id: str) -> None:
        """Rollback helper to clean up failed provisioning attempts."""

        self._ensure_authenticated()
        vm_type, node, vmid = self._parse_external_id(external_id)
        api_path = f"/nodes/{node}/{vm_type}/{vmid}"
        self._api_delete(api_path)

    def resolve_node(self, location: str) -> str:
        node = self.node_map.get(location) or self.default_node
        if not node:
            raise ValueError(f"No Proxmox node configured for location: {location}")
        return node

    def resolve_plan_template(self, plan: str) -> dict[str, Any]:
        template = self.plan_templates.get(plan)
        if not template:
            raise ValueError(f"No Proxmox plan template configured for plan: {plan}")
        return dict(template)

    def _get_next_vmid(self) -> str:
        result = self._api_get("/cluster/nextid")
        if not result:
            raise RuntimeError("Unable to fetch next VMID from Proxmox")
        return str(result)

    def _parse_external_id(self, external_id: str) -> tuple[str, str, str]:
        try:
            vm_type, node, vmid = external_id.split(":", maxsplit=2)
        except ValueError as exc:  # noqa: BLE001
            raise ValueError("Invalid external id format; expected '<type>:<node>:<vmid>'") from exc
        return vm_type, node, vmid

    def _ensure_authenticated(self) -> None:
        if not self.ticket:
            self._authenticate()

    def _authenticate(self) -> None:
        username = f"{self.user}@{self.realm}"
        response = self.session.post(
            f"{self.base_url}/api2/json/access/ticket",
            data={"username": username, "password": self.password},
        )
        response.raise_for_status()

        data = response.json().get("data", {})
        self.ticket = data.get("ticket")
        self.csrf_token = data.get("CSRFPreventionToken")

        if not self.ticket:
            raise RuntimeError("Proxmox authentication did not return a ticket")

        self.session.cookies.set("PVEAuthCookie", self.ticket)

    def _api_get(self, path: str) -> Any:
        response = self.session.get(f"{self.base_url}/api2/json{path}")
        return self._handle_response(response)

    def _api_post(self, path: str, payload: dict[str, Any]) -> Any:
        headers = self._csrf_headers()
        response = self.session.post(f"{self.base_url}/api2/json{path}", data=payload, headers=headers)
        return self._handle_response(response)

    def _api_delete(self, path: str) -> Any:
        headers = self._csrf_headers()
        response = self.session.delete(f"{self.base_url}/api2/json{path}", headers=headers)
        return self._handle_response(response)

    def _csrf_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.csrf_token:
            headers["CSRFPreventionToken"] = self.csrf_token
        return headers

    def _handle_response(self, response: Response) -> Any:
        response.raise_for_status()
        body = response.json()
        return body.get("data")
