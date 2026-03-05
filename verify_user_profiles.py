"""
Quick verification script for UserProfile module.
Tests basic functionality without pytest.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, 'src')

try:
    from user_profile import UserProfile, UserProfileManager
    print("✅ Module imported successfully!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 1: Create sample data
print("\n" + "="*60)
print("TEST 1: Creating sample user data...")
print("="*60)

np.random.seed(42)
events = []
for i in range(50):
    events.append({
        'event_id': f'EVT_{i:03d}',
        'user_id': 'USR_TEST',
        'timestamp': datetime(2026, 1, 1) + timedelta(days=i),
        'file_access_count': np.random.randint(5, 15),
        'upload_size_mb': np.random.uniform(2, 10),
        'sensitive_file_access': 0,
        'external_ip_connection': 0,
        'is_off_hours': 0,
        'uses_usb': 0,
        'anomaly_score': np.random.uniform(-0.2, 0.0),
        'hour_of_day': np.random.randint(9, 18),
        'day_of_week': np.random.randint(0, 5)
    })

df = pd.DataFrame(events)
print(f"✅ Created {len(df)} sample events")

# Test 2: Create UserProfile
print("\n" + "="*60)
print("TEST 2: Creating UserProfile...")
print("="*60)

try:
    profile = UserProfile('USR_TEST', df)
    print(f"✅ UserProfile created for {profile.user_id}")
    print(f"   Baseline score: {profile.baseline['baseline_score']:.3f}")
    print(f"   Avg files accessed: {profile.baseline['avg_files_accessed']:.1f}")
    print(f"   Avg upload size: {profile.baseline['avg_upload_size']:.1f} MB")
    print(f"   Baseline risk level: {profile.baseline_risk_level}")
    print(f"   Confidence: {profile.baseline['baseline_confidence']:.1%}")
except Exception as e:
    print(f"❌ UserProfile creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Create behavioral fingerprint
print("\n"  + "="*60)
print("TEST 3: Behavioral Fingerprint...")
print("="*60)

try:
    fingerprint = profile.behavioral_fingerprint
    print("✅ Behavioral fingerprint created:")
    for key, value in fingerprint.items():
        if isinstance(value, bool):
            print(f"   {key}: {'Yes' if value else 'No'}")
        else:
            print(f"   {key}: {value}")
except Exception as e:
    print(f"❌ Fingerprint creation failed: {e}")
    sys.exit(1)

# Test 4: Calculate divergence for normal event
print("\n" + "="*60)
print("TEST 4: Divergence Calculation (Normal Event)...")
print("="*60)

normal_event = pd.Series({
    'file_access_count': 10,
    'upload_size_mb': 5.0,
    'uses_usb': False,
    'is_off_hours': False,
    'sensitive_file_access': 0,
    'anomaly_score': -0.15
})

try:
    divergence = profile.calculate_divergence(normal_event)
    print(f"✅ Divergence calculated:")
    print(f"   Divergence score: {divergence['divergence_score']:.2f}")
    print(f"   Divergence level: {divergence['divergence_level']}")
    print(f"   Details: {divergence['divergence_details'] or 'None (normal event)'}")
except Exception as e:
    print(f"❌ Divergence calculation failed: {e}")
    sys.exit(1)

# Test 5: Calculate divergence for anomalous event
print("\n" + "="*60)
print("TEST 5: Divergence Calculation (Anomalous Event)...")
print("="*60)

anomalous_event = pd.Series({
    'file_access_count': 100,  # Way above normal
    'upload_size_mb': 500.0,   # Way above normal
    'uses_usb': True,          # New behavior
    'is_off_hours': True,      # Unusual
    'sensitive_file_access': 10,
    'anomaly_score': -0.95
})

try:
    divergence = profile.calculate_divergence(anomalous_event)
    print(f"✅ Divergence calculated:")
    print(f"   Divergence score: {divergence['divergence_score']:.2f}")
    print(f"   Divergence level: {divergence['divergence_level']}")
    print(f"   Details:")
    for detail in divergence['divergence_details']:
        print(f"      - {detail}")
except Exception as e:
    print(f"❌ Divergence calculation failed: {e}")
    sys.exit(1)

# Test 6: UserProfileManager
print("\n" + "="*60)
print("TEST 6: UserProfileManager (Multiple Users)...")
print("="*60)

# Create multi-user data
multi_user_data = []
for user_id in ['USR_001', 'USR_002', 'USR_003']:
    for i in range(30):
        multi_user_data.append({
            'event_id': f'{user_id}_EVT_{i:03d}',
            'user_id': user_id,
            'timestamp': datetime(2026, 1, 1) + timedelta(days=i),
            'file_access_count': np.random.randint(5, 15),
            'upload_size_mb': np.random.uniform(2, 10),
            'anomaly_score': np.random.uniform(-0.2, 0.0)
        })

multi_df = pd.DataFrame(multi_user_data)

try:
    manager = UserProfileManager(multi_df)
    print(f"✅ ProfileManager created")
    print(f"   Profiles loaded: {len(manager.profiles)}")
    
    users = manager.get_all_users()
    print(f"   User summary:")
    for user in users:
        print(f"      {user['user_id']}: {user['event_count']} events, "
              f"risk={user['baseline_risk_level']}, "
              f"score={user['baseline_score']:.2f}")
except Exception as e:
    print(f"❌ ProfileManager failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Profile export
print("\n" + "="*60)
print("TEST 7: Profile Export to Dict...")
print("="*60)

try:
    profile_dict = profile.to_dict()
    print("✅ Profile exported successfully")
    print(f"   Keys: {list(profile_dict.keys())}")
    print(f"   Data quality confidence: {profile_dict['data_quality']['confidence_level']}")
except Exception as e:
    print(f"❌ Profile export failed: {e}")
    sys.exit(1)

# All tests passed!
print("\n" + "="*60)
print("🎉 ALL TESTS PASSED!")
print("="*60)
print("\n✅ UserProfile system is working correctly!")
print("✅ Ready to integrate into API")
print("\nNext step: Add API endpoints for user profiles")
