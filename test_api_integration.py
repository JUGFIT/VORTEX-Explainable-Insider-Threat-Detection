"""
Quick API Integration Test

Tests that:
1. API can import all modules
2. ProfileManager initializes correctly
3. New endpoints are accessible
"""

import sys
import os

print("="*60)
print("API INTEGRATION TEST")
print("="*60)

# Test 1: Import API module
print("\nTEST 1: Importing API module...")
try:
    # Add project root to path
    sys.path.insert(0, '.')
    
    # Try importing main (this will test all imports)
    print("   Importing src.api.main...")
    from src.api import main
    print("   ✅ API module imported successfully!")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Check new schemas exist
print("\nTEST 2: Checking new schema classes...")
try:
    assert hasattr(main, 'UserSummary'), "UserSummary schema missing"
    assert hasattr(main, 'UserBaseline'), "UserBaseline schema missing"
    assert hasattr(main, 'DivergenceAnalysis'), "DivergenceAnalysis schema missing"
    print("   ✅ All new schemas found!")
except AssertionError as e:
    print(f"   ❌ Schema check failed: {e}")
    sys.exit(1)

# Test 3: Check DataStore has profile_manager field
print("\nTEST 3: Checking DataStore has profile_manager...")
try:
    data_store = main.DataStore()
    assert hasattr(data_store, 'profile_manager'), "DataStore missing profile_manager field"
    assert data_store.profile_manager is None, "profile_manager should start as None"
    print("   ✅ DataStore properly configured!")
except AssertionError as e:
    print(f"   ❌ DataStore check failed: {e}")
    sys.exit(1)

# Test 4: Check app has new endpoints
print("\nTEST 4: Checking new API endpoints exist...")
try:
    app = main.app
    
    # Get all routes
    routes = [route.path for route in app.routes]
    
    assert "/users" in routes, "/users endpoint missing"
    assert "/users/{user_id}/baseline" in routes, "/users/{user_id}/baseline endpoint missing"
    assert "/users/{user_id}/divergence/{event_id}" in routes, "/users/{user_id}/divergence/{event_id} endpoint missing"
    
    print("   ✅ All new endpoints registered!")
    print("   Routes added:")
    print("      - GET /users")
    print("      - GET /users/{user_id}/baseline")
    print("      - GET /users/{user_id}/divergence/{event_id}")
except AssertionError as e:
    print(f"   ❌ Endpoint check failed: {e}")
    sys.exit(1)

# Test 5: Check that profile manager can initialize (with dummy data)
print("\nTEST 5: Testing ProfileManager initialization...")
try:
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # Create minimal test data
    test_data = []
    for i in range(10):
        test_data.append({
            'event_id': f'TEST_{i}',
            'user_id': 'TEST_USER',
            'timestamp': datetime.now() - timedelta(days=i),
            'file_access_count': 5,
            'upload_size_mb': 2.0,
            'anomaly_score': -0.1
        })
    
    df = pd.DataFrame(test_data)
    
    # Initialize profile manager
    from src.user_profile import initialize_profile_manager
    pm = initialize_profile_manager(df)
    
    assert pm is not None, "ProfileManager is None"
    assert len(pm.profiles) == 1, f"Expected 1 profile, got {len(pm.profiles)}"
    assert 'TEST_USER' in pm.profiles, "TEST_USER not in profiles"
    
    print("   ✅ ProfileManager initializes correctly!")
    print(f"   Created profile for {list(pm.profiles.keys())[0]}")
except Exception as e:
    print(f"   ❌ ProfileManager test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# All tests passed!
print("\n" + "="*60)
print("🎉 ALL INTEGRATION TESTS PASSED!")
print("="*60)
print("\n✅ API is ready to start!")
print("✅ New endpoints are properly registered")
print("✅ ProfileManager integration working")
print("\nNext step: Start API server and test endpoints")
print("Command: python -m src.api.main")
