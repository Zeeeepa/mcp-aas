import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Pages
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import ToolDetails from './pages/ToolDetails';
import Profile from './pages/Profile';
import AdminDashboard from './pages/AdminDashboard';
import NotFound from './pages/NotFound';

// Styles
import './styles/global.css';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <Router>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<Home />} />
        
        {/* Tool routes */}
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/tools/:id" element={<ToolDetails />} />
        <Route path="/profile" element={<Profile />} />
        
        {/* Admin route */}
        <Route path="/admin" element={<AdminDashboard />} />
        
        {/* Not found */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  </React.StrictMode>
);
