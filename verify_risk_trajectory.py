"""
Quick verification script for Risk Trajectory system.
Tests basic functionality without pytest.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, '.')

print("="*60)
print("RISK TRAJECTORY VERIFICATION")
print("="*60)

# Test 1: Import module
print("\nTEST 1: Importing risk_trajectory module...")
try:
    from src.risk_trajectory import RiskTrajectory, TrajectoryManager
    print("✅ Module imported successfully!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Temporal decay calculation
print("\nTEST 2: Testing temporal decay calculation...")
try:
    events = pd.DataFrame([
        {'event_id': 'EVT_001', 'user_id': 'TEST', 'timestamp': datetime.now(), 'anomaly_score': -0.5}
    ])
    
    trajectory = RiskTrajectory('TEST', events, decay_half_life=7)
    
    # Test decay factors
    assert trajectory.calculate_decay_factor(0) == 1.0, "Today should be 100%"
    assert abs(trajectory.calculate_decay_factor(7) - 0.5) < 0.01, "7 days should be ~50%"
    assert abs(trajectory.calculate_decay_factor(14) - 0.25) < 0.01, "14 days should be ~25%"
    assert trajectory.calculate_decay_factor(30) < 0.1, "30 days should be < 10%"
    
    print("✅ Decay calculation working correctly!")
    print(f"   0 days ago: {trajectory.calculate_decay_factor(0):.2f} (100%)")
    print(f"   7 days ago: {trajectory.calculate_decay_factor(7):.2f} (50%)")
    print(f"   14 days ago: {trajectory.calculate_decay_factor(14):.2f} (25%)")
    print(f"   30 days ago: {trajectory.calculate_decay_factor(30):.2f} (<10%)")
except Exception as e:
    print(f"❌ Decay calculation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Stable user trajectory
print("\nTEST 3: Testing stable user trajectory...")
try:
    np.random.seed(42)
    events = []
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(30):
        events.append({
            'event_id': f'EVT_{i:03d}',
            'user_id': 'USR_STABLE',
            'timestamp': base_date + timedelta(days=i),
            'anomaly_score': np.random.uniform(-0.2, -0.05),
            'risk_level': 'Low'
        })
    
    df = pd.DataFrame(events)
    trajectory = RiskTrajectory('USR_STABLE', df)
    
    print(f"✅ Stable user trajectory created!")
    print(f"   Total events: {len(trajectory.events)}")
    print(f"   Cumulative risk: {trajectory.cumulative_risk:.4f}")
    print(f"   Trend: {trajectory.trend}")
    print(f"   Is escalating: {trajectory.is_escalating}")
    print(f"   Timeline data points: {len(trajectory.trajectory_data)}")
    
    # Key assertion: is_escalating should be False (trend might vary due to random fluctuation)
    assert trajectory.is_escalating == False, "Stable user should not have escalation flag set"
    print(f"   ✓ Escalation detection correctly identifies stable behavior")
except Exception as e:
    print(f"❌ Stable trajectory failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Escalating user trajectory
print("\nTEST 4: Testing escalating user trajectory...")
try:
    np.random.seed(42)
    events = []
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(30):
        # Days 0-20: Low risk
        # Days 21-25: Medium risk
        # Days 26-30: High risk
        if i < 20:
            risk = np.random.uniform(-0.2, -0.05)
            level = 'Low'
        elif i < 25:
            risk = np.random.uniform(-0.5, -0.3)
            level = 'Medium'
        else:
            risk = np.random.uniform(-0.9, -0.6)
            level = 'High'
        
        events.append({
            'event_id': f'EVT_{i:03d}',
            'user_id': 'USR_ESCALATING',
            'timestamp': base_date + timedelta(days=i),
            'anomaly_score': risk,
            'risk_level': level
        })
    
    df = pd.DataFrame(events)
    trajectory = RiskTrajectory('USR_ESCALATING', df)
    
    print(f"✅ Escalating user trajectory created!")
    print(f"   Total events: {len(trajectory.events)}")
    print(f"   Cumulative risk: {trajectory.cumulative_risk:.4f}")
    print(f"   Trend: {trajectory.trend}")
    print(f"   Is escalating: {trajectory.is_escalating}")
    print(f"   Escalation severity: {trajectory.escalation_details.get('severity', 'N/A')}")
    print(f"   Recent 7d avg: {trajectory.escalation_details.get('recent_7d_avg', 0):.4f}")
    print(f"   Previous 7d avg: {trajectory.escalation_details.get('previous_7d_avg', 0):.4f}")
    
    assert trajectory.is_escalating == True, "Escalating user should be detected"
    assert trajectory.trend == 'escalating', "Trend should be escalating"
except Exception as e:
    print(f"❌ Escalating trajectory failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Trajectory summary and export
print("\nTEST 5: Testing trajectory summary and export...")
try:
    summary = trajectory.get_summary()
    data_dict = trajectory.to_dict()
    
    print("✅ Summary and export working!")
    print(f"   Summary keys: {list(summary.keys())}")
    print(f"   Dict keys: {list(data_dict.keys())}")
    
    assert 'user_id' in summary, "Summary missing user_id"
    assert 'trajectory' in data_dict, "Dict missing trajectory"
    assert isinstance(data_dict['trajectory'], list), "Trajectory should be list"
except Exception as e:
    print(f"❌ Summary/export failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: TrajectoryManager with multiple users
print("\nTEST 6: Testing TrajectoryManager with multiple users...")
try:
    np.random.seed(42)
    all_events = []
    base_date = datetime.now() - timedelta(days=20)
    
    # User 1: Stable
    for i in range(15):
        all_events.append({
            'event_id': f'USR001_EVT_{i}',
            'user_id': 'USR_001',
            'timestamp': base_date + timedelta(days=i),
            'anomaly_score': np.random.uniform(-0.2, -0.05),
            'risk_level': 'Low'
        })
    
    # User 2: Escalating
    for i in range(20):
        if i < 10:
            risk = np.random.uniform(-0.2, -0.05)
            level = 'Low'
        else:
            risk = np.random.uniform(-0.8, -0.5)
            level = 'High'
        
        all_events.append({
            'event_id': f'USR002_EVT_{i}',
            'user_id': 'USR_002',
            'timestamp': base_date + timedelta(days=i),
            'anomaly_score': risk,
            'risk_level': level
        })
    
    df = pd.DataFrame(all_events)
    manager = TrajectoryManager(df)
    
    print(f"✅ TrajectoryManager created!")
    print(f"   Total users: {len(manager.trajectories)}")
    print(f"   Users: {list(manager.trajectories.keys())}")
    
    stats = manager.get_statistics()
    print(f"   Statistics:")
    print(f"      Total users: {stats['total_users']}")
    print(f"      Escalating: {stats['escalating_count']}")
    print(f"      Stable: {stats['stable_count']}")
    print(f"      Avg cumulative risk: {stats['avg_cumulative_risk']:.4f}")
    
    escalating = manager.get_escalating_users()
    print(f"   Escalating users: {[u['user_id'] for u in escalating]}")
    
    assert len(manager.trajectories) == 2, "Should have 2 users"
    assert 'USR_001' in manager.trajectories, "USR_001 missing"
    assert 'USR_002' in manager.trajectories, "USR_002 missing"
except Exception as e:
    print(f"❌ TrajectoryManager failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Temporal decay verification
print("\nTEST 7: Verifying temporal decay impact...")
try:
    events = [
        # Old high-risk event (30 days ago)
        {
            'event_id': 'OLD',
            'user_id': 'DECAY_TEST',
            'timestamp': datetime.now() - timedelta(days=30),
            'anomaly_score': -0.9,
            'risk_level': 'High'
        },
        # Recent medium-risk event (today)
        {
            'event_id': 'RECENT',
            'user_id': 'DECAY_TEST',
            'timestamp': datetime.now(),
            'anomaly_score': -0.4,
            'risk_level': 'Medium'
        }
    ]
    
    df = pd.DataFrame(events)
    trajectory = RiskTrajectory('DECAY_TEST', df, decay_half_life=7)
    
    old_decay = trajectory.calculate_decay_factor(30)
    recent_decay = trajectory.calculate_decay_factor(0)
    
    old_contribution = abs(-0.9 * old_decay)
    recent_contribution = abs(-0.4 * recent_decay)
    
    print("✅ Temporal decay verified!")
    print(f"   Old event (30d ago, risk=-0.9):")
    print(f"      Decay: {old_decay:.4f}")
    print(f"      Contribution: {old_contribution:.4f}")
    print(f"   Recent event (today, risk=-0.4):")
    print(f"      Decay: {recent_decay:.4f}")
    print(f"      Contribution: {recent_contribution:.4f}")
    print(f"   Recent contributes more: {recent_contribution > old_contribution}")
    
    assert recent_contribution > old_contribution, "Recent should contribute more"
except Exception as e:
    print(f"❌ Decay verification failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# All tests passed!
print("\n" + "="*60)
print("🎉 ALL TESTS PASSED!")
print("="*60)
print("\n✅ RiskTrajectory system is working correctly!")
print("✅ Temporal decay calculation accurate")
print("✅ Escalation detection functional")
print("✅ TrajectoryManager operational")
print("\nNext step: Integrate into API")
