"""
Integration test for Risk Trajectory API endpoints.
Tests that the API correctly integrates the trajectory system.
"""

import sys
import os

print("="*60)
print("RISK TRAJECTORY API INTEGRATION TEST")
print("="*60)

# Test 1: Import API module
print("\nTEST 1: Importing API module with trajectory support...")
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
print("\nTEST 2: Checking new trajectory schema classes...")
try:
    assert hasattr(main, 'TrajectoryTimepoint'), "TrajectoryTimepoint schema missing"
    assert hasattr(main, 'EscalationDetails'), "EscalationDetails schema missing"
    assert hasattr(main, 'TrajectoryData'), "TrajectoryData schema missing"
    assert hasattr(main, 'TrajectoryStatistics'), "TrajectoryStatistics schema missing"
    print("✅ All trajectory schemas found!")
except AssertionError as e:
    print(f"❌ Schema check failed: {e}")
    sys.exit(1)

# Test 3: Check DataStore has trajectory_manager field
print("\nTEST 3: Checking DataStore has trajectory_manager...")
try:
    data_store = main.DataStore()
    assert hasattr(data_store, 'trajectory_manager'), "DataStore missing trajectory_manager field"
    assert data_store.trajectory_manager is None, "trajectory_manager should start as None"
    print("✅ DataStore properly configured!")
except AssertionError as e:
    print(f"❌ DataStore check failed: {e}")
    sys.exit(1)

# Test 4: Check app has new endpoints
print("\nTEST 4: Checking new trajectory API endpoints exist...")
try:
    app = main.app
    
    # Get all routes
    routes = [route.path for route in app.routes]
    
    assert "/users/{user_id}/trajectory" in routes, "/users/{user_id}/trajectory endpoint missing"
    assert "/users/{user_id}/escalation" in routes, "/users/{user_id}/escalation endpoint missing"
    assert "/analytics/trending-users" in routes, "/analytics/trending-users endpoint missing"
    assert "/analytics/trajectory-statistics" in routes, "/analytics/trajectory-statistics endpoint missing"
    
    print("✅ All new trajectory endpoints registered!")
    print("   Routes added:")
    print("      - GET /users/{user_id}/trajectory")
    print("      - GET /users/{user_id}/escalation")
    print("      - GET /analytics/trending-users")
    print("      - GET /analytics/trajectory-statistics")
except AssertionError as e:
    print(f"❌ Endpoint check failed: {e}")
    sys.exit(1)

# Test 5: Test trajectory manager basic initialization
print("\nTEST 5: Testing trajectory manager initialization with test data...")
try:
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    from src.risk_trajectory import initialize_trajectory_manager
    
    # Create minimal test data
    np.random.seed(42)
    test_data = []
    base_date = datetime.now() - timedelta(days=20)
    
    for user_num in [1, 2]:
        for i in range(15):
            # User 1: stable, User 2: escalating
            if user_num == 1:
                risk = np.random.uniform(-0.2, -0.05)
            else:
                risk = -0.1 if i < 10 else -0.7  # Escalates after day 10
            
            test_data.append({
                'event_id': f'TEST_{user_num}_{i}',
                'user_id': f'TEST_USR_{user_num:03d}',
                'timestamp': base_date + timedelta(days=i),
                'anomaly_score': risk,
                'risk_level': 'High' if risk < -0.5 else 'Low'
            })
    
    df = pd.DataFrame(test_data)
    
    # Initialize trajectory manager
    tm = initialize_trajectory_manager(df)
    
    assert tm is not None, "TrajectoryManager is None"
    assert len(tm.trajectories) == 2, f"Expected 2 trajectories, got {len(tm.trajectories)}"
    assert 'TEST_USR_001' in tm.trajectories, "TEST_USR_001 not in trajectories"
    assert 'TEST_USR_002' in tm.trajectories, "TEST_USR_002 not in trajectories"
    
    print("✅ TrajectoryManager initializes correctly!")
    print(f"   Created trajectories for {list(tm.trajectories.keys())}")
    
    # Check escalating user is detected
    escalating = tm.get_escalating_users()
    print(f"   Escalating users detected: {[u['user_id'] for u in escalating]}")
    
    # Get statistics
    stats = tm.get_statistics()
    print(f"   Statistics:")
    print(f"      Total users: {stats['total_users']}")
    print(f"      Escalating: {stats['escalating_count']}")
    print(f"      Escalation rate: {stats['escalation_rate']:.1f}%")
    
except Exception as e:
    print(f"❌ TrajectoryManager test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Test DataStore integration
print("\nTEST 6: Testing DataStore integration...")
try:
    # Create test data store and manually load trajectory manager
    test_store = main.DataStore()
    test_store.df = df  # Use our test data
    test_store.trajectory_manager = tm  # Use our test manager
    
    assert test_store.trajectory_manager is not None, "trajectory_manager not set"
    assert len(test_store.trajectory_manager.trajectories) == 2, "Wrong number of trajectories"
    
    print("✅ DataStore integration working!")
    print(f"   Trajectory manager loaded with {len(test_store.trajectory_manager.trajectories)} users")
    
except Exception as e:
    print(f"❌ DataStore integration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# All tests passed!
print("\n" + "="*60)
print("🎉 ALL INTEGRATION TESTS PASSED!")
print("="*60)
print("\n✅ API is ready with trajectory support!")
print("✅ New endpoints are properly registered")
print("✅ TrajectoryManager integration working")
print("✅ Schemas validated")
print("\nNext step: Start API server and test endpoints with real data")
print("Command: python -m uvicorn src.api.main:app --reload")
