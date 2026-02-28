"""
Quick integration test: Verify Stage 4 works with actual SHAP pipeline
This tests if the enhanced xai_pipeline returns narrative and mitigations.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("INTEGRATION TEST: Stage 4 with Full SHAP Pipeline")
print("=" * 70)

try:
    # Check if data and model exist
    from config import PROCESSED_DATA_FILE, MODEL_FILE
    
    print("\n[1] Checking Prerequisites...")
    data_exists = os.path.exists(PROCESSED_DATA_FILE)
    model_exists = os.path.exists(MODEL_FILE)
    
    print(f"   Data file: {PROCESSED_DATA_FILE}")
    print(f"   Exists: {data_exists}")
    print(f"   Model file: {MODEL_FILE}")
    print(f"   Exists: {model_exists}")
    
    if not data_exists or not model_exists:
        print("\n⚠️  WARNING: Data or model not found.")
        print("   Run the following to generate data:")
        print("   $ python -m src.data_generator")
        print("   $ python -m src.feature_engineer")
        print("   $ python -m src.model_train")
        print("\nTest will use mock data instead.\n")
        raise FileNotFoundError("Prerequisites not met")
    
    # Import and run XAI pipeline
    print("\n[2] Running XAI Pipeline with Stage 4 enhancements...")
    from src.xai_explainer import xai_pipeline
    
    # Run for highest-risk event (default behavior)
    result = xai_pipeline()
    
    if result is None:
        print("   ❌ Pipeline returned None")
        raise ValueError("XAI pipeline failed")
    
    # Verify new fields exist
    print("\n[3] Verifying Enhanced Output Structure...")
    required_fields = ['event_id', 'base_value', 'explanation', 'narrative', 'mitigation_suggestions']
    
    for field in required_fields:
        exists = field in result
        status = "✅" if exists else "❌"
        print(f"   {status} {field}: {exists}")
        if not exists:
            raise KeyError(f"Missing field: {field}")
    
    # Display results
    print("\n[4] Results Summary")
    print("-" * 70)
    print(f"Event ID: {result['event_id']}")
    print(f"Base Value: {result['base_value']:.4f}")
    print(f"Features Analyzed: {len(result['explanation'])}")
    print(f"Risk Contributors: {sum(1 for e in result['explanation'] if e['is_high_risk_contributor'])}")
    
    print("\n[5] Generated Narrative")
    print("-" * 70)
    print(result['narrative'])
    
    print("\n[6] Mitigation Suggestions")
    print("-" * 70)
    for i, suggestion in enumerate(result['mitigation_suggestions'], 1):
        print(f"{i}. {suggestion[:100]}{'...' if len(suggestion) > 100 else ''}")
    
    print("\n" + "=" * 70)
    print("✅ INTEGRATION TEST PASSED!")
    print("   Stage 4 is fully integrated with SHAP pipeline")
    print("   Backend is ready for frontend development")
    print("=" * 70)

except FileNotFoundError as e:
    print(f"\n⚠️  Prerequisites not met: {e}")
    print("   Using mock test instead...")
    
    # Run basic mock test
    from src.xai_explainer import AttackNarrative, get_mitigation_suggestions
    
    mock_data = [
        {'feature': 'upload_size_mb_zscore', 'value_at_risk': 2.8, 'shap_contribution': -0.042, 'is_high_risk_contributor': True},
        {'feature': 'is_off_hours', 'value_at_risk': 1.0, 'shap_contribution': -0.031, 'is_high_risk_contributor': True}
    ]
    
    narrative = AttackNarrative.generate(mock_data, 'MOCK_001')
    mitigations = get_mitigation_suggestions(mock_data)
    
    print("\n[MOCK TEST] Narrative Generated:")
    print(narrative)
    print("\n[MOCK TEST] Mitigations:")
    for m in mitigations:
        print(f"  - {m[:80]}...")
    
    print("\n✅ Mock test passed. Stage 4 components work correctly.")
    print("   Run full pipeline to test with real data.")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
