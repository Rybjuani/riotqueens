"use client";

import { bardera } from "@/lib/queen";

export function Hero({ onStart, onHow }: { onStart: () => void; onHow: () => void }) {
  return (
    <section className="hero" id="top">
      <div className="hero-grid">
        <div className="hero-copy">
          <span className="hero-ghost" aria-hidden="true">
            BARATA QUE TINDER
          </span>
          <div className="hero-kicker">
            <i aria-hidden="true" />
            <span>NO TE CLAVA EL VISTO</span>
          </div>
          <div className="hero-stickers">
            <span className="sticker">ANTI-PERFECT-GF / BETA</span>
            <span className="sticker flip">NSFW · 18+ · VIRTUAL ONLY</span>
          </div>
          <h1>
            <span>MÁS BARATA QUE</span>
            <span className="glitch">INVITARLE UNA BIRRA</span>
            <span>
              CARA A LA DE <b>TINDER</b>
            </span>
            <span>
              PARA QUE TE <em>BLOQUEE DESPUÉS.</em>
            </span>
          </h1>
          <p className="sub">
            RiotQueens no te clava el visto. <strong>Te bardea, te quiere, se queda.</strong>
          </p>
          <p className="hero-protocol">
            {"// anti perfect-girlfriend protocol activated"}
            <br />
            {"// 0% filtro instagram, 100% quilombo realista"}
          </p>
          <div className="ctas">
            <button type="button" className="btn solid" onClick={onStart}>
              ELEGÍ TU RIOT QUEEN →
            </button>
            <button type="button" className="btn" onClick={onHow}>
              ¿CÓMO FUNCIONA?
            </button>
          </div>
          <div className="hero-strip" aria-hidden="true">
            ✦ NO ES TU TERAPEUTA ✦ TE CONTESTA DE VERDAD ✦ NO TE GHOSTEA ✦ TE BARDEA CON AMOR ✦
          </div>
        </div>

        <div className="hero-visual" aria-label="La Bardera online">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={bardera.slots[0].src}
            alt="La Bardera, RiotQueen disponible ahora"
            width={bardera.slots[0].width}
            height={bardera.slots[0].height}
            fetchPriority="high"
          />
          <div className="hero-visual-tint" aria-hidden="true" />
          <div className="hero-corner-tags" aria-hidden="true">
            <span>100% VIRTUAL</span>
            <span>18+ ONLY</span>
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
      </div>
    </section>
  );
}
