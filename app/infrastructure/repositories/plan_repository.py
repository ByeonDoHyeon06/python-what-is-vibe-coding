from typing import Dict, Iterable, Optional

from app.domain.models.plan import Plan


class PlanRepository:
    """In-memory catalog of provisionable plans."""

    def __init__(self):
        self._plans: Dict[str, Plan] = {}

    def add(self, plan: Plan) -> None:
        if plan.name in self._plans:
            raise ValueError(f"Plan {plan.name} already exists")
        self._plans[plan.name] = plan

    def update(self, plan: Plan) -> None:
        self._plans[plan.name] = plan

    def get(self, name: str) -> Optional[Plan]:
        return self._plans.get(name)

    def list(self) -> Iterable[Plan]:
        return list(self._plans.values())

    def delete(self, name: str) -> None:
        if name in self._plans:
            del self._plans[name]
