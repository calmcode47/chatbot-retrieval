import React, { useState } from "react";
import Navbar from "./components/Navbar";
import PlasmaMesh from "./components/PlasmaMesh";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import About from "./pages/About";
import { useScrollReveal } from './hooks/useScrollReveal';
import "./App.css";

function App() {
  const [activePage, setActivePage] = useState(
    () => localStorage.getItem("documind_active_page") || "home"
  );

  useScrollReveal(activePage);

  const handleSetActivePage = (page) => {
    setActivePage(page);
    localStorage.setItem("documind_active_page", page);
  };

  const renderPage = () => {
    switch (activePage) {
      case "home":
        return <Home setPage={handleSetActivePage} />;
      case "dashboard":
        return <Dashboard />;
      case "about":
        return <About />;
      default:
        return <Home setPage={handleSetActivePage} />;
    }
  };

  return (
    <div className="app-container">
      {/* 3D Plasma Background Layer */}
      <PlasmaMesh />

      {/* Navigation Header */}
      <Navbar currentPage={activePage} onNavigate={handleSetActivePage} />

      {/* Main Pages */}
      <div className="main-content-layout">
        {renderPage()}
      </div>
    </div>
  );
}

export default App;
