import React from "react";
import { Routes, Route, Link, NavLink } from "react-router-dom";
import Home from "./pages/Home.jsx";
import TwinView from "./pages/TwinView.jsx";
import Analytics from "./pages/Analytics.jsx";
import DashboardPage from "./pages/Dashboard.jsx";

import "./styles/app.css";

function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="logo">Digital Twin · Smart Building</div>
        <nav className="nav-links">
          <NavLink to="/" end>
            Home
          </NavLink>
          <NavLink to="/dashboard">Dashboard</NavLink>
          <NavLink to="/twin">Twin View</NavLink>
          <NavLink to="/analytics">Analytics</NavLink>
        </nav>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/twin" element={<TwinView />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </main>
      <footer className="app-footer">
        <span>Digital Twin MVP — demo build</span>
        <Link to="/twin">Open Twin</Link>
      </footer>
    </div>
  );
}

export default App;


