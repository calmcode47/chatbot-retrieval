import React, { useState } from "react";
import Navbar from "./components/Navbar";
import ThreeBackground from "./components/ThreeBackground";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import About from "./pages/About";
import "./App.css";

function App() {
  const [activePage, setActivePage] = useState(
    () => localStorage.getItem("documind_active_page") || "home"
  );

  const handleSetActivePage = (page) => {
    setActivePage(page);
    localStorage.setItem("documind_active_page", page);
  };

  const renderPage = () => {
    switch (activePage) {
      case "home":
        return <Home setActivePage={handleSetActivePage} />;
      case "dashboard":
        return <Dashboard />;
      case "about":
        return <About />;
      default:
        return <Home setActivePage={handleSetActivePage} />;
    }
  };

  return (
    <div className="app-container">
      {/* 3D Constellation Background Layer */}
      <ThreeBackground />

      {/* Navigation Header */}
      <Navbar activePage={activePage} setActivePage={handleSetActivePage} />

      {/* Main Pages */}
      <div className="main-content-layout">
        {renderPage()}
      </div>
    </div>
  );
}

export default App;
