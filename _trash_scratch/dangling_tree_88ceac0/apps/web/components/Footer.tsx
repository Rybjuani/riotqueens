export function Footer() {
  return (
    <footer className="site-footer">
      <div className="wrap">
        <span>
          <strong>RiotQueens.ai</strong> — Personajes virtuales y ficticios mayores de
          18 años. Fantasía adulta, consentida y simulada.
        </span>
        <span>+18 · PERSONAJES VIRTUALES · QUEEN AL FRENTE</span>
        <span>
          <a href="/legal">/legal</a>
          <a href="/privacy">/privacy</a>
          <a href="#chat">/chat →</a>
        </span>
        <span>© {new Date().getFullYear()} RIOTQUEENS.AI — ANTI-PERFECT-GF</span>
      </div>
    </footer>
  );
}
