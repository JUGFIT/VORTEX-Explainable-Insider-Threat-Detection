"""
Risk Trajectory System

This module tracks how user risk evolves over time with temporal decay.

Key Features:
- Temporal decay: Recent events matter more than old events
- Cumulative risk calculation: Weighted sum of all events
- Escalation detection: Identifies increasing risk trends
- Timeline data: Formatted for frontend visualization

Author: VORTEX Team
Phase: 2A - Core Infrastructure (Session 3)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class RiskTrajectory:
    """
    Tracks a single user's risk evolution over time.
    
    Uses temporal decay to weight recent events more heavily than old events.
    Detects escalation patterns and provides timeline data for visualization.
    """
    
    def __init__(self, user_id: str, historical_events: pd.DataFrame, decay_half_life: int = 7):
        """
        Initialize risk trajectory for a user.
        
        Args:
            user_id: User identifier
            historical_events: DataFrame of user's events (must have timestamp, anomaly_score)
            decay_half_life: Number of days for decay to reach 50% (default: 7 days)
        """
        self.user_id = user_id
        self.decay_half_life = decay_half_life
        
        # Sort events by timestamp
        if 'timestamp' in historical_events.columns:
            self.events = historical_events.sort_values('timestamp').copy()
        else:
            self.events = historical_events.copy()
        
        # Calculate trajectory
        self.trajectory_data = None
        self.cumulative_risk = 0.0
        self.trend = 'stable'
        self.is_escalating = False
        
        if len(self.events) > 0:
            self._calculate_trajectory()
    
    def calculate_decay_factor(self, days_ago: float) -> float:
        """
        Calculate temporal decay factor using exponential decay.
        
        Formula: decay = 0.5^(days_ago / half_life)
        
        Examples:
            - 0 days ago: 1.0 (100% weight)
            - 7 days ago (1 half-life): 0.5 (50% weight)
            - 14 days ago (2 half-lives): 0.25 (25% weight)
            - 30 days ago: ~0.03 (3% weight)
        
        Args:
            days_ago: Number of days since event
            
        Returns:
            Decay factor between 0 and 1
        """
        if days_ago < 0:
            days_ago = 0
        
        return 0.5 ** (days_ago / self.decay_half_life)
    
    def _calculate_trajectory(self):
        """
        Calculate complete risk trajectory with temporal decay.
        
        Generates timeline data showing:
        - Daily aggregated risk
        - Cumulative risk over time
        - Decay-weighted risk
        - Event counts and risk levels
        """
        if len(self.events) == 0:
            self.trajectory_data = []
            self.cumulative_risk = 0.0
            return
        
        # Ensure timestamp is datetime
        if 'timestamp' not in self.events.columns:
            # If no timestamp, use indices as days
            self.events['timestamp'] = pd.date_range(
                start=datetime.now() - timedelta(days=len(self.events)),
                periods=len(self.events),
                freq='D'
            )
        
        self.events['timestamp'] = pd.to_datetime(self.events['timestamp'])
        
        # Use the dataset's own latest timestamp as "now" so that
        # decay and lookback windows work correctly regardless of when
        # the server is running relative to the data's date range.
        self.data_max_ts = self.events['timestamp'].max()
        now = self.data_max_ts
        
        # Calculate days ago for each event
        self.events['days_ago'] = (now - self.events['timestamp']).dt.total_seconds() / 86400
        
        # Calculate decay factor for each event
        self.events['decay_factor'] = self.events['days_ago'].apply(self.calculate_decay_factor)
        
        # Calculate decay-weighted risk
        if 'anomaly_score' in self.events.columns:
            # Clean NaNs before calculation
            score_series = self.events['anomaly_score'].fillna(0)
            age_series = self.events['days_ago']
            
            # Ensure decay_factor is also a series for element-wise multiplication
            decay_factors_series = self.events['decay_factor']
            
            self.events['weighted_risk'] = score_series * decay_factors_series
        else:
            self.events['weighted_risk'] = 0.0
        
        # Calculate cumulative risk (sum of weighted risks)
        self.cumulative_risk = float(self.events['weighted_risk'].sum())
        
        # Group by date for timeline
        self.events['date'] = self.events['timestamp'].dt.date
        
        timeline = []
        for date, group in self.events.groupby('date'):
            # Calculate metrics for this date
            event_count = len(group)
            avg_risk = float(group['anomaly_score'].mean()) if 'anomaly_score' in group.columns else 0.0
            
            # Count risk levels
            if 'risk_level' in group.columns:
                high_risk = int((group['risk_level'] == 'High').sum())
                medium_risk = int((group['risk_level'] == 'Medium').sum())
                low_risk = int((group['risk_level'] == 'Low').sum())
            else:
                high_risk = medium_risk = low_risk = 0
            
            # Cumulative risk up to this date
            cumulative_to_date = float(group['weighted_risk'].sum())
            if np.isnan(cumulative_to_date):
                cumulative_to_date = 0.0
                
            # Average decay factor for this date
            avg_decay = float(group['decay_factor'].mean())
            if np.isnan(avg_decay):
                avg_decay = 1.0
            
            timeline.append({
                'date': str(date),
                'events': int(event_count),
                'avg_risk': float(round(avg_risk, 4)),
                'cumulative_risk': float(round(cumulative_to_date, 4)),
                'avg_decay_factor': float(round(avg_decay, 4)),
                'high_risk_events': int(high_risk),
                'medium_risk_events': int(medium_risk),
                'low_risk_events': int(low_risk)
            })
        
        # Sort by date
        timeline.sort(key=lambda x: x['date'])
        
        # Add running cumulative risk
        running_cumulative = 0.0
        for entry in timeline:
            running_cumulative += entry['cumulative_risk']
            entry['running_cumulative_risk'] = round(running_cumulative, 4)
        
        self.trajectory_data = timeline
        
        # Detect escalation
        self._detect_escalation()
        self._determine_trend()
    
    def _detect_escalation(self):
        """
        Detect if user's risk is escalating.
        
        Compares recent activity (last 7 days) vs previous activity (days 8-14).
        Escalation is flagged if recent risk is significantly higher.
        """
        if len(self.events) < 5:  # Need minimum events to detect trend
            self.is_escalating = False
            self.escalation_details = {
                'recent_7d_avg': 0.0,
                'previous_7d_avg': 0.0,
                'percent_change': 0.0,
                'recent_event_count': 0,
                'previous_event_count': 0,
                'threshold_met': False,
                'severity': 'None',
                'reason': 'Insufficient data (< 5 events)'
            }
            # Use the data's own max timestamp instead of real-time now
            # so windows work correctly for synthetic/historical data
            now = getattr(self, 'data_max_ts', pd.Timestamp(datetime.now()))
            return
        
        # Use the data's own max timestamp instead of real-time now
        # so windows work correctly for synthetic/historical data
        now = getattr(self, 'data_max_ts', pd.Timestamp(datetime.now()))
        
        # Recent events (last 7 days)
        recent_cutoff = now - timedelta(days=7)
        recent_events = self.events[self.events['timestamp'] >= recent_cutoff]
        
        # Previous events (days 8-14)
        previous_start = now - timedelta(days=14)
        previous_end = recent_cutoff
        previous_events = self.events[
            (self.events['timestamp'] >= previous_start) & 
            (self.events['timestamp'] < previous_end)
        ]
        
        if len(recent_events) == 0:
            self.is_escalating = False
            self.escalation_details = {
                'recent_7d_avg': 0.0,
                'previous_7d_avg': 0.0,
                'percent_change': 0.0,
                'recent_event_count': 0,
                'previous_event_count': len(previous_events),
                'threshold_met': False,
                'severity': 'None',
                'reason': 'No recent events'
            }
            return
        
        # Calculate average risk for each period
        recent_avg = float(recent_events['anomaly_score'].mean()) if 'anomaly_score' in recent_events.columns else 0.0
        
        if len(previous_events) > 0 and 'anomaly_score' in previous_events.columns:
            previous_avg = float(previous_events['anomaly_score'].mean())
        else:
            previous_avg = float(self.events['anomaly_score'].mean()) if 'anomaly_score' in self.events.columns else 0.0
        
        # Escalation detection
        # Scores are negative (Isolation Forest): more positive = more anomalous.
        # Escalating if recent average is at least 10% higher (less negative / more positive)
        # than the previous average, using absolute comparison to handle negatives correctly.
        if previous_avg < 0:
            # previous is negative: escalating if recent is less negative by >=10%
            self.is_escalating = recent_avg > (previous_avg * 0.90)
        else:
            # previous is near zero or positive: escalating if recent is 10% higher
            self.is_escalating = recent_avg > (previous_avg * 1.10)
        
        # Calculate percent change
        if previous_avg > 0:
            percent_change = ((recent_avg - previous_avg) / previous_avg) * 100
        else:
            percent_change = 0.0
            
        self.escalation_details = {
            'recent_7d_avg': round(recent_avg, 4),
            'previous_7d_avg': round(previous_avg, 4),
            'percent_change': round(percent_change, 2),
            'recent_event_count': len(recent_events),
            'previous_event_count': len(previous_events),
            'threshold_met': self.is_escalating,
            'severity': self._categorize_escalation_severity(recent_avg, previous_avg)
        }
    
    def _categorize_escalation_severity(self, recent_avg: float, previous_avg: float) -> str:
        """Categorize escalation severity based on relative change between periods."""
        if not self.is_escalating:
            return 'None'
        
        # Calculate how much more anomalous recent period is vs previous
        # Works for both negative and positive score ranges
        if previous_avg < 0 and recent_avg < 0:
            # Both negative: percent improvement toward zero (less negative = more risky)
            change_ratio = abs(recent_avg) / abs(previous_avg)  # < 1 means less negative = more risky
            pct_change = (1 - change_ratio) * 100  # positive = escalating
        elif previous_avg == 0:
            pct_change = 100.0 if recent_avg > 0 else 0.0
        else:
            pct_change = ((recent_avg - previous_avg) / abs(previous_avg)) * 100
        
        if pct_change >= 40:
            return 'Critical'
        elif pct_change >= 25:
            return 'High'
        elif pct_change >= 10:
            return 'Medium'
        else:
            return 'Low'
    
    def _determine_trend(self):
        """
        Determine overall trend direction: escalating, stable, or declining.
        
        Uses linear regression on cumulative risk over time.
        """
        if len(self.trajectory_data) < 3:
            self.trend = 'stable'
            return
        
        # Extract running cumulative risk
        cumulative_risks = [entry['running_cumulative_risk'] for entry in self.trajectory_data]
        
        # Simple trend: compare first half vs second half
        mid_point = len(cumulative_risks) // 2
        first_half_avg = np.mean(cumulative_risks[:mid_point])
        second_half_avg = np.mean(cumulative_risks[mid_point:])
        
        # Trend determination (risk is positive, so higher = worse)
        if second_half_avg > first_half_avg * 1.2:  # 20% increase in risk
            self.trend = 'escalating'
        elif second_half_avg < first_half_avg * 0.8:  # 20% decrease in risk
            self.trend = 'declining'
        else:
            self.trend = 'stable'
    
    def get_trajectory(self, lookback_days: Optional[int] = None) -> List[Dict]:
        """
        Get trajectory timeline data, optionally filtered by lookback period.
        
        Args:
            lookback_days: Number of days to include (default: all)
            
        Returns:
            List of daily trajectory data points
        """
        if self.trajectory_data is None or len(self.trajectory_data) == 0:
            return []
        
        if lookback_days is None:
            return self.trajectory_data
        
        # Filter to lookback period — relative to the dataset's own max timestamp
        # (not datetime.now()) so windows work correctly for historical datasets.
        reference_ts = getattr(self, 'data_max_ts', None)
        if reference_ts is None:
            reference_ts = pd.Timestamp(datetime.now())
        cutoff_date = (reference_ts - timedelta(days=lookback_days)).date()
        
        filtered = [
            entry for entry in self.trajectory_data
            if pd.to_datetime(entry['date']).date() >= cutoff_date
        ]
        
        # If we have only 1 point in the filtered window (common for new injections),
        # add a "ghost" point from the previous day with 0 risk to help Recharts
        # draw a visible line/area.
        if len(filtered) == 1 and len(self.trajectory_data) > 1:
            idx = self.trajectory_data.index(filtered[0])
            if idx > 0:
                # Add the preceding point regardless of cutoff
                filtered.insert(0, self.trajectory_data[idx-1])
            else:
                # Create a zero-stats point for the day before
                prev_date = pd.to_datetime(filtered[0]['date']) - timedelta(days=1)
                ghost = filtered[0].copy()
                ghost['date'] = prev_date.strftime('%Y-%m-%d')
                ghost['events'] = 0
                ghost['avg_risk'] = 0.0
                ghost['cumulative_risk'] = 0.0
                ghost['running_cumulative_risk'] = 0.0
                filtered.insert(0, ghost)
        
        return filtered
    
    def get_summary(self) -> Dict:
        """
        Get summary of trajectory status.
        
        Returns:
            Dictionary with current status, trend, escalation info
        """
        return {
            'user_id': self.user_id,
            'total_events': len(self.events),
            'cumulative_risk': round(self.cumulative_risk, 4),
            'trend': self.trend,
            'is_escalating': self.is_escalating,
            'escalation_details': self.escalation_details if hasattr(self, 'escalation_details') else {},
            'timeline_length': len(self.trajectory_data) if self.trajectory_data else 0,
            'decay_half_life_days': self.decay_half_life
        }
    
    def to_dict(self) -> Dict:
        """Export complete trajectory as dictionary for API responses."""
        return {
            'user_id': self.user_id,
            'current_cumulative_risk': float(self.cumulative_risk),
            'trend': str(self.trend),
            'is_escalating': bool(self.is_escalating),
            'event_count': int(len(self.events)),
            'escalation_severity': str(self.escalation_details.get('severity', 'None') if self.escalation_details else 'None')
        }


class TrajectoryManager:
    """
    Manages risk trajectories for all users.
    
    Provides caching and bulk operations for trajectory analysis.
    """
    
    def __init__(self, data_df: pd.DataFrame, decay_half_life: int = 7):
        """
        Initialize trajectory manager.
        
        Args:
            data_df: DataFrame with all events for all users
            decay_half_life: Decay half-life in days
        """
        self.data_df = data_df
        self.decay_half_life = decay_half_life
        self.trajectories = {}
        
        # Calculate trajectories for all users
        self._calculate_all_trajectories()
    
    def _calculate_all_trajectories(self):
        """Calculate trajectories for all users in dataset."""
        if 'user_id' not in self.data_df.columns:
            print("Warning: No user_id column in data. Cannot create trajectories.")
            return
        
        unique_users = self.data_df['user_id'].unique()
        
        print(f"Calculating risk trajectories for {len(unique_users)} users...")
        for user_id in unique_users:
            user_events = self.data_df[self.data_df['user_id'] == user_id].copy()
            self.trajectories[user_id] = RiskTrajectory(
                user_id, 
                user_events, 
                decay_half_life=self.decay_half_life
            )
        
        print(f"✅ Calculated {len(self.trajectories)} risk trajectories")
    
    def get_trajectory(self, user_id: str) -> Optional[RiskTrajectory]:
        """Get trajectory for specific user."""
        return self.trajectories.get(user_id)
    
    def get_users_by_trend(self, trend: str = 'escalating') -> List[Dict]:
        """
        Get all users with a specific trend.
        
        Args:
            trend: 'escalating', 'stable', or 'declining'
            
        Returns:
            List of user summaries with matching trend
        """
        matching_users = []
        
        for user_id, trajectory in self.trajectories.items():
            if trajectory.trend == trend:
                summary = trajectory.get_summary()
                matching_users.append(summary)
        
        # Sort by cumulative risk (most negative first)
        matching_users.sort(key=lambda x: x['cumulative_risk'])
        
        return matching_users
    
    def get_escalating_users(self) -> List[Dict]:
        """Get all users with escalating risk (convenience method)."""
        escalating = []
        
        for user_id, trajectory in self.trajectories.items():
            if trajectory.is_escalating:
                summary = trajectory.get_summary()
                escalating.append(summary)
        
        # Sort by escalation severity
        severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3, 'None': 4}
        escalating.sort(
            key=lambda x: (
                severity_order.get(x['escalation_details'].get('severity', 'None'), 4),
                x['cumulative_risk']
            )
        )
        
        return escalating
    
    def get_statistics(self) -> Dict:
        """Get overall statistics across all users."""
        if len(self.trajectories) == 0:
            return {
                'total_users': 0,
                'escalating_count': 0,
                'stable_count': 0,
                'declining_count': 0,
                'avg_cumulative_risk': 0.0
            }
        
        escalating_count = sum(1 for t in self.trajectories.values() if t.is_escalating)
        trends = [t.trend for t in self.trajectories.values()]
        
        return {
            'total_users': len(self.trajectories),
            'escalating_count': escalating_count,
            'stable_count': trends.count('stable'),
            'declining_count': trends.count('declining'),
            'avg_cumulative_risk': round(
                np.mean([t.cumulative_risk for t in self.trajectories.values()]),
                4
            ),
            'escalation_rate': round(escalating_count / len(self.trajectories) * 100, 2)
        }


# Global instance (initialized by API)
trajectory_manager: Optional[TrajectoryManager] = None


def initialize_trajectory_manager(data_df: pd.DataFrame, decay_half_life: int = 7) -> TrajectoryManager:
    """
    Initialize the global trajectory manager.
    
    Args:
        data_df: Full event dataset
        decay_half_life: Decay half-life in days
        
    Returns:
        TrajectoryManager instance
    """
    global trajectory_manager
    trajectory_manager = TrajectoryManager(data_df, decay_half_life)
    return trajectory_manager


def get_trajectory_manager() -> Optional[TrajectoryManager]:
    """Get the global trajectory manager instance."""
    return trajectory_manager
