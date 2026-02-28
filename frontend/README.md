# VORTEX Frontend

Modern React-based frontend for the VORTEX Insider Threat Detection System.

## 🎨 Features

- **Real-time Dashboard**: Monitor security events and threats in real-time
- **Interactive SHAP Explanations**: Visualize ML model decisions with detailed feature contributions
- **User Behavioral Profiles**: Track user baselines and risk trajectories
- **Attack Chain Detection**: Identify and investigate complex attack patterns
- **Advanced Analytics**: Trending users and pattern recognition
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Dark Mode**: Eye-friendly dark theme optimized for SOC analysts

## 🛠️ Tech Stack

- **Framework**: React 18 + Vite
- **Routing**: React Router v6
- **Styling**: TailwindCSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **HTTP Client**: Axios

## 📦 Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies (already done if you followed the setup):
```bash
npm install
```

3. Configure environment variables:
Edit `.env` file to point to your backend API:
```env
VITE_API_URL=http://localhost:8000
```

## 🚀 Running the Application

### Development Mode
```bash
npm run dev
```
The application will be available at http://localhost:5173

### Production Build
```bash
npm run build
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Common/
│   │   │   ├── LoadingSpinner.jsx
│   │   │   └── RiskBadge.jsx
│   │   ├── Dashboard/
│   │   │   └── StatsCard.jsx
│   │   └── Layout/
│   │       ├── Header.jsx
│   │       ├── Sidebar.jsx
│   │       └── Layout.jsx
│   ├── pages/
│   │   ├── Dashboard.jsx
│   │   ├── Alerts.jsx
│   │   ├── EventDetail.jsx
│   │   ├── Users.jsx
│   │   ├── UserProfile.jsx
│   │   └── Analytics.jsx
│   ├── services/
│   │   └── api.js
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── .env
├── tailwind.config.js
├── postcss.config.js
├── vite.config.js
└── package.json
```

## 🎯 Main Pages

### 1. Dashboard (`/`)
- System overview with key metrics
- Recent high-risk events
- Risk distribution charts
- Weekly trend analysis

### 2. Alerts (`/alerts`)
- Comprehensive list of all security events
- Filter by risk level
- Search by event ID or user ID
- Quick navigation to event details

### 3. Event Detail (`/event/:eventId`)
- Full SHAP explanation with feature contributions
- Human-readable threat narrative
- Actionable mitigation suggestions
- Interactive visualizations

### 4. Users (`/users`)
- List all monitored users
- Baseline risk scores and confidence levels
- Search functionality
- Quick access to user profiles

### 5. User Profile (`/user/:userId`)
- Comprehensive behavioral profile
- 30-day risk trajectory visualization
- Behavioral fingerprint
- Attack chains and recent events

### 6. Analytics (`/analytics`)
- Trending high-risk users
- Detected attack patterns
- Escalation metrics
- Pattern statistics

## 🔌 API Integration

The frontend connects to the VORTEX backend API running on port 8000. All API calls are defined in `src/services/api.js`.

### Available Endpoints

- `GET /health` - System health check
- `GET /risks` - Fetch risk events
- `GET /explain/:eventId` - Get SHAP explanation
- `GET /baselines/users` - List all users
- `GET /baselines/users/:userId` - User baseline
- `GET /trajectory/:userId` - User risk trajectory
- `GET /chains/user/:userId` - User attack chains
- `GET /analytics/trending-users` - Trending users
- `GET /analytics/attack-patterns` - Attack patterns

## 🎨 Customization

### Colors
Edit `tailwind.config.js` to customize the color scheme:
```javascript
colors: {
  'vortex-dark': '#0a0e27',
  'vortex-accent': '#4f46e5',
  'risk-critical': '#ef4444',
  'risk-high': '#f59e0b',
  'risk-medium': '#fbbf24',
  'risk-low': '#10b981',
}
```

### API URL
Update `.env` file:
```env
VITE_API_URL=https://your-api-url.com
```

## 🔧 Development

### Hot Reload
Vite provides instant hot module replacement (HMR). Changes appear immediately.

### Linting
```bash
npm run lint
```

### Build
```bash
npm run build
```

## 📊 Key Features Implemented

✅ **Dashboard**
- Real-time statistics
- Risk distribution pie chart
- Weekly trend bar chart
- Recent events table

✅ **SHAP Explanations**
- Feature contribution bar chart
- Threat narratives
- Mitigation suggestions
- Detailed feature analysis

✅ **User Management**
- User grid with search
- Baseline risk scoring
- Confidence visualization

✅ **Risk Trajectories**
- 30-day cumulative risk chart
- Escalation detection
- Trend indicators

✅ **Analytics**
- Trending users ranking
- Attack pattern cards
- Escalation metrics

## 🚦 Starting the Full System

1. **Start Backend** (in main project directory):
```bash
python -m src.api.main
```

2. **Start Frontend** (in frontend directory):
```bash
npm run dev
```

3. **Access Application**:
- Frontend: http://localhost:5173
- Backend API Docs: http://localhost:8000/docs

## 🎯 Usage Flow

1. View **Dashboard** for system overview
2. Navigate to **Alerts** to see all events
3. Click on an event to see **SHAP Explanation**
4. Click on a user to view **User Profile** with trajectory
5. Check **Analytics** for trending threats

## 🛡️ Security Notes

- All API calls are made through axios with proper error handling
- Environment variables keep configuration separate
- CORS is properly configured on backend
- No sensitive data is stored in frontend

## 📝 Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Advanced filtering and sorting
- [ ] Export reports as PDF
- [ ] User authentication and roles
- [ ] Customizable dashboards
- [ ] Dark/Light mode toggle
- [ ] Mobile app version

## 🤝 Contributing

This frontend is part of the VORTEX project. Follow React best practices and maintain the established code structure.

## 📄 License

Same as the main VORTEX project.

---

**Built with ❤️ for Security Analysts**
