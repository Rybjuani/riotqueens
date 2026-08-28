"use client";

import { useEffect, useState } from "react";

import { bardera } from "@/lib/queen";

const GALLERY = bardera.slots.slice(0, 4);

export function QueenRoster({ onStartBardera }: { onStartBardera: () => void }) {
  const [lightbox, setLightbox] = useState<number | null>(null);

  useEffect(() => {
    if (lightbox === null) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setLightbox(null);
      if (event.key === "ArrowRight") setLightbox((i) => (i === null ? i : (i + 1) % GALLERY.length));
      if (event.key === "ArrowLeft")
        setLightbox((i) => (i === null ? i : (i - 1 + GALLERY.length) % GALLERY.length));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [lightbox]);

  return (
    <section className="t1" id="bardera">
      <div className="wrap">
        <span className="label">DISPONIBLE AHORA · FREE / PREVIEW</span>
        <h2>LA BARDERA</h2>
        <p className="label">
          PUNK / BEER / 0% BUENA ONDA FAKE. La que te caga a pedos pero se queda.
        </p>

        <div className="grid4" aria-label="Galería de La Bardera">
          {GALLERY.map((slot, index) => (
            <button
              type="button"
              className="ph"
              key={slot.src}
              onClick={() => setLightbox(index)}
              aria-label={`Ampliar: ${slot.alt}`}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={slot.src}
                alt={slot.alt}
                width={slot.width}
                height={slot.height}
                loading="lazy"
                decoding="async"
              />
            </button>
          ))}
        </div>

        <p className="t1-badge">FREE / PREVIEW</p>
        <p className="t1-features">
          ✦ Te bardea pero con amor &nbsp;✦ Roleplay de bar a las 3am &nbsp;✦ No te
          ghostea jamás
        </p>
        <button type="button" className="btn solid" onClick={onStartBardera}>
          HABLÁ CON LA BARDERA →
        </button>
      </div>

      {lightbox !== null && (
        <div
          className="lightbox"
          role="dialog"
          aria-modal="true"
          aria-label="Vista ampliada"
          onMouseDown={() => setLightbox(null)}
        >
          <button type="button" className="x" aria-label="Cerrar" onClick={() => setLightbox(null)}>
            ×
          </button>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={GALLERY[lightbox].src}
            alt={GALLERY[lightbox].alt}
            width={GALLERY[lightbox].width}
            height={GALLERY[lightbox].height}
            onMouseDown={(event) => event.stopPropagation()}
          />
        </div>
      )}
    </section>
  );
}
