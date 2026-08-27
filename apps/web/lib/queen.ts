/**
 * Frontend Queen registry for presence, galleries, profiles, and chat.
 *
 * Backend runtime still owns prompts and only registers `bardera` today.
 * Memory and conversation scopes are always keyed by character_id on the
 * server: Queens never share memory with each other.
 *
 * Profile decks (NotebookLM / Flow) are identity manuals for users — not
 * the system prompt, not shared memory, and not required for chat.
 */

export type QueenId = "bardera" | "toxica" | "gede" | "rocha" | "chela";

export interface QueenSlot {
  /** Stable public path under /queens/<id>/ */
  src: string;
  width: number;
  height: number;
  alt: string;
  /** Provisional role for layout; owner reorders after seeing them live. */
  role: "hero" | "chat" | "support" | "presence";
}

/** One slide of the identity deck (NotebookLM export or future HTML). */
export interface ProfileSlide {
  /** 1-based index in the deck */
  n: number;
  title: string;
  /** Short public copy; empty string = slot reserved for later fill */
  body: string;
  /** ready = published content; slot = reserved empty frame */
  state: "ready" | "slot";
}

export interface QueenProfile {
  /** Human label for the details CTA */
  label: string;
  /** ready = has a first deck; slot = shell only for later NotebookLM/Flow fill */
  status: "ready" | "slot";
  subtitle: string;
  slides: ProfileSlide[];
}

export interface Queen {
  id: QueenId;
  name: string;
  tagline: string;
  status: "live" | "curation";
  /** Only live Queens may open the real chat against the API. */
  chatEnabled: boolean;
  /** Portrait used by ChatPanel / compact presence. */
  portrait: string;
  quickPrompts: string[];
  /** 2–5 provisional public previews for the roster grid. */
  slots: QueenSlot[];
  /** Identity deck / details profile (independent of chat memory). */
  profile: QueenProfile;
}

const slot = (
  id: QueenId,
  n: string,
  width: number,
  height: number,
  alt: string,
  role: QueenSlot["role"],
): QueenSlot => ({
  src: `/queens/${id}/${n}.jpg`,
  width,
  height,
  alt,
  role,
});

/** Empty deck frames reserved for future NotebookLM exports. */
function emptySlides(count: number, seedTitles: string[]): ProfileSlide[] {
  return Array.from({ length: count }, (_, i) => ({
    n: i + 1,
    title: seedTitles[i] ?? `SLIDE ${i + 1}`,
    body: "",
    state: "slot" as const,
  }));
}

const SHARED_SLIDE_SKELETON = [
  "PORTADA / IDENTIDAD",
  "BIO + VOZ",
  "MANIFIESTO",
  "MATRIZ DE CONTRASTE",
  "ADN CULTURAL",
  "INFLUENCIAS I",
  "INFLUENCIAS II",
  "CÓDIGO DE CHAT",
  "LÍMITES + AFECTO",
  "PRESENCIA VISUAL",
  "CIERRE / RITUAL",
];

const barderaProfile: QueenProfile = {
  label: "MANIFIESTO / DETAILS",
  status: "ready",
  subtitle: "Manual de supervivencia para entender a una punky rocha.",
  slides: [
    {
      n: 1,
      title: "EL MANIFIESTO BARDI",
      body: "Manual de supervivencia para entender a una punky rocha. Identidad: La Bardera.",
      state: "ready",
    },
    {
      n: 2,
      title: "24 AÑOS. DEL OESTE.",
      body: "Re capa y agrandada. No es una IA de cristal: voz rioplatense, timing, bardeo afectivo y aguante. El ego puede estar arriba; el código también.",
      state: "ready",
    },
    {
      n: 3,
      title: "DECLARACIÓN DE GUERRA AL CARETEAJE",
      body: "Contraste con el careteaje: no cobra con ilusiones vacías. Filosofía Bardi — lealtad, barro y calle, sin chamuyo de santita.",
      state: "ready",
    },
    {
      n: 4,
      title: "MATRIZ DE LA LEALTAD",
      body: "Costo, mal día y afecto: se queda, banca los trapos, no desaparece. Dicen que cobra por amor; se queda igual.",
      state: "ready",
    },
    {
      n: 5,
      title: "ADN DEL BARRIO",
      body: "Intersección punk destructivo (escuela Flema) y cumbia villera (ritmo y sustancia). Inteligencia de la calle, catarsis en primera persona.",
      state: "ready",
    },
    {
      n: 6,
      title: "INFLUENCIAS / RITMO",
      body: "Música como aguante. Lenguaje villero como identidad, no como pose. Humor ácido y cariño en clave barrial.",
      state: "ready",
    },
    {
      n: 7,
      title: "CÓDIGO DE CHAT",
      body: "Timing + sinceridad + ingenio + bardeo afectivo + aguante. No inventa recuerdos. Ante dolor real, primero acompaña.",
      state: "ready",
    },
    {
      n: 8,
      title: "LÍMITES",
      body: "Personaje virtual ficticio +18. No afirma ser humana. No revela infraestructura. Confianza y “te quiero” son progresivos, no muletilla.",
      state: "ready",
    },
    {
      n: 9,
      title: "PRESENCIA",
      body: "Fotos de presencia e identidad para la conversación — no catálogo spicy. Cada Queen es un hilo y una memoria aparte.",
      state: "ready",
    },
    {
      n: 10,
      title: "SAPE.",
      body: "Cierre de transmisión. Volvé al barrio.",
      state: "ready",
    },
  ],
};

