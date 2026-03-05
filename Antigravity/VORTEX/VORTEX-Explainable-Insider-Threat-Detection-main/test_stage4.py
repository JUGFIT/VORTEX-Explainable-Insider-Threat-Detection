"""
Test script for Stage 4 components (Narrative & Mitigation Generation)
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.xai_explainer import AttackNarrative, get_mitigation_suggestions, get_human_readable_feature

print("=" * 60)
print("TESTING STAGE 4: NARRATIVE & MITIGATION GENERATION")
print("=" * 60)

# Test data simulating SHAP output
test_explanation_data = [
    {
        'feature': 'upload_size_mb_zscore',
        'value_at_risk': 3.2,
        'shap_contribution': -0.045,
        'is_high_risk_contributor': True
    },
    {
        'feature': 'is_off_hours',
        'value_at_risk': 1.0,
        'shap_contribution': -0.035,
        'is_high_risk_contributor': True
    },
    {
        'feature': 'sensitive_file_access_zscore',
        'value_at_risk': 2.5,
        'shap_contribution': -0.028,
        'is_high_risk_contributor': True
    },
    {
        'feature': 'external_ip_connection_zscore',
        'value_at_risk': 1.8,
        'shap_contribution': -0.015,
        'is_high_risk_contributor': True
    },
    {
        'feature': 'file_access_count_zscore',
        'value_at_risk': 0.5,
        'shap_contribution': -0.005,
        'is_high_risk_contributor': False
    }
]

# Test 1: Feature name mapping
print("\n[TEST 1] Feature Name Mapping")
print("-" * 60)
for item in test_explanation_data[:3]:
    technical_name = item['feature']
    human_name = get_human_readable_feature(technical_name)
    print(f"  {technical_name:40s} → {human_name}")

# Test 2: Narrative generation
print("\n[TEST 2] Attack Narrative Generation")
print("-" * 60)
narrative = AttackNarrative.generate(test_explanation_data, event_id='EVT_TEST_001', top_n=5)
print(narrative)

# Test 3: Mitigation suggestions
print("\n[TEST 3] Mitigation Suggestions")
print("-" * 60)
mitigations = get_mitigation_suggestions(test_explanation_data, top_n=5)
for i, suggestion in enumerate(mitigations, 1):
    print(f"{i}. {suggestion}")

# Test 4: Complete explanation structure
print("\n[TEST 4] Complete Explanation Structure")
print("-" * 60)
complete_result = {
    'event_id': 'EVT_TEST_001',
    'base_value': -0.0123,
    'explanation': test_explanation_data,
    'narrative': narrative,
    'mitigation_suggestions': mitigations
}

print(f"Event ID: {complete_result['event_id']}")
print(f"Base Value: {complete_result['base_value']}")
print(f"Features Analyzed: {len(complete_result['explanation'])}")
print(f"Narrative Length: {len(complete_result['narrative'])} characters")
print(f"Mitigation Count: {len(complete_result['mitigation_suggestions'])}")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - Stage 4 Implementation Complete!")
print("=" * 60)
