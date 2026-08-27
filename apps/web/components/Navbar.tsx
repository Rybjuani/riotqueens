"use client";

export function Navbar({ onCta }: { onCta: () => void }) {
  return (
    <header className="site-header">
      <div className="wrap">
        <a className="brand-lockup" href="#top" aria-label="RiotQueens.ai, inicio">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/brand/riotqueens-logo.jpeg" alt="" width={1024} height={1024} decoding="async" />
          <span className="label glitch">RQ · RiotQueens.ai</span>
        </a>
        <nav aria-label="Navegación principal">
          <a href="#como">¿CÓMO?</a>
          <a href="#manifiesto">MANIFIESTO</a>
          <a href="#tiers">TIERS</a>
          <button type="button" className="nav-link" onClick={onCta}>
            CHAT →
          </button>
        </nav>
      </div>
    </header>
  );
}
