from datetime import datetime
import uuid

from fastapi import FastAPI, Header, HTTPException, Depends

from app.core.auth import require_ops_api_key
from app.core.idempotency_store import SQLiteIdempotencyStore
from app.core.logging import get_logger, log_event
from app.domain.schemas import (
    IngestRequest,
    IngestResponse,
    Event,
    BudgetRunRequest,
    BudgetRunResponse,
)
from app.services.router import route_event
from app.services.actuator import execute_decision
from app.services.run_budget_cycle import run_budget_cycle


app = FastAPI(title="AI Control Plane")
logger = get_logger()

# Persistent idempotency store (survives restarts)
idem_store = SQLiteIdempotencyStore()


def _process_ingest(ingest_req: IngestRequest, idempotency_key: str | None) -> IngestResponse:
    """
    Canonical ingest pipeline runner:
    - enforce idempotency key
    - reuse or create Event (persistent)
    - Decide (router)
    - Act v0 (safe execution)
    - structured logging
    - returns {event, decision}
    """

    # Gate 1: Idempotency-Key is required
    if not idempotency_key:
        log_event(
            logger,
            event_name="ingest_rejected",
            fields={
                "reason": "missing_idempotency_key",
                "event_type": ingest_req.event_type,
                "source": ingest_req.source,
            },
        )
        raise HTTPException(status_code=400, detail="Missing Idempotency-Key header")

    # Gate 2: Reuse existing Event if this key was already processed (persistent)
    existing_event = idem_store.get(idempotency_key)
    if existing_event:
        log_event(
            logger,
            event_name="ingest_duplicate",
            fields={
                "idempotency_key": idempotency_key,
                "event_id": existing_event.event_id,
                "event_type": existing_event.event_type,
                "source": existing_event.source,
            },
        )

        # Decide
        decision = route_event(existing_event)
        log_event(
            logger,
            event_name="decision_created",
            fields={
                "decision_id": decision.decision_id,
                "event_id": decision.event_id,
                "route": decision.route,
                "risk_level": decision.risk_level,
                "reason": decision.reason,
            },
        )

        # Act (safe execution)
        try:
            action_result = execute_decision(existing_event, decision)
            log_event(
                logger,
                event_name="action_executed"
                if action_result.status == "executed"
                else "action_noop",
                fields={
                    "action_id": action_result.action_id,
                    "event_id": action_result.event_id,
                    "decision_id": action_result.decision_id,
                    "action_type": action_result.action_type,
                    "status": action_result.status,
                    "artifact_path": action_result.artifact_path,
                    "reason": action_result.reason,
                },
            )
        except Exception as e:
            log_event(
                logger,
                event_name="action_failed",
                fields={
                    "event_id": existing_event.event_id,
                    "decision_id": decision.decision_id,
                    "route": decision.route,
                    "error": str(e),
                },
            )

        return IngestResponse(event=existing_event, decision=decision)

    # Create new canonical Event
    event = Event(
        event_id=str(uuid.uuid4()),
        event_type=ingest_req.event_type,
        source=ingest_req.source,
        timestamp=datetime.utcnow(),
        actor=ingest_req.actor,
        payload=ingest_req.payload,
        metadata=ingest_req.metadata,
    )

    log_event(
        logger,
        event_name="ingest_created",
        fields={
            "idempotency_key": idempotency_key,
            "event_id": event.event_id,
            "event_type": event.event_type,
            "source": event.source,
        },
    )

    # Persist Event for idempotency (survives restart)
    idem_store.set(idempotency_key, event)

    # Decide
    decision = route_event(event)
    log_event(
        logger,
        event_name="decision_created",
        fields={
            "decision_id": decision.decision_id,
            "event_id": decision.event_id,
            "route": decision.route,
            "risk_level": decision.risk_level,
            "reason": decision.reason,
        },
    )

    # Act (safe execution)
    try:
        action_result = execute_decision(event, decision)
        log_event(
            logger,
            event_name="action_executed"
            if action_result.status == "executed"
            else "action_noop",
            fields={
                "action_id": action_result.action_id,
                "event_id": action_result.event_id,
                "decision_id": action_result.decision_id,
                "action_type": action_result.action_type,
                "status": action_result.status,
                "artifact_path": action_result.artifact_path,
                "reason": action_result.reason,
            },
        )
    except Exception as e:
        log_event(
            logger,
            event_name="action_failed",
            fields={
                "event_id": event.event_id,
                "decision_id": decision.decision_id,
                "route": decision.route,
                "error": str(e),
            },
        )

    return IngestResponse(event=event, decision=decision)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/ops/ping")
def ops_ping(_: None = Depends(require_ops_api_key)):
    return {"status": "ok", "message": "ops route reachable"}


@app.post("/ingest/api", response_model=IngestResponse)
def ingest_api(
    ingest_req: IngestRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    return _process_ingest(ingest_req, idempotency_key)


class _InMemorySheetClient:
    """
    Minimal in-memory sheet client for endpoint-driven workflow execution.
    This keeps the endpoint thin and testable before real Google Sheets integration.
    """

    def __init__(self):
        self.calls = []
        self.sheets = {
            "Audit_Log": [
                [
                    "run_id",
                    "period_id",
                    "income_amount",
                    "total_allocated",
                    "weekly_leftover",
                    "target_block_id",
                    "status",
                    "timestamp",
                ]
            ]
        }

    def write_cell(self, sheet_name, cell_ref, value):
        self.calls.append((sheet_name, cell_ref, value))

    def get_sheet(self, sheet_name):
        return self.sheets.get(sheet_name, [])


@app.post("/budget/run", response_model=BudgetRunResponse)
def run_budget(request: BudgetRunRequest):
    result = run_budget_cycle(
        template_values=request.template_values,
        income_values=request.income_values,
        control_values=request.control_values,
        weekly_output_values=request.weekly_output_values,
        period_id=request.period_id,
        output_sheet_name=request.output_sheet_name,
        income_sheet_name=request.income_sheet_name,
        audit_sheet_name=request.audit_sheet_name,
        sheet_client=_InMemorySheetClient(),
    )

    allocation_result = result["allocation_result"]
    run_input = result["run_input"]

    return BudgetRunResponse(
        run_id=result["run_id"],
        period_id=run_input.period_id,
        decision_status=allocation_result.decision_status,
        total_allocated_to_categories=allocation_result.total_allocated_to_categories,
        weekly_leftover_amount=allocation_result.weekly_leftover_amount,
        grand_total_written=allocation_result.grand_total_written,
        target_block_id=run_input.target_block.block_id,
    )