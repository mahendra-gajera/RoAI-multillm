"""
Admin Dashboard - Cross-Session Monitoring and System Health
Multi-page Streamlit admin interface
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from pathlib import Path
import json

# Import audit logger
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.audit_logger import AuditLogger, AuditEventType, AuditSeverity


st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="🔧",
    layout="wide"
)

# Initialize audit logger
if "audit_logger" not in st.session_state:
    st.session_state.audit_logger = AuditLogger()


def load_historical_metrics():
    """Load historical metrics from audit logs."""
    audit_logger = st.session_state.audit_logger

    # Query last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    events = audit_logger.query_events(
        start_date=start_date,
        end_date=end_date,
        limit=10000
    )

    return events


def main():
    st.title("🔧 Admin Dashboard")
    st.markdown("*Cross-session monitoring and system health*")

    st.divider()

    # Top-level metrics
    st.markdown("## 📊 System Overview")

    col1, col2, col3, col4 = st.columns(4)

    events = load_historical_metrics()

    with col1:
        st.metric("Total Events (30d)", f"{len(events):,}")

    with col2:
        llm_events = [e for e in events if e.event_type == AuditEventType.LLM_REQUEST]
        st.metric("LLM Requests", f"{len(llm_events):,}")

    with col3:
        error_events = [e for e in events if e.severity == AuditSeverity.ERROR]
        st.metric("Errors", f"{len(error_events):,}")

    with col4:
        unique_users = len(set(e.user_id for e in events))
        st.metric("Unique Users", unique_users)

    st.divider()

    # Tabs
    tabs = st.tabs([
        "📈 Metrics",
        "🔍 Audit Logs",
        "🛡️ Security",
        "💰 Cost Analysis",
        "⚙️ System Health"
    ])

    # Tab 1: Metrics
    with tabs[0]:
        st.markdown("### Historical Metrics")

        if not events:
            st.info("No historical data available")
        else:
            # Events over time
            df_events = pd.DataFrame([
                {
                    "timestamp": datetime.fromisoformat(e.timestamp.rstrip('Z')),
                    "event_type": e.event_type,
                    "severity": e.severity
                }
                for e in events
            ])

            # Daily events chart
            df_daily = df_events.groupby(df_events["timestamp"].dt.date).size().reset_index()
            df_daily.columns = ["Date", "Events"]

            fig = px.line(
                df_daily,
                x="Date",
                y="Events",
                title="Daily Event Volume (30 days)"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Events by type
            col1, col2 = st.columns(2)

            with col1:
                event_counts = df_events["event_type"].value_counts()
                fig = px.pie(
                    values=event_counts.values,
                    names=event_counts.index,
                    title="Events by Type"
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                severity_counts = df_events["severity"].value_counts()
                fig = px.bar(
                    x=severity_counts.index,
                    y=severity_counts.values,
                    title="Events by Severity",
                    labels={"x": "Severity", "y": "Count"}
                )
                st.plotly_chart(fig, use_container_width=True)

    # Tab 2: Audit Logs
    with tabs[1]:
        st.markdown("### Audit Log Viewer")

        col1, col2, col3 = st.columns(3)

        with col1:
            event_type_filter = st.selectbox(
                "Event Type",
                ["All"] + [t.value for t in AuditEventType]
            )

        with col2:
            severity_filter = st.selectbox(
                "Severity",
                ["All"] + [s.value for s in AuditSeverity]
            )

        with col3:
            limit = st.number_input("Max Results", 10, 1000, 100)

        # Query events
        filtered_events = events

        if event_type_filter != "All":
            filtered_events = [e for e in filtered_events if e.event_type == event_type_filter]

        if severity_filter != "All":
            filtered_events = [e for e in filtered_events if e.severity == severity_filter]

        # Display events
        st.markdown(f"**Showing {len(filtered_events[:limit])} of {len(filtered_events)} events**")

        for event in filtered_events[:limit]:
            with st.expander(f"{event.timestamp} - {event.event_type} - {event.action}"):
                st.json({
                    "Event ID": event.event_id,
                    "User ID": event.user_id,
                    "Severity": event.severity,
                    "Details": event.details,
                    "Hash": event.hash[:16] + "..."
                })

    # Tab 3: Security
    with tabs[2]:
        st.markdown("### Security Monitoring")

        # Verify chain integrity
        if st.button("Verify Audit Log Integrity"):
            with st.spinner("Verifying..."):
                result = st.session_state.audit_logger.verify_chain_integrity()

                if result["intact"]:
                    st.success(f"✅ Audit log integrity verified: {result['verified_events']} events intact")
                else:
                    st.error(f"⚠️ Integrity issues found: {len(result['broken_chains'])} broken chains")
                    st.json(result)

        # Security events
        security_events = [e for e in events if e.event_type == AuditEventType.SECURITY_EVENT]

        if security_events:
            st.warning(f"⚠️ {len(security_events)} security events detected")

            for event in security_events[:10]:
                st.error(f"**{event.timestamp}**: {event.action}")
                st.json(event.details)
        else:
            st.success("✅ No security events detected")

        # Rate limit hits
        rate_limit_events = [e for e in events if e.event_type == AuditEventType.RATE_LIMIT_HIT]

        if rate_limit_events:
            st.info(f"ℹ️ {len(rate_limit_events)} rate limit hits")

            # Group by user
            user_limits = {}
            for event in rate_limit_events:
                user = event.user_id
                user_limits[user] = user_limits.get(user, 0) + 1

            st.bar_chart(user_limits)

    # Tab 4: Cost Analysis
    with tabs[3]:
        st.markdown("### Cost Analysis")

        # Extract LLM response events with cost data
        llm_responses = [
            e for e in events
            if e.event_type == AuditEventType.LLM_RESPONSE and e.details.get("cost", 0) > 0
        ]

        if llm_responses:
            # Total cost
            total_cost = sum(e.details.get("cost", 0) for e in llm_responses)
            st.metric("Total Cost (30d)", f"${total_cost:.2f}")

            # Cost by provider
            provider_costs = {}
            for event in llm_responses:
                provider = event.details.get("provider", "unknown")
                cost = event.details.get("cost", 0)
                provider_costs[provider] = provider_costs.get(provider, 0) + cost

            col1, col2 = st.columns(2)

            with col1:
                fig = px.pie(
                    values=list(provider_costs.values()),
                    names=list(provider_costs.keys()),
                    title="Cost by Provider"
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Cost over time
                df_cost = pd.DataFrame([
                    {
                        "date": datetime.fromisoformat(e.timestamp.rstrip('Z')).date(),
                        "cost": e.details.get("cost", 0)
                    }
                    for e in llm_responses
                ])

                daily_cost = df_cost.groupby("date")["cost"].sum().reset_index()

                fig = px.line(
                    daily_cost,
                    x="date",
                    y="cost",
                    title="Daily Cost Trend"
                )
                st.plotly_chart(fig, use_container_width=True)

            # Top cost users
            user_costs = {}
            for event in llm_responses:
                user = event.user_id
                cost = event.details.get("cost", 0)
                user_costs[user] = user_costs.get(user, 0) + cost

            st.markdown("#### Top Users by Cost")
            sorted_users = sorted(user_costs.items(), key=lambda x: x[1], reverse=True)[:10]

            df_users = pd.DataFrame(sorted_users, columns=["User", "Cost"])
            df_users["Cost"] = df_users["Cost"].apply(lambda x: f"${x:.4f}")
            st.dataframe(df_users, use_container_width=True)

        else:
            st.info("No cost data available")

    # Tab 5: System Health
    with tabs[4]:
        st.markdown("### System Health")

        # Success rate
        llm_responses = [e for e in events if e.event_type == AuditEventType.LLM_RESPONSE]

        if llm_responses:
            successes = sum(1 for e in llm_responses if e.details.get("success", False))
            success_rate = (successes / len(llm_responses)) * 100

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Success Rate", f"{success_rate:.1f}%")

            with col2:
                avg_latency = sum(e.details.get("latency", 0) for e in llm_responses) / len(llm_responses)
                st.metric("Avg Latency", f"{avg_latency:.2f}s")

            with col3:
                total_tokens = sum(e.details.get("tokens", 0) for e in llm_responses)
                st.metric("Total Tokens", f"{total_tokens:,}")

            # Errors over time
            error_events = [e for e in events if e.severity == AuditSeverity.ERROR]

            if error_events:
                df_errors = pd.DataFrame([
                    {
                        "date": datetime.fromisoformat(e.timestamp.rstrip('Z')).date(),
                        "error": 1
                    }
                    for e in error_events
                ])

                daily_errors = df_errors.groupby("date")["error"].sum().reset_index()

                fig = px.bar(
                    daily_errors,
                    x="date",
                    y="error",
                    title="Daily Error Count"
                )
                st.plotly_chart(fig, use_container_width=True)

            # Recent errors
            st.markdown("#### Recent Errors")
            for event in error_events[:5]:
                st.error(f"**{event.timestamp}**: {event.action}")
                if event.details.get("error"):
                    st.code(event.details["error"])

        else:
            st.info("No response data available")

        # Export options
        st.divider()
        st.markdown("### Export Data")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Export Compliance Report"):
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                output_file = f"data/audit_logs/compliance_report_{datetime.now().strftime('%Y%m%d')}.json"

                result = st.session_state.audit_logger.export_compliance_report(
                    start_date=start_date,
                    end_date=end_date,
                    output_file=output_file
                )

                st.success(f"Report exported: {result['output_file']}")
                st.json(result)

        with col2:
            if st.button("Verify Integrity"):
                result = st.session_state.audit_logger.verify_chain_integrity()
                if result["intact"]:
                    st.success("✅ All audit logs verified")
                else:
                    st.error("⚠️ Integrity issues detected")
                st.json(result)


if __name__ == "__main__":
    main()
