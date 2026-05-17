from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    event_type: str = Field(..., description="Type of event")
    source: str = Field("api", description="Where this event came from")
    actor: Optional[str] = None
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SlackIngestRequest(BaseModel):
    text: str
    user: Optional[str] = None
    channel: Optional[str] = None
    ts: Optional[str] = None


class Event(BaseModel):
    event_id: str
    event_type: str
    source: str
    timestamp: datetime
    actor: Optional[str] = None
    payload: Dict[str, Any]
    metadata: Dict[str, Any]


class Decision(BaseModel):
    decision_id: str
    event_id: str
    route: str
    reason: str
    risk_level: str = "low"
    proposed_action: Dict[str, Any] = Field(default_factory=dict)
    error_code: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    next_steps: Optional[str] = None


class IngestResponse(BaseModel):
    event: Event
    decision: Decision


class ActionResult(BaseModel):
    action_id: str
    event_id: str
    decision_id: str
    action_type: str
    status: str
    artifact_path: Optional[str] = None
    reason: str
    error_code: Optional[str] = None
    next_steps: Optional[str] = None


class TemplateLine(BaseModel):
    category_id: str
    display_name: str
    target_amount: Decimal
    allocation_order: int
    is_active: bool


class WeeklyIncomeInput(BaseModel):
    period_id: str
    income_amount: Decimal
    status: str
    notes: Optional[str] = None


class OutputBlockRef(BaseModel):
    block_id: str
    band_index: int
    block_index_within_band: int
    start_row: int
    end_row: int
    label_col: int
    amount_col: int


class AllocationRunInput(BaseModel):
    period_id: str
    income: WeeklyIncomeInput
    template_lines: List[TemplateLine]
    target_block: OutputBlockRef


class WeeklyAllocationLine(BaseModel):
    period_id: str
    category_id: str
    display_name: str
    target_amount: Decimal
    allocated_amount: Decimal
    allocation_order: int
    status: str


class WeeklyAllocationResult(BaseModel):
    period_id: str
    starting_income: Decimal
    lines: List[WeeklyAllocationLine]
    total_allocated_to_categories: Decimal
    weekly_leftover_amount: Decimal
    grand_total_written: Decimal
    decision_status: str


class SheetWriteAction(BaseModel):
    action_id: str
    sheet_name: str
    cell_ref: str
    value: str | Decimal
    action_type: str
    reason: str


class ActionPlan(BaseModel):
    run_id: str
    period_id: str
    target_block: OutputBlockRef
    write_actions: List[SheetWriteAction]


class RawSheetBundle(BaseModel):
    raw_template_rows: List[Dict[str, Any]]
    raw_income_rows: List[Dict[str, Any]]
    raw_control_rows: Dict[str, Any]


class BudgetRunRequest(BaseModel):
    period_id: str
    template_values: List[List[Any]]
    income_values: List[List[Any]]
    control_values: List[List[Any]]
    weekly_output_values: List[List[Any]]
    output_sheet_name: str = "Weekly_Output"
    income_sheet_name: str = "Income_Input"
    audit_sheet_name: str = "Audit_Log"


class BudgetRunLiveRequest(BaseModel):
    period_id: str = Field(
        ...,
        description="Budget period to run from live Google Sheets data, e.g. 2026-W12",
    )


class BudgetRunResponse(BaseModel):
    run_id: str
    period_id: str
    decision_status: str
    total_allocated_to_categories: Decimal
    weekly_leftover_amount: Decimal
    grand_total_written: Decimal
    target_block_id: str