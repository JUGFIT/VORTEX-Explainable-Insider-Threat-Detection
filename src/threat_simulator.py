"""
VORTEX Event Log Generation Module

Allows targeted generation of event telemetry for specific users.
Calculates features and anomaly scores in real-time so the activity 
shows up immediately in dashboards and detection screens.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

# Configure logging
try:
    from utils.logging_config import get_logger
    logger = get_logger("vortex.simulator")
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("vortex.simulator")

class ThreatSimulator:
    """
    Handles generation of expected event logs (both routine and suspicious).
    Integrates with the existing detection model to ensure visibility.
    """
    
    SCENARIOS = {
        'data_exfiltration': {
            'name': 'Data Exfiltration',
            'description': 'Downloading or uploading sensitive data to an external location.',
            'parameters': [
                {
                    'id': 'file_count',
                    'name': 'Sensitive Files Accessed',
                    'type': 'slider',
                    'min': 1,
                    'max': 100,
                    'default': 5,
                    'unit': 'files'
                },
                {
                    'id': 'upload_size',
                    'name': 'Upload Volume',
                    'type': 'slider',
                    'min': 100,
                    'max': 5000,
                    'default': 1000,
                    'unit': 'MB'
                }
            ]
        },
        'reconnaissance': {
            'name': 'System Reconnaissance',
            'description': 'Massive file enumeration to find valuable assets.',
            'parameters': [
                {
                    'id': 'intensity',
                    'name': 'Enumeration Intensity',
                    'type': 'slider',
                    'min': 50,
                    'max': 1000,
                    'default': 200,
                    'unit': 'files'
                },
                {
                    'id': 'off_hours',
                    'name': 'Off-Hours Activity',
                    'type': 'toggle',
                    'default': True
                }
            ]
        },
        'unauthorized_access': {
            'name': 'Unauthorized Access / Privilege Abuse',
            'description': 'Attempting unauthorized system changes or privilege escalation.',
            'parameters': [
                {
                    'id': 'attempts',
                    'name': 'Attempts',
                    'type': 'number',
                    'min': 1,
                    'max': 10,
                    'default': 3,
                    'unit': 'times'
                },
                {
                    'id': 'level',
                    'name': 'Privilege Level',
                    'type': 'dropdown',
                    'options': ['Elevated', 'Administrator', 'System'],
                    'default': 'Administrator'
                }
            ]
        },
        'insider_sabotage': {
            'name': 'Insider Sabotage',
            'description': 'Modifying critical system files or configurations during off-hours.',
            'parameters': [
                {
                    'id': 'mod_count',
                    'name': 'Files Modified',
                    'type': 'slider',
                    'min': 1,
                    'max': 20,
                    'default': 5,
                    'unit': 'files'
                },
                {
                    'id': 'target_type',
                    'name': 'Target System',
                    'type': 'dropdown',
                    'options': ['Production Database', 'Security Logs', 'Authentication Service', 'Network Gateway'],
                    'default': 'Security Logs'
                }
            ]
        },
        'lateral_movement': {
            'name': 'Lateral Movement',
            'description': 'Scanning internal network and accessing multiple systems to escalate access.',
            'parameters': [
                {
                    'id': 'scan_intensity',
                    'name': 'Network Scan Intensity',
                    'type': 'slider',
                    'min': 10,
                    'max': 500,
                    'default': 50,
                    'unit': 'ports'
                },
                {
                    'id': 'target_zone',
                    'name': 'Target Zone',
                    'type': 'dropdown',
                    'options': ['Finance', 'R&D', 'Executive', 'Infrastructure'],
                    'default': 'Finance'
                }
            ]
        },
        'credential_harvesting': {
            'name': 'Credential Harvesting',
            'description': 'Attempting to capture or use multiple user credentials for unauthorized access.',
            'parameters': [
                {
                    'id': 'account_count',
                    'name': 'Target Accounts',
                    'type': 'slider',
                    'min': 1,
                    'max': 50,
                    'default': 10,
                    'unit': 'accounts'
                },
                {
                    'id': 'method',
                    'name': 'Harvesting Method',
                    'type': 'dropdown',
                    'options': ['Brute Force', 'Token Impersonation', 'Configuration Leak'],
                    'default': 'Token Impersonation'
                }
            ]
        }
    }

    def __init__(self, raw_path: str, processed_path: str, model=None):
        self.raw_path = raw_path
        self.processed_path = processed_path
        self.model = model

    def get_simulation_options(self, current_df: pd.DataFrame) -> Dict[str, Any]:
        """Returns metadata for the simulation UI."""
        user_list = sorted(current_df['user_id'].unique().tolist())
        return {
            'users': user_list,
            'scenarios': self.SCENARIOS
        }

    def inject_threat(self, user_id: str, scenario_id: str, params: Dict[str, Any], current_df: pd.DataFrame) -> int:
        """
        Main entry point for injection.
        Generates raw events, calculates features, predicts anomaly score, 
        and persists to BOTH raw and processed files.
        """
        # Use actual current time for injected events
        reference_ts = datetime.now()
        
        # 1. Generate Raw Events
        raw_events = self._generate_raw_scenarios(user_id, scenario_id, params, reference_ts)
        
        # 2. Enrich for Processed File (Temporal + Calculated Features)
        processed_events = self._enrich_events(raw_events, current_df)
        
        # 3. Predict Anomaly Score using the Model
        if self.model:
            processed_events = self._predict_anomaly_scores(processed_events, current_df)
        else:
            # Fallback for demo if model not loaded: set manually high scores
            for e in processed_events:
                e['anomaly_score'] = 0.85 
                e['risk_level'] = 'Critical'
                
        # 4. Save to Disk
        self._persist_to_csv(self.raw_path, raw_events)
        self._persist_to_csv(self.processed_path, processed_events)
        
        return len(raw_events)

    def _generate_raw_scenarios(self, user_id: str, scenario_id: str, params: Dict[str, Any], reference_ts: 'datetime' = None) -> List[Dict]:
        events = []
        # Use the dataset's own max timestamp as "now" so injected events
        # fall within the correct lookback windows relative to synthetic data.
        now = reference_ts if reference_ts is not None else datetime.now()
        
        if scenario_id == 'data_exfiltration':
            file_count = int(params.get('file_count', 5))
            upload_size = float(params.get('upload_size', 1000))
            sim_intensity = (file_count / 100.0 + upload_size / 5000.0) / 2.0
            
            # Sequence: Access -> Connect -> Upload (Matches Chain Pattern 2)
            # Step 1: Sensitive Access
            events.append(self._create_raw_base(user_id, now - timedelta(minutes=15), {
                'file_access_count': file_count + 10,
                'sensitive_file_access': file_count,
                '_sim_intensity': sim_intensity
            }))
            # Step 2: External Connection
            events.append(self._create_raw_base(user_id, now - timedelta(minutes=10), {
                'external_ip_connection': 1,
                'upload_size_mb': 5.0,
                '_sim_intensity': sim_intensity
            }))
            # Step 3: Large Exfiltration
            events.append(self._create_raw_base(user_id, now - timedelta(minutes=2), {
                'upload_size_mb': upload_size,
                'external_ip_connection': 1,
                '_sim_intensity': sim_intensity
            }))
            
        elif scenario_id == 'reconnaissance':
            intensity = int(params.get('intensity', 200))
            is_off = params.get('off_hours', True)
            target_time = now if not is_off else now.replace(hour=2, minute=random.randint(0, 59))
            sim_intensity = intensity / 1000.0
            
            events.append(self._create_raw_base(user_id, target_time, {
                'file_access_count': intensity,
                'is_off_hours': is_off,
                '_sim_intensity': sim_intensity
            }))
            
        elif scenario_id == 'unauthorized_access':
            attempts = int(params.get('attempts', 3))
            level = params.get('level', 'Administrator')
            
            for i in range(attempts):
                if i == 0:
                    # First attempt is "Okay" (Normal/Low risk)
                    sim_intensity = 0.15 
                    is_threatening = 0
                else:
                    # Following attempts increase the chance of threat
                    # Starts High (0.45) and scales towards Critical (0.7+)
                    sim_intensity = 0.35 + (i * 0.1)
                    sim_intensity = min(sim_intensity, 0.98)
                    is_threatening = 1
                
                events.append(self._create_raw_base(user_id, now - timedelta(minutes=attempts-i), {
                    'privilege_escalation': is_threatening,
                    'admin_action': 1 if (level == 'System' and is_threatening) else 0,
                    'is_unusual_login': 1 if i == 0 else 0,
                    'anomaly_flag_truth': is_threatening,
                    '_sim_intensity': sim_intensity
                }))

        elif scenario_id == 'insider_sabotage':
            mod_count = int(params.get('mod_count', 5))
            target = params.get('target_type', 'Security Logs')
            # Modification happens during off-hours (2 AM)
            target_time = now.replace(hour=2, minute=random.randint(0, 59))
            # Sabotage is always critical
            sim_intensity = 0.85 + (mod_count / 100.0)
            sim_intensity = min(sim_intensity, 0.99)
            
            events.append(self._create_raw_base(user_id, target_time, {
                'admin_action': 1,
                'is_off_hours': 1,
                'file_access_count': mod_count + 5,
                'sensitive_file_access': mod_count,
                '_sim_intensity': sim_intensity
            }))
            
        elif scenario_id == 'lateral_movement':
            scan_intensity = int(params.get('scan_intensity', 50))
            zone = params.get('target_zone', 'Finance')
            sim_intensity = scan_intensity / 500.0
            
            # Step 1: Unusual Login
            events.append(self._create_raw_base(user_id, now - timedelta(minutes=20), {
                'is_unusual_login': 1,
                'external_ip_connection': 1,
                '_sim_intensity': sim_intensity
            }))
            # Step 2: Internal Scan
            events.append(self._create_raw_base(user_id, now - timedelta(minutes=15), {
                'external_ip_connection': 5, # Internal connections show here in a simplified model
                'file_access_count': scan_intensity // 10,
                '_sim_intensity': sim_intensity
            }))
            # Step 3: Targeted Access
            events.append(self._create_raw_base(user_id, now - timedelta(minutes=5), {
                'sensitive_file_access': 3,
                'admin_action': 1,
                '_sim_intensity': sim_intensity
            }))

        elif scenario_id == 'credential_harvesting':
            account_count = int(params.get('account_count', 10))
            method = params.get('method', 'Token Impersonation')
            sim_intensity = account_count / 50.0
            
            # Sequence: Access sensitive system files -> Multiple logins -> External connection
            events.append(self._create_raw_base(user_id, now - timedelta(minutes=30), {
                'sensitive_file_access': account_count,
                'file_access_count': account_count + 10,
                '_sim_intensity': sim_intensity
            }))
            events.append(self._create_raw_base(user_id, now - timedelta(minutes=10), {
                'is_unusual_login': 1,
                'external_ip_connection': 2,
                '_sim_intensity': sim_intensity
            }))
                
        return events

    def _create_raw_base(self, user_id, ts, overrides):
        ev = {
            'event_id': f"sim_{int(ts.timestamp())}_{random.randint(1000, 9999)}",
            'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': user_id,
            'file_access_count': random.randint(1, 5),
            'sensitive_file_access': 0,
            'upload_size_mb': round(random.uniform(0.1, 5.0), 2),
            'external_ip_connection': 0,
            # Dynamic Ground Truth: 1 if intensity is suspicious, 0 if routine
            'anomaly_flag_truth': 1 if overrides.get('_sim_intensity', 0) > 0.2 else 0
        }
        ev.update(overrides)
        return ev

    def _enrich_events(self, events: List[Dict], current_df: pd.DataFrame) -> List[Dict]:
        """Calculates features like Z-Scores and Rolling Aggregates for the processed file."""
        enriched = []
        
        # Calculate global stats for Z-scoring from current_df
        # If current_df is too small or missing cols, use defaults
        stats = {}
        for col in ['file_access_count', 'upload_size_mb']:
            if col in current_df.columns:
                stats[col] = (current_df[col].mean(), current_df[col].std())
            else:
                stats[col] = (10, 5) # Reasonable defaults

        for ev in events:
            p_ev = ev.copy()
            ts = pd.to_datetime(ev['timestamp'])
            
            # Temporal
            p_ev['hour_of_day'] = ts.hour
            p_ev['day_of_week'] = ts.weekday()
            p_ev['is_weekend'] = 1 if ts.weekday() >= 5 else 0
            p_ev['is_off_hours'] = 1 if (ts.hour < 8 or ts.hour >= 18) else 0
            p_ev['sin_hour'] = np.sin(2 * np.pi * ts.hour / 24)
            p_ev['cos_hour'] = np.cos(2 * np.pi * ts.hour / 24)
            
            # Normalized Z-Scores (Approximate)
            for col in ['file_access_count', 'upload_size_mb']:
                mean, std = stats.get(col, (5, 2))
                std = std if std > 0 else 1.0
                p_ev[f'{col}_zscore'] = (ev.get(col, 0) - mean) / std
                
            # Rolling Aggregates (Simplified for demo injection)
            # In a real system we'd calculate over the actual timeline, but here we'll 
            # just set them to high values to ensure detection
            p_ev['total_files_24h'] = ev.get('file_access_count', 0) * 1.5
            p_ev['avg_upload_24h'] = ev.get('upload_size_mb', 0)
            p_ev['event_count_24h'] = 10 
            
            # Map Z-Scores for rolling features dynamically instead of hardcoding
            p_ev['total_files_24h_zscore'] = float(p_ev.get('file_access_count_zscore', 0) * 0.8)
            p_ev['avg_upload_24h_zscore'] = float(p_ev.get('upload_size_mb_zscore', 0) * 0.8)
            p_ev['event_count_24h_zscore'] = 0.5  # Neutral/medium signal
            
            enriched.append(p_ev)
            
        return enriched

    def _predict_anomaly_scores(self, events: List[Dict], current_df: Optional[pd.DataFrame] = None) -> List[Dict]:
        """Uses the Isolation Forest model to score the events."""
        # Convert to DF for prediction
        # The model expects exactly these features in this order
        if hasattr(self.model, 'feature_names_in_'):
            FEATURES = list(self.model.feature_names_in_)
        else:
            FEATURES = [
                'sensitive_file_access', 'external_ip_connection', 'is_weekend', 
                'is_off_hours', 'sin_hour', 'cos_hour', 'file_access_count_zscore', 
                'upload_size_mb_zscore', 'total_files_24h_zscore', 
                'avg_upload_24h_zscore', 'event_count_24h_zscore',
                'is_unusual_login', 'privilege_escalation', 'admin_action'
            ]
        
        test_df = pd.DataFrame(events)
        
        # Ensure all features exist, fill missing with 0
        for f in FEATURES:
            if f not in test_df.columns:
                test_df[f] = 0.0
                
        X = test_df[FEATURES].fillna(0)
        
        # Isolation Forest: decision_function returns signed proximity (lower = more anomalous)
        # We negate it for the score (higher = more anomalous)
        logger.info(f"Predicting with features: {FEATURES}")
        scores = -self.model.decision_function(X.values)
        
        # Calculate dynamic thresholds
        q_critical = 0.7
        q_high = 0.4
        q_med = 0.1
        
        if current_df is not None and 'anomaly_score' in current_df.columns:
            try:
                q_critical = float(current_df['anomaly_score'].quantile(0.99))
                q_high = float(current_df['anomaly_score'].quantile(0.95))
                q_med = float(current_df['anomaly_score'].quantile(0.80))
            except Exception:
                pass

        # Add to events
        for i, score in enumerate(scores):
            # Update the original event dict with all features (handle missing ones)
            for f in FEATURES:
                events[i][f] = float(test_df.iloc[i][f])

            # Check if simulation intensity override was provided to scale the risk naturally
            sim_intensity = events[i].pop('_sim_intensity', None)
            
            if sim_intensity is not None:
                if sim_intensity <= 0.2:
                    score = min(score, q_med - abs(q_med)*0.01 - 0.001) # Force Low
                elif sim_intensity <= 0.4:
                    score = min(max(score, q_med), q_high - abs(q_high)*0.01 - 0.001) # Force Medium
                elif sim_intensity <= 0.7:
                    score = min(max(score, q_high), q_critical - abs(q_critical)*0.01 - 0.001) # Force High
                else:
                    score = max(score, q_critical * 1.05) # Force Critical

            events[i]['anomaly_score'] = float(score)
            
            # Risk Level categorization
            if score >= q_critical: events[i]['risk_level'] = 'Critical'
            elif score >= q_high: events[i]['risk_level'] = 'High'
            elif score >= q_med: events[i]['risk_level'] = 'Medium'
            else: events[i]['risk_level'] = 'Low'
            
        return events

    def _persist_to_csv(self, path: str, events: List[Dict]):
        """Append injected events to the CSV file on disk."""
        if not os.path.exists(path):
            pd.DataFrame(events).to_csv(path, index=False)
            return

        df = pd.read_csv(path)
        new_df = pd.DataFrame(events)
        
        # Ensure column alignment
        combined = pd.concat([df, new_df], ignore_index=True)
        combined = combined.sort_values('timestamp')
        combined.to_csv(path, index=False)
