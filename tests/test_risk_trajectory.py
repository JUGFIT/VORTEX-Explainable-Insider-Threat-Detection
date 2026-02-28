"""
Unit Tests for Risk Trajectory System

Tests RiskTrajectory and TrajectoryManager classes for:
- Temporal decay calculation
- Cumulative risk calculation
- Escalation detection
- Trend analysis
- Timeline data generation

Author: VORTEX Team
Phase: 2A - Core Infrastructure (Session 3)
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.risk_trajectory import RiskTrajectory, TrajectoryManager, initialize_trajectory_manager


class TestRiskTrajectory:
    """Test suite for RiskTrajectory class."""
    
    @pytest.fixture
    def stable_user_events(self):
        """Create events for a stable user (low risk throughout)."""
        np.random.seed(42)
        events = []
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(30):
            events.append({
                'event_id': f'EVT_{i:03d}',
                'user_id': 'USR_STABLE',
                'timestamp': base_date + timedelta(days=i),
                'anomaly_score': np.random.uniform(-0.2, -0.05),  # Low risk
                'risk_level': 'Low'
            })
        
        return pd.DataFrame(events)
    
    @pytest.fixture
    def escalating_user_events(self):
        """Create events for escalating user (risk increases over time)."""
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
        
        return pd.DataFrame(events)
    
    def test_decay_factor_calculation(self):
        """Test temporal decay factor calculation."""
        events = pd.DataFrame([
            {'event_id': 'EVT_001', 'user_id': 'TEST', 'timestamp': datetime.now(), 'anomaly_score': -0.5}
        ])
        
        trajectory = RiskTrajectory('TEST', events, decay_half_life=7)
        
        # Test decay factors
        assert trajectory.calculate_decay_factor(0) == 1.0  # Today: 100%
        assert abs(trajectory.calculate_decay_factor(7) - 0.5) < 0.01  # 1 half-life: 50%
        assert abs(trajectory.calculate_decay_factor(14) - 0.25) < 0.01  # 2 half-lives: 25%
        assert trajectory.calculate_decay_factor(30) < 0.1  # 30 days: < 10%
    
    def test_trajectory_calculation_stable_user(self, stable_user_events):
        """Test trajectory calculation for stable user."""
        trajectory = RiskTrajectory('USR_STABLE', stable_user_events)
        
        # Should have trajectory data
        assert trajectory.trajectory_data is not None
        assert len(trajectory.trajectory_data) > 0
        
        # Should not be escalating
        assert trajectory.is_escalating == False
        assert trajectory.trend in ['stable', 'declining']
        
        # Cumulative risk should be low (all events have low risk)
        assert trajectory.cumulative_risk > -5.0  # Not too negative
    
    def test_trajectory_calculation_escalating_user(self, escalating_user_events):
        """Test trajectory calculation for escalating user."""
        trajectory = RiskTrajectory('USR_ESCALATING', escalating_user_events)
        
        # Should detect escalation
        assert trajectory.is_escalating == True
        assert trajectory.trend == 'escalating'
        
        # Recent risk should be higher than previous
        assert trajectory.escalation_details['recent_7d_avg'] < trajectory.escalation_details['previous_7d_avg']
        
        # Escalation severity should be detected
        assert trajectory.escalation_details['severity'] in ['Medium', 'High', 'Critical']
    
    def test_escalation_detection_insufficient_data(self):
        """Test escalation detection with insufficient data."""
        events = pd.DataFrame([
            {'event_id': 'EVT_001', 'user_id': 'TEST', 'timestamp': datetime.now(), 'anomaly_score': -0.5},
            {'event_id': 'EVT_002', 'user_id': 'TEST', 'timestamp': datetime.now() - timedelta(days=1), 'anomaly_score': -0.6'}
        ])
        
        trajectory = RiskTrajectory('TEST', events)
        
        # Should not detect escalation with only 2 events
        assert trajectory.is_escalating == False
        assert 'Insufficient data' in trajectory.escalation_details['reason']
    
    def test_get_trajectory_with_lookback(self, stable_user_events):
        """Test getting trajectory with lookback filter."""
        trajectory = RiskTrajectory('USR_STABLE', stable_user_events)
        
        # Get last 7 days
        recent = trajectory.get_trajectory(lookback_days=7)
        
        # Should have at most 7 entries
        assert len(recent) <= 7
        
        # All dates should be within 7 days
        for entry in recent:
            date = pd.to_datetime(entry['date']).date()
            days_diff = (datetime.now().date() - date).days
            assert days_diff <= 7
    
    def test_get_summary(self, escalating_user_events):
        """Test trajectory summary generation."""
        trajectory = RiskTrajectory('USR_ESCALATING', escalating_user_events)
        
        summary = trajectory.get_summary()
        
        # Check summary structure
        assert 'user_id' in summary
        assert 'total_events' in summary
        assert 'cumulative_risk' in summary
        assert 'trend' in summary
        assert 'is_escalating' in summary
        assert 'escalation_details' in summary
        
        # Values should be correct
        assert summary['user_id'] == 'USR_ESCALATING'
        assert summary['total_events'] == 30
        assert summary['is_escalating'] == True
    
    def test_to_dict_export(self, stable_user_events):
        """Test trajectory export to dictionary."""
        trajectory = RiskTrajectory('USR_STABLE', stable_user_events)
        
        data = trajectory.to_dict()
        
        # Check structure
        assert 'user_id' in data
        assert 'trajectory' in data
        assert 'current_cumulative_risk' in data
        assert 'trend' in data
        assert 'is_escalating' in data
        assert 'summary' in data
        
        # Trajectory should be a list
        assert isinstance(data['trajectory'], list)
        
        # Each timeline entry should have required fields
        if len(data['trajectory']) > 0:
            entry = data['trajectory'][0]
            assert 'date' in entry
            assert 'events' in entry
            assert 'avg_risk' in entry
            assert 'cumulative_risk' in entry


class TestTrajectoryManager:
    """Test suite for TrajectoryManager class."""
    
    @pytest.fixture
    def multi_user_data(self):
        """Create data for multiple users with different patterns."""
        np.random.seed(42)
        all_events = []
        base_date = datetime.now() - timedelta(days=30)
        
        # User 1: Stable
        for i in range(20):
            all_events.append({
                'event_id': f'USR001_EVT_{i}',
                'user_id': 'USR_001',
                'timestamp': base_date + timedelta(days=i),
                'anomaly_score': np.random.uniform(-0.2, -0.05),
                'risk_level': 'Low'
            })
        
        # User 2: Escalating
        for i in range(25):
            if i < 15:
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
        
        # User 3: Declining (was risky, now improving)
        for i in range(20):
            if i < 10:
                risk = np.random.uniform(-0.8, -0.5)
                level = 'High'
            else:
                risk = np.random.uniform(-0.2, -0.05)
                level = 'Low'
            
            all_events.append({
                'event_id': f'USR003_EVT_{i}',
                'user_id': 'USR_003',
                'timestamp': base_date + timedelta(days=i),
                'anomaly_score': risk,
                'risk_level': level
            })
        
        return pd.DataFrame(all_events)
    
    def test_manager_initialization(self, multi_user_data):
        """Test trajectory manager initialization."""
        manager = TrajectoryManager(multi_user_data)
        
        # Should create trajectories for all 3 users
        assert len(manager.trajectories) == 3
        assert 'USR_001' in manager.trajectories
        assert 'USR_002' in manager.trajectories
        assert 'USR_003' in manager.trajectories
    
    def test_get_trajectory(self, multi_user_data):
        """Test getting specific user's trajectory."""
        manager = TrajectoryManager(multi_user_data)
        
        trajectory = manager.get_trajectory('USR_001')
        
        assert trajectory is not None
        assert trajectory.user_id == 'USR_001'
        assert isinstance(trajectory, RiskTrajectory)
    
    def test_get_users_by_trend(self, multi_user_data):
        """Test getting users filtered by trend."""
        manager = TrajectoryManager(multi_user_data)
        
        escalating = manager.get_users_by_trend('escalating')
        
        # Should find USR_002 (escalating user)
        assert len(escalating) >= 1
        user_ids = [u['user_id'] for u in escalating]
        assert 'USR_002' in user_ids
    
    def test_get_escalating_users(self, multi_user_data):
        """Test getting all escalating users."""
        manager = TrajectoryManager(multi_user_data)
        
        escalating = manager.get_escalating_users()
        
        # Should find at least USR_002
        assert len(escalating) >= 1
        
        # Should be sorted by severity
        if len(escalating) > 1:
            severities = [u['escalation_details']['severity'] for u in escalating]
            # Check that Critical/High come before Low
            assert severities == sorted(severities, key=lambda x: {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}.get(x, 4))
    
    def test_get_statistics(self, multi_user_data):
        """Test getting overall statistics."""
        manager = TrajectoryManager(multi_user_data)
        
        stats = manager.get_statistics()
        
        # Check structure
        assert 'total_users' in stats
        assert 'escalating_count' in stats
        assert 'stable_count' in stats
        assert 'declining_count' in stats
        assert 'avg_cumulative_risk' in stats
        assert 'escalation_rate' in stats
        
        # Values should be correct
        assert stats['total_users'] == 3
        assert stats['escalating_count'] >= 1  # At least USR_002


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""
    
    def test_scenario_sudden_escalation(self):
        """
        Scenario: User suddenly becomes risky after being normal.
        Should detect escalation.
        """
        np.random.seed(42)
        events = []
        base_date = datetime.now() - timedelta(days=20)
        
        # Days 0-15: Normal activity
        for i in range(15):
            events.append({
                'event_id': f'EVT_{i}',
                'user_id': 'SUDDEN_THREAT',
                'timestamp': base_date + timedelta(days=i),
                'anomaly_score': np.random.uniform(-0.15, -0.05),
                'risk_level': 'Low'
            })
        
        # Days 16-20: Sudden high-risk activity
        for i in range(15, 20):
            events.append({
                'event_id': f'EVT_{i}',
                'user_id': 'SUDDEN_THREAT',
                'timestamp': base_date + timedelta(days=i),
                'anomaly_score': np.random.uniform(-0.95, -0.7),
                'risk_level': 'High'
            })
        
        df = pd.DataFrame(events)
        trajectory = RiskTrajectory('SUDDEN_THREAT', df)
        
        # Should detect escalation
        assert trajectory.is_escalating == True
        assert trajectory.trend == 'escalating'
        assert trajectory.escalation_details['severity'] in ['High', 'Critical']
    
    def test_scenario_temporal_decay_verification(self):
        """
        Scenario: Old high-risk event should have less impact than recent medium-risk event.
        """
        events = [
            # Old high-risk event (30 days ago)
            {
                'event_id': 'OLD',
                'user_id': 'TEST',
                'timestamp': datetime.now() - timedelta(days=30),
                'anomaly_score': -0.9,
                'risk_level': 'High'
            },
            # Recent medium-risk event (today)
            {
                'event_id': 'RECENT',
                'user_id': 'TEST',
                'timestamp': datetime.now(),
                'anomaly_score': -0.4,
                'risk_level': 'Medium'
            }
        ]
        
        df = pd.DataFrame(events)
        trajectory = RiskTrajectory('TEST', df, decay_half_life=7)
        
        # Calculate individual contributions
        old_decay = trajectory.calculate_decay_factor(30)
        recent_decay = trajectory.calculate_decay_factor(0)
        
        old_contribution = -0.9 * old_decay
        recent_contribution = -0.4 * recent_decay
        
        # Recent event should contribute more to cumulative risk
        assert abs(recent_contribution) > abs(old_contribution)


def test_module_imports():
    """Test that all required modules import correctly."""
    from src.risk_trajectory import (
        RiskTrajectory,
        TrajectoryManager,
        initialize_trajectory_manager,
        get_trajectory_manager
    )
    
    # Should not raise any exceptions
    assert RiskTrajectory is not None
    assert TrajectoryManager is not None


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
