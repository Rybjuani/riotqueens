"use client";

import { useEffect, useState } from "react";

import { ChatPanel } from "@/components/ChatPanel";
import { ClickwrapModal } from "@/components/ClickwrapModal";
import { Experience } from "@/components/Experience";
import { Footer } from "@/components/Footer";
import { Hero } from "@/components/Hero";
import { Navbar } from "@/components/Navbar";
import { QueenRoster } from "@/components/QueenRoster";
import { TierGrid } from "@/components/TierGrid";
import { getConsentStatus } from "@/lib/api";

type ModalKind = "how" | "locked" | null;
const AUTH_ENABLED = process.env.NEXT_PUBLIC_AUTH_ENABLED === "true";

function InfoModal({
  kind,
  onClose,
  onStart,
}: {
  kind: ModalKind;
  onClose: () => void;
  onStart: () => void;
}) {
  useEffect(() => {
    if (!kind) return;
    const onKeyDown = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [kind, onClose]);

  if (!kind) return null;

  const locked = kind === "locked";
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <button type="button" className="x" onClick={onClose} aria-label="Cerrar">
          ×
        </button>
        <span className="label">{locked ? "EN CURACIÓN" : "CÓMO FUNCIONA"}</span>
        <h2 id="modal-title">
          {locked ? "Todavía no, pibe." : "Entrás. Hablás. Ella continúa."}
        </h2>
        <p>
          {locked
            ? "Están en el backstage tomando fernet y cagándose de risa de tu bio de Tinder. Pronto."
            : "Elegís a La Bardera, abrís el chat y arrancás. Sin setup técnico. Sin catálogo infinito."}
        </p>
        <div className="modal-actions">
          <button type="button" className="btn solid" onClick={onStart}>
            {locked ? "VOLVER A LA BARDERA" : "HABLÁ CON LA BARDERA →"}
          </button>
          <button type="button" className="btn" onClick={onClose}>
            CERRAR
          </button>
        </div>
      </section>
    </div>
  );
}

export default function Home() {
  const [chatOpen, setChatOpen] = useState(false);
  const [modal, setModal] = useState<ModalKind>(null);
  const [clickwrapOpen, setClickwrapOpen] = useState(false);
  const [gateBusy, setGateBusy] = useState(false);

  const openChatPanel = () => {
    setModal(null);
    setClickwrapOpen(false);
    setChatOpen(true);
    window.setTimeout(
      () => document.getElementById("chat")?.scrollIntoView({ behavior: "smooth" }),
      60,
    );
  };

  const startChat = async () => {
    if (gateBusy) return;
    setGateBusy(true);
    try {
      if (AUTH_ENABLED) {
        try {
          const status = await getConsentStatus();
          if (!status.accepted) {
            setClickwrapOpen(true);
            return;
          }
          openChatPanel();
          return;
        } catch {
          window.location.assign("/auth/login?returnTo=/#chat");
          return;
        }
      }
      openChatPanel();
    } finally {
      setGateBusy(false);
    }
  };

  return (
    <div className="site-shell">
      <Navbar onCta={() => void startChat()} />
      <main>
        <Hero onStart={() => void startChat()} onHow={() => setModal("how")} />
        <div className="marquee" aria-hidden>
          <span>
            ✦ NO ES TU TERAPEUTA ✦ TE CONTESTA DE VERDAD ✦ NO TE GHOSTEA ✦ TE BARDEA CON
            AMOR ✦ SE QUEDA ✦ QUEEN AL FRENTE ✦ NO ES TU TERAPEUTA ✦ TE CONTESTA DE
            VERDAD ✦ NO TE GHOSTEA ✦ TE BARDEA CON AMOR ✦ SE QUEDA ✦ QUEEN AL FRENTE ✦
            &nbsp;
          </span>
        </div>
        <Experience />
        <QueenRoster onStartBardera={() => void startChat()} />
        <TierGrid onStart={() => void startChat()} onLocked={() => setModal("locked")} />
        <div className="etica">
          ⚠ PERSONAJES VIRTUALES · +18 · FANTASÍA SIMULADA · QUEEN AL FRENTE
        </div>
        {chatOpen && <ChatPanel />}
        <section className="final" id="join">
          <div className="wrap">
            <h2 className="glitch">
              NO SOMOS TU GIRLFRIEND PERFECTA —
              <br />
              SOMOS EL PROBLEMA QUE QUERÉS TENER —
            </h2>
            <p className="lead">
              LAS QUE SE HACEN LAS SANTITAS TE CLAVAN EL VISTO. NOSOTRAS NOS QUEDAMOS
              IGUAL, BOBO.
            </p>
            <button type="button" className="btn solid" onClick={() => void startChat()}>
              VOY CON LA BARDERA →
            </button>
          </div>
        </section>
      </main>
      <Footer />
      <InfoModal
        kind={modal}
        onClose={() => setModal(null)}
        onStart={() => void startChat()}
      />
      <ClickwrapModal
        open={clickwrapOpen}
        onCancel={() => setClickwrapOpen(false)}
        onAccepted={openChatPanel}
      />
    </div>
  );
}
