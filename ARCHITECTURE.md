# 🏗️ Architecture Documentation

## Multi-LLM Risk Intelligence Platform - System Architecture

**Version**: 1.1.0
**Last Updated**: February 27, 2026
**Status**: Production Ready

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Design Decisions](#design-decisions)
7. [Scalability](#scalability)
8. [Security Architecture](#security-architecture)
9. [Deployment Architecture](#deployment-architecture)

---

## 1. System Overview

The Multi-LLM Risk Intelligence Platform is built with a **microservices-inspired architecture** that separates concerns into distinct, loosely-coupled components. The system follows **SOLID principles** and uses **dependency injection** for flexibility.

### Key Architectural Goals

1. **Modularity**: Each component has a single responsibility
2. **Extensibility**: Easy to add new LLM providers or features
3. **Observable**: Full transparency at every layer
4. **Cost-Effective**: Intelligent routing for optimal cost/performance
5. **Compliance-Ready**: Built-in audit trails and security controls

### Core Architectural Patterns

- **Gateway Pattern**: Unified interface for multiple LLM providers
- **Strategy Pattern**: Pluggable routing strategies
- **Observer Pattern**: Metrics and logging observers
- **Chain of Responsibility**: Request processing pipeline
- **Factory Pattern**: Service instantiation

---

## 2. Architecture Diagram

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       CLIENT LAYER                            │
│  ┌────────────────┐         ┌──────────────────┐            │
│  │  Streamlit UI  │         │   REST API       │            │
│  │  (Web Browser) │         │   (Future)       │            │
│  └────────┬───────┘         └────────┬─────────┘            │
└───────────┼──────────────────────────┼───────────────────────┘
            │                          │
            v                          v
┌──────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Main Application Logic                   │   │
│  │  • Task Creation & Validation                         │   │
│  │  • UI State Management                                │   │
│  │  • Session Management                                 │   │
│  └────────────────────┬─────────────────────────────────┘   │
└────────────────────────┼────────────────────────────────────┘
                         │
                         v
┌──────────────────────────────────────────────────────────────┐
│                    ROUTING LAYER                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │          LLMRouter (Intelligent Routing)           │     │
│  │                                                     │     │
│  │  Decision Matrix:                                  │     │
│  │  ├─ Strict JSON? ────────────► OpenAI            │     │
│  │  ├─ Context > 80k? ───────────► Gemini           │     │
│  │  ├─ Multi-Document? ──────────► Gemini           │     │
│  │  ├─ Business Impact > 0.8? ───► Ensemble         │     │
│  │  └─ Default ──────────────────► OpenAI           │     │
│  │                                                     │     │
│  │  • Cost Estimation                                 │     │
│  │  • Routing Explanation Generation                 │     │
│  │  • Threshold Configuration                         │     │
│  └────────────────────┬───────────────────────────────┘     │
└────────────────────────┼────────────────────────────────────┘
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
       v                 v                 v
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   OpenAI     │  │   Gemini     │  │  Ensemble    │
│   Service    │  │   Service    │  │  Service     │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                         v
┌──────────────────────────────────────────────────────────────┐
│                    GATEWAY LAYER                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │              AI Gateway (Unified Interface)         │     │
│  │                                                     │     │
│  │  ┌───────────────┐         ┌──────────────────┐  │     │
│  │  │   Basic       │         │   Advanced       │  │     │
│  │  │   Gateway     │         │   Gateway        │  │     │
│  │  │               │         │   • Caching      │  │     │
│  │  │   • OpenAI    │         │   • Rate Limit   │  │     │
│  │  │     SDK       │         │   • Budgets      │  │     │
│  │  │   • Gemini    │         │   • Dedup        │  │     │
│  │  │     SDK       │         └──────────────────┘  │     │
│  │  └───────────────┘                                │     │
│  │                                                     │     │
│  │  • Request Standardization                         │     │
│  │  • Response Normalization                          │     │
│  │  • Error Handling                                  │     │
│  │  • Token Counting                                  │     │
│  │  • Cost Calculation                                │     │
│  └────────────────────┬───────────────────────────────┘     │
└────────────────────────┼────────────────────────────────────┘
                         │
       ┌─────────────────┼─────────────────┐
       │                                   │
       v                                   v
┌──────────────┐                    ┌──────────────┐
│   OpenAI     │                    │   Google     │
│   API        │                    │   Gemini API │
│              │                    │              │
│ GPT-4o-mini  │                    │ Gemini 2.0   │
│ GPT-4o       │                    │ Flash        │
└──────────────┘                    └──────────────┘

                         │
                         v
┌──────────────────────────────────────────────────────────────┐
│                 OBSERVABILITY LAYER                           │
│  ┌────────────────────────────────────────────────────┐     │
│  │         Cross-Cutting Concerns                      │     │
│  │                                                     │     │
│  │  ┌─────────────────┐  ┌────────────────────────┐  │     │
│  │  │ Observability   │  │   Cost Calculator      │  │     │
│  │  │ Service         │  │   • Token tracking     │  │     │
│  │  │ • Metrics       │  │   • Cost computation   │  │     │
│  │  │ • Events        │  │   • Savings analysis   │  │     │
│  │  │ • Aggregation   │  └────────────────────────┘  │     │
│  │  └─────────────────┘                              │     │
│  │                                                     │     │
│  │  ┌─────────────────┐  ┌────────────────────────┐  │     │
│  │  │ Audit Logger    │  │   RoAI Calculator      │  │     │
│  │  │ • Hash chain    │  │   • ROI tracking       │  │     │
│  │  │ • Compliance    │  │   • Value measurement  │  │     │
│  │  │ • Integrity     │  └────────────────────────┘  │     │
│  │  └─────────────────┘                              │     │
│  │                                                     │     │
│  │  ┌─────────────────┐  ┌────────────────────────┐  │     │
│  │  │ Prompt Manager  │  │   Admin Dashboard      │  │     │
│  │  │ • Versioning    │  │   • Monitoring         │  │     │
│  │  │ • A/B testing   │  │   • Analytics          │  │     │
│  │  └─────────────────┘  └────────────────────────┘  │     │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                         │
                         v
┌──────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                 │
│  ┌────────────────────────────────────────────────────┐     │
│  │              Persistent Storage                     │     │
│  │                                                     │     │
│  │  • Audit Logs (JSONL, append-only)                │     │
│  │  • Prompt Versions (JSON)                          │     │
│  │  • Configuration (.env)                            │     │
│  │  • Sample Scenarios (JSON)                         │     │
│  │  • Cache (In-Memory)                               │     │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Component Details

### 3.1 Task Model (`app/models/task.py`)

**Purpose**: Domain model representing a risk analysis task

**Responsibilities**:
- Define task attributes and constraints
- Validation using Pydantic
- Type safety with enums

**Key Attributes**:
```python
- task_id: str (UUID)
- description: str (task prompt)
- requires_strict_json: bool
- context_length: int (token estimate)
- multi_document: bool
- business_impact: float (0-1)
- task_type: TaskType (enum)
```

**Design Patterns**: Domain Model, Value Object

---

### 3.2 LLM Router (`app/router.py`)

**Purpose**: Intelligent model selection engine

**Routing Algorithm**:
```
Priority 1: strict_json=true → OpenAI
Priority 2: context > 80k → Gemini
Priority 3: multi_document=true → Gemini
Priority 4: business_impact > 0.8 → Ensemble
Priority 5: Default → OpenAI
```

**Key Methods**:
- `route(task)`: Returns selected model
- `get_routing_reason(task)`: Human-readable explanation
- `get_routing_details(task)`: Full routing context
- `estimate_cost_savings(task)`: Cost comparison

**Configurability**:
- Thresholds via `.env`
- Pluggable routing strategies
- Easy to extend with new rules

**Design Patterns**: Strategy, Chain of Responsibility

---

### 3.3 AI Gateway (`app/gateway.py`)

**Purpose**: Unified interface for multiple LLM providers

**Key Features**:
- Abstraction over OpenAI and Gemini SDKs
- Standardized request/response format
- Automatic token counting
- Cost calculation
- Error handling

**Standardized Response**:
```python
{
    "success": bool,
    "content": str,
    "input_tokens": int,
    "output_tokens": int,
    "total_tokens": int,
    "cost": float,
    "model": str,
    "latency": float,
    "provider": str,
    "error": str | None
}
```

**Design Patterns**: Gateway, Adapter, Facade

---

### 3.4 OpenAI Service (`app/services/openai_service.py`)

**Purpose**: OpenAI-specific risk analysis

**Key Methods**:
- `analyze_risk()`: Risk scoring with JSON output
- `get_compliance_explanation()`: Regulatory analysis
- `detect_fraud_patterns()`: Fraud detection
- `get_metrics()`: Service statistics

**Features**:
- Structured JSON outputs
- Low temperature for deterministic results
- Metrics tracking
- Error recovery

---

### 3.5 Gemini Service (`app/services/gemini_service.py`)

**Purpose**: Gemini-specific long-context analysis

**Key Methods**:
- `analyze_long_context()`: Extended context processing
- `multi_document_correlation()`: Cross-document analysis
- `analyze_document_risk()`: Document review
- `get_metrics()`: Service statistics

**Features**:
- 100k+ token support
- Multi-document processing
- JSON parsing with fallbacks
- Markdown handling

---

### 3.6 Ensemble Service (`app/services/ensemble_service.py`)

**Purpose**: Dual-model validation for critical decisions

**Algorithm**:
1. Execute OpenAI and Gemini **in parallel**
2. Compare risk scores
3. Calculate deviation
4. Make decision:
   - High deviation (>15 pts) → Escalate to human
   - Agreement → Use higher confidence result
   - Moderate deviation → Confidence-weighted average

**Decision Types**:
- **CONSENSUS**: Models agree
- **WEIGHTED_AVERAGE**: Moderate deviation
- **ESCALATE**: High deviation (requires human review)

**Metrics**:
- Agreement rate
- Escalation rate
- Total cost (both models)

---

### 3.7 Advanced Gateway (`app/advanced_gateway.py`)

**Purpose**: Enterprise features on top of basic gateway

**Features**:

#### Caching
- In-memory cache with TTL
- Cache key generation (MD5 hash)
- Hit/miss tracking
- Cost savings calculation

#### Rate Limiting
- Token bucket algorithm
- Per-user tracking
- Minute and hour windows
- Automatic enforcement

#### Budget Controls
- Daily and monthly limits
- Pre-request validation
- Post-request tracking
- Automatic reset logic

**Design Patterns**: Decorator, Proxy

---

### 3.8 Audit Logger (`app/utils/audit_logger.py`)

**Purpose**: Tamper-proof compliance logging

**Architecture**:
```
Event 1 → Hash 1
          ↓
Event 2 → Hash 2 (includes Hash 1)
          ↓
Event 3 → Hash 3 (includes Hash 2)
          ↓
       ... (chain continues)
```

**Key Features**:
- Cryptographic hash chain (SHA-256)
- 10 event types
- Query & search
- Integrity verification
- Compliance reports (JSON export)

**Storage Format**: JSONL (JSON Lines)
- One event per line
- Append-only
- Daily rotation

---

### 3.9 Prompt Manager (`app/utils/prompt_manager.py`)

**Purpose**: Prompt versioning and A/B testing

**Features**:

#### Version Control
- Template-based prompts
- Variable substitution
- Version history
- Performance tracking per version

#### A/B Testing
- Traffic splitting
- Variant selection (consistent per user)
- Performance recording
- Statistical significance

**Storage**: JSON files in `data/prompts/`

---

### 3.10 Observability Service (`app/services/observability_service.py`)

**Purpose**: Centralized metrics aggregation

**Tracked Metrics**:
- Per-model: requests, tokens, cost, latency
- Session: total requests, cost, duration
- Ensemble: agreement rate, escalations
- Distribution: % per model

**Dashboard Data**: Prepared for Streamlit visualizations

---

## 4. Data Flow

### 4.1 Single Request Flow

```
1. User Input (Streamlit UI)
   │
   v
2. Task Creation & Validation
   │ (Pydantic validation)
   v
3. Routing Decision
   │ (LLMRouter.route())
   v
4. Service Selection
   ├─ OpenAI Service (if "openai")
   ├─ Gemini Service (if "gemini")
   └─ Ensemble Service (if "ensemble")
   │
   v
5. Gateway Call
   │ (AIGateway.call_openai/gemini)
   v
6. External API Call
   │ (OpenAI/Gemini API)
   v
7. Response Standardization
   │ (_standardize_response)
   v
8. Metrics Tracking
   │ (ObservabilityService.log_request)
   v
9. Cost Calculation
   │ (CostCalculator.track_session_cost)
   v
10. RoAI Tracking
    │ (RoAICalculator.track_session_value)
    v
11. Result Display
    │ (Streamlit UI)
    v
12. Audit Logging
    (AuditLogger.log_llm_response)
```

### 4.2 Ensemble Request Flow

```
1. Ensemble Triggered (business_impact > 0.8)
   │
   v
2. Parallel Execution
   ├─ OpenAI Analysis (async)
   └─ Gemini Analysis (async)
   │
   v
3. Results Collection
   │ (both complete)
   v
4. Comparison Analysis
   │ • Calculate score deviation
   │ • Extract confidence levels
   │ • Determine agreement
   v
5. Decision Logic
   │
   ├─ High Deviation (>15)
   │  └─► ESCALATE (human review)
   │
   ├─ Agreement
   │  └─► CONSENSUS (use higher confidence)
   │
   └─ Moderate Deviation
      └─► WEIGHTED_AVERAGE (confidence-weighted)
   │
   v
6. Aggregated Result
   │ • Final score
   │ • Risk level
   │ • Reasoning
   │ • Escalation flag
   v
7. Metrics Update
   │ • Agreement tracking
   │ • Escalation tracking
   │ • Cost aggregation
   v
8. Response to User
```

### 4.3 Caching Flow

```
1. Request Received
   │
   v
2. Generate Cache Key
   │ (MD5 hash of: provider + messages + params)
   v
3. Check Cache
   │
   ├─ Cache HIT ───► Return cached response
   │                 │
   │                 v
   │              Update hit counter
   │                 │
   │                 v
   │              Calculate cost saved
   │                 │
   │                 v
   │              Return to user
   │
   └─ Cache MISS ──► Continue to API call
                     │
                     v
                  Execute request
                     │
                     v
                  Store in cache
                     │
                     v
                  Update miss counter
                     │
                     v
                  Return to user
```

---

## 5. Technology Stack

### Core Technologies

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **UI Framework** | Streamlit | 1.31+ | Interactive web interface |
| **LLM SDK** | OpenAI Python | 2.8+ | OpenAI API integration |
| **LLM SDK** | Google Generative AI | Latest | Gemini API integration |
| **Validation** | Pydantic | 2.0+ | Data validation & typing |
| **Visualization** | Plotly | 5.18+ | Interactive charts |
| **Config** | python-dotenv | 1.0+ | Environment management |
| **HTTP** | httpx | 0.23+ | Async HTTP client |
| **Testing** | pytest | 8.0+ | Unit testing |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Container** | Docker | Containerization |
| **Orchestration** | Docker Compose | Multi-container apps |
| **Storage** | File System | Logs, prompts, config |
| **Cache** | In-Memory Dict | Response caching |

### Development Tools

| Tool | Purpose |
|------|---------|
| **Git** | Version control |
| **Virtual Environment** | Dependency isolation |
| **pip** | Package management |

---

## 6. Design Decisions

### 6.1 Why Not LiteLLM?

**Initial Plan**: Use LiteLLM for unified gateway

**Issue**: Windows Long Path limitations prevented installation

**Solution**: Direct SDK integration
- ✅ Simpler dependency tree
- ✅ Windows-compatible
- ✅ Full control over implementation
- ✅ Easier to debug
- ❌ Need to manage multiple SDKs manually

### 6.2 Why Pydantic for Task Model?

**Rationale**:
- Runtime validation
- Type safety
- Automatic documentation
- JSON serialization
- IDE support

### 6.3 Why Streamlit for UI?

**Rationale**:
- Rapid prototyping
- Python-native (no JavaScript)
- Built-in interactivity
- Easy deployment
- Good for internal tools

**Trade-offs**:
- Not ideal for public-facing apps
- Limited customization
- Session state complexity

### 6.4 Why In-Memory Caching?

**Rationale**:
- Simple implementation
- No external dependencies
- Fast access (<1ms)
- Good for POC/demo

**Trade-offs**:
- Not persistent across restarts
- Single-process only
- Memory constraints

**Production Alternative**: Redis, Memcached

### 6.5 Why JSONL for Audit Logs?

**Rationale**:
- Append-only (tamper-resistant)
- Line-by-line parsing
- Streaming support
- Standard format
- Easy to grep/analyze

**Trade-offs**:
- No indexing
- Sequential reads
- File rotation needed

**Production Alternative**: PostgreSQL, MongoDB

### 6.6 Why Cryptographic Hash Chain?

**Rationale**:
- Tamper detection
- Compliance requirement (SOC 2)
- No database needed
- Simple implementation

**How It Works**:
```
Hash(Event N) = SHA256(Event N + Hash(Event N-1))
```

Any tampering breaks the chain.

---

## 7. Scalability

### Current Limitations (v1.1)

| Component | Limit | Reason |
|-----------|-------|--------|
| **Throughput** | ~60 req/min/user | Rate limiting |
| **Concurrency** | Single process | Streamlit architecture |
| **Cache** | Memory-bound | In-memory storage |
| **Audit Logs** | File I/O bound | Append-only files |

### Scaling Strategies

#### Horizontal Scaling

```
Current: Single Streamlit Instance

Future: Load-Balanced Multi-Instance
┌─────────────┐
│ Load        │
│ Balancer    │
└──────┬──────┘
       │
   ┌───┴───┬───────┬───────┐
   v       v       v       v
 [App1] [App2] [App3] [App4]
   │       │       │       │
   └───────┴───┬───┴───────┘
               │
        ┌──────┴──────┐
        │   Shared    │
        │   Redis     │
        │   Cache     │
        └─────────────┘
```

#### Vertical Scaling

- Increase memory for larger caches
- More CPU cores for parallel requests
- Faster disk I/O for audit logs

#### Caching Strategy

**Current**: In-memory (single instance)

**Future**:
```
Level 1: In-Memory (L1 cache, <1ms)
Level 2: Redis (L2 cache, <10ms)
Level 3: API Call (>1000ms)
```

#### Database Migration

**Current**: File-based storage

**Future**:
```
Audit Logs → PostgreSQL (indexed, queryable)
Prompts → PostgreSQL (versioned, relational)
Metrics → InfluxDB (time-series)
Cache → Redis (distributed)
```

---

## 8. Security Architecture

### 8.1 Defense in Depth

```
Layer 1: Network Security
├─ HTTPS only
├─ Firewall rules
└─ Rate limiting

Layer 2: Application Security
├─ Input validation (Pydantic)
├─ API key management (.env)
├─ Budget controls
└─ Rate limiting per user

Layer 3: Data Security
├─ Audit logging (tamper-proof)
├─ No sensitive data in logs
├─ Encrypted at rest (optional)
└─ Access control (future)

Layer 4: Operational Security
├─ Regular key rotation
├─ Integrity verification
├─ Monitoring & alerts
└─ Incident response
```

### 8.2 Threat Model

| Threat | Mitigation |
|--------|-----------|
| **API Key Leakage** | Environment variables, .gitignore |
| **Cost Abuse** | Budget controls, rate limiting |
| **Log Tampering** | Cryptographic hash chain |
| **DoS Attack** | Rate limiting, timeouts |
| **Prompt Injection** | Input sanitization, validation |
| **Data Exfiltration** | Audit logging, access control |

### 8.3 Compliance Mappings

#### SOC 2 Type II
- ✅ Audit logging (Security)
- ✅ Access control framework (Security)
- ✅ Change management (Prompt versioning)
- ✅ Monitoring (Observability)
- ✅ Incident response (Alerts)

#### GDPR
- ✅ Right to erasure (Delete logs)
- ✅ Data export (Compliance reports)
- ✅ Audit trail (All requests logged)
- ✅ Consent management (Future)

#### HIPAA
- ✅ Audit controls (Complete logs)
- ✅ Integrity controls (Hash chain)
- ⚠️ Encryption at rest (Optional)
- ⚠️ BAA required (OpenAI/Google)

---

## 9. Deployment Architecture

### 9.1 Development

```
Developer Machine
├── Python 3.9+
├── Virtual Environment
├── Streamlit (localhost:8501)
├── .env (API keys)
└── Local file storage
```

### 9.2 Docker (Single Container)

```
Docker Host
└── Container: roai-multillm
    ├── Streamlit App (port 8501)
    ├── Python 3.11
    ├── All dependencies
    └── Volume mounts:
        ├── ./data → /app/data
        └── ./.env → /app/.env
```

### 9.3 Production (Future)

```
┌─────────────────────────────────────┐
│          Load Balancer               │
│         (AWS ALB / Nginx)            │
└────────────┬────────────────────────┘
             │
    ┌────────┼────────┐
    v        v        v
┌───────┐ ┌───────┐ ┌───────┐
│ App 1 │ │ App 2 │ │ App 3 │  (Auto-scaling)
└───┬───┘ └───┬───┘ └───┬───┘
    │         │         │
    └─────────┼─────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    v                   v
┌─────────┐       ┌──────────┐
│  Redis  │       │   RDS    │
│ (Cache) │       │ (Logs)   │
└─────────┘       └──────────┘
```

**Infrastructure**:
- **Compute**: AWS ECS, Google Cloud Run, or Kubernetes
- **Cache**: Redis Cluster
- **Database**: PostgreSQL (RDS)
- **Storage**: S3 for backups
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack or CloudWatch

---

## 10. Future Enhancements

### Phase 2 (v1.2)

- [ ] Claude (Anthropic) integration
- [ ] REST API layer
- [ ] Real-time alerts (Slack, Email)
- [ ] Advanced A/B testing (Bayesian)
- [ ] Cost forecasting
- [ ] Redis caching

### Phase 3 (v2.0)

- [ ] Multi-tenant architecture
- [ ] Machine learning for routing
- [ ] Anomaly detection
- [ ] Custom model fine-tuning
- [ ] GraphQL API
- [ ] Mobile app

---

## Appendix: Component Dependency Graph

```
main.py
├── router.py
│   └── models/task.py
├── gateway.py
├── services/
│   ├── openai_service.py
│   │   └── gateway.py
│   ├── gemini_service.py
│   │   └── gateway.py
│   ├── ensemble_service.py
│   │   ├── openai_service.py
│   │   └── gemini_service.py
│   └── observability_service.py
├── utils/
│   ├── cost_calculator.py
│   ├── roai_calculator.py
│   ├── prompt_manager.py
│   └── audit_logger.py
└── advanced_gateway.py
    ├── gateway.py
    ├── prompt_manager.py
    └── audit_logger.py
```

---

**Document Version**: 1.0
**Maintained By**: Architecture Team
**Next Review**: Q2 2026
