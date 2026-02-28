"""
LIVE DEMO: Understanding Unit Tests with Real Examples
This shows exactly what the tests do and why they're useful
"""

from app.router import LLMRouter
from app.models.task import Task
from app.utils.cost_calculator import CostCalculator
from app.utils.roai_calculator import RoAICalculator

print("=" * 70)
print("🎯 LIVE DEMO: Unit Test Examples")
print("=" * 70)

# ============================================================================
# EXAMPLE 1: Router Test - Does it pick the right AI model?
# ============================================================================
print("\n📍 EXAMPLE 1: Router Intelligence Test")
print("-" * 70)

router = LLMRouter()

# Test Case 1: Small task with strict JSON needed
print("\n✅ TEST 1: Small task requiring JSON format")
task1 = Task(
    description="Analyze $500 transaction - need JSON output",
    requires_strict_json=True,
    context_length=1000,
    business_impact=0.5
)

selected_model = router.route(task1)
reason = router.get_routing_reason(task1)

print(f"   Task: {task1.description}")
print(f"   Selected Model: {selected_model}")
print(f"   Reason: {reason}")
print(f"   ✅ PASS: Correctly chose OpenAI (best for JSON)" if selected_model == "openai" else "   ❌ FAIL")

# Test Case 2: Large document analysis
print("\n✅ TEST 2: Large 500-page document (120k tokens)")
task2 = Task(
    description="Analyze 500-page loan application",
    requires_strict_json=False,
    context_length=120000,  # 120k tokens - too big for OpenAI
    business_impact=0.6
)

selected_model2 = router.route(task2)
reason2 = router.get_routing_reason(task2)

print(f"   Task: {task2.description}")
print(f"   Context: {task2.context_length:,} tokens (huge!)")
print(f"   Selected Model: {selected_model2}")
print(f"   Reason: {reason2}")
print(f"   ✅ PASS: Correctly chose Gemini (2M token window)" if selected_model2 == "gemini" else "   ❌ FAIL")

# Test Case 3: High-risk wire transfer
print("\n✅ TEST 3: $500,000 wire transfer (high risk)")
task3 = Task(
    description="$500,000 international wire to new beneficiary",
    requires_strict_json=False,
    context_length=2000,
    business_impact=0.95  # Very high risk!
)

selected_model3 = router.route(task3)
reason3 = router.get_routing_reason(task3)

print(f"   Task: {task3.description}")
print(f"   Business Impact: {task3.business_impact} (CRITICAL)")
print(f"   Selected Model: {selected_model3}")
print(f"   Reason: {reason3}")
print(f"   ✅ PASS: Correctly chose Ensemble (dual validation)" if selected_model3 == "ensemble" else "   ❌ FAIL")

# ============================================================================
# EXAMPLE 2: Cost Calculator Test - Are we calculating costs correctly?
# ============================================================================
print("\n\n📍 EXAMPLE 2: Cost Calculator Accuracy Test")
print("-" * 70)

calculator = CostCalculator()

print("\n✅ TEST 4: Calculate cost for 10,000 input + 5,000 output tokens")

# OpenAI GPT-4o-mini
cost_openai = calculator.calculate_openai_cost(10000, 5000, "gpt-4o-mini")
print(f"   OpenAI GPT-4o-mini: ${cost_openai:.6f}")

# OpenAI GPT-4o (premium)
cost_gpt4o = calculator.calculate_openai_cost(10000, 5000, "gpt-4o")
print(f"   OpenAI GPT-4o:      ${cost_gpt4o:.6f} (16x more expensive)")

# Gemini Flash
cost_gemini = calculator.calculate_gemini_cost(10000, 5000, "gemini-2.0-flash")
print(f"   Gemini 2.0 Flash:   ${cost_gemini:.6f} (cheapest!)")

# Verify Gemini is cheapest
print(f"\n   ✅ PASS: Gemini is cheapest (${cost_gemini:.6f})" if cost_gemini < cost_openai else "   ❌ FAIL")

# Verify GPT-4o is most expensive
print(f"   ✅ PASS: GPT-4o is most expensive (${cost_gpt4o:.6f})" if cost_gpt4o > cost_openai and cost_gpt4o > cost_gemini else "   ❌ FAIL")

# ============================================================================
# EXAMPLE 3: RoAI Calculator Test - Are we profitable?
# ============================================================================
print("\n\n📍 EXAMPLE 3: RoAI (Return on AI Investment) Test")
print("-" * 70)

roai_calc = RoAICalculator()

print("\n✅ TEST 5: Calculate ROI for fraud detection system")
print("   Scenario: $100 LLM cost, $50,000 fraud prevented, $2,000 manual cost saved")

result = roai_calc.calculate_roai(
    llm_cost=100.0,
    fraud_prevented=50000.0,
    manual_cost_saved=2000.0
)

print(f"\n   LLM Cost:           ${result['llm_cost']}")
print(f"   Fraud Prevented:    ${result['breakdown']['fraud_prevented']:,.0f}")
print(f"   Manual Cost Saved:  ${result['breakdown']['manual_cost_saved']:,.0f}")
print(f"   Total Value:        ${result['total_value_generated']:,.0f}")
print(f"   Net Value:          ${result['net_value']:,.0f}")
print(f"   ───────────────────────────────")
print(f"   🎉 RoAI:             {result['roai_multiplier']} (Every $1 → ${result['roai']:.0f})")
print(f"   ROI Percentage:     {result['roi_percent']}%")

# Expected: (50000 + 2000 - 100) / 100 = 519
expected_roai = (50000 + 2000 - 100) / 100
actual_roai = result['roai']

print(f"\n   Expected RoAI: {expected_roai:.0f}x")
print(f"   Actual RoAI:   {actual_roai:.0f}x")
print(f"   ✅ PASS: RoAI calculation correct!" if abs(actual_roai - expected_roai) < 1 else "   ❌ FAIL")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n\n" + "=" * 70)
print("📊 SUMMARY: Why Unit Tests Matter")
print("=" * 70)
print("""
Unit tests verify that each component works correctly:

1. 🧠 ROUTER TESTS
   → Ensure AI model selection is intelligent
   → Example: High-risk tasks use Ensemble validation
   → Result: Save money + increase accuracy

2. 💰 COST CALCULATOR TESTS
   → Verify cost calculations are accurate
   → Example: Gemini is cheaper than OpenAI for same tokens
   → Result: Budget tracking works correctly

3. 📈 RoAI CALCULATOR TESTS
   → Prove AI investment is profitable
   → Example: $100 spent → $52,000 value = 519x ROI
   → Result: Show business value to executives

✅ All tests passing = System works as designed
❌ Tests failing = We found a bug before users do!
""")

print("=" * 70)
print("🎯 Run 'pytest tests/' to verify all 23 tests automatically!")
print("=" * 70)
