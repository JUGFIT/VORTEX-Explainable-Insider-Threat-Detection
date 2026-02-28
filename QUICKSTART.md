# 🚀 VORTEX Quick Start Guide - Frontend & Backend

## Prerequisites

- Python 3.8+
- Node.js 16+ and npm
- Git

## 📦 Installation

### 1. Backend Setup

Navigate to the project root directory:
```bash
cd c:\Users\offic\Documents\Code\Antigravity\VORTEX\VORTEX-Explainable-Insider-Threat-Detection-main
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### 2. Frontend Setup

Navigate to frontend directory:
```bash
cd frontend
```

Install npm dependencies (already installed):
```bash
npm install
```

## 🎯 Running the System

### Step 1: Generate Data and Train Model (First Time Only)

From the project root directory:

```bash
# Generate synthetic data
python -m src.data_gen

# Engineer features
python -m src.feature_engineer

# Train the model
python -m src.model_train
```

### Step 2: Start the Backend API

From the project root directory:
```bash
python -m src.api.main
```

The backend will be available at:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Step 3: Start the Frontend

Open a new terminal, navigate to frontend directory:
```bash
cd frontend
npm run dev
```

The frontend will be available at:
- Frontend: http://localhost:5173

## 🎉 You're Ready!

Open your browser and navigate to:
**http://localhost:5173**

## 📋 Quick Tour

### Dashboard
- View system statistics
- See risk distribution
- Monitor recent high-risk events

### Alerts Page
- Browse all security events
- Filter by risk level
- Search by event/user ID

### Event Details
- Click any event to see SHAP explanation
- View threat narrative
- See mitigation suggestions

### Users Page
- Browse all monitored users
- View baseline risk scores
- Access user profiles

### User Profile
- See 30-day risk trajectory
- View behavioral fingerprint
- Check attack chains
- Review recent events

### Analytics
- Trending high-risk users
- Attack pattern detection
- Escalation metrics

## 🛠️ Development Tips

### Backend Development

Monitor backend logs in terminal:
```bash
python -m src.api.main
```

Access API documentation:
http://localhost:8000/docs

### Frontend Development

Hot reload is enabled by default. Make changes and they'll appear instantly.

**Key Files:**
- `src/pages/` - All page components
- `src/components/` - Reusable components
- `src/services/api.js` - API integration
- `src/index.css` - Global styling

### Customization

**Change API URL:**
Edit `frontend/.env`:
```env
VITE_API_URL=http://your-backend-url:8000
```

**Change Colors:**
Edit `frontend/tailwind.config.js`

**Add New Pages:**
1. Create component in `src/pages/`
2. Add route in `src/App.jsx`
3. Add navigation link in `src/components/Layout/Sidebar.jsx`

## 🔧 Troubleshooting

### Backend won't start
- Check if port 8000 is available
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify data is generated: Check for files in `data/` directory

### Frontend won't start
- Check if port 5173 is available
- Delete `node_modules` and run `npm install` again
- Check for errors in terminal

### API calls failing
- Ensure backend is running on port 8000
- Check CORS configuration in backend
- Verify `.env` file has correct API URL

### No data showing
- Run the pipeline to generate data:
  ```bash
  python -m src.data_gen
  python -m src.feature_engineer
  python -m src.model_train
  ```

## 📊 Sample Workflow

1. **Start Backend** → See console output confirming it's running
2. **Generate Data** → Run data generation scripts (first time only)
3. **Start Frontend** → Open http://localhost:5173
4. **Explore Dashboard** → View system overview
5. **Check Alerts** → Browse security events
6. **Investigate Event** → Click to see SHAP explanation
7. **View User Profile** → See behavioral patterns
8. **Analyze Trends** → Check analytics page

## 🎨 Screenshots Location

Once running, you'll see:
- **Dark modern theme** with purple/indigo accents
- **Interactive charts** using Recharts
- **Responsive tables** with filtering and search
- **Real-time data** from your backend API

## 📝 Next Steps

- [ ] Customize the color scheme
- [ ] Add more visualizations
- [ ] Implement user authentication
- [ ] Add export functionality
- [ ] Create custom dashboards
- [ ] Set up production deployment

## 🔐 Security Notes

- Backend CORS is configured for localhost:5173
- No authentication implemented (add for production)
- All data is synthetic for demonstration

## 💡 Tips

- Keep both terminals open (backend + frontend)
- Use Chrome/Firefox DevTools for debugging
- Check Network tab for API call details
- Backend API docs at `/docs` are interactive

## 🎯 Production Deployment

### Backend
```bash
pip install uvicorn[standard]
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
npm run build
# Serve the dist/ folder with nginx or your preferred server
```

---

**Need Help?** Check the main README.md files in root and frontend directories.

**Enjoying VORTEX?** Star the repository! ⭐
