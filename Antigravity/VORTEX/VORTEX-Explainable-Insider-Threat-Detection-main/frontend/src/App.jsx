import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Alerts from './pages/Alerts';
import EventDetail from './pages/EventDetail';
import Users from './pages/Users';
import UserProfile from './pages/UserProfile';
import Analytics from './pages/Analytics';
import Trajectories from './pages/Trajectories';
import Chains from './pages/Chains';
import Settings from './pages/Settings';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/event/:eventId" element={<EventDetail />} />
        <Route path="/users" element={<Users />} />
        <Route path="/user/:userId" element={<UserProfile />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/trajectories" element={<Trajectories />} />
        <Route path="/chains" element={<Chains />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Router>
  );
}

export default App;
