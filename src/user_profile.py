"""
User Profile Management System

This module manages individual user behavioral profiles, including:
- Baseline calculation from historical data
- Behavioral fingerprinting (typical patterns)
- Divergence detection (how much current behavior differs from baseline)
- Dynamic baseline updates
- Global org-wide baseline for meaningful user comparison

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


class GlobalOrgBaseline:
    """
    Computes org-wide baseline statistics from the full dataset.
    
    This is the single source of truth for what is 'normal' across
    the organisation. Individual users are then compared against this.
    """

    def __init__(self, data_df: pd.DataFrame):
        self.mean_score: float = 0.0
        self.std_score: float = 0.1
        self.p50: float = 0.0
        self.p75: float = 0.0
        self.p90: float = 0.0
        self.p95: float = 0.0

        # Org-wide behavioural averages
        self.org_off_hours_rate: float = 0.0      # fraction of events off-hours
        self.org_sensitive_file_rate: float = 0.0  # fraction of events with sensitive access
        self.org_external_ip_rate: float = 0.0     # fraction with external IP connections
        self.org_avg_upload_mb: float = 0.0        # avg MB per event
        self.org_usb_rate: float = 0.0             # fraction with USB usage

        self._compute(data_df)

    def _compute(self, df: pd.DataFrame):
        if df is None or len(df) == 0:
            return

        if 'anomaly_score' in df.columns:
            scores = df['anomaly_score'].dropna()
            if len(scores) > 0:
                self.mean_score = float(scores.mean())
                self.std_score  = float(scores.std()) or 0.01
                self.p50 = float(scores.quantile(0.50))
                self.p75 = float(scores.quantile(0.75))
                self.p90 = float(scores.quantile(0.90))
                self.p95 = float(scores.quantile(0.95))

        n = len(df)
        if n > 0:
            if 'is_off_hours' in df.columns:
                self.org_off_hours_rate = float(df['is_off_hours'].mean())
            if 'sensitive_file_access' in df.columns:
                self.org_sensitive_file_rate = float((df['sensitive_file_access'] > 0).mean())
            if 'external_ip_connection' in df.columns:
                self.org_external_ip_rate = float((df['external_ip_connection'] > 0).mean())
            if 'upload_size_mb' in df.columns:
                self.org_avg_upload_mb = float(df['upload_size_mb'].mean())
            if 'uses_usb' in df.columns:
                self.org_usb_rate = float(df['uses_usb'].mean())

    def to_dict(self) -> Dict:
        return {
            'mean_score': round(self.mean_score, 4),
            'std_score': round(self.std_score, 4),
            'p50': round(self.p50, 4),
            'p75': round(self.p75, 4),
            'p90': round(self.p90, 4),
            'p95': round(self.p95, 4),
            'org_off_hours_rate': round(self.org_off_hours_rate, 4),
            'org_sensitive_file_rate': round(self.org_sensitive_file_rate, 4),
            'org_external_ip_rate': round(self.org_external_ip_rate, 4),
            'org_avg_upload_mb': round(self.org_avg_upload_mb, 4),
            'org_usb_rate': round(self.org_usb_rate, 4),
        }


class UserProfile:
    """
    Manages behavioral profile for a single user.

    Calculates and tracks:
    - Normal behavior baseline (what's typical for this user)
    - Behavioral fingerprint (unique patterns)
    - Risk trajectory over time
    - Divergence from baseline
    - Global context (z-score vs the whole organisation)
    """

    def __init__(self, user_id: str, historical_events: pd.DataFrame,
                 global_baseline: Optional[GlobalOrgBaseline] = None):
        """
        Initialize user profile from historical events.

        Args:
            user_id: Unique user identifier
            historical_events: DataFrame of user's past events
            global_baseline: Org-wide baseline for meaningful comparison
        """
        self.user_id = user_id
        self.historical_events = historical_events
        self._global_baseline = global_baseline
        self.baseline = self.calculate_baseline()
        self.behavioral_fingerprint = self.create_behavioral_fingerprint()
        self.baseline_risk_level = self.categorize_baseline_risk()

    def calculate_baseline(self) -> Dict:
        """
        Calculate user's normal behavior baseline from historical data.

        Uses only "normal" events (anomaly_score < 0.1) to establish
        what is typical/expected for this user.

        Returns:
            Dictionary containing baseline metrics
        """
        # Filter to normal events only (not flagged as risky)
        if 'timestamp' in self.historical_events.columns:
            # Ensure timestamp is datetime for duration calculations
            self.historical_events['timestamp'] = pd.to_datetime(self.historical_events['timestamp'])

        if 'anomaly_score' in self.historical_events.columns:
            normal_events = self.historical_events[
                self.historical_events['anomaly_score'] < 0.1
            ]
        else:
            normal_events = self.historical_events

        if len(normal_events) == 0:
            return self._get_default_baseline()

        # Calculate baseline metrics
        self.baseline = {
            # File access patterns
            'avg_files_accessed': float(normal_events.get('file_access_count', pd.Series([0])).mean()),
            '90th_files_accessed': float(normal_events.get('file_access_count', pd.Series([0])).quantile(0.9)),

            # Upload patterns
            'avg_upload_size': float(normal_events.get('upload_size_mb', pd.Series([0])).mean()),
            '90th_upload_size': float(normal_events.get('upload_size_mb', pd.Series([0])).quantile(0.9)),

            # Temporal patterns
            'typical_hours': [int(h) for h in self._calculate_typical_hours(normal_events)],
            'typical_days': [int(d) for d in self._calculate_typical_days(normal_events)],
            'off_hours_frequency': float(self._calculate_off_hours_frequency(normal_events)),

            # Risk baseline (mean of "stable" behaviour)
            'baseline_score': float(normal_events.get('anomaly_score', pd.Series([0.0])).mean()),
            'mean_anomaly_score': float(normal_events.get('anomaly_score', pd.Series([0.0])).mean()),

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

        return self.baseline

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
            'baseline_score': 0.0,
            'baseline_score_std': 0.05,
            'events_per_day': 1.0,
            'historical_event_count': 0,
            'normal_event_count': 0,
            'baseline_confidence': 0.0
        }

    def _calculate_typical_hours(self, events: pd.DataFrame) -> List[int]:
        """Calculate user's typical work hours."""
        if 'timestamp' not in events.columns or len(events) == 0:
            return [9, 10, 11, 14, 15, 16]

        if 'hour_of_day' in events.columns:
            hours = events['hour_of_day']
        else:
            hours = pd.to_datetime(events['timestamp']).dt.hour

        hour_counts = hours.value_counts()
        cumulative_pct = hour_counts.sort_values(ascending=False).cumsum() / len(hours)
        typical_hours = cumulative_pct[cumulative_pct <= 0.8].index.tolist()

        return sorted(typical_hours) if typical_hours else [9, 10, 11, 14, 15, 16]

    def _calculate_typical_days(self, events: pd.DataFrame) -> List[int]:
        """Calculate user's typical work days (0=Monday, 6=Sunday)."""
        if 'timestamp' not in events.columns or len(events) == 0:
            return [0, 1, 2, 3, 4]

        if 'day_of_week' in events.columns:
            days = events['day_of_week']
        else:
            days = pd.to_datetime(events['timestamp']).dt.dayofweek

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
        Create a behavioral fingerprint — unique patterns for this user.
        Computes per-user rates so they can be compared to org averages.
        """
        ev = self.historical_events
        n = len(ev) or 1

        off_hours_rate = float(ev['is_off_hours'].mean()) if 'is_off_hours' in ev.columns else 0.0
        sensitive_rate = float((ev['sensitive_file_access'] > 0).mean()) if 'sensitive_file_access' in ev.columns else 0.0
        external_ip_rate = float((ev['external_ip_connection'] > 0).mean()) if 'external_ip_connection' in ev.columns else 0.0
        avg_upload_mb = float(ev['upload_size_mb'].mean()) if 'upload_size_mb' in ev.columns else 0.0
        usb_rate = float(ev['uses_usb'].mean()) if 'uses_usb' in ev.columns else 0.0
        avg_file_access = float(ev['file_access_count'].mean()) if 'file_access_count' in ev.columns else 0.0

        fingerprint = {
            # Rates (0-1) for easy comparison
            'off_hours_rate': round(off_hours_rate, 4),
            'sensitive_file_rate': round(sensitive_rate, 4),
            'external_ip_rate': round(external_ip_rate, 4),
            'usb_rate': round(usb_rate, 4),
            'avg_upload_mb': round(avg_upload_mb, 4),
            'avg_file_access_count': round(avg_file_access, 4),

            # Boolean flags (derived from rates for backwards compat)
            'uses_usb': self._check_usb_usage(),
            'accesses_sensitive_files': self._check_sensitive_access(),
            'avg_sensitive_files_per_event': self._calculate_avg_sensitive_access(),
            'works_weekends': self._check_weekend_work(),
            'works_off_hours': off_hours_rate > 0.1,
            'uses_external_ips': self._check_external_connections(),
            'typical_ip_count': self._calculate_typical_ip_count(),
            'has_elevated_privileges': self._check_privilege_use(),
            'is_high_activity_user': avg_file_access > 20,
            'is_data_heavy_user': avg_upload_mb > 50,

            # Legacy fields (kept for backward compat)
            'after_hours_ratio_mean': round(off_hours_rate, 4),
            'file_access_events_mean': round(avg_file_access, 4),
            'usb_usage_mean': round(usb_rate, 4),
            'sensitive_files_mean': round(sensitive_rate, 4),
        }

        return fingerprint

    def _check_usb_usage(self) -> bool:
        if 'uses_usb' in self.historical_events.columns:
            return bool(self.historical_events['uses_usb'].sum() > 0)
        return False

    def _check_sensitive_access(self) -> bool:
        if 'sensitive_file_access' in self.historical_events.columns:
            return bool(self.historical_events['sensitive_file_access'].sum() > 0)
        return False

    def _calculate_avg_sensitive_access(self) -> float:
        if 'sensitive_file_access' in self.historical_events.columns:
            return float(self.historical_events['sensitive_file_access'].mean())
        return 0.0

    def _check_weekend_work(self) -> bool:
        weekend_days = [5, 6]
        return any(day in self.baseline['typical_days'] for day in weekend_days)

    def _check_external_connections(self) -> bool:
        if 'external_ip_connection' in self.historical_events.columns:
            return bool(self.historical_events['external_ip_connection'].sum() > 0)
        return False

    def _calculate_typical_ip_count(self) -> int:
        return 1

    def _check_privilege_use(self) -> bool:
        return False

    def categorize_baseline_risk(self) -> str:
        """Categorize user risk based on density of high-anomaly events."""
        if 'anomaly_score' not in self.historical_events.columns or len(self.historical_events) == 0:
            return 'Low'

        score_data = self.historical_events['anomaly_score']
        critical_count = len(score_data[score_data >= 0.4])
        high_risk_count = len(score_data[score_data >= 0.25])

        if critical_count >= 15 or high_risk_count >= 50:
            return 'High'
        if critical_count >= 5 or high_risk_count >= 20:
            return 'Medium'
        return 'Low'

    def compute_global_context(self) -> Dict:
        """
        Compute how this user's risk profile compares to the org-wide baseline.

        Returns a dict with z-score relative to org, percentile band, per-metric
        comparisons (user rate vs org rate), and a plain-English risk_vs_org label.
        """
        gb = self._global_baseline
        ev = self.historical_events

        if gb is None or len(ev) == 0:
            return {
                'user_mean_score': 0.0,
                'global_mean': 0.0,
                'global_std': 0.1,
                'global_p50': 0.0,
                'global_p95': 0.0,
                'zscore_vs_global': 0.0,
                'pct_events_above_global_p95': 0.0,
                'risk_vs_org': 'average',
                'metrics': {},
            }

        if 'anomaly_score' in ev.columns:
            user_mean = float(ev['anomaly_score'].mean())
            pct_above_p95 = float((ev['anomaly_score'] > gb.p95).mean())
        else:
            user_mean = 0.0
            pct_above_p95 = 0.0

        zscore = (user_mean - gb.mean_score) / max(gb.std_score, 0.001)

        # Determine label
        if zscore > 1.5:
            risk_vs_org = 'high'
        elif zscore > 0.5:
            risk_vs_org = 'above_average'
        elif zscore < -0.5:
            risk_vs_org = 'below_average'
        else:
            risk_vs_org = 'average'

        # Per-metric comparisons (user value vs org average) — all already rates
        fp = self.behavioral_fingerprint
        metrics = {
            'off_hours': {
                'user': round(fp.get('off_hours_rate', 0.0), 4),
                'org':  round(gb.org_off_hours_rate, 4),
                'ratio': round(fp.get('off_hours_rate', 0.0) / max(gb.org_off_hours_rate, 0.001), 2),
            },
            'sensitive_file': {
                'user': round(fp.get('sensitive_file_rate', 0.0), 4),
                'org':  round(gb.org_sensitive_file_rate, 4),
                'ratio': round(fp.get('sensitive_file_rate', 0.0) / max(gb.org_sensitive_file_rate, 0.001), 2),
            },
            'external_ip': {
                'user': round(fp.get('external_ip_rate', 0.0), 4),
                'org':  round(gb.org_external_ip_rate, 4),
                'ratio': round(fp.get('external_ip_rate', 0.0) / max(gb.org_external_ip_rate, 0.001), 2),
            },
            'upload_mb': {
                'user': round(fp.get('avg_upload_mb', 0.0), 4),
                'org':  round(gb.org_avg_upload_mb, 4),
                'ratio': round(fp.get('avg_upload_mb', 0.0) / max(gb.org_avg_upload_mb, 0.001), 2),
            },
            'usb': {
                'user': round(fp.get('usb_rate', 0.0), 4),
                'org':  round(gb.org_usb_rate, 4),
                'ratio': round(fp.get('usb_rate', 0.0) / max(gb.org_usb_rate, 0.001), 2),
            },
        }

        return {
            'user_mean_score': round(user_mean, 4),
            'global_mean': round(gb.mean_score, 4),
            'global_std': round(gb.std_score, 4),
            'global_p50': round(gb.p50, 4),
            'global_p95': round(gb.p95, 4),
            'zscore_vs_global': round(zscore, 2),
            'pct_events_above_global_p95': round(pct_above_p95 * 100, 2),
            'risk_vs_org': risk_vs_org,
            'metrics': metrics,
        }

    def calculate_divergence(self, new_event: pd.Series) -> Dict:
        """
        Calculate how much a new event diverges from this user's baseline.
        """
        divergence_score = 0.0
        divergence_details = []

        if isinstance(new_event, pd.Series):
            event = new_event.to_dict()
        else:
            event = new_event

        if 'file_access_count' in event:
            file_z_score = (
                (event['file_access_count'] - self.baseline['avg_files_accessed']) /
                max(self.baseline.get('std_files_accessed', 1.0), 1.0)
            )
            if abs(file_z_score) > 2.0:
                divergence_score += abs(file_z_score) * 0.2
                divergence_details.append(
                    f"File access {abs(file_z_score):.1f}x above normal baseline"
                )

        if 'upload_size_mb' in event:
            upload_z_score = (
                (event['upload_size_mb'] - self.baseline['avg_upload_size']) /
                max(self.baseline.get('std_upload_size', 1.0), 1.0)
            )
            if abs(upload_z_score) > 2.0:
                divergence_score += abs(upload_z_score) * 0.3
                divergence_details.append(
                    f"Upload size {abs(upload_z_score):.1f}x above normal baseline"
                )

        if event.get('uses_usb', False) and not self.behavioral_fingerprint['uses_usb']:
            divergence_score += 0.5
            divergence_details.append("NEW BEHAVIOR: USB usage (never seen before)")

        if 'is_off_hours' in event:
            if event['is_off_hours'] and not self.behavioral_fingerprint['works_off_hours']:
                divergence_score += 0.3
                divergence_details.append("OFF-HOURS: Activity outside typical work hours")

        if 'sensitive_file_access' in event:
            if event['sensitive_file_access'] > 0:
                expected = self.behavioral_fingerprint['avg_sensitive_files_per_event']
                if event['sensitive_file_access'] > expected * 3:
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
        if score > 1.0:
            return 'High'
        elif score > 0.5:
            return 'Medium'
        else:
            return 'Low'

    def to_dict(self) -> Dict:
        """Export profile as dictionary for API responses."""
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
            }),
            'global_context': _to_native(self.compute_global_context()),
        }


class UserProfileManager:
    """
    Manages profiles for all users.
    Handles loading, caching, and updating profiles.
    """

    def __init__(self, data_df: pd.DataFrame):
        self.data_df = data_df
        self.profiles = {}
        # Compute global org-wide baseline once
        self.global_baseline = GlobalOrgBaseline(data_df)
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

    def get_or_create_profile(self, user_id: str) -> 'UserProfile':
        if user_id in self.profiles:
            return self.profiles[user_id]

        user_events = self.data_df[self.data_df['user_id'] == user_id].copy()
        profile = UserProfile(user_id, user_events, global_baseline=self.global_baseline)
        self.profiles[user_id] = profile
        return profile

    def get_profile(self, user_id: str) -> Optional['UserProfile']:
        return self.profiles.get(user_id)

    def get_all_users(self) -> List[Dict]:
        users = []
        for user_id, profile in self.profiles.items():
            gc = profile.compute_global_context()
            users.append({
                'user_id': user_id,
                'event_count': profile.baseline['historical_event_count'],
                'baseline_risk_level': profile.baseline_risk_level,
                'baseline_score': profile.baseline['baseline_score'],
                'confidence': profile.baseline['baseline_confidence'],
            })

        risk_order = {'High': 0, 'Medium': 1, 'Low': 2}
        users.sort(key=lambda x: (risk_order.get(x['baseline_risk_level'], 3), -x['baseline_score']))
        return users

    def update_profile(self, user_id: str, new_events: pd.DataFrame):
        if user_id in self.profiles:
            updated_events = pd.concat([
                self.profiles[user_id].historical_events,
                new_events
            ], ignore_index=True)
            self.profiles[user_id] = UserProfile(user_id, updated_events,
                                                  global_baseline=self.global_baseline)
        else:
            self.profiles[user_id] = UserProfile(user_id, new_events,
                                                  global_baseline=self.global_baseline)


# Global instance (will be initialized by API)
profile_manager: Optional[UserProfileManager] = None


def initialize_profile_manager(data_df: pd.DataFrame):
    global profile_manager
    profile_manager = UserProfileManager(data_df)
    return profile_manager


def get_profile_manager() -> Optional[UserProfileManager]:
    return profile_manager
