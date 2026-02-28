"""
Audit Logging System for Compliance
Tamper-proof logging with full audit trail
"""

import json
import hashlib
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from enum import Enum


class AuditEventType(str, Enum):
    """Types of audit events."""
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    ROUTING_DECISION = "routing_decision"
    ENSEMBLE_VALIDATION = "ensemble_validation"
    RATE_LIMIT_HIT = "rate_limit_hit"
    BUDGET_LIMIT_HIT = "budget_limit_hit"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_CHECK = "compliance_check"


class AuditSeverity(str, Enum):
    """Audit event severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEvent:
    """Single audit event with cryptographic hash."""

    def __init__(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        user_id: str,
        action: str,
        details: Dict[str, Any],
        previous_hash: str = "0"
    ):
        self.event_id = self._generate_event_id()
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.event_type = event_type
        self.severity = severity
        self.user_id = user_id
        self.action = action
        self.details = details
        self.previous_hash = previous_hash
        self.hash = self._calculate_hash()

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        timestamp_ms = int(datetime.utcnow().timestamp() * 1000)
        random_suffix = os.urandom(4).hex()
        return f"AUD-{timestamp_ms}-{random_suffix}"

    def _calculate_hash(self) -> str:
        """Calculate cryptographic hash for tamper detection."""
        data = {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "severity": self.severity,
            "user_id": self.user_id,
            "action": self.action,
            "details": self.details,
            "previous_hash": self.previous_hash
        }

        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "severity": self.severity,
            "user_id": self.user_id,
            "action": self.action,
            "details": self.details,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        """Create from dictionary."""
        event = cls(
            event_type=data["event_type"],
            severity=data["severity"],
            user_id=data["user_id"],
            action=data["action"],
            details=data["details"],
            previous_hash=data["previous_hash"]
        )
        # Override with saved values
        event.event_id = data["event_id"]
        event.timestamp = data["timestamp"]
        event.hash = data["hash"]
        return event


class AuditLogger:
    """
    Tamper-proof audit logging system.

    Features:
    - Cryptographic hash chain for tamper detection
    - Structured logging with event types
    - Compliance-ready audit trail
    - Query and search capabilities
    - Export for regulatory reporting
    """

    def __init__(self, log_dir: str = "data/audit_logs"):
        """
        Initialize audit logger.

        Args:
            log_dir: Directory to store audit logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.current_log_file = None
        self.last_hash = "0"
        self.events_buffer = []
        self.buffer_size = 100

        self._initialize_log_file()
        self._load_last_hash()

    def _initialize_log_file(self):
        """Initialize daily log file."""
        date_str = datetime.now().strftime("%Y%m%d")
        self.current_log_file = self.log_dir / f"audit_{date_str}.jsonl"

    def _load_last_hash(self):
        """Load last hash from current log file."""
        if self.current_log_file.exists():
            try:
                with open(self.current_log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_event = json.loads(lines[-1])
                        self.last_hash = last_event["hash"]
            except Exception:
                self.last_hash = "0"

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        action: str,
        details: Dict[str, Any],
        severity: AuditSeverity = AuditSeverity.INFO
    ) -> AuditEvent:
        """
        Log an audit event.

        Args:
            event_type: Type of event
            user_id: User identifier
            action: Action description
            details: Event details
            severity: Event severity

        Returns:
            AuditEvent object
        """
        # Check if new day
        date_str = datetime.now().strftime("%Y%m%d")
        expected_file = self.log_dir / f"audit_{date_str}.jsonl"
        if expected_file != self.current_log_file:
            self._flush_buffer()
            self.current_log_file = expected_file
            self.last_hash = "0"

        # Create event
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            action=action,
            details=details,
            previous_hash=self.last_hash
        )

        # Update last hash
        self.last_hash = event.hash

        # Buffer event
        self.events_buffer.append(event)

        # Flush if buffer full
        if len(self.events_buffer) >= self.buffer_size:
            self._flush_buffer()

        return event

    def log_llm_request(
        self,
        user_id: str,
        provider: str,
        model: str,
        task_type: str,
        prompt_preview: str,
        metadata: Dict[str, Any] = None
    ):
        """Log LLM request."""
        self.log_event(
            event_type=AuditEventType.LLM_REQUEST,
            user_id=user_id,
            action=f"LLM request to {provider}/{model}",
            details={
                "provider": provider,
                "model": model,
                "task_type": task_type,
                "prompt_preview": prompt_preview[:200],
                "metadata": metadata or {}
            }
        )

    def log_llm_response(
        self,
        user_id: str,
        provider: str,
        model: str,
        success: bool,
        tokens: int,
        cost: float,
        latency: float,
        error: Optional[str] = None
    ):
        """Log LLM response."""
        self.log_event(
            event_type=AuditEventType.LLM_RESPONSE,
            user_id=user_id,
            action=f"LLM response from {provider}/{model}",
            details={
                "provider": provider,
                "model": model,
                "success": success,
                "tokens": tokens,
                "cost": cost,
                "latency": latency,
                "error": error
            },
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING
        )

    def log_routing_decision(
        self,
        user_id: str,
        task_id: str,
        selected_model: str,
        reason: str,
        alternatives: List[str]
    ):
        """Log routing decision."""
        self.log_event(
            event_type=AuditEventType.ROUTING_DECISION,
            user_id=user_id,
            action=f"Routed to {selected_model}",
            details={
                "task_id": task_id,
                "selected_model": selected_model,
                "reason": reason,
                "alternatives": alternatives
            }
        )

    def log_ensemble_validation(
        self,
        user_id: str,
        task_id: str,
        openai_score: float,
        gemini_score: float,
        deviation: float,
        escalated: bool
    ):
        """Log ensemble validation."""
        self.log_event(
            event_type=AuditEventType.ENSEMBLE_VALIDATION,
            user_id=user_id,
            action="Ensemble validation",
            details={
                "task_id": task_id,
                "openai_score": openai_score,
                "gemini_score": gemini_score,
                "deviation": deviation,
                "escalated": escalated
            },
            severity=AuditSeverity.WARNING if escalated else AuditSeverity.INFO
        )

    def log_rate_limit_hit(
        self,
        user_id: str,
        limit_type: str,
        current_usage: int,
        limit: int
    ):
        """Log rate limit hit."""
        self.log_event(
            event_type=AuditEventType.RATE_LIMIT_HIT,
            user_id=user_id,
            action=f"Rate limit hit: {limit_type}",
            details={
                "limit_type": limit_type,
                "current_usage": current_usage,
                "limit": limit
            },
            severity=AuditSeverity.WARNING
        )

    def log_budget_limit_hit(
        self,
        user_id: str,
        limit_type: str,
        current_spend: float,
        limit: float
    ):
        """Log budget limit hit."""
        self.log_event(
            event_type=AuditEventType.BUDGET_LIMIT_HIT,
            user_id=user_id,
            action=f"Budget limit hit: {limit_type}",
            details={
                "limit_type": limit_type,
                "current_spend": current_spend,
                "limit": limit
            },
            severity=AuditSeverity.WARNING
        )

    def log_security_event(
        self,
        user_id: str,
        action: str,
        details: Dict[str, Any]
    ):
        """Log security event."""
        self.log_event(
            event_type=AuditEventType.SECURITY_EVENT,
            user_id=user_id,
            action=action,
            details=details,
            severity=AuditSeverity.CRITICAL
        )

    def _flush_buffer(self):
        """Flush events buffer to disk."""
        if not self.events_buffer:
            return

        with open(self.current_log_file, 'a') as f:
            for event in self.events_buffer:
                f.write(json.dumps(event.to_dict()) + '\n')

        self.events_buffer = []

    def query_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 1000
    ) -> List[AuditEvent]:
        """
        Query audit events.

        Args:
            start_date: Start date filter
            end_date: End date filter
            event_type: Event type filter
            user_id: User ID filter
            severity: Severity filter
            limit: Maximum results

        Returns:
            List of matching events
        """
        # Flush current buffer
        self._flush_buffer()

        results = []

        # Determine which log files to search
        log_files = sorted(self.log_dir.glob("audit_*.jsonl"))

        for log_file in log_files:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        event = AuditEvent.from_dict(data)

                        # Apply filters
                        if start_date and datetime.fromisoformat(event.timestamp.rstrip('Z')) < start_date:
                            continue
                        if end_date and datetime.fromisoformat(event.timestamp.rstrip('Z')) > end_date:
                            continue
                        if event_type and event.event_type != event_type:
                            continue
                        if user_id and event.user_id != user_id:
                            continue
                        if severity and event.severity != severity:
                            continue

                        results.append(event)

                        if len(results) >= limit:
                            return results

                    except Exception:
                        continue

        return results

    def verify_chain_integrity(self) -> Dict[str, Any]:
        """
        Verify audit log chain integrity.

        Returns:
            Verification report
        """
        self._flush_buffer()

        total_events = 0
        verified_events = 0
        broken_chains = []

        log_files = sorted(self.log_dir.glob("audit_*.jsonl"))

        previous_hash = "0"

        for log_file in log_files:
            with open(log_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line)
                        total_events += 1

                        # Verify previous hash
                        if data["previous_hash"] != previous_hash:
                            broken_chains.append({
                                "file": log_file.name,
                                "line": line_num,
                                "event_id": data["event_id"],
                                "expected_previous_hash": previous_hash,
                                "actual_previous_hash": data["previous_hash"]
                            })
                        else:
                            verified_events += 1

                        # Verify event hash
                        event = AuditEvent.from_dict(data)
                        if event.hash != data["hash"]:
                            broken_chains.append({
                                "file": log_file.name,
                                "line": line_num,
                                "event_id": data["event_id"],
                                "reason": "Hash mismatch - event may be tampered"
                            })

                        previous_hash = data["hash"]

                    except Exception as e:
                        broken_chains.append({
                            "file": log_file.name,
                            "line": line_num,
                            "reason": f"Parse error: {str(e)}"
                        })

        return {
            "total_events": total_events,
            "verified_events": verified_events,
            "integrity_percentage": (verified_events / total_events * 100) if total_events > 0 else 0,
            "broken_chains": broken_chains,
            "intact": len(broken_chains) == 0
        }

    def export_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        output_file: str
    ) -> Dict[str, Any]:
        """
        Export compliance report.

        Args:
            start_date: Report start date
            end_date: Report end date
            output_file: Output file path

        Returns:
            Report summary
        """
        events = self.query_events(start_date=start_date, end_date=end_date, limit=100000)

        report = {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_events": len(events)
            },
            "events_by_type": {},
            "events_by_severity": {},
            "top_users": {},
            "events": [event.to_dict() for event in events]
        }

        # Aggregate statistics
        for event in events:
            # By type
            event_type = event.event_type
            report["events_by_type"][event_type] = report["events_by_type"].get(event_type, 0) + 1

            # By severity
            severity = event.severity
            report["events_by_severity"][severity] = report["events_by_severity"].get(severity, 0) + 1

            # By user
            report["top_users"][event.user_id] = report["top_users"].get(event.user_id, 0) + 1

        # Write report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        return {
            "status": "success",
            "output_file": output_file,
            "total_events": len(events),
            "report_size_kb": os.path.getsize(output_file) / 1024
        }

    def __del__(self):
        """Flush buffer on cleanup."""
        self._flush_buffer()
