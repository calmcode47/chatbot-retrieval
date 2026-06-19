import React from "react";
import { LayoutDashboard, Home, Info, Brain } from "lucide-react";

export default function Navbar({ activePage, setActivePage }) {
  const navItems = [
    { id: "home", label: "Home", icon: Home },
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "about", label: "About", icon: Info },
  ];

  return (
    <header className="navbar-container">
      <div className="navbar-logo" onClick={() => setActivePage("home")}>
        <Brain className="logo-icon" />
        <span className="logo-text">DocuMind</span>
      </div>
      <nav className="navbar-links">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              className={`nav-button ${activePage === item.id ? "active" : ""}`}
              onClick={() => setActivePage(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </header>
  );
}