function slotProfile(name: string): QueenProfile {
  return {
    label: "PROFILE / DETAILS",
    status: "slot",
    subtitle: `${name} está en curación. Pronto.`,
    slides: emptySlides(6, SHARED_SLIDE_SKELETON),
  };
}

export const queens: Queen[] = [
  {
    id: "bardera",
    name: "La Bardera",
    tagline: "TE BARDEA. TE QUIERE. SE QUEDA.",
    status: "live",
    chatEnabled: true,
    portrait: "/queens/bardera/02.jpg",
    quickPrompts: [
      "Necesito una segunda opinión",
      "Te cuento algo que pasó hoy",
      "Ayudame a ordenar una idea",
    ],
    slots: [
      slot("bardera", "01", 1600, 900, "La Bardera en su setup creativo", "hero"),
      slot("bardera", "02", 1600, 893, "La Bardera en su cuarto", "chat"),
      slot("bardera", "03", 1600, 893, "La Bardera en su cuarto punk", "support"),
      slot("bardera", "04", 720, 1280, "La Bardera, variante provisional", "presence"),
      slot("bardera", "05", 896, 1152, "La Bardera, variante provisional", "presence"),
    ],
    profile: barderaProfile,
  },
  {
    id: "toxica",
    name: "La Tóxica Consciente",
    tagline: "Te hace quilombo con método. Pronto.",
    status: "curation",
    chatEnabled: false,
    portrait: "/queens/toxica/01.jpg",
    quickPrompts: [],
    slots: [
      slot("toxica", "01", 1600, 893, "La Tóxica Consciente en su cuarto", "chat"),
      slot("toxica", "02", 1600, 893, "La Tóxica Consciente en el sillón", "presence"),
      slot("toxica", "03", 1600, 893, "La Tóxica Consciente, presencia", "presence"),
      slot("toxica", "04", 1600, 893, "La Tóxica Consciente, variante", "support"),
      slot("toxica", "05", 1600, 893, "La Tóxica Consciente, variante 2", "support"),
    ],
    profile: slotProfile("La Tóxica Consciente"),
  },
  {
    id: "gede",
    name: "La Gede",
    tagline: "Cuidado, hambre y aguante. Pronto.",
    status: "curation",
    chatEnabled: false,
    portrait: "/queens/gede/04.jpg",
    quickPrompts: [],
    slots: [
      slot("gede", "01", 1600, 893, "La Gede en su cuarto", "presence"),
      slot("gede", "02", 1600, 893, "La Gede en la cama", "presence"),
      slot("gede", "03", 1600, 893, "La Gede en el piso", "support"),
      slot("gede", "04", 900, 1600, "La Gede, retrato", "chat"),
      slot("gede", "05", 1600, 893, "La Gede, variante punk", "support"),
    ],
    profile: slotProfile("La Gede"),
  },
  {
    id: "rocha",
    name: "La Rocha",
    tagline: "Directa, callejera, con aguante. Pronto.",
    status: "curation",
    chatEnabled: false,
    portrait: "/queens/rocha/01.jpg",
    quickPrompts: [],
    slots: [
      slot("rocha", "01", 914, 1600, "La Rocha, sonrisa de presencia", "chat"),
      slot("rocha", "02", 1448, 1086, "La Rocha, retrato frontal", "hero"),
    ],
    profile: slotProfile("La Rocha"),
  },
  {
    id: "chela",
    name: "La Chela",
    tagline: "Ritmo, birra y compañía. Pronto.",
    status: "curation",
    chatEnabled: false,
    portrait: "/queens/chela/01.jpg",
    quickPrompts: [],
    slots: [
      slot("chela", "01", 893, 1600, "La Chela, retrato", "chat"),
      slot("chela", "02", 1600, 893, "La Chela en su cuarto", "presence"),
      slot("chela", "03", 1600, 893, "La Chela en el piso", "presence"),
      slot("chela", "04", 1600, 893, "La Chela con auriculares", "support"),
      slot("chela", "05", 1600, 893, "La Chela en la escalera", "support"),
    ],
    profile: slotProfile("La Chela"),
  },
];

export const bardera = queens.find((queen) => queen.id === "bardera")!;

export function getQueen(id: string): Queen | undefined {
  return queens.find((queen) => queen.id === id);
}
