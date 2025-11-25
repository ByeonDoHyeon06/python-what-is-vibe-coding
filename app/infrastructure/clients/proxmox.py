from typing import Tuple

import httpx

from app.domain.models.plan import PlanSpec
from app.domain.models.proxmox_host import ProxmoxHostConfig
from app.domain.models.server import Server


class ProxmoxClient:
    """Thin wrapper around Proxmox HTTP API (https://pve.proxmox.com/pve-docs/api-viewer/)."""

    def __init__(self):
        self.http = httpx.Client(timeout=10.0, verify=False)

    def authenticate(self, host: ProxmoxHostConfig) -> Tuple[str, str | None]:
        """Login with username/password and return (ticket, csrf)."""

        base_url = host.api_url.rstrip("/")
        login_payload = {
            "username": f"{host.username}@{host.realm}" if host.realm else host.username,
            "password": host.password,
        }
        response = self.http.post(f"{base_url}/api2/json/access/ticket", data=login_payload)
        response.raise_for_status()
        data = response.json()["data"]
        return data["ticket"], data.get("CSRFPreventionToken")

    def _headers(self, ticket: str, csrf: str | None) -> dict[str, str]:
        headers = {"Cookie": f"PVEAuthCookie={ticket}"}
        if csrf:
            headers["CSRFPreventionToken"] = csrf
        return headers

    def provision_server(self, server: Server, plan: PlanSpec, host: ProxmoxHostConfig) -> str:
        """Provision a server and return the Proxmox-assigned identifier."""

        ticket, csrf = self.authenticate(host)
        node = plan.proxmox_node or host.node
        if not node:
            raise ValueError("Proxmox node must be configured on the plan or host")

        base_url = host.api_url.rstrip("/")
        vm_name = f"vm-{server.id}"
        vmid = self._generate_vmid(server)

        if plan.template_vmid:
            response = self.http.post(
                f"{base_url}/api2/json/nodes/{node}/qemu/{plan.template_vmid}/clone",
                data={
                    "newid": vmid,
                    "name": vm_name,
                    "target": node,
                    "full": 1,
                    "storage": plan.disk_storage or "local-lvm",
                },
                headers=self._headers(ticket, csrf),
            )
            response.raise_for_status()
        else:
            payload = {
                "vmid": vmid,
                "name": vm_name,
                "cores": plan.vcpu,
                "memory": plan.memory_mb,
                "sockets": 1,
                "ostype": "l26",
                "virtio0": f"{plan.disk_storage or 'local-lvm'}:{plan.disk_gb}G",
            }

            response = self.http.post(
                f"{base_url}/api2/json/nodes/{node}/qemu",
                data=payload,
                headers=self._headers(ticket, csrf),
            )
            response.raise_for_status()

        # ensure resources match plan for cloned templates
        self.http.put(
            f"{base_url}/api2/json/nodes/{node}/qemu/{vmid}/config",
            data={
                "cores": plan.vcpu,
                "memory": plan.memory_mb,
                "name": vm_name,
                "virtio0": f"{plan.disk_storage or 'local-lvm'}:{plan.disk_gb}G",
            },
            headers=self._headers(ticket, csrf),
        ).raise_for_status()

        return str(vmid)

    def destroy_server(self, external_id: str, host: ProxmoxHostConfig, node: str | None = None) -> None:
        """Rollback helper to clean up failed provisioning attempts."""

        ticket, csrf = self.authenticate(host)
        target_node = node or host.node
        if not target_node:
            raise ValueError("Proxmox node required to delete VM")

        response = self.http.delete(
            f"{host.api_url.rstrip('/')}/api2/json/nodes/{target_node}/qemu/{external_id}",
            headers=self._headers(ticket, csrf),
        )
        response.raise_for_status()

    @staticmethod
    def _generate_vmid(server: Server) -> int:
        return abs(server.id.int % 2_000_000_000) or 1000
