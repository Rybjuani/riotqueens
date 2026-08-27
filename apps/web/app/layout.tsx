import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "RiotQueens.ai — ANTI-PERFECT-GF / BETA",
  description:
    "No te clava el visto. Te bardea, te quiere, se queda. Experiencia +18 con personajes virtuales y ficticios.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
