"""
Temporal Pattern Detection System

Detects long-term behavioral shifts, low-and-slow attacks, and activity spikes.

Key Features:
- Low-and-Slow Attack Tracking (cumulative risk over 14-30 days)
- Frequency Anomaly Engine (spikes in event volume)
- First-Occurrence Detection (USB, Sensitive Access, Off-hours)
- Behavioral Drift Analysis (comparing recent 7d vs historical baseline)

Author: VORTEX Team
Phase: 2A - Core Infrastructure (Session 5)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict


class TemporalPatternDetector:
    """
    Analyzes historical event data to find subtle temporal patterns and shifts.
    """
    
    def __init__(self, user_id: str, events: pd.DataFrame, baseline: Optional[Dict] = None):
        """
        Args:
            user_id: User identifier
            events: DataFrame of user's events
            baseline: User's calculated baseline from UserProfile
        """
        self.user_id = user_id
        self.events = events.copy()
        self.baseline = baseline or {}
        
        # Ensure timestamp is datetime
        if 'timestamp' in self.events.columns:
            self.events['timestamp'] = pd.to_datetime(self.events['timestamp'])
            self.events = self.events.sort_values('timestamp')
            
        self.detected_patterns = []
        self._analyze_patterns()
        
    def _analyze_patterns(self):
        """Run all temporal analysis modules."""
        if len(self.events) < 5:
            return # Insufficient data for pattern analysis
            
        self._detect_low_and_slow()
        self._detect_frequency_spikes()
        self._detect_novelty_events()
        self._detect_behavioral_drift()

    def _detect_low_and_slow(self, window_days: int = 30):
        """
        Detects persistent suspicious activity that stays below single-event thresholds.
        """
        if 'anomaly_score' not in self.events.columns:
            return

        # Look for events with 'suspect' but not 'alert' scores (e.g., between -0.1 and -0.4)
        suspect_events = self.events[
            (self.events['anomaly_score'] < -0.1) & 
            (self.events['anomaly_score'] > -0.5)
        ]
        
        if len(suspect_events) < 10:
            return # Not enough persistence
            
        # Check if these are spread over time
        timespan = (suspect_events['timestamp'].max() - suspect_events['timestamp'].min()).days
        if timespan < 7:
            return # Too clumped together (that's a spike, not low-and-slow)
            
        # Calculate cumulative suspicion density
        avg_risk = suspect_events['anomaly_score'].mean()
        
        self.detected_patterns.append({
            'type': 'low_and_slow',
            'name': 'Low-and-Slow Suspicious Activity',
            'severity': 'Medium' if len(suspect_events) < 20 else 'High',
            'confidence': min(len(suspect_events) / 50.0, 1.0),
            'description': f"Persistent suspicious activity ({len(suspect_events)} events) over {timespan} days.",
            'metrics': {
                'event_count': len(suspect_events),
                'timespan_days': timespan,
                'avg_risk_score': round(avg_risk, 4)
            }
        })

    def _detect_frequency_spikes(self):
        """
        Detects sudden increases in event volume relative to historical average.
        """
        if len(self.events) < 10:
            return

        # Calculate historical average (events per day)
        total_days = max((self.events['timestamp'].max() - self.events['timestamp'].min()).days, 1)
        avg_events_per_day = len(self.events) / total_days
        
        # Check last 3 days
        recent_cutoff = datetime.now() - timedelta(days=3)
        recent_events = self.events[self.events['timestamp'] > recent_cutoff]
        recent_avg = len(recent_events) / 3.0
        
        if avg_events_per_day > 0 and recent_avg > (avg_events_per_day * 3.0):
            self.detected_patterns.append({
                'type': 'frequency_spike',
                'name': 'Activity Frequency Spike',
                'severity': 'Medium',
                'description': f"Recent activity volume ({recent_avg:.1f} events/day) is {recent_avg/avg_events_per_day:.1f}x higher than historical average.",
                'metrics': {
                    'historical_avg': float(round(avg_events_per_day, 2)),
                    'recent_avg': float(round(recent_avg, 2)),
                    'multiplier': float(round(recent_avg/avg_events_per_day, 1)) if avg_events_per_day > 0 else 0.0
                }
            })

    def _detect_novelty_events(self):
        """
        Detects first-time occurrences of high-risk actions.
        """
        indicators = {
            'uses_usb': 'First USB Usage',
            'sensitive_file_access': 'First Sensitive File Access',
            'is_off_hours': 'First Off-Hours Activity',
            'external_ip_connection': 'First External Connection'
        }
        
        for col, display_name in indicators.items():
            if col not in self.events.columns:
                continue
                
            # Find the first positive occurrence
            occurrences = self.events[self.events[col] == True] if self.events[col].dtype == bool else self.events[self.events[col] > 0]
            
            if len(occurrences) == 1:
                # If there's only one ever, and it's recent (within 7 days)
                is_recent = (datetime.now() - occurrences.iloc[0]['timestamp']).days <= 7
                if is_recent:
                    self.detected_patterns.append({
                        'type': 'novelty',
                        'name': display_name,
                        'severity': 'Medium',
                        'description': f"First time this user has performed: {display_name}.",
                        'timestamp': occurrences.iloc[0]['timestamp'].isoformat()
                    })

    def _detect_behavioral_drift(self):
        """
        Detects shifts in core work metrics between recent activity and history.
        """
        if len(self.events) < 20: 
            return

        recent_cutoff = datetime.now() - timedelta(days=7)
        recent = self.events[self.events['timestamp'] > recent_cutoff]
        historic = self.events[self.events['timestamp'] <= recent_cutoff]
        
        if len(recent) < 5 or len(historic) < 10:
            return

        metrics_to_check = ['file_access_count', 'upload_size_mb']
        significant_drifts = []

        for metric in metrics_to_check:
            if metric not in self.events.columns:
                continue
                
            h_mean = historic[metric].mean()
            r_mean = recent[metric].mean()

            # NaN protection
            if np.isnan(h_mean): h_mean = 0.0
            if np.isnan(r_mean): r_mean = 0.0
            
            # If 2x increase and absolute difference is material
            # Add zero-division check for h_mean
            if h_mean > 0 and r_mean > (h_mean * 2.0):
                significant_drifts.append(f"{metric.replace('_', ' ')} increased {r_mean/h_mean:.1f}x")

        if significant_drifts:
            self.detected_patterns.append({
                'type': 'behavioral_drift',
                'name': 'Behavioral Identity Shift',
                'severity': 'High',
                'description': f"Fundamental shift detected in: {', '.join(significant_drifts)}.",
                'metrics': {
                    'indicators': significant_drifts
                }
            })

    def get_patterns(self) -> List[Dict]:
        return self.detected_patterns

    def get_summary(self) -> Dict:
        # Ensure all values are JSON compatible types
        highest_severity = max([p['severity'] for p in self.detected_patterns], default='Low')
        return {
            'user_id': self.user_id,
            'pattern_count': int(len(self.detected_patterns)), # Cast to int
            'highest_severity': highest_severity,
            'patterns': [p['type'] for p in self.detected_patterns]
        }


class TemporalManager:
    """
    Manages temporal pattern detection across all users.
    """
    def __init__(self, data_df: pd.DataFrame):
        self.data_df = data_df
        self.detectors = {}
        self._initialize_all()

    def _initialize_all(self):
        if 'user_id' not in self.data_df.columns:
            return
            
        unique_users = self.data_df['user_id'].unique()
        for user_id in unique_users:
            user_slice = self.data_df[self.data_df['user_id'] == user_id]
            self.detectors[user_id] = TemporalPatternDetector(user_id, user_slice)

    def get_user_patterns(self, user_id: str) -> List[Dict]:
        detector = self.detectors.get(user_id)
        return detector.get_patterns() if detector else []

    def get_statistics(self) -> Dict:
        """Global stats for temporal patterns."""
        all_patterns = []
        for d in self.detectors.values():
            all_patterns.extend(d.get_patterns())
            
        total_user_count = max(len(self.detectors), 1)
        
        # Calculate severity counts
        severity_counts = defaultdict(int)
        for p in all_patterns:
            severity_counts[p['severity']] += 1

        # Count users with at least one pattern
        users_with_patterns = sum(1 for d in self.detectors.values() if len(d.detected_patterns) > 0)

        return {
            'total_users_tracked': int(len(self.detectors)),
            'total_patterns_detected': int(len(all_patterns)),
            'users_with_patterns': int(users_with_patterns),
            'avg_patterns_per_user': float(round(len(all_patterns) / total_user_count, 2)),
            'by_type': {
                'low_and_slow': int(len([p for p in all_patterns if p['type'] == 'low_and_slow'])),
                'frequency_spike': int(len([p for p in all_patterns if p['type'] == 'frequency_spike'])),
                'novelty': int(len([p for p in all_patterns if p['type'] == 'novelty'])),
                'behavioral_drift': int(len([p for p in all_patterns if p['type'] == 'behavioral_drift']))
            },
            'by_severity': {
                'Critical': int(severity_counts['Critical']),
                'High': int(severity_counts['High']),
                'Medium': int(severity_counts['Medium']),
                'Low': int(severity_counts['Low'])
            }
        }

# Helpers for API
_global_temporal_manager = None

def initialize_temporal_manager(df: pd.DataFrame):
    global _global_temporal_manager
    _global_temporal_manager = TemporalManager(df)
    return _global_temporal_manager

def get_temporal_manager():
    return _global_temporal_manager
