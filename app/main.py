"""
Multi-LLM Risk Intelligence Platform - Streamlit UI
Main application interface for intelligent LLM routing and risk analysis
"""

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime

# Import core components
from app.models.task import Task, TaskType
from app.router import LLMRouter
from app.gateway import AIGateway
from app.services.openai_service import OpenAIService
from app.services.gemini_service import GeminiService
from app.services.ensemble_service import EnsembleService
from app.services.observability_service import ObservabilityService
from app.utils.cost_calculator import CostCalculator
from app.utils.roai_calculator import RoAICalculator


# Page configuration
st.set_page_config(
    page_title="Multi-LLM Risk Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .routing-decision {
        background-color: #e8f4f8;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .result-card {
        background-color: #f9f9f9;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin: 1rem 0;
    }
    .success-badge {
        background-color: #d4edda;
        color: #155724;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .warning-badge {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .danger-badge {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.25rem 0.75rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "gateway" not in st.session_state:
        st.session_state.gateway = AIGateway(verbose=False)

    if "router" not in st.session_state:
        st.session_state.router = LLMRouter()

    if "openai_service" not in st.session_state:
        st.session_state.openai_service = OpenAIService(st.session_state.gateway)

    if "gemini_service" not in st.session_state:
        st.session_state.gemini_service = GeminiService(st.session_state.gateway)

    if "ensemble_service" not in st.session_state:
        st.session_state.ensemble_service = EnsembleService(st.session_state.gateway)

    if "observability" not in st.session_state:
        st.session_state.observability = ObservabilityService()

    if "cost_calculator" not in st.session_state:
        st.session_state.cost_calculator = CostCalculator()

    if "roai_calculator" not in st.session_state:
        st.session_state.roai_calculator = RoAICalculator()

    if "analysis_history" not in st.session_state:
        st.session_state.analysis_history = []


def load_sample_scenarios():
    """Load sample risk scenarios from JSON file."""
    scenarios_path = Path("data/sample_risk_scenarios.json")
    if scenarios_path.exists():
        with open(scenarios_path, 'r') as f:
            return json.load(f)
    return []


def analyze_task(task: Task):
    """
    Analyze task using intelligent routing.

    Args:
        task: Task object to analyze

    Returns:
        Dictionary with analysis results
    """
    # Get routing decision
    selected_model = st.session_state.router.route(task)
    routing_details = st.session_state.router.get_routing_details(task)

    # Execute analysis based on routing
    if selected_model == "openai":
        result = st.session_state.openai_service.analyze_risk(task)
        provider = "openai"
    elif selected_model == "gemini":
        result = st.session_state.gemini_service.analyze_long_context(task)
        provider = "gemini"
    else:  # ensemble
        ensemble_result = st.session_state.ensemble_service.analyze_with_validation(task)
        result = ensemble_result["ensemble_decision"]
        result["metadata"] = ensemble_result["metadata"]
        result["ensemble_details"] = {
            "openai": ensemble_result["openai_result"],
            "gemini": ensemble_result["gemini_result"],
            "comparison": ensemble_result["comparison"]
        }
        provider = "ensemble"

        # Log ensemble request
        st.session_state.observability.log_ensemble_request(ensemble_result)

    # Log request to observability
    if provider != "ensemble":
        st.session_state.observability.log_request(
            provider=provider,
            task_type=task.task_type,
            metadata=result.get("metadata", {}),
            result=result
        )

    # Track costs
    cost = result.get("metadata", {}).get("cost", 0)
    st.session_state.cost_calculator.track_session_cost(provider, cost)

    # Track RoAI metrics (estimate manual time saved)
    manual_hours_saved = 0.25  # Assume 15 minutes saved per analysis
    st.session_state.roai_calculator.track_session_value(
        llm_cost=cost,
        manual_hours_saved=manual_hours_saved,
        requests=1
    )

    return {
        "routing": routing_details,
        "result": result,
        "provider": provider
    }


def display_routing_decision(routing_details):
    """Display routing decision with explanation."""
    st.markdown('<div class="routing-decision">', unsafe_allow_html=True)
    st.markdown("### 🎯 Routing Decision")

    col1, col2 = st.columns([1, 2])

    with col1:
        selected = routing_details["selected_model"].upper()
        if selected == "OPENAI":
            badge_class = "success-badge"
        elif selected == "GEMINI":
            badge_class = "warning-badge"
        else:
            badge_class = "danger-badge"

        st.markdown(f'<div class="{badge_class}">Selected: {selected}</div>', unsafe_allow_html=True)

    with col2:
        st.write(f"**Reason:** {routing_details['reason']}")

    # Show task characteristics
    with st.expander("📊 Task Characteristics"):
        chars = routing_details["task_characteristics"]
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Context Length", f"{chars['context_length']:,} tokens")
            st.metric("Business Impact", f"{chars['business_impact']:.0%}")

        with col2:
            st.write(f"**Strict JSON:** {'✅ Yes' if chars['requires_strict_json'] else '❌ No'}")
            st.write(f"**Multi-Document:** {'✅ Yes' if chars['multi_document'] else '❌ No'}")

        with col3:
            st.write(f"**Task Type:** {chars['task_type']}")

    st.markdown('</div>', unsafe_allow_html=True)


def display_analysis_result(result, provider):
    """Display analysis result based on provider."""
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown("### 📋 Analysis Results")

    if provider == "ensemble":
        display_ensemble_result(result)
    else:
        display_single_model_result(result, provider)

    st.markdown('</div>', unsafe_allow_html=True)


def display_single_model_result(result, provider):
    """Display result from single model (OpenAI or Gemini)."""
    # Risk score and confidence
    col1, col2, col3 = st.columns(3)

    with col1:
        risk_score = result.get("risk_score", 50)
        st.metric("Risk Score", f"{risk_score}/100")

    with col2:
        confidence = result.get("confidence", 0.5)
        st.metric("Confidence", f"{confidence:.0%}")

    with col3:
        risk_level = result.get("risk_level", "MEDIUM")
        st.metric("Risk Level", risk_level)

    # Reasoning/Analysis
    st.markdown("#### 💡 Analysis")

    if "reasoning" in result:
        st.write(result["reasoning"])
    elif "detailed_analysis" in result:
        st.write(result["detailed_analysis"])
    elif "explanation" in result:
        st.write(result["explanation"])

    # Additional details
    if "primary_concerns" in result and result["primary_concerns"]:
        with st.expander("⚠️ Primary Concerns"):
            for concern in result["primary_concerns"]:
                st.write(f"- {concern}")

    if "key_findings" in result and result["key_findings"]:
        with st.expander("🔍 Key Findings"):
            for finding in result["key_findings"]:
                st.write(f"- {finding}")

    if "recommendation" in result:
        st.info(f"**Recommendation:** {result['recommendation']}")


def display_ensemble_result(result):
    """Display ensemble validation result."""
    st.markdown("#### 🔀 Ensemble Validation")

    # Decision summary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        final_score = result.get("final_score", 50)
        st.metric("Final Score", f"{final_score}/100")

    with col2:
        confidence = result.get("confidence", 0.5)
        st.metric("Confidence", f"{confidence:.0%}")

    with col3:
        decision_type = result.get("decision_type", "UNKNOWN")
        st.metric("Decision Type", decision_type)

    with col4:
        requires_review = result.get("requires_human_review", False)
        review_status = "⚠️ YES" if requires_review else "✅ NO"
        st.metric("Human Review", review_status)

    # Reasoning
    st.write(f"**Decision Logic:** {result.get('reasoning', 'N/A')}")

    # Model comparison
    if "ensemble_details" in result:
        with st.expander("📊 Model Comparison"):
            details = result["ensemble_details"]
            comparison = details.get("comparison", {})

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**OpenAI**")
                st.write(f"Risk Score: {comparison.get('openai_score', 'N/A')}")
                st.write(f"Confidence: {comparison.get('openai_confidence', 0):.2f}")

            with col2:
                st.markdown("**Gemini**")
                st.write(f"Risk Score: {comparison.get('gemini_score', 'N/A')}")
                st.write(f"Confidence: {comparison.get('gemini_confidence', 0):.2f}")

            st.divider()
            st.write(f"**Score Deviation:** {comparison.get('score_deviation', 0):.1f} points")
            st.write(f"**Agreement:** {'✅ Yes' if comparison.get('agreement') else '❌ No'}")


def display_metrics(result):
    """Display performance metrics."""
    metadata = result.get("metadata", {})

    st.markdown("### 📈 Performance Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        latency = metadata.get("latency", 0)
        st.metric("Latency", f"{latency:.2f}s")

    with col2:
        cost = metadata.get("cost", 0)
        st.metric("Cost", f"${cost:.4f}")

    with col3:
        input_tokens = metadata.get("input_tokens", 0)
        st.metric("Input Tokens", f"{input_tokens:,}")

    with col4:
        output_tokens = metadata.get("output_tokens", 0)
        st.metric("Output Tokens", f"{output_tokens:,}")


def display_sidebar_statistics():
    """Display session statistics in sidebar."""
    st.sidebar.markdown("## 📊 Session Statistics")

    # Get dashboard metrics
    dashboard = st.session_state.observability.get_dashboard_metrics()

    # Session overview
    st.sidebar.markdown("### Overview")
    st.sidebar.metric("Total Requests", dashboard["session"]["total_requests"])
    st.sidebar.metric("Total Cost", f"${dashboard['session']['total_cost']:.4f}")

    duration_min = dashboard["session"]["duration_seconds"] / 60
    st.sidebar.metric("Session Duration", f"{duration_min:.1f} min")

    # Distribution
    st.sidebar.markdown("### Model Distribution")
    dist = dashboard["distribution"]

    if dist["openai"]["count"] > 0:
        st.sidebar.write(f"🟢 OpenAI: {dist['openai']['count']} ({dist['openai']['percentage']:.0f}%)")

    if dist["gemini"]["count"] > 0:
        st.sidebar.write(f"🟡 Gemini: {dist['gemini']['count']} ({dist['gemini']['percentage']:.0f}%)")

    if dist["ensemble"]["count"] > 0:
        st.sidebar.write(f"🔴 Ensemble: {dist['ensemble']['count']} ({dist['ensemble']['percentage']:.0f}%)")

    # RoAI
    st.sidebar.markdown("### 💰 Return on AI")
    roai_data = st.session_state.roai_calculator.get_session_roai()
    st.sidebar.metric("RoAI Multiplier", roai_data.get("roai_multiplier", "0.0x"))
    st.sidebar.metric("Net Value", f"${roai_data.get('net_value', 0):.2f}")

    # Cost breakdown
    with st.sidebar.expander("💵 Cost Breakdown"):
        perf = dashboard["performance"]
        st.write(f"**OpenAI:** ${perf['openai']['total_cost']:.4f}")
        st.write(f"**Gemini:** ${perf['gemini']['total_cost']:.4f}")
        st.write(f"**Ensemble:** ${perf['ensemble']['total_cost']:.4f}")

    # Performance
    with st.sidebar.expander("⚡ Performance"):
        st.write(f"**OpenAI Avg:** {perf['openai']['avg_latency']:.2f}s")
        st.write(f"**Gemini Avg:** {perf['gemini']['avg_latency']:.2f}s")
        if perf['ensemble']['avg_latency'] > 0:
            st.write(f"**Ensemble Avg:** {perf['ensemble']['avg_latency']:.2f}s")

    # Reset button
    if st.sidebar.button("🔄 Reset Session"):
        st.session_state.observability.reset_metrics()
        st.session_state.cost_calculator.reset_session()
        st.session_state.roai_calculator.reset_session()
        st.session_state.analysis_history = []
        st.rerun()


def main():
    """Main application function."""
    # Initialize
    initialize_session_state()

    # Header
    st.markdown('<div class="main-header">🧠 Multi-LLM Risk Intelligence Platform</div>', unsafe_allow_html=True)
    st.markdown("*Intelligent routing for optimal LLM selection based on task complexity, context, and business impact*")

    st.divider()

    # Sidebar statistics
    display_sidebar_statistics()

    # Main content
    tabs = st.tabs(["🎯 Risk Analysis", "📚 Sample Scenarios", "📊 Analytics Dashboard"])

    # Tab 1: Risk Analysis
    with tabs[0]:
        st.markdown("## Risk Analysis")

        col1, col2 = st.columns([2, 1])

        with col1:
            task_type = st.selectbox(
                "Task Type",
                options=[t.value for t in TaskType],
                format_func=lambda x: x.replace("_", " ").title()
            )

        with col2:
            temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.1)

        # Task configuration
        col1, col2, col3 = st.columns(3)

        with col1:
            business_impact = st.slider("Business Impact", 0.0, 1.0, 0.5, 0.05)

        with col2:
            context_length = st.number_input("Context Length (tokens)", 0, 200000, 1000, 1000)

        with col3:
            multi_document = st.checkbox("Multi-Document Analysis")

        requires_strict_json = st.checkbox("Require Structured JSON Output", value=True)

        # Task description
        task_description = st.text_area(
            "Task Description / Scenario",
            height=200,
            placeholder="Enter the risk scenario or task description here..."
        )

        # Analyze button
        if st.button("🚀 Analyze Risk", type="primary", use_container_width=True):
            if not task_description:
                st.error("Please enter a task description")
            else:
                with st.spinner("Analyzing..."):
                    # Create task
                    task = Task(
                        description=task_description,
                        task_type=task_type,
                        requires_strict_json=requires_strict_json,
                        context_length=context_length,
                        multi_document=multi_document,
                        business_impact=business_impact
                    )

                    # Analyze
                    analysis = analyze_task(task)

                    # Store in history
                    st.session_state.analysis_history.append({
                        "timestamp": datetime.now(),
                        "task": task,
                        "analysis": analysis
                    })

                    # Display results
                    st.success("✅ Analysis Complete!")

                    display_routing_decision(analysis["routing"])
                    display_analysis_result(analysis["result"], analysis["provider"])
                    display_metrics(analysis["result"])

    # Tab 2: Sample Scenarios
    with tabs[1]:
        st.markdown("## 📚 Sample Risk Scenarios")
        st.markdown("Pre-configured scenarios demonstrating intelligent routing")

        scenarios = load_sample_scenarios()

        if scenarios:
            for idx, scenario in enumerate(scenarios):
                with st.expander(f"{idx+1}. {scenario['name']} → Expected: {scenario['expected_model'].upper()}"):
                    st.write(f"**Description:** {scenario['description']}")
                    st.write(f"**Expected Model:** {scenario['expected_model'].upper()}")
                    st.write(f"**Reason:** {scenario['expected_reason']}")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Context:** {scenario['context_length']:,} tokens")
                    with col2:
                        st.write(f"**Impact:** {scenario['business_impact']:.0%}")
                    with col3:
                        st.write(f"**Type:** {scenario['task_type']}")

                    if st.button(f"Run Scenario {idx+1}", key=f"scenario_{idx}"):
                        with st.spinner("Analyzing scenario..."):
                            task = Task(
                                description=scenario["description"],
                                task_type=scenario["task_type"],
                                requires_strict_json=scenario["requires_strict_json"],
                                context_length=scenario["context_length"],
                                multi_document=scenario["multi_document"],
                                business_impact=scenario["business_impact"]
                            )

                            analysis = analyze_task(task)

                            st.success("✅ Scenario Analysis Complete!")
                            display_routing_decision(analysis["routing"])
                            display_analysis_result(analysis["result"], analysis["provider"])
                            display_metrics(analysis["result"])
        else:
            st.info("No sample scenarios found. Create data/sample_risk_scenarios.json to add scenarios.")

    # Tab 3: Analytics Dashboard
    with tabs[2]:
        st.markdown("## 📊 Analytics Dashboard")

        dashboard = st.session_state.observability.get_dashboard_metrics()

        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Requests", dashboard["session"]["total_requests"])

        with col2:
            st.metric("Total Cost", f"${dashboard['session']['total_cost']:.4f}")

        with col3:
            duration_min = dashboard["session"]["duration_seconds"] / 60
            st.metric("Session Duration", f"{duration_min:.1f} min")

        with col4:
            roai_data = st.session_state.roai_calculator.get_session_roai()
            st.metric("RoAI", roai_data.get("roai_multiplier", "0.0x"))

        st.divider()

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Model Distribution")
            dist = dashboard["distribution"]
            if dashboard["session"]["total_requests"] > 0:
                import plotly.graph_objects as go

                fig = go.Figure(data=[go.Pie(
                    labels=["OpenAI", "Gemini", "Ensemble"],
                    values=[dist["openai"]["count"], dist["gemini"]["count"], dist["ensemble"]["count"]],
                    marker=dict(colors=['#2ecc71', '#f39c12', '#e74c3c'])
                )])
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No requests yet")

        with col2:
            st.markdown("### Cost Breakdown")
            if dashboard["session"]["total_cost"] > 0:
                import plotly.graph_objects as go

                perf = dashboard["performance"]
                fig = go.Figure(data=[go.Bar(
                    x=["OpenAI", "Gemini", "Ensemble"],
                    y=[perf["openai"]["total_cost"], perf["gemini"]["total_cost"], perf["ensemble"]["total_cost"]],
                    marker=dict(color=['#2ecc71', '#f39c12', '#e74c3c'])
                )])
                fig.update_layout(yaxis_title="Cost ($)", height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No costs yet")

        # Performance comparison
        st.markdown("### Performance Comparison")
        perf = dashboard["performance"]

        perf_data = {
            "Model": ["OpenAI", "Gemini", "Ensemble"],
            "Avg Latency (s)": [
                perf["openai"]["avg_latency"],
                perf["gemini"]["avg_latency"],
                perf["ensemble"]["avg_latency"]
            ],
            "Total Cost ($)": [
                perf["openai"]["total_cost"],
                perf["gemini"]["total_cost"],
                perf["ensemble"]["total_cost"]
            ],
            "Total Tokens": [
                perf["openai"]["total_tokens"],
                perf["gemini"]["total_tokens"],
                0  # Ensemble doesn't track tokens directly
            ]
        }

        st.dataframe(perf_data, use_container_width=True)


if __name__ == "__main__":
    main()
