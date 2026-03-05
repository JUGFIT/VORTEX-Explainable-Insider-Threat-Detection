#!/bin/bash
# =============================================================================
# VORTEX Phase 1 - Quick Verification Script
# =============================================================================
# This script verifies that Phase 1 implementation is complete and working.
# Run this before starting frontend development.
#
# Usage: bash verify_phase1.sh
# =============================================================================

echo "======================================================================"
echo "🔍 VORTEX PHASE 1 VERIFICATION"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_TOTAL=0

# Function to run test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    ((TESTS_TOTAL++))
    echo -n "[$TESTS_TOTAL] Testing: $test_name ... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

echo "Checking Python environment..."
echo "----------------------------------------------------------------------"

# Test 1: Python version
run_test "Python available" "python --version"

# Test 2: Import core modules
run_test "Core modules import" "python -c 'import pandas, numpy, sklearn, shap, fastapi'"

# Test 3: Import xai_explainer components
run_test "Stage 4 components import" "python -c 'from src.xai_explainer import AttackNarrative, get_mitigation_suggestions, get_human_readable_feature'"

# Test 4: Import API components
run_test "API components import" "python -c 'from src.api.main import app, ExplanationResponse'"

echo ""
echo "Checking file structure..."
echo "----------------------------------------------------------------------"

# Test 5: Check data files structure
run_test "Data directory exists" "test -d data"

# Test 6: Check models directory
run_test "Models directory exists" "test -d models"

# Test 7: Check src directory
run_test "Source directory exists" "test -d src"

# Test 8: Check API directory
run_test "API directory exists" "test -d src/api"

echo ""
echo "Verifying Stage 4 implementation..."
echo "----------------------------------------------------------------------"

# Test 9: Feature name mapping exists
run_test "Feature name mapping defined" "python -c 'from src.xai_explainer import FEATURE_NAME_MAP; assert len(FEATURE_NAME_MAP) > 30, \"Not enough features mapped\"'"

# Test 10: AttackNarrative class exists
run_test "AttackNarrative class defined" "python -c 'from src.xai_explainer import AttackNarrative; assert hasattr(AttackNarrative, \"generate\"), \"generate method missing\"'"

# Test 11: Mitigation function exists
run_test "Mitigation function defined" "python -c 'from src.xai_explainer import get_mitigation_suggestions; import inspect; assert callable(get_mitigation_suggestions), \"Not callable\"'"

# Test 12: API schema has narrative field
run_test "API schema includes narrative" "python -c 'from src.api.main import ExplanationResponse; assert \"narrative\" in ExplanationResponse.__fields__, \"narrative field missing\"'"

# Test 13: API schema has mitigation_suggestions field
run_test "API schema includes mitigations" "python -c 'from src.api.main import ExplanationResponse; assert \"mitigation_suggestions\" in ExplanationResponse.__fields__, \"mitigation_suggestions field missing\"'"

echo ""
echo "Testing Stage 4 functionality..."
echo "----------------------------------------------------------------------"

# Test 14: Feature name translation works
run_test "Feature name translation" "python -c 'from src.xai_explainer import get_human_readable_feature; result = get_human_readable_feature(\"upload_size_mb_zscore\"); assert \"Upload\" in result or \"upload\" in result.lower()'"

# Test 15: Narrative generation works
run_test "Narrative generation" "python -c '
from src.xai_explainer import AttackNarrative
test_data = [{\"feature\": \"upload_size_mb_zscore\", \"value_at_risk\": 3.2, \"shap_contribution\": -0.045, \"is_high_risk_contributor\": True}]
narrative = AttackNarrative.generate(test_data, \"TEST\")
assert len(narrative) > 50, \"Narrative too short\"
assert \"risk\" in narrative.lower() or \"threat\" in narrative.lower(), \"Missing risk/threat keywords\"
'"

# Test 16: Mitigation generation works
run_test "Mitigation generation" "python -c '
from src.xai_explainer import get_mitigation_suggestions
test_data = [{\"feature\": \"sensitive_file_access\", \"value_at_risk\": 2.5, \"shap_contribution\": -0.03, \"is_high_risk_contributor\": True}]
suggestions = get_mitigation_suggestions(test_data)
assert len(suggestions) >= 1, \"No suggestions generated\"
assert isinstance(suggestions, list), \"Wrong return type\"
'"

echo ""
echo "======================================================================"
echo "📊 TEST RESULTS"
echo "======================================================================"
echo ""
echo "Tests Passed: $TESTS_PASSED / $TESTS_TOTAL"
echo ""

# Determine overall status
PASS_PERCENTAGE=$((TESTS_PASSED * 100 / TESTS_TOTAL))

if [ $TESTS_PASSED -eq $TESTS_TOTAL ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "🎉 Phase 1 implementation is COMPLETE and VERIFIED!"
    echo ""
    echo "Next steps:"
    echo "  1. Start the backend: python -m src.api.main"
    echo "  2. Visit API docs: http://localhost:8000/docs"
    echo "  3. Begin frontend development"
    echo ""
    exit 0
elif [ $PASS_PERCENTAGE -ge 80 ]; then
    echo -e "${YELLOW}⚠️  MOST TESTS PASSED ($PASS_PERCENTAGE%)${NC}"
    echo ""
    echo "Phase 1 is mostly complete but some issues detected."
    echo "Review failed tests above and fix before proceeding."
    echo ""
    exit 1
else
    echo -e "${RED}❌ MULTIPLE TESTS FAILED ($PASS_PERCENTAGE%)${NC}"
    echo ""
    echo "Phase 1 implementation has significant issues."
    echo "Please review the failed tests and fix them."
    echo ""
    exit 2
fi
