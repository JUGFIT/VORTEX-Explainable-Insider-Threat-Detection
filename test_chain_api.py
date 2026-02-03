"""
Integration test for Event Chain API endpoints.
Tests that the API correctly integrates the chain detection system.
"""

import sys
import os

print("="*60)
print("EVENT CHAIN API INTEGRATION TEST")
print("="*60)

# Test 1: Import API module
print("\nTEST 1: Importing API module with chain support...")
try:
    sys.path.insert(0, '.')
    from src.api import main
    print("✅ API module imported successfully!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Check new schemas exist
print("\nTEST 2: Checking new chain schema classes...")
try:
    assert hasattr(main, 'ChainEvent'), "ChainEvent schema missing"
    assert hasattr(main, 'EventChain'), "EventChain schema missing"
    assert hasattr(main, 'ChainSummary'), "ChainSummary schema missing"
    assert hasattr(main, 'ChainStatistics'), "ChainStatistics schema missing"
    print("✅ All chain schemas found!")
except AssertionError as e:
    print(f"❌ Schema check failed: {e}")
    sys.exit(1)

# Test 3: Check DataStore has chain_manager field
print("\nTEST 3: Checking DataStore has chain_manager...")
try:
    data_store = main.DataStore()
    assert hasattr(data_store, 'chain_manager'), "DataStore missing chain_manager field"
    assert data_store.chain_manager is None, "chain_manager should start as None"
    print("✅ DataStore properly configured!")
except AssertionError as e:
    print(f"❌ DataStore check failed: {e}")
    sys.exit(1)

# Test 4: Check app has new endpoints
print("\nTEST 4: Checking new chain API endpoints exist...")
try:
    app = main.app
    
    # Get all routes
    routes = [route.path for route in app.routes]
    
    assert "/users/{user_id}/chains" in routes, "/users/{user_id}/chains endpoint missing"
    assert "/users/{user_id}/chains/summary" in routes, "/users/{user_id}/chains/summary endpoint missing"
    assert "/analytics/chains" in routes, "/analytics/chains endpoint missing"
    assert "/analytics/chain-statistics" in routes, "/analytics/chain-statistics endpoint missing"
    
    print("✅ All new chain endpoints registered!")
    print("   Routes added:")
    print("      - GET /users/{user_id}/chains")
    print("      - GET /users/{user_id}/chains/summary")
    print("      - GET /analytics/chains")
    print("      - GET /analytics/chain-statistics")
except AssertionError as e:
    print(f"❌ Endpoint check failed: {e}")
    sys.exit(1)

# Test 5: Test chain manager initialization with test data
print("\nTEST 5: Testing chain manager initialization with test data...")
try:
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    from src.event_chains import initialize_chain_detector
    
    # Create test data with a known chain
    events = []
    base_date = datetime.now() - timedelta(days=1)
    
    # Exfiltration chain
    events.append({
        'event_id': 'EVT_001', 'user_id': 'USR_ATK', 'timestamp': base_date,
        'hour_of_day': 2, 'is_off_hours': True, 'file_access_count': 5, 'upload_size_mb': 1.0, 'anomaly_score': -0.3, 'risk_level': 'Medium'
    })
    events.append({
        'event_id': 'EVT_002', 'user_id': 'USR_ATK', 'timestamp': base_date + timedelta(minutes=30),
        'hour_of_day': 2, 'is_off_hours': True, 'file_access_count': 100, 'upload_size_mb': 1.0, 'anomaly_score': -0.5, 'risk_level': 'High'
    })
    events.append({
        'event_id': 'EVT_003', 'user_id': 'USR_ATK', 'timestamp': base_date + timedelta(hours=1),
        'hour_of_day': 3, 'is_off_hours': True, 'file_access_count': 5, 'upload_size_mb': 500.0, 'anomaly_score': -0.8, 'risk_level': 'High'
    })
    
    df = pd.DataFrame(events)
    
    # Initialize
    cm = initialize_chain_detector(df)
    
    assert cm is not None
    assert len(cm.get_all_chains()) >= 1
    
    print("✅ ChainManager initializes correctly!")
    print(f"   Detected {len(cm.get_all_chains())} chains")
    
except Exception as e:
    print(f"❌ ChainManager test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# All tests passed!
print("\n" + "="*60)
print("🎉 ALL INTEGRATION TESTS PASSED!")
print("="*60)
print("\n✅ API is ready with Event Chain support!")
