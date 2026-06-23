import React from "react";

export default function Navbar({ currentPage, onNavigate }) {
  return (
    <nav style={{
      position:'fixed', top:0, left:0, right:0, zIndex:100,
      height:60, display:'flex', alignItems:'center',
      background:'rgba(4, 4, 9, 0.88)',
      backdropFilter:'blur(20px)',
      borderBottom:'1px solid var(--border-subtle)',
    }}>
      <div className="container" style={{ display:'flex', alignItems:'center', justifyContent:'space-between' }}>

        {/* Logo */}
        <button onClick={() => onNavigate('home')}
                style={{ background:'none', border:'none', cursor:'pointer', display:'flex', alignItems:'center', gap:'var(--sp-md)' }}>
          {/* Prism-shaped icon */}
          <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
            <polygon points="13,2 24,20 2,20"
                     stroke="#7c3aed" strokeWidth="1.5" fill="rgba(124,58,237,0.08)" />
            <polygon points="13,7 20,20 6,20"
                     stroke="#a78bfa" strokeWidth="0.8" fill="rgba(167,139,250,0.06)" />
            <circle cx="13" cy="16" r="2" fill="#7c3aed" />
          </svg>
          <span style={{ fontFamily:'var(--font-display)', fontSize:'1.35rem', letterSpacing:'0.08em', color:'var(--text-primary)' }}>
            DOCU<span style={{ color:'var(--violet-soft)' }}>MIND</span>
          </span>
        </button>

        {/* Nav links */}
        <div style={{ display:'flex', gap:'var(--sp-xs)' }}>
          {['home','dashboard','about'].map(page => (
            <button key={page} onClick={() => onNavigate(page)} style={{
              padding:'7px 15px',
              background:    currentPage === page ? 'var(--violet-dim)'  : 'transparent',
              border:        currentPage === page ? '1px solid var(--violet-border)' : '1px solid transparent',
              borderRadius:  'var(--r-md)',
              color:         currentPage === page ? 'var(--violet-soft)' : 'var(--text-muted)',
              fontFamily:    'var(--font-condensed)',
              fontWeight:    600,
              fontSize:      '0.875rem',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              cursor:        'pointer',
              transition:    'all var(--t-base) var(--ease-out)',
            }}>
              {page}
            </button>
          ))}
        </div>

        {/* Status */}
        <div style={{ display:'flex', alignItems:'center', gap:'var(--sp-sm)' }}>
          <span style={{ width:6, height:6, borderRadius:'50%', background:'#22c55e',
                          boxShadow:'0 0 7px rgba(34,197,94,0.7)' }} />
          <span className="mono-sm" style={{ color:'var(--text-muted)' }}>OFFLINE · SECURE</span>
        </div>

      </div>
    </nav>
  );
}
