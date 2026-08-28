"use client";

import { useEffect, useState } from "react";

import {
  acceptConsent,
  CONSENT_AGE_GATE_VERSION,
  CONSENT_PRIVACY_VERSION,
  CONSENT_TERMS_VERSION,
} from "@/lib/api";

type Props = {
  open: boolean;
  onAccepted: () => void;
  onCancel: () => void;
};

export function ClickwrapModal({ open, onAccepted, onCancel }: Props) {
  const [ageOk, setAgeOk] = useState(false);
  const [legalOk, setLegalOk] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onCancel();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onCancel]);

  if (!open) return null;

  const canContinue = ageOk && legalOk && !submitting;

  const submit = async () => {
    if (!canContinue) return;
    setSubmitting(true);
    setError(null);
    try {
      await acceptConsent({
        age_confirmed: true,
        age_gate_version: CONSENT_AGE_GATE_VERSION,
        terms_version: CONSENT_TERMS_VERSION,
        privacy_version: CONSENT_PRIVACY_VERSION,
      });
      onAccepted();
    } catch {
      setError("No se pudo registrar la aceptación. Reintentá.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onCancel}>
      <section
        className="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="clickwrap-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <button type="button" className="x" onClick={onCancel} aria-label="Cerrar">
          ×
        </button>
        <span className="label">ACCESO +18</span>
        <h2 id="clickwrap-title">Antes de hablar con la Queen</h2>
        <p>
          RiotQueens.ai es entretenimiento virtual ficticio para mayores de edad. Sin
          casillas no hay chat.
        </p>
        <label className="clickwrap-row">
          <input
            type="checkbox"
            checked={ageOk}
            onChange={(event) => setAgeOk(event.target.checked)}
          />
          <span>Confirmo que tengo 18 años o más y la mayoría de edad aplicable.</span>
        </label>
        <label className="clickwrap-row">
          <input
            type="checkbox"
            checked={legalOk}
            onChange={(event) => setLegalOk(event.target.checked)}
          />
          <span>
            Acepto los{" "}
            <a href="/legal" target="_blank" rel="noreferrer">
              Términos de Uso
            </a>{" "}
            y la{" "}
            <a href="/privacy" target="_blank" rel="noreferrer">
              Política de Privacidad
            </a>
            .
          </span>
        </label>
        {error && (
          <p className="chat-error" role="alert">
            {error}
          </p>
        )}
        <div className="modal-actions">
          <button
            type="button"
            className="btn solid"
            disabled={!canContinue}
            onClick={() => void submit()}
          >
            {submitting ? "REGISTRANDO…" : "ENTRAR AL CHAT →"}
          </button>
          <button type="button" className="btn" onClick={onCancel}>
            CANCELAR
          </button>
        </div>
      </section>
    </div>
  );
}
