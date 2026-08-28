import Link from "next/link";
import { notFound } from "next/navigation";

import { getQueen, type QueenId } from "@/lib/queen";

const VALID: QueenId[] = ["bardera", "toxica", "gede", "rocha", "chela"];

export function generateStaticParams() {
  return VALID.map((id) => ({ id }));
}

export default function QueenProfilePage({ params }: { params: { id: string } }) {
  const queen = getQueen(params.id);
  if (!queen) notFound();

  const ready = queen.profile.status === "ready";
  const readySlides = queen.profile.slides.filter((slide) => slide.state === "ready");

  return (
    <div className="queen-page">
      <Link href="/#tiers">← VOLVER</Link>
      <span className="label" style={{ display: "block", marginTop: 18 }}>
        {queen.status === "live" ? "DISPONIBLE" : "EN CURACIÓN"}
      </span>
      <h1>{queen.name}</h1>
      <p className="lead">{queen.tagline}</p>
      <div className="actions">
        {queen.chatEnabled ? (
          <Link className="btn solid" href="/#chat">
            HABLÁ CON ELLA →
          </Link>
        ) : (
          <span className="btn" style={{ opacity: 0.5 }}>
            PRONTO
          </span>
        )}
        <Link className="btn" href="/#bardera">
          VER A LA BARDERA
        </Link>
      </div>

      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={queen.portrait}
        alt={queen.name}
        width={900}
        height={1200}
        style={{ maxWidth: 360, width: "100%", border: "1px solid #333", marginTop: 12 }}
      />

      <div className="deck" aria-label={`Presencia de ${queen.name}`}>
        {ready ? (
          readySlides.map((slide) => (
            <article className="slide" key={`${queen.id}-${slide.n}`}>
              <h3>
                {String(slide.n).padStart(2, "0")} · {slide.title}
              </h3>
              {slide.body ? <p>{slide.body}</p> : null}
            </article>
          ))
        ) : (
          <article className="slide slot">
            <h3>EN CURACIÓN</h3>
            <p>Esta Queen es canónica. Su chat se abre cuando esté lista.</p>
          </article>
        )}
      </div>
    </div>
  );
}
