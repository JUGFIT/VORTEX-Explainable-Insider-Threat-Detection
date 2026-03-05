# VORTEX Backend API Analysis & Frontend Integration Plan

## 📋 **Complete Backend API Endpoints**

Based on analysis of `src/api/main.py`, here are ALL available endpoints:

### **1. System Health & Status**
- `GET /` - API status check
- `GET /health` - Detailed health check (data loaded, model loaded, event counts)
- `GET /metrics` - Model performance metrics (AUC, F1, precision, recall)
- `POST /reload` - Reload data and model

### **2. Risk Events**
- `GET /risks` - Get all risk events (supports filtering by risk_level, limit)
- `GET /risks/user/{user_id}` - Get user-specific risk summary with recent events
- `POST /predict/batch` - Batch prediction for new events

### **3. SHAP Explanations**
- `GET /explain/{event_id}` - Get SHAP explanation for specific event

### **4. User Baselines (Phase 2A)**
- `GET /baselines/users` - Get all users with baseline summaries
- `GET /baselines/users/{user_id}` - Get detailed baseline for specific user
- `GET /baselines/divergence/{event_id}` - Get divergence analysis for event vs baseline

### **5. Risk Trajectories (Phase 2A Session 3)**
- `GET /users/{user_id}/trajectory` - Get 30-day risk trajectory for user
  - Query params: `days` (default: 30)
- `GET /users/{user_id}/escalation` - Get escalation detection details
- `GET /users/{user_id}/patterns` - Get temporal anomaly patterns

### **6. Attack Chains (Phase 2B)**
- `GET /chains/user/{user_id}` - Get attack chains for specific user
- `GET /chains/high-risk` - Get all high-risk chains (severity >= High)
- `GET /users/{user_id}/chains/summary` - Get chain summary for user
- `GET /analytics/chains` - Get all chains with analytics
- `GET /analytics/chain-statistics` - Get chain statistics

### **7. Analytics**
- `GET /analytics/trending-users` - Get users with escalating risk
  - Query params: `top_n` (default: 10), `days` (default: 7)
- `GET /analytics/attack-patterns` - Get detected attack patterns with statistics

### **8. Pipeline Management**
- `POST /pipeline/run-all` - Run full data pipeline (data gen → features → model)
- `POST /pipeline/data-generation` - Run data generation only
- `POST /pipeline/feature-engineering` - Run feature engineering only
- `POST /pipeline/model-training` - Run model training only

### **9. Simulation (MISSING - NEEDS TO BE ADDED)**
- `GET /simulation/options` - Get available users and scenarios (NOT IMPLEMENTED)
- `POST /simulation/inject` - Inject threat scenario (NOT IMPLEMENTED)

---

## 📊 **Data Analysis**

### **Dataset Information**

Let me check the actual data to answer your questions about users and CSV structure.

**Location:** `data/processed/processed_data.csv`

**Key Fields:**
- `user_id` - User identifier
- `timestamp` - Event timestamp
- `anomaly_score` - Risk score (0-1)
- `anomaly_flag` - Ground truth label (0=normal, 1=anomaly)
- `risk_level` - Categorized risk (Low/Medium/High/Critical)
- Plus ~40+ behavioral features

---

## 🎯 **Frontend-Backend Integration Status**

### **✅ Currently Used Endpoints**

| Frontend Component | Backend Endpoint | Status |
|-------------------|------------------|--------|
| Dashboard stats | `/health` | ✅ Working |
| Dashboard events | `/risks` | ✅ Working |
| Dashboard users | `/baselines/users` | ✅ Working |
| Trending Users Widget | `/analytics/trending-users` | ✅ Working |
| Global Alert Feed | `/analytics/attack-patterns` | ✅ Working |
| Alerts page | `/risks` | ✅ Working |
| Event Detail | `/explain/{event_id}` | ✅ Working |
| Users list | `/baselines/users` | ✅ Working |
| User Profile baseline | `/baselines/users/{user_id}` | ✅ Working |
| User Profile trajectory | `/users/{user_id}/trajectory` | ✅ Working |
| User Profile events | `/risks/user/{user_id}` | ✅ Working |
| User Profile chains | `/chains/user/{user_id}` | ✅ Working |
| Analytics trending | `/analytics/trending-users` | ✅ Working |
| Analytics patterns | `/analytics/attack-patterns` | ✅ Working |

### **❌ Unused/Missing Endpoints**

