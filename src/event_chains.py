"""
Event Chain Detection System

Detects sequences of events that form known attack patterns.

Key Features:
- Pre-defined attack patterns (data exfiltration, insider threat, reconnaissance)
- Temporal chain matching (events within time window)
- Risk amplification (chain risk > sum of parts)
- Attack narrative generation (human-readable stories)
- Phase detection (reconnaissance → execution → exfiltration)

Author: VORTEX Team
Phase: 2A - Core Infrastructure (Session 4)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict


class EventChainDetector:
    """
    Detects multi-event attack chains in user behavior.
    
    Analyzes sequences of events to identify known attack patterns.
    Chains are more dangerous than individual events - risk is amplified.
    """
    
    # Pre-defined attack patterns
    # Each pattern is a list of required event characteristics
    ATTACK_PATTERNS = {
        'data_exfiltration': {
            'name': 'Data Exfiltration Attack',
            'severity': 'Critical',
            'patterns': [
                # Pattern 1: Classic exfiltration
                {
                    'sequence': ['off_hours_access', 'mass_file_access', 'large_upload'],
                    'description': 'Off-hours access followed by mass file access and large upload',
                    'min_events': 3,
                    'max_time_window_hours': 8
                },
                # Pattern 2: Stealthy exfiltration
                {
                    'sequence': ['sensitive_file_access', 'external_connection', 'repeated_uploads'],
                    'description': 'Sensitive file access with external connection and repeated uploads',
                    'min_events': 3,
                    'max_time_window_hours': 24
                },
                # Pattern 3: USB exfiltration
                {
                    'sequence': ['privilege_escalation', 'mass_file_access', 'usb_usage'],
                    'description': 'Privilege escalation, mass file access, then USB usage',
                    'min_events': 3,
                    'max_time_window_hours': 4
                }
            ],
            'amplification_factor': 2.0
        },
        
        'insider_threat': {
            'name': 'Insider Threat Pattern',
            'severity': 'High',
            'patterns': [
                # Pattern 1: Revenge/sabotage
                {
                    'sequence': ['off_hours', 'privilege_use', 'system_modification'],
                    'description': 'Off-hours activity with privilege abuse and system changes',
                    'min_events': 3,
                    'max_time_window_hours': 12
                },
                # Pattern 2: Data theft
                {
                    'sequence': ['unusual_login', 'sensitive_access', 'external_connection'],
                    'description': 'Unusual login accessing sensitive files with external connection',
                    'min_events': 3,
                    'max_time_window_hours': 6
                }
            ],
            'amplification_factor': 1.8
        },
        
        'reconnaissance': {
            'name': 'Reconnaissance Activity',
            'severity': 'Medium',
            'patterns': [
                # Pattern 1: Information gathering
                {
                    'sequence': ['unusual_login', 'mass_file_enum', 'minimal_upload'],
                    'description': 'Login followed by file enumeration without upload',
                    'min_events': 2,
                    'max_time_window_hours': 4
                },
                # Pattern 2: System mapping
                {
                    'sequence': ['privilege_check', 'system_access', 'network_scan'],
                    'description': 'Privilege checking with system and network access',
                    'min_events': 2,
                    'max_time_window_hours': 8
                }
            ],
            'amplification_factor': 1.5
        },
        
        'privilege_abuse': {
            'name': 'Privilege Abuse Pattern',
            'severity': 'High',
            'patterns': [
                # Pattern 1: Escalation and exploitation
                {
                    'sequence': ['privilege_escalation', 'unauthorized_access', 'data_modification'],
                    'description': 'Privilege escalation followed by unauthorized access and changes',
                    'min_events': 3,
                    'max_time_window_hours': 6
                }
            ],
            'amplification_factor': 1.9
        }
    }
    
    def __init__(self, user_id: str, events: pd.DataFrame, time_window_hours: int = 24):
        """
        Initialize event chain detector for a user.
        
        Args:
            user_id: User identifier
            events: DataFrame of user's events
            time_window_hours: Maximum time window for chains (default: 24 hours)
        """
        self.user_id = user_id
        self.events = events.copy()
        self.time_window_hours = time_window_hours
        
        # Ensure timestamp is datetime
        if 'timestamp' in self.events.columns:
            self.events['timestamp'] = pd.to_datetime(self.events['timestamp'])
            self.events = self.events.sort_values('timestamp')
        
        self.detected_chains = []
        self._detect_chains()
    
    def _classify_event(self, event: pd.Series) -> Set[str]:
        """
        Classify an event based on its characteristics.
        
        Returns a set of tags describing the event (e.g., 'off_hours', 'mass_file_access')
        """
        tags = set()
        
        # Off-hours access (before 6 AM or after 10 PM)
        if 'hour_of_day' in event:
            hour = event['hour_of_day']
            if hour < 6 or hour >= 22:
                tags.add('off_hours_access')
                tags.add('off_hours')
        
        if event.get('is_off_hours', False):
            tags.add('off_hours_access')
            tags.add('off_hours')
        
        # Mass file access (>20 files)
        if 'file_access_count' in event:
            if event['file_access_count'] > 20:
                tags.add('mass_file_access')
            if event['file_access_count'] > 50:
                tags.add('mass_file_enum')
        
        # Large upload (>50 MB)
        if 'upload_size_mb' in event:
            if event['upload_size_mb'] > 50:
                tags.add('large_upload')
            if event['upload_size_mb'] < 1:
                tags.add('minimal_upload')
            if event['upload_size_mb'] > 10:  # Multiple uploads
                tags.add('repeated_uploads')
        
        # Sensitive file access
        if event.get('sensitive_file_access', 0) > 0:
            tags.add('sensitive_file_access')
            tags.add('sensitive_access')
        
        # External connection
        if event.get('external_ip_connection', 0) > 0:
            tags.add('external_connection')
        
        # USB usage
        if event.get('uses_usb', False):
            tags.add('usb_usage')
        
        # Privilege patterns
        if event.get('privilege_escalation', False):
            tags.add('privilege_escalation')
            tags.add('privilege_use')
        
        # Unusual login (new location, new time, etc.)
        if event.get('is_unusual_login', False):
            tags.add('unusual_login')
        
        # Weekend access
        if 'day_of_week' in event:
            if event['day_of_week'] >= 5:  # Saturday or Sunday
                tags.add('weekend_access')
        
        # System access (admin actions, etc.)
        if event.get('admin_action', False):
            tags.add('system_access')
            tags.add('system_modification')
        
        # High risk event
        if 'risk_level' in event:
            if event['risk_level'] == 'High':
                tags.add('high_risk_action')
        
        # Catch-all for any high-risk indicators
        if event.get('anomaly_score', 0) < -0.6:
            tags.add('high_risk_action')
        
        return tags
    
    def _detect_chains(self):
        """
        Detect attack chains in user's events.
        
        Scans through events looking for patterns that match known attack chains.
        """
        if len(self.events) < 2:
            return  # Need at least 2 events to form a chain
        
        # Classify all events
        event_tags = []
        for idx, event in self.events.iterrows():
            tags = self._classify_event(event)
            event_tags.append({
                'index': idx,
                'timestamp': event.get('timestamp', datetime.now()),
                'event_id': event.get('event_id', f'evt_{idx}'),
                'tags': tags,
                'anomaly_score': event.get('anomaly_score', 0),
                'risk_level': event.get('risk_level', 'Low')
            })
        
        # Look for pattern matches
        for pattern_type, pattern_config in self.ATTACK_PATTERNS.items():
            for pattern_def in pattern_config['patterns']:
                chains = self._find_pattern_matches(
                    event_tags,
                    pattern_def,
                    pattern_type,
                    pattern_config
                )
                self.detected_chains.extend(chains)
        
        # Sort chains by risk (highest first)
        self.detected_chains.sort(key=lambda x: x['chain_risk'], reverse=True)
    
    def _find_pattern_matches(
        self,
        event_tags: List[Dict],
        pattern_def: Dict,
        pattern_type: str,
        pattern_config: Dict
    ) -> List[Dict]:
        """
        Find all instances of a specific pattern in the events.
        
        Args:
            event_tags: List of classified events
            pattern_def: Pattern definition to match
            pattern_type: Type of pattern (e.g., 'data_exfiltration')
            pattern_config: Overall pattern configuration
            
        Returns:
            List of detected chains
        """
        chains = []
        sequence = pattern_def['sequence']
        max_window = timedelta(hours=pattern_def['max_time_window_hours'])
        
        # Sliding window approach
        for i in range(len(event_tags)):
            start_event = event_tags[i]
            
            # Check if this event could start the pattern
            if not any(tag in start_event['tags'] for tag in [sequence[0], sequence[0].replace('_', ' ')]):
                # First tag doesn't match - check alternative naming
                first_tag_match = False
                for tag in start_event['tags']:
                    if sequence[0] in tag or tag in sequence[0]:
                        first_tag_match = True
                        break
                if not first_tag_match:
                    continue
            
            # Try to match the rest of the sequence
            matched_events = [start_event]
            matched_indices = {0}  # Track which sequence positions are matched
            
            # Look ahead for matching events within time window
            for j in range(i + 1, len(event_tags)):
                check_event = event_tags[j]
                
                # Check if within time window
                time_diff = check_event['timestamp'] - start_event['timestamp']
                if time_diff > max_window:
                    break  # Too far in time
                
                # Check if this event matches any remaining sequence position
                for seq_idx in range(1, len(sequence)):
                    if seq_idx in matched_indices:
                        continue  # Already matched
                    
                    required_tag = sequence[seq_idx]
                    # Flexible matching - check if tag contains or is contained
                    tag_match = False
                    for event_tag in check_event['tags']:
                        if required_tag in event_tag or event_tag in required_tag:
                            tag_match = True
                            break
                    
                    if tag_match:
                        matched_events.append(check_event)
                        matched_indices.add(seq_idx)
                        break  # Matched this event, move to next
            
            # Check if we matched enough events
            if len(matched_events) >= pattern_def['min_events']:
                # Calculate chain risk
                individual_risks = [e['anomaly_score'] for e in matched_events]
                sum_risk = sum(individual_risks)
                amplified_risk = sum_risk * pattern_config['amplification_factor']
                
                chain = {
                    'chain_id': f"{pattern_type}_{i}_{datetime.now().timestamp()}",
                    'user_id': self.user_id,
                    'pattern_type': pattern_type,
                    'pattern_name': pattern_config['name'],
                    'severity': pattern_config['severity'],
                    'pattern_description': pattern_def['description'],
                    'events': matched_events,
                    'event_count': len(matched_events),
                    'start_time': matched_events[0]['timestamp'],
                    'end_time': matched_events[-1]['timestamp'],
                    'duration_hours': (matched_events[-1]['timestamp'] - matched_events[0]['timestamp']).total_seconds() / 3600,
                    'individual_risk_sum': round(sum_risk, 4),
                    'chain_risk': round(amplified_risk, 4),
                    'amplification_factor': pattern_config['amplification_factor'],
                    'matched_sequence': [sequence[i] for i in sorted(matched_indices)],
                    'narrative': self._build_narrative(matched_events, pattern_def, pattern_config)
                }
                
                chains.append(chain)
        
        return chains
    
    def _build_narrative(
        self,
        events: List[Dict],
        pattern_def: Dict,
        pattern_config: Dict
    ) -> str:
        """
        Build a human-readable narrative describing the attack chain.
        
        Args:
            events: List of events in the chain
            pattern_def: Pattern definition
            pattern_config: Pattern configuration
            
        Returns:
            Narrative string
        """
        if len(events) == 0:
            return "No events in chain"
        
        start_time = events[0]['timestamp'].strftime('%Y-%m-%d %H:%M')
        end_time = events[-1]['timestamp'].strftime('%H:%M')
        duration = (events[-1]['timestamp'] - events[0]['timestamp']).total_seconds() / 3600
        
        narrative = f"**{pattern_config['name']} Detected**\n\n"
        narrative += f"**Severity**: {pattern_config['severity']}\n"
        narrative += f"**Time Window**: {start_time} to {end_time} ({duration:.1f} hours)\n"
        narrative += f"**Pattern**: {pattern_def['description']}\n\n"
        narrative += f"**Event Sequence**:\n"
        
        for idx, event in enumerate(events, 1):
            time_str = event['timestamp'].strftime('%H:%M')
            risk_str = event['risk_level']
            tags_str = ', '.join(list(event['tags'])[:3])  # Top 3 tags
            
            narrative += f"{idx}. [{time_str}] {tags_str} (Risk: {risk_str})\n"
        
        narrative += f"\n**Risk Assessment**:\n"
        narrative += f"- Individual event risks: {', '.join([str(round(e['anomaly_score'], 2)) for e in events])}\n"
        narrative += f"- Combined risk (sum): {sum(e['anomaly_score'] for e in events):.2f}\n"
        narrative += f"- Amplified chain risk: {sum(e['anomaly_score'] for e in events) * pattern_config['amplification_factor']:.2f}\n"
        narrative += f"- Amplification factor: {pattern_config['amplification_factor']}x\n"
        
        return narrative
    
    def get_chains(self, min_severity: Optional[str] = None) -> List[Dict]:
        """
        Get detected chains, optionally filtered by severity.
        
        Args:
            min_severity: Minimum severity ('Medium', 'High', 'Critical')
            
        Returns:
            List of detected chains
        """
        if min_severity is None:
            return self.detected_chains
        
        severity_order = {'Medium': 0, 'High': 1, 'Critical': 2}
        min_level = severity_order.get(min_severity, 0)
        
        filtered = [
            chain for chain in self.detected_chains
            if severity_order.get(chain['severity'], 0) >= min_level
        ]
        
        return filtered
    
    def get_summary(self) -> Dict:
        """
        Get summary of detected chains.
        
        Returns:
            Dictionary with chain statistics
        """
        if len(self.detected_chains) == 0:
            return {
                'user_id': self.user_id,
                'total_chains': 0,
                'chains_by_severity': {},
                'chains_by_type': {},
                'highest_risk': 0.0,
                'most_dangerous_pattern': None
            }
        
        chains_by_severity = defaultdict(int)
        chains_by_type = defaultdict(int)
        
        for chain in self.detected_chains:
            chains_by_severity[chain['severity']] += 1
            chains_by_type[chain['pattern_type']] += 1
        
        most_dangerous = max(self.detected_chains, key=lambda x: x['chain_risk'])
        
        return {
            'user_id': self.user_id,
            'total_chains': len(self.detected_chains),
            'chains_by_severity': dict(chains_by_severity),
            'chains_by_type': dict(chains_by_type),
            'highest_risk': round(most_dangerous['chain_risk'], 4),
            'most_dangerous_pattern': most_dangerous['pattern_name'],
            'critical_count': chains_by_severity.get('Critical', 0),
            'high_count': chains_by_severity.get('High', 0),
            'medium_count': chains_by_severity.get('Medium', 0)
        }


class ChainDetectorManager:
    """
    Manages chain detection for all users.
    """
    
    def __init__(self, data_df: pd.DataFrame, time_window_hours: int = 24):
        """
        Initialize chain detector manager.
        
        Args:
            data_df: DataFrame with all events
            time_window_hours: Time window for chain detection
        """
        self.data_df = data_df
        self.time_window_hours = time_window_hours
        self.detectors = {}
        
        self._detect_all_chains()
    
    def _detect_all_chains(self):
        """Detect chains for all users."""
        if 'user_id' not in self.data_df.columns:
            print("Warning: No user_id column. Cannot detect chains.")
            return
        
        unique_users = self.data_df['user_id'].unique()
        
        print(f"Detecting event chains for {len(unique_users)} users...")
        for user_id in unique_users:
            user_events = self.data_df[self.data_df['user_id'] == user_id].copy()
            self.detectors[user_id] = EventChainDetector(
                user_id,
                user_events,
                time_window_hours=self.time_window_hours
            )
        
        total_chains = sum(len(d.detected_chains) for d in self.detectors.values())
        print(f"✅ Detected {total_chains} event chains across all users")
    
    def get_detector(self, user_id: str) -> Optional[EventChainDetector]:
        """Get chain detector for specific user."""
        return self.detectors.get(user_id)
    
    def get_all_chains(self, min_severity: Optional[str] = None) -> List[Dict]:
        """
        Get all detected chains across all users.
        
        Args:
            min_severity: Minimum severity filter
            
        Returns:
            List of all chains, sorted by risk
        """
        all_chains = []
        for detector in self.detectors.values():
            chains = detector.get_chains(min_severity=min_severity)
            all_chains.extend(chains)
        
        all_chains.sort(key=lambda x: x['chain_risk'], reverse=True)
        return all_chains
    
    def get_statistics(self) -> Dict:
        """Get overall statistics."""
        all_chains = self.get_all_chains()
        
        if len(all_chains) == 0:
            return {
                'total_users': len(self.detectors),
                'total_chains': 0,
                'critical_chains': 0,
                'high_chains': 0,
                'users_with_chains': 0,
                'avg_chains_per_user': 0.0
            }
        
        severity_counts = defaultdict(int)
        for chain in all_chains:
            severity_counts[chain['severity']] += 1
        
        users_with_chains = sum(1 for d in self.detectors.values() if len(d.detected_chains) > 0)
        
        return {
            'total_users': len(self.detectors),
            'total_chains': len(all_chains),
            'critical_chains': severity_counts['Critical'],
            'high_chains': severity_counts['High'],
            'medium_chains': severity_counts['Medium'],
            'users_with_chains': users_with_chains,
            'avg_chains_per_user': round(len(all_chains) / len(self.detectors), 2)
        }


# Global instance
chain_detector_manager: Optional[ChainDetectorManager] = None


def initialize_chain_detector(data_df: pd.DataFrame, time_window_hours: int = 24) -> ChainDetectorManager:
    """Initialize global chain detector manager."""
    global chain_detector_manager
    chain_detector_manager = ChainDetectorManager(data_df, time_window_hours)
    return chain_detector_manager


def get_chain_detector_manager() -> Optional[ChainDetectorManager]:
    """Get global chain detector manager."""
    return chain_detector_manager
