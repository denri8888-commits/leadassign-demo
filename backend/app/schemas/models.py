from pydantic import BaseModel, Field


class SettingsUpdate(BaseModel):
    team_capacity: int | None = None
    manager_capacities: dict[str, int] | None = None
    recency_lambda: float | None = None
    recency_half_life_days: float | None = None
    prior_strength: float | None = None
    min_observations: int | None = None
    extra_manager_monthly_cost: float | None = None
    working_days_per_month: int | None = None
    form_recent_days: int | None = None
    form_previous_days: int | None = None
    form_short_days: int | None = None
    form_long_days: int | None = None
    form_dip_threshold: float | None = None
    assignment_mode: str | None = None
    applications_per_day: int | None = None
    demo_seed: int | None = None


class OverrideRequest(BaseModel):
    manager: str
    reason: str = Field(description="Причина изменения рекомендации")
    comment: str = ""


class DemoGenerateRequest(BaseModel):
    seed: int = 42
    scenario: str = "normal"


class SimulationRequest(BaseModel):
    days: int = 14
    auto_share: float = 0.5


class ImportMappingRequest(BaseModel):
    kind: str
    mapping: dict[str, str]
    filename: str


class ApiError(BaseModel):
    error: str
    details: list[str] = []
    hint: str | None = None