| Endpoint | Potential Use | Priority |
|----------|--------------|----------|
| `/users/{user_id}/escalation` | User profile escalation details | Medium |
| `/users/{user_id}/patterns` | User profile temporal patterns | Medium |
| `/baselines/divergence/{event_id}` | Event detail divergence gauge | High |
| `/chains/high-risk` | Dedicated chains page | Low |
| `/analytics/chains` | Analytics page | Low |
| `/analytics/chain-statistics` | Analytics dashboard | Medium |
| `/pipeline/*` | Settings/Admin page | Low |
| `/simulation/*` | **CRITICAL - NEEDS IMPLEMENTATION** | **HIGH** |

---

## 🚀 **Threat Injection Module - Complete Specification**

### **Backend Requirements (TO BE IMPLEMENTED)**

#### **1. GET /simulation/options**
Returns available users and threat scenarios.

**Response Schema:**
```json
{
  "users": [
    {
      "user_id": "user_001",
      "current_risk_level": "Low",
      "baseline_score": 0.234,
      "recent_events": 45
    }
  ],
  "scenarios": [
    {
      "id": "data_exfiltration",
      "name": "Data Exfiltration",
      "description": "Simulates unauthorized data extraction via USB or large file uploads",
      "intensity_params": {
        "type": "file_count",
        "min": 10,
        "max": 100,
        "default": 50,
        "unit": "files"
      }
    },
    {
      "id": "ransomware",
      "name": "Ransomware Preparation",
      "description": "Simulates reconnaissance and file encryption preparation",
      "intensity_params": {
        "type": "upload_size",
        "min": 100,
        "max": 5000,
        "default": 2000,
        "unit": "MB"
      }
    },
    {
      "id": "reconnaissance",
      "name": "Network Reconnaissance",
      "description": "Simulates suspicious network scanning and access attempts",
      "intensity_params": {
        "type": "access_attempts",
        "min": 20,
        "max": 200,
        "default": 100,
        "unit": "attempts"
      }
    }
  ]
}
```

#### **2. POST /simulation/inject**
Injects a threat scenario for a specific user.

**Request Schema:**
```json
{
  "user_id": "user_042",
  "scenario_id": "data_exfiltration",
  "intensity": 75,
  "parameters": {
    "file_count": 75,
    "duration_hours": 2,
    "obvious": false
  }
}
```

**Response Schema:**
```json
{
  "status": "success",
  "message": "Threat scenario injected successfully",
  "injection_details": {
    "user_id": "user_042",
    "scenario": "Data Exfiltration",
    "events_generated": 12,
    "expected_risk_level": "High",
    "chain_created": true,
    "chain_id": "chain_xyz123"
  },
  "timestamp": "2026-02-16T21:30:00"
}
```

---

## 🎨 **Frontend Simulation Panel Design**

### **Component Structure**

```
SimulationPanel (Modal/Drawer)
├── Header
│   ├── Title: "Threat Simulation - Demo Mode"
│   ├── Close button
│   └── Warning badge: "⚠️ Demo Environment"
│
├── Step 1: User Selection
│   ├── Search/Filter input
│   ├── User dropdown/select
│   └── User info card (current risk, baseline, recent activity)
│
├── Step 2: Scenario Selection
│   ├── Scenario cards (3 options)
│   │   ├── Data Exfiltration 🗂️
│   │   ├── Ransomware 🦠
│   │   └── Reconnaissance 🔍
│   └── Selected scenario details
│
├── Step 3: Intensity Configuration
│   ├── Slider (dynamic based on scenario)
│   ├── Real-time preview
│   │   ├── Expected events: ~12
│   │   ├── Expected risk: High
│   │   └── Detection probability: 95%
│   └── Advanced options (collapsible)
│       ├── Duration (hours)
│       ├── Obviousness toggle
│       └── Time of day
│
├── Step 4: Confirmation
│   ├── Summary card
│   └── "Inject Threat" button (primary, large)
│
└── Result Display (after injection)
    ├── Success animation
    ├── Generated events list
    ├── "View in Dashboard" button
    └── "View User Profile" button
```

### **Intensity Parameters by Scenario**

**Data Exfiltration:**
- Slider: 10-100 files
- Additional: File size (MB), USB usage (yes/no)
- Preview: "Will generate ~X events over Y hours"

**Ransomware:**
- Slider: 100-5000 MB upload size
- Additional: Encryption simulation (yes/no), Backup access (yes/no)
- Preview: "High risk chain with Z events"

**Reconnaissance:**
- Slider: 20-200 access attempts
- Additional: Failed login attempts, Port scanning simulation
- Preview: "Medium-High risk, W suspicious events"

---

## 📈 **Data Statistics (TO BE VERIFIED)**

Let me check the actual CSV to provide exact numbers...

