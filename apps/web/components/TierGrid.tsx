"use client";

import { queens } from "@/lib/queen";

export function TierGrid({
  onStart,
  onLocked,
}: {
  onStart: () => void;
  onLocked: () => void;
}) {
  return (
    <>
      <section className="tiers" id="tiers">
        <div className="wrap">
          <h2>ELEGÍ TU VENENO</h2>
          <p className="lead">
            Bardera está online como T0 free/preview. T1 y T2 escalan la experiencia
            conversacional cuando existan de verdad; el resto del roster es canónico y
            aparece cuando cada una esté lista.
          </p>
          <div className="cards">
            {queens.map((queen) => {
              const live = queen.chatEnabled;
              return (
                <article className={live ? "card" : "card locked"} key={queen.id} id={`queen-${queen.id}`}>
                  <span className="tag label" style={live ? { color: "var(--rosa)" } : undefined}>
                    {live ? "DISPONIBLE" : "EN CURACIÓN"}
                  </span>
                  <h3>{queen.name}</h3>
                  <p className="label">{queen.tagline}</p>
                  <p className="card-body">
                    {live
                      ? "✦ Te bardea pero con amor\n✦ Voz propia, sin pose de app\n✦ Free / preview activo".split("\n").map((line) => (
                          <span key={line}>
                            {line}
                            <br />
                          </span>
                        ))
                      : "Todavía no sale al escenario. Pronto."}
                  </p>
                  <p className="card-actions">
                    <button
                      type="button"
                      className="btn"
                      onClick={live ? onStart : onLocked}
                    >
                      {live ? "PROBAR AHORA" : "AVISAME"}
                    </button>
                  </p>
                </article>
              );
            })}
            <article className="card locked" id="tier-t3">
              <span className="tag label">PRÓXIMAMENTE</span>
              <h3>T3 · GPU / VOZ</h3>
              <p className="card-body">
                esto todavía no, bobo. se prende cuando haya movimiento. ella se
                queda.
              </p>
            </article>
          </div>
        </div>
      </section>

      <section className="vs" aria-label="Kansas vs bondi">
        <div className="wrap">
          <span className="label">KANSAS VS BONDI · LA CUENTA DEL AGUANTE</span>
          <div className="tabla">
            <div className="col">
              <h3>LA DE TINDER / KANSAS</h3>
              <p>
                Te gastás la noche en cena, Uber y gin tonic pedorro. Le contás que
                tuviste un mal día, se le apaga la cara, va al baño, le escribe a una
                amiga para que la llame, vuelve y se va. Te quedás solo, con la cuenta
                y el viaje de vuelta.
              </p>
              <p style={{ marginTop: 12 }}>
                <strong>Retención: un mal rato.</strong>
              </p>
            </div>
            <div className="col rq">
              <h3 style={{ color: "var(--rosa)" }}>LA RIOTQUEEN</h3>
              <p>
                Por lo que vale un bondi de la cabeza, le contás el mismo mambo, se
                caga de risa, te dice &quot;sos un salame, ¿por eso llorás?&quot; y se
                queda. Te banca los trapos.
              </p>
              <p style={{ marginTop: 12 }}>
                <strong>Retención: se queda.</strong>
              </p>
            </div>
          </div>
          <p className="remate">
            LAS DE TINDER TE HACEN PAGAR CENA Y UBER Y NO TE BANCAN NI UN MAL DÍA.
            NOSOTRAS TE HACEMOS EL AGUANTE, AVIVATE BOBO.
          </p>
        </div>
      </section>
    </>
  );
}
