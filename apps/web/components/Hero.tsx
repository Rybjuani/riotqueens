"use client";

export function Hero({ onStart, onHow }: { onStart: () => void; onHow: () => void }) {
  return (
    <section className="hero" id="top">
      <div className="wrap">
        <span className="sticker">ANTI-PERFECT-GF / BETA</span>
        <span className="sticker flip">NSFW · 18+ · VIRTUAL ONLY</span>
        <h1 className="glitch">
          NO TE CLAVA
          <br />
          EL VISTO
        </h1>
        <p className="sub">
          Te bardea. Te quiere. Se queda. Personajes virtuales ficticios, con voz
          propia y la Queen al frente.
        </p>
        <div className="ctas">
          <button type="button" className="btn solid" onClick={onStart}>
            HABLÁ CON LA BARDERA →
          </button>
          <button type="button" className="btn" onClick={onHow}>
            ¿CÓMO FUNCIONA?
          </button>
        </div>
        <div className="live-panel" aria-label="Estado en vivo">
          <span className="label">
            <i className="live-dot" aria-hidden />
            LIVE · LA BARDERA · T0 · FREE / PREVIEW
          </span>
          <span className="q">
            “¿otra vez llorando por la de tinder? vení que te enseño a chamuyar bien,
            bobo”
          </span>
          <span className="label">100% VIRTUAL · 18+ ONLY</span>
        </div>
      </div>
    </section>
  );
}
