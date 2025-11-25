from typing import Dict, Iterable, Optional

from app.domain.models.plan import PlanSpec


class PlanRepository:
    """In-memory store for admin-defined hosting plans."""

    def __init__(self):
        self._plans: Dict[str, PlanSpec] = {}

    def add(self, plan: PlanSpec) -> None:
        self._plans[plan.name] = plan

    def get(self, name: str) -> Optional[PlanSpec]:
        return self._plans.get(name)

    def list(self) -> Iterable[PlanSpec]:
        return self._plans.values()
