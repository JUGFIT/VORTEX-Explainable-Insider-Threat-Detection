"""
User Profile Management System

This module manages individual user behavioral profiles, including:
- Baseline calculation from historical data
- Behavioral fingerprinting (typical patterns)
- Divergence detection (how much current behavior differs from baseline)
- Dynamic baseline updates

Author: VORTEX Team
Phase: 2A - Core Infrastructure
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os
from collections import defaultdict


class UserProfile:
    """
    Manages behavioral profile for a single user.
    
    Calculates and tracks:
    - Normal behavior baseline (what's typical for this user)
    - Behavioral fingerprint (unique patterns)
    - Risk trajectory over time
    - Divergence from baseline
    """
    
    def __init__(self, user_id: str, historical_events: pd.DataFrame):
        """
        Initialize user profile from historical events.
        
        Args:
            user_id: Unique user identifier
            historical_events: DataFrame of user's past events
        """
        self.user_id = user_id
        self.historical_events = historical_events
        self.baseline = self.calculate_baseline()
        self.behavioral_fingerprint = self.create_behavioral_fingerprint()
        self.baseline_risk_level = self.categorize_baseline_risk()
        
    def calculate_baseline(self) -> Dict:
        """
        Calculate user's normal behavior baseline from historical data.
        
        Uses only "normal" events (anomaly_score > -0.3) to establish
        what is typical/expected for this user.
        
        Returns:
            Dictionary containing baseline metrics
        """
        # Filter to normal events only (not flagged as risky)
        if 'timestamp' in self.historical_events.columns:
            # Ensure timestamp is datetime for duration calculations
            self.historical_events['timestamp'] = pd.to_datetime(self.historical_events['timestamp'])

        if 'anomaly_score' in self.historical_events.columns:
            # High scores (> 0.4) are anomalies; normal baseline is established from stable activity
            normal_events = self.historical_events[
                self.historical_events['anomaly_score'] < 0.2
            ]
        else:
            # If no anomaly scores yet, use all events
            normal_events = self.historical_events
        
        if len(normal_events) == 0:
            # No normal events - return conservative defaults
            return self._get_default_baseline()
        
        # Calculate baseline metrics
        baseline = {
            # File access patterns
            'avg_files_accessed': float(normal_events.get('file_access_count', pd.Series([0])).mean()),
            'std_files_accessed': float(normal_events.get('file_access_count', pd.Series([0])).std() or 0.0),
            'max_files_accessed': float(normal_events.get('file_access_count', pd.Series([0])).max()),
            
            # Upload patterns
            'avg_upload_size': float(normal_events.get('upload_size_mb', pd.Series([0])).mean()),
            'std_upload_size': float(normal_events.get('upload_size_mb', pd.Series([0])).std() or 0.0),
            'max_upload_size': float(normal_events.get('upload_size_mb', pd.Series([0])).max()),
            
            # Temporal patterns
            'typical_hours': [int(h) for h in self._calculate_typical_hours(normal_events)],
            'typical_days': [int(d) for d in self._calculate_typical_days(normal_events)],
            'off_hours_frequency': float(self._calculate_off_hours_frequency(normal_events)),
            
            # Risk baseline
            'baseline_score': float(normal_events.get('anomaly_score', pd.Series([-0.1])).mean()),
            'baseline_score_std': float(normal_events.get('anomaly_score', pd.Series([0])).std() or 0.0),
            
            # Activity level
            'events_per_day': float(len(normal_events) / max(
                (normal_events['timestamp'].max() - normal_events['timestamp'].min()).days,
                1
            ) if 'timestamp' in normal_events.columns else 1.0),
            
            # Data sufficiency
            'historical_event_count': int(len(self.historical_events)),
            'normal_event_count': int(len(normal_events)),
            'baseline_confidence': float(min(len(normal_events) / 90.0, 1.0))
        }
        
        return baseline
    
    def _get_default_baseline(self) -> Dict:
        """Return conservative default baseline when no historical data available."""
        return {
            'avg_files_accessed': 5.0,
            'std_files_accessed': 3.0,
            'max_files_accessed': 10.0,
            'avg_upload_size': 2.0,
            'std_upload_size': 5.0,
            'max_upload_size': 10.0,
            'typical_hours': [9, 10, 11, 14, 15, 16],
            'typical_days': [0, 1, 2, 3, 4],  # Mon-Fri
            'off_hours_frequency': 0.0,
            'baseline_score': -0.1,
            'baseline_score_std': 0.05,
            'events_per_day': 1.0,
            'historical_event_count': 0,
            'normal_event_count': 0,
            'baseline_confidence': 0.0
        }
    
    def _calculate_typical_hours(self, events: pd.DataFrame) -> List[int]:
        """Calculate user's typical work hours."""
        if 'timestamp' not in events.columns or len(events) == 0:
            return [9, 10, 11, 14, 15, 16]  # Default business hours
        
        # Extract hour from timestamp
        if 'hour_of_day' in events.columns:
            hours = events['hour_of_day']
        else:
            hours = pd.to_datetime(events['timestamp']).dt.hour
        
        # Get hours that account for 80% of activity
        hour_counts = hours.value_counts()
        cumulative_pct = hour_counts.sort_values(ascending=False).cumsum() / len(hours)
        typical_hours = cumulative_pct[cumulative_pct <= 0.8].index.tolist()
        
        return sorted(typical_hours) if typical_hours else [9, 10, 11, 14, 15, 16]
    
    def _calculate_typical_days(self, events: pd.DataFrame) -> List[int]:
        """Calculate user's typical work days (0=Monday, 6=Sunday)."""
        if 'timestamp' not in events.columns or len(events) == 0:
            return [0, 1, 2, 3, 4]  # Default: Monday-Friday
        
        # Extract day of week
        if 'day_of_week' in events.columns:
            days = events['day_of_week']
        else:
            days = pd.to_datetime(events['timestamp']).dt.dayofweek
        
        # Get days that account for 80% of activity
        day_counts = days.value_counts()
        typical_days = day_counts[day_counts >= len(events) * 0.1].index.tolist()
        
        return sorted(typical_days) if typical_days else [0, 1, 2, 3, 4]
    
    def _calculate_off_hours_frequency(self, events: pd.DataFrame) -> float:
        """Calculate how often user works off-hours (0.0 to 1.0)."""
        if 'is_off_hours' not in events.columns or len(events) == 0:
            return 0.0
        
        return events['is_off_hours'].mean()
    
    def create_behavioral_fingerprint(self) -> Dict:
        """
        Create a behavioral fingerprint - unique patterns for this user.
        
        Identifies behaviors like:
        - Does user typically use USB?
        - Does user access sensitive files regularly?
        - Does user work weekends?
        - What are their typical connection IPs?
        
        Returns:
            Dictionary of behavioral flags and patterns
        """
        fingerprint = {
            # USB usage
            'uses_usb': self._check_usb_usage(),
            
            # Sensitive file access
            'accesses_sensitive_files': self._check_sensitive_access(),
            'avg_sensitive_files_per_event': self._calculate_avg_sensitive_access(),
            
            # Work patterns
            'works_weekends': self._check_weekend_work(),
            'works_off_hours': self.baseline['off_hours_frequency'] > 0.1,
            
            # External connections
            'uses_external_ips': self._check_external_connections(),
            'typical_ip_count': self._calculate_typical_ip_count(),
            
            # Privilege patterns
            'has_elevated_privileges': self._check_privilege_use(),
            
            # Activity patterns
            'is_high_activity_user': self.baseline['avg_files_accessed'] > 20,
            'is_data_heavy_user': self.baseline['avg_upload_size'] > 50
        }
        
        return fingerprint
    
    def _check_usb_usage(self) -> bool:
        """Check if user typically uses USB devices."""
        if 'uses_usb' in self.historical_events.columns:
            return self.historical_events['uses_usb'].sum() > 0
        return False
    
    def _check_sensitive_access(self) -> bool:
        """Check if user regularly accesses sensitive files."""
        if 'sensitive_file_access' in self.historical_events.columns:
            return self.historical_events['sensitive_file_access'].sum() > 0
        return False
    
    def _calculate_avg_sensitive_access(self) -> float:
        """Calculate average sensitive files accessed per event."""
        if 'sensitive_file_access' in self.historical_events.columns:
            return self.historical_events['sensitive_file_access'].mean()
        return 0.0
    
    def _check_weekend_work(self) -> bool:
        """Check if user works on weekends (Saturday=5, Sunday=6)."""
        weekend_days = [5, 6]
        return any(day in self.baseline['typical_days'] for day in weekend_days)
    
    def _check_external_connections(self) -> bool:
        """Check if user connects to external IPs."""
        if 'external_ip_connection' in self.historical_events.columns:
            return self.historical_events['external_ip_connection'].sum() > 0
        return False
    
    def _calculate_typical_ip_count(self) -> int:
        """Calculate typical number of unique IPs user connects to."""
        # Placeholder - would need actual IP data
        return 1
    
    def _check_privilege_use(self) -> bool:
        """Check if user has/uses elevated privileges."""
        # Placeholder - would need privilege data
        return False
    
    def categorize_baseline_risk(self) -> str:
        """
        Categorize user's baseline risk level.
        
        Some users have inherently risky baselines (e.g., sys admins).
        This is normal for them, but still elevated compared to regular users.
        
        Returns:
            'Low', 'Medium', or 'High'
        """
        baseline_score = self.baseline['baseline_score']
        
        if baseline_score > 0.3:
            return 'High'  # User's normal is already risky
        elif baseline_score > 0.15:
            return 'Medium'  # Elevated baseline
        else:
            return 'Low'  # Normal baseline
    
    def calculate_divergence(self, new_event: pd.Series) -> Dict:
        """
        Calculate how much a new event diverges from this user's baseline.
        
        Args:
            new_event: Single event (pandas Series or dict)
            
        Returns:
            Dictionary with divergence score and details
        """
        divergence_score = 0.0
        divergence_details = []
        
        # Convert to dict if Series
        if isinstance(new_event, pd.Series):
            event = new_event.to_dict()
        else:
            event = new_event
        
        # File access divergence
        if 'file_access_count' in event:
            file_z_score = (
                (event['file_access_count'] - self.baseline['avg_files_accessed']) /
                max(self.baseline['std_files_accessed'], 1.0)
            )
            if abs(file_z_score) > 2.0:  # More than 2 std deviations
                divergence_score += abs(file_z_score) * 0.2
                divergence_details.append(
                    f"File access {abs(file_z_score):.1f}x above normal baseline"
                )
        
        # Upload size divergence
        if 'upload_size_mb' in event:
            upload_z_score = (
                (event['upload_size_mb'] - self.baseline['avg_upload_size']) /
                max(self.baseline['std_upload_size'], 1.0)
            )
            if abs(upload_z_score) > 2.0:
                divergence_score += abs(upload_z_score) * 0.3
                divergence_details.append(
                    f"Upload size {abs(upload_z_score):.1f}x above normal baseline"
                )
        
        # New behavior detection
        if event.get('uses_usb', False) and not self.behavioral_fingerprint['uses_usb']:
            divergence_score += 0.5
            divergence_details.append("NEW BEHAVIOR: USB usage (never seen before)")
        
        # Off-hours divergence
        if 'is_off_hours' in event:
            if event['is_off_hours'] and not self.behavioral_fingerprint['works_off_hours']:
                divergence_score += 0.3
                divergence_details.append("OFF-HOURS: Activity outside typical work hours")
        
        # Sensitive file access divergence
        if 'sensitive_file_access' in event:
            if event['sensitive_file_access'] > 0:
                expected = self.behavioral_fingerprint['avg_sensitive_files_per_event']
                if event['sensitive_file_access'] > expected * 3:  # 3x normal
                    divergence_score += 0.4
                    divergence_details.append(
                        f"Sensitive file access 3x above baseline ({event['sensitive_file_access']} vs {expected:.1f})"
                    )
        
        return {
            'divergence_score': divergence_score,
            'divergence_level': self._categorize_divergence(divergence_score),
            'divergence_details': divergence_details,
            'baseline_comparison': {
                'user_baseline_score': self.baseline['baseline_score'],
                'event_score': event.get('anomaly_score', 0.0),
                'baseline_risk_level': self.baseline_risk_level
            }
        }
    
    def _categorize_divergence(self, score: float) -> str:
        """Categorize divergence score."""
        if score > 1.0:
            return 'High'
        elif score > 0.5:
            return 'Medium'
        else:
            return 'Low'
    
    def to_dict(self) -> Dict:
        """Export profile as dictionary for API responses."""
        # Helper to convert numpy types to native types
        def _to_native(val):
            if isinstance(val, (np.integer, np.int64, np.int32)):
                return int(val)
            if isinstance(val, (np.floating, np.float64, np.float32)):
                return float(val)
            if isinstance(val, (np.bool_, bool)):
                return bool(val)
            if isinstance(val, dict):
                return {k: _to_native(v) for k, v in val.items()}
            if isinstance(val, (list, tuple)):
                return [_to_native(i) for i in val]
            return val

        return {
            'user_id': self.user_id,
            'baseline': _to_native(self.baseline),
            'behavioral_fingerprint': _to_native(self.behavioral_fingerprint),
            'baseline_risk_level': str(self.baseline_risk_level),
            'is_baseline_elevated': bool(self.baseline_risk_level in ['Medium', 'High']),
            'data_quality': _to_native({
                'historical_events': self.baseline['historical_event_count'],
                'confidence': self.baseline['baseline_confidence'],
                'confidence_level': 'High' if self.baseline['baseline_confidence'] > 0.8 else
                                   'Medium' if self.baseline['baseline_confidence'] > 0.5 else 'Low'
            })
        }


class UserProfileManager:
    """
    Manages profiles for all users.
    Handles loading, caching, and updating profiles.
    """
    
    def __init__(self, data_df: pd.DataFrame):
        """
        Initialize profile manager with event data.
        
        Args:
            data_df: DataFrame containing all events for all users
        """
        self.data_df = data_df
        self.profiles = {}  # Cache of loaded profiles
        self._load_all_profiles()
    
    def _load_all_profiles(self):
        """Load profiles for all users in the dataset."""
        if 'user_id' not in self.data_df.columns:
            print("Warning: No user_id column in data. Cannot create profiles.")
            return
        
        unique_users = self.data_df['user_id'].unique()
        
        print(f"Loading profiles for {len(unique_users)} users...")
        for user_id in unique_users:
            self.profiles[user_id] = self.get_or_create_profile(user_id)
        
        print(f"✅ Loaded {len(self.profiles)} user profiles")
    
    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """
        Get existing profile or create new one.
        
        Args:
            user_id:  User identifier
            
        Returns:
            UserProfile instance
        """
        if user_id in self.profiles:
            return self.profiles[user_id]
        
        # Get user's historical events
        user_events = self.data_df[self.data_df['user_id'] == user_id].copy()
        
        # Create and cache profile
        profile = UserProfile(user_id, user_events)
        self.profiles[user_id] = profile
        
        return profile
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get profile for a specific user."""
        return self.profiles.get(user_id)
    
    def get_all_users(self) -> List[Dict]:
        """
        Get summary of all users for API listing.
        
        Returns:
            List of user summaries
        """
        users = []
        for user_id, profile in self.profiles.items():
            users.append({
                'user_id': user_id,
                'event_count': profile.baseline['historical_event_count'],
                'baseline_risk_level': profile.baseline_risk_level,
                'baseline_score': profile.baseline['baseline_score'],
                'confidence': profile.baseline['baseline_confidence']
            })
        
        # Sort by baseline risk (High first)
        risk_order = {'High': 0, 'Medium': 1, 'Low': 2}
        users.sort(key=lambda x: (risk_order.get(x['baseline_risk_level'], 3), x['baseline_score']))
        
        return users
    
    def update_profile(self, user_id: str, new_events: pd.DataFrame):
        """
        Update a user's profile with new events.
        
        Args:
            user_id: User to update
            new_events: New events to add to history
        """
        if user_id in self.profiles:
            # Append new events to existing data
            updated_events = pd.concat([
                self.profiles[user_id].historical_events,
                new_events
            ], ignore_index=True)
            
            # Recreate profile with updated data
            self.profiles[user_id] = UserProfile(user_id, updated_events)
        else:
            # Create new profile
            self.profiles[user_id] = UserProfile(user_id, new_events)


# Global instance (will be initialized by API)
profile_manager: Optional[UserProfileManager] = None


def initialize_profile_manager(data_df: pd.DataFrame):
    """
    Initialize the global profile manager.
    Called by API on startup.
    
    Args:
        data_df: Full event dataset
    """
    global profile_manager
    profile_manager = UserProfileManager(data_df)
    return profile_manager


def get_profile_manager() -> Optional[UserProfileManager]:
    """Get the global profile manager instance."""
    return profile_manager
