"""
Unit Tests for User Profile System

Tests the UserProfile and UserProfileManager classes for:
- Baseline calculation
- Behavioral fingerprinting
- Divergence detection
- Profile management

Author: VORTEX Team
Phase: 2A - Core Infrastructure
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.user_profile import UserProfile, UserProfileManager, initialize_profile_manager


class TestUserProfile:
    """Test suite for UserProfile class."""
    
    @pytest.fixture
    def sample_user_events(self):
        """Create sample historical events for testing."""
        np.random.seed(42)
        
        # Generate 100 events for a single user
        events = []
        base_date = datetime(2026, 1, 1)
        
        for i in range(100):
            # Most events are normal
            is_normal = i < 80  # 80% normal, 20% anomalous
            
            event = {
                'event_id': f'EVT_{i:03d}',
                'user_id': 'USR_TEST',
                'timestamp': base_date + timedelta(days=i // 3, hours=np.random.randint(9, 18)),
                'file_access_count': np.random.randint(3, 12) if is_normal else np.random.randint(30, 80),
                'upload_size_mb': np.random.uniform(1, 10) if is_normal else np.random.uniform(100, 500),
                'sensitive_file_access': 0 if is_normal else 1,
                'external_ip_connection': 0,
                'is_off_hours': 0 if is_normal else 1,
                'uses_usb': 0,
                'anomaly_score': np.random.uniform(-0.2, 0.0) if is_normal else np.random.uniform(-0.9, -0.5),
                'hour_of_day': np.random.randint(9, 18) if is_normal else np.random.randint(20, 24),
                'day_of_week': np.random.randint(0, 5) if is_normal else np.random.randint(5, 7)
            }
            events.append(event)
        
        return pd.DataFrame(events)
    
    def test_baseline_calculation_normal_user(self, sample_user_events):
        """Test baseline calculation for a user with normal history."""
        profile = UserProfile('USR_TEST', sample_user_events)
        
        baseline = profile.baseline
        
        # Check that baseline exists
        assert baseline is not None
        assert 'avg_files_accessed' in baseline
        assert 'avg_upload_size' in baseline
        assert 'baseline_score' in baseline
        
        # Baseline should be calculated from normal events only
        # Normal events have lower file access (3-12 range)
        assert baseline['avg_files_accessed'] < 15, "Baseline should exclude anomalous events"
        
        # Normal events have smaller uploads (1-10 MB)
        assert baseline['avg_upload_size'] < 15, "Baseline should use normal upload sizes"
        
        # Check confidence
        assert baseline['baseline_confidence'] > 0.5, "Should have decent confidence with 100 events"
    
    def test_baseline_calculation_insufficient_data(self):
        """Test baseline with very few events."""
        # Only 5 events
        events = pd.DataFrame([
            {
                'event_id': f'EVT_{i}',
                'user_id': 'USR_NEW',
                'timestamp': datetime(2026, 1, i+1),
                'file_access_count': 5,
                'upload_size_mb': 2.0,
                'anomaly_score': -0.1
            }
            for i in range(5)
        ])
        
        profile = UserProfile('USR_NEW', events)
        
        # Should still create baseline, but with low confidence
        assert profile.baseline['baseline_confidence'] < 0.1
        assert profile.baseline['historical_event_count'] == 5
    
    def test_baseline_risk_categorization(self, sample_user_events):
        """Test baseline risk level categorization."""
        profile = UserProfile('USR_TEST', sample_user_events)
        
        # Most events are normal, so baseline risk should be Low
        assert profile.baseline_risk_level in ['Low', 'Medium']
        
        # Create a high-risk user (all events are risky)
        risky_events = sample_user_events.copy()
        risky_events['anomaly_score'] = -0.7  # All high risk
        
        risky_profile = UserProfile('USR_RISKY', risky_events)
        assert risky_profile.baseline_risk_level == 'High'
    
    def test_behavioral_fingerprint_creation(self, sample_user_events):
        """Test behavioral fingerprint generation."""
        profile = UserProfile('USR_TEST', sample_user_events)
        
        fingerprint = profile.behavioral_fingerprint
        
        # Check fingerprint structure
        assert 'uses_usb' in fingerprint
        assert 'accesses_sensitive_files' in fingerprint
        assert 'works_weekends' in fingerprint
        assert 'works_off_hours' in fingerprint
        
        # User has some sensitive file access (in anomalous events)
        assert fingerprint['accesses_sensitive_files'] == True
        
        # User has some weekend work (day_of_week 5, 6)
        # (only in anomalous events in our sample)
        # This might be True or False depending on data
        assert isinstance(fingerprint['works_weekends'], bool)
    
    def test_divergence_calculation_normal_event(self, sample_user_events):
        """Test divergence calculation for a normal event."""
        profile = UserProfile('USR_TEST', sample_user_events)
        
        # Create a normal event (within baseline)
        normal_event = pd.Series({
            'file_access_count': 8,  # Within normal range
            'upload_size_mb': 5.0,   # Within normal range
            'uses_usb': False,
            'is_off_hours': False,
            'sensitive_file_access': 0,
            'anomaly_score': -0.1
        })
        
        divergence = profile.calculate_divergence(normal_event)
        
        # Divergence should be low
        assert divergence['divergence_level'] == 'Low'
        assert divergence['divergence_score'] < 0.5
        assert len(divergence['divergence_details']) == 0  # No significant divergences
    
    def test_divergence_calculation_anomalous_event(self, sample_user_events):
        """Test divergence calculation for an anomalous event."""
        profile = UserProfile('USR_TEST', sample_user_events)
        
        # Create an anomalous event (far from baseline)
        anomalous_event = pd.Series({
            'file_access_count': 100,  # Way above normal
            'upload_size_mb': 1000.0,  # Way above normal
            'uses_usb': False,
            'is_off_hours': True,      # Unusual
            'sensitive_file_access': 10,  # High
            'anomaly_score': -0.9
        })
        
        divergence = profile.calculate_divergence(anomalous_event)
        
        # Divergence should be high
        assert divergence['divergence_level'] in ['Medium', 'High']
        assert divergence['divergence_score'] > 0.5
        assert len(divergence['divergence_details']) > 0  # Should have explanations
    
    def test_divergence_new_behavior_detection(self, sample_user_events):
        """Test detection of new behaviors."""
        # User never uses USB in history
        sample_user_events['uses_usb'] = 0
        
        profile = UserProfile('USR_TEST', sample_user_events)
        
        # New event with USB usage
        new_behavior_event = pd.Series({
            'file_access_count': 8,
            'upload_size_mb': 5.0,
            'uses_usb': True,  # NEW BEHAVIOR!
            'is_off_hours': False,
            'sensitive_file_access': 0,
            'anomaly_score': -0.3
        })
        
        divergence = profile.calculate_divergence(new_behavior_event)
        
        # Should flag new behavior
        assert divergence['divergence_score'] > 0.4  # Gets 0.5 penalty for new behavior
        assert any('USB' in detail or 'NEW BEHAVIOR' in detail 
                  for detail in divergence['divergence_details'])
    
    def test_to_dict_export(self, sample_user_events):
        """Test profile export to dictionary."""
        profile = UserProfile('USR_TEST', sample_user_events)
        
        profile_dict = profile.to_dict()
        
        # Check structure
        assert 'user_id' in profile_dict
        assert 'baseline' in profile_dict
        assert 'behavioral_fingerprint' in profile_dict
        assert 'baseline_risk_level' in profile_dict
        assert 'is_baseline_elevated' in profile_dict
        assert 'data_quality' in profile_dict
        
        # Check data quality info
        assert profile_dict['data_quality']['historical_events'] == 100
        assert 'confidence_level' in profile_dict['data_quality']


class TestUserProfileManager:
    """Test suite for UserProfileManager class."""
    
    @pytest.fixture
    def sample_multi_user_data(self):
        """Create sample data for multiple users."""
        np.random.seed(42)
        
        all_events = []
        users = ['USR_001', 'USR_002', 'USR_003']
        
        for user_id in users:
            for i in range(50):  # 50 events per user
                event = {
                    'event_id': f'{user_id}_EVT_{i:03d}',
                    'user_id': user_id,
                    'timestamp': datetime(2026, 1, 1) + timedelta(days=i),
                    'file_access_count': np.random.randint(3, 15),
                    'upload_size_mb': np.random.uniform(1, 20),
                    'sensitive_file_access': 0,
                    'external_ip_connection': 0,
                    'is_off_hours': 0,
                    'uses_usb': 0,
                    'anomaly_score': np.random.uniform(-0.2, 0.0),
                    'hour_of_day': np.random.randint(9, 18),
                    'day_of_week': np.random.randint(0, 5)
                }
                all_events.append(event)
        
        return pd.DataFrame(all_events)
    
    def test_manager_initialization(self, sample_multi_user_data):
        """Test profile manager initialization with multi-user data."""
        manager = UserProfileManager(sample_multi_user_data)
        
        # Should create profiles for all 3 users
        assert len(manager.profiles) == 3
        assert 'USR_001' in manager.profiles
        assert 'USR_002' in manager.profiles
        assert 'USR_003' in manager.profiles
    
    def test_get_or_create_profile(self, sample_multi_user_data):
        """Test getting/creating profiles."""
        manager = UserProfileManager(sample_multi_user_data)
        
        # Get existing profile
        profile = manager.get_or_create_profile('USR_001')
        assert profile is not None
        assert profile.user_id == 'USR_001'
        
        # Same instance should be returned (cached)
        profile2 = manager.get_or_create_profile('USR_001')
        assert profile is profile2
    
    def test_get_all_users_summary(self, sample_multi_user_data):
        """Test getting summary of all users."""
        manager = UserProfileManager(sample_multi_user_data)
        
        users = manager.get_all_users()
        
        # Should return 3 users
        assert len(users) == 3
        
        # Check structure
        for user in users:
            assert 'user_id' in user
            assert 'event_count' in user
            assert 'baseline_risk_level' in user
            assert 'baseline_score' in user
            assert 'confidence' in user
    
    def test_profile_update_with_new_events(self, sample_multi_user_data):
        """Test updating a profile with new events."""
        manager = UserProfileManager(sample_multi_user_data)
        
        original_profile = manager.get_profile('USR_001')
        original_event_count = original_profile.baseline['historical_event_count']
        
        # Add new events
        new_events = pd.DataFrame([
            {
                'event_id': 'USR_001_NEW_001',
                'user_id': 'USR_001',
                'timestamp': datetime(2026, 3, 1),
                'file_access_count': 8,
                'upload_size_mb': 5.0,
                'anomaly_score': -0.1
            }
        ])
        
        manager.update_profile('USR_001', new_events)
        
        # Profile should be updated
        updated_profile = manager.get_profile('USR_001')
        assert updated_profile.baseline['historical_event_count'] == original_event_count + 1


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""
    
    def test_scenario_normal_user_anomalous_event(self):
        """
        Scenario: Normal user suddenly performs risky action.
        Should detect high divergence.
        """
        # Create normal user history
        np.random.seed(42)
        normal_events = []
        for i in range(90):
            normal_events.append({
                'event_id': f'EVT_{i}',
                'user_id': 'USR_NORMAL',
                'timestamp': datetime(2026, 1, 1) + timedelta(days=i // 3),
                'file_access_count': np.random.randint(5, 12),
                'upload_size_mb': np.random.uniform(2, 8),
                'sensitive_file_access': 0,
                'is_off_hours': 0,
                'uses_usb': 0,
                'anomaly_score': np.random.uniform(-0.15, -0.05),
                'hour_of_day': np.random.randint(9, 17)
            })
        
        df = pd.DataFrame(normal_events)
        profile = UserProfile('USR_NORMAL', df)
        
        # Now user performs highly anomalous action
        suspicious_event = pd.Series({
            'file_access_count': 80,      # 10x normal!
            'upload_size_mb': 500.0,      # 100x normal!
            'sensitive_file_access': 15,  # NEW behavior
            'is_off_hours': True,         # NEW behavior
            'uses_usb': False,
            'anomaly_score': -0.95
        })
        
        divergence = profile.calculate_divergence(suspicious_event)
        
        # Should detect as highly divergent
        assert divergence['divergence_level'] == 'High'
        assert len(divergence['divergence_details']) >= 2  # Multiple red flags
    
    def test_scenario_sysadmin_elevated_baseline(self):
        """
        Scenario: System admin has naturally risky baseline.
        Their "normal" includes sensitive access and off-hours work.
        """
        # Create sys admin history (naturally elevated)
        np.random.seed(42)
        admin_events = []
        for i in range(100):
            admin_events.append({
                'event_id': f'EVT_{i}',
                'user_id': 'USR_ADMIN',
                'timestamp': datetime(2026, 1, 1) + timedelta(days=i // 3),
                'file_access_count': np.random.randint(20, 50),  # High activity
                'upload_size_mb': np.random.uniform(10, 100),    # Larger uploads
                'sensitive_file_access': 1,                      # Regular sensitive access
                'is_off_hours': np.random.choice([0, 1]),       # Works off-hours
                'uses_usb': 0,
                'anomaly_score': np.random.uniform(-0.4, -0.2),  # Elevated baseline
                'hour_of_day': np.random.randint(8, 22)         # Wider hours
            })
        
        df = pd.DataFrame(admin_events)
        profile = UserProfile('USR_ADMIN', df)
        
        # Check that baseline is elevated
        assert profile.baseline_risk_level in ['Medium', 'High']
        assert profile.behavioral_fingerprint['accesses_sensitive_files'] == True
        
        # Admin's normal event shouldn't trigger high divergence
        normal_admin_event = pd.Series({
            'file_access_count': 35,
            'upload_size_mb': 50.0,
            'sensitive_file_access': 1,
            'is_off_hours': True,
            'uses_usb': False,
            'anomaly_score': -0.3
        })
        
        divergence = profile.calculate_divergence(normal_admin_event)
        
        # Should be low divergence (normal for this admin)
        assert divergence['divergence_level'] in ['Low', 'Medium']


def test_module_imports():
    """Test that all required modules import correctly."""
    from src.user_profile import (
        UserProfile,
        UserProfileManager,
        initialize_profile_manager,
        get_profile_manager
    )
    
    # Should not raise any exceptions
    assert UserProfile is not None
    assert UserProfileManager is not None


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
