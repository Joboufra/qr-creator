"use client";

import { useEffect, useMemo, useState } from "react";

type Format = "png" | "svg";
type Level = "L" | "M" | "Q" | "H";
type Style = "square" | "dots";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

const levels: Record<Level, string> = {
  L: "Bajo",
  M: "Medio",
  Q: "Alto",
  H: "Máximo",
};

const swatches = ["#ef4444", "#f97316", "#facc15", "#06b6d4", "#a855f7"];
const bgSwatches = ["#ffffff", "#e2e8f0", "#f5f5f5", "#0f172a", "#0b0f1a"];

function InfoHint({ text }: { text: string }) {
  return (
    <span className="relative inline-flex items-center align-middle group">
      <svg
        aria-hidden="true"
        focusable="false"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        className="ml-2 h-4 w-4 text-white/70 transition group-hover:scale-105 group-hover:text-accent"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 9.75v4.5m0-7.5h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
        />
      </svg>
      <span className="pointer-events-none absolute left-1/2 top-[-6px] z-10 w-52 -translate-x-1/2 -translate-y-full rounded-lg border border-white/15 bg-[#130a0f]/95 px-3 py-2 text-[11px] text-white opacity-0 shadow-[0_12px_40px_rgba(0,0,0,0.3)] backdrop-blur transition duration-200 group-hover:opacity-100">
        {text}
      </span>
    </span>
  );
}

export default function Page() {
  const [data, setData] = useState("Texto de ejemplo o URL");
  const [format, setFormat] = useState<Format>("png");
  const [level, setLevel] = useState<Level>("M");
  const [boxSize, setBoxSize] = useState(10);
  const [border, setBorder] = useState(2);
  const [fillColor, setFillColor] = useState("#ef4444");
  const [backColor, setBackColor] = useState("#ffffff");
  const [style, setStyle] = useState<Style>("square");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const isSvg = format === "svg";
  const effectiveStyle: Style = isSvg ? "square" : style;

  const controlBase =
    "w-full rounded-xl border border-white/15 bg-white/10 px-4 py-3 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-accent/60 shadow-[0_10px_40px_-30px_rgba(0,0,0,1)]";
  const selectBase =
    controlBase +
    " appearance-none pr-10 bg-[url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 20 20'%3E%3Cpath fill='%23f7f2f3' d='M5 7l5 6 5-6z'/%3E%3C/svg%3E\")] bg-[length:18px_18px] bg-[right_12px_center] bg-no-repeat";

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  const params = useMemo(() => {
    const p = new URLSearchParams({
      data,
      format,
      error_correction: level,
      box_size: String(boxSize),
      border: String(border),
      fill_color: fillColor,
      back_color: backColor,
      style: effectiveStyle,
    });
    return p.toString();
  }, [data, format, level, boxSize, border, fillColor, backColor, effectiveStyle]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const url = `${API_BASE}/api/qr?${params}`;
      const headers: Record<string, string> = {};
      if (API_KEY) headers["X-API-Key"] = API_KEY;

      const res = await fetch(url, { headers });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `Error HTTP ${res.status}`);
      }

      const blob = await res.blob();
      const objectUrl = URL.createObjectURL(blob);
      setPreviewUrl(objectUrl);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="max-w-5xl mx-auto px-6 py-10 space-y-8 min-h-screen lg:overflow-visible">
      <header className="space-y-3">
        <p className="text-xs uppercase tracking-[0.35em] text-zinc-400">Joboufra: QR Creator</p>
        <h1 className="text-4xl sm:text-5xl font-semibold font-display bg-gradient-to-r from-white via-rose-200 to-orange-200 bg-clip-text text-transparent drop-shadow-[0_6px_40px_rgba(239,68,68,0.25)]">
          Generador de QRs
        </h1>
        <p className="text-zinc-300 max-w-2xl">Ajusta formato, estilo y colores para crear tu QR al vuelo.</p>
      </header>

      <div className="grid lg:grid-cols-[1.1fr_0.9fr] gap-6">
        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/10 via-white/5 to-transparent backdrop-blur px-6 py-7 space-y-5 shadow-[0_20px_80px_-40px_rgba(0,0,0,1)]"
        >
          <div className="space-y-2">
            <label htmlFor="data" className="text-sm text-zinc-300">
              Texto o URL <InfoHint text="Contenido a codificar; acepta texto, URL o cualquier string corto." />
            </label>
            <input
              id="data"
              name="data"
              value={data}
              onChange={(e) => setData(e.target.value)}
              required
              className={controlBase}
              placeholder="Texto de ejemplo o URL"
            />
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="format" className="text-sm text-zinc-300">
                Formato <InfoHint text="SVG es vectorial y acepta colores; el estilo punteado solo aplica a PNG." />
              </label>
              <select
                id="format"
                value={format}
                onChange={(e) => setFormat(e.target.value as Format)}
                className={selectBase}
              >
                <option value="png">PNG</option>
                <option value="svg">SVG</option>
              </select>
            </div>

            <div className="space-y-2">
              <label htmlFor="level" className="text-sm text-zinc-300">
                Corrección de error <InfoHint text="Mayor nivel hace el QR más robusto a daños pero más denso." />
              </label>
              <select
                id="level"
                value={level}
                onChange={(e) => setLevel(e.target.value as Level)}
                className={selectBase}
              >
                {Object.entries(levels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="boxSize" className="text-sm text-zinc-300">
                Tamaño del módulo <InfoHint text="Escala el tamaño de cada píxel del QR en la imagen final." />
              </label>
              <input
                id="boxSize"
                type="number"
                min={1}
                max={32}
                value={boxSize}
                onChange={(e) => setBoxSize(Number(e.target.value))}
                className={controlBase}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="border" className="text-sm text-zinc-300">
                Borde (módulos) <InfoHint text="Margen alrededor del QR; 4 es el estándar." />
              </label>
              <input
                id="border"
                type="number"
                min={0}
                max={10}
                value={border}
                onChange={(e) => setBorder(Number(e.target.value))}
                className={controlBase}
              />
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="style" className="text-sm text-zinc-300">
                Estilo del QR<InfoHint text="Cuadrado clásico o punteado circular (solo PNG)." />
              </label>
              <select
                id="style"
                value={effectiveStyle}
                onChange={(e) => setStyle(e.target.value as Style)}
                className={`${selectBase} ${isSvg ? "opacity-60 cursor-not-allowed" : ""}`}
                disabled={isSvg}
              >
                <option value="square">Cuadrado</option>
                <option value="dots">Punteado</option>
              </select>
            </div>
            <div className="space-y-2">
              <label htmlFor="fillColor" className="text-sm text-zinc-300">
                Color QR <InfoHint text="Color de los módulos del QR; usa hex o el selector rápido." />
              </label>
              <input
                id="fillColor"
                type="color"
                value={fillColor}
                onChange={(e) => setFillColor(e.target.value)}
                className="w-full h-11 rounded-xl border border-white/10 bg-transparent"
                style={{ backgroundColor: fillColor }}
              />
              <div className="flex flex-wrap gap-2">
                {swatches.map((color) => (
                  <button
                    type="button"
                    key={color}
                    onClick={() => setFillColor(color)}
                    aria-label={`Color ${color}`}
                    className="h-8 w-8 rounded-full border border-white/30 transition hover:scale-105"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <label htmlFor="backColor" className="text-sm text-zinc-300">
                Fondo <InfoHint text="Color de fondo del QR; evita bajo contraste con el color QR." />
              </label>
              <input
                id="backColor"
                type="color"
                value={backColor}
                onChange={(e) => setBackColor(e.target.value)}
                className="w-full h-11 rounded-xl border border-white/10 bg-transparent"
                style={{ backgroundColor: backColor }}
              />
              <div className="flex flex-wrap gap-2">
                {bgSwatches.map((color) => (
                  <button
                    type="button"
                    key={color}
                    onClick={() => setBackColor(color)}
                    aria-label={`Fondo ${color}`}
                    className="h-8 w-8 rounded-full border border-white/30 transition hover:scale-105"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>
          </div>

          {error ? <p className="text-sm text-red-300">{error}</p> : null}

          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-accent px-5 py-3 font-semibold text-white transition hover:translate-y-[-1px] hover:shadow-[0_14px_34px_rgba(239,68,68,0.25)] active:scale-[0.99] disabled:opacity-70"
          >
            {loading ? "Generando..." : "Generar QR"}
          </button>
        </form>

        <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/10 via-white/5 to-transparent px-5 py-6 flex flex-col gap-4 shadow-[0_20px_80px_-40px_rgba(0,0,0,1)]">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-zinc-400">Previsualizacion</p>
              <p className="text-lg font-medium">Resultado</p>
            </div>
            {previewUrl ? (
              <a
                href={previewUrl}
                download={`qr.${format}`}
                className="inline-flex items-center gap-2 rounded-lg bg-accent/90 px-3 py-2 text-sm font-semibold text-white shadow-[0_10px_30px_rgba(239,68,68,0.35)] transition hover:translate-y-[-1px] hover:bg-accent"
              >
                <svg
                  aria-hidden="true"
                  focusable="false"
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 2a.75.75 0 0 1 .75.75v8.69l2.1-2.1a.75.75 0 0 1 1.06 1.06l-3.4 3.4a.75.75 0 0 1-1.06 0l-3.4-3.4a.75.75 0 1 1 1.06-1.06l2.1 2.1V2.75A.75.75 0 0 1 10 2Zm-5.5 12.25a.75.75 0 0 1 .75-.75h9.5a.75.75 0 0 1 0 1.5h-9.5a.75.75 0 0 1-.75-.75Z"
                    clipRule="evenodd"
                  />
                </svg>
                Descargar QR
              </a>
            ) : null}
          </div>

          <div className="flex-1 grid place-items-center rounded-xl border border-dashed border-white/15 bg-[radial-gradient(circle_at_20%_20%,rgba(239,68,68,0.07),transparent_40%),rgba(255,255,255,0.03)] min-h-[280px] p-4 transition">
            {previewUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={previewUrl}
                alt="QR preview"
                className="max-h-72 w-auto rounded-lg bg-white shadow-lg transition ease-out duration-300 animate-fade-in"
              />
            ) : (
              <div className="text-sm text-zinc-400 text-center space-y-2">
                <p>Envia el formulario y veras el QR aqui.</p>
                <p className="text-xs text-zinc-500">Admite PNG/SVG, estilos cuadrado o punteado.</p>
              </div>
            )}
          </div>
        </div>
      </div>
      <footer className="pt-6 text-center text-sm text-zinc-500 space-y-2">
        <div>Jose Boullosa | 2025</div>
        <div className="flex items-center justify-center gap-4 text-xs text-zinc-400">
          <a
            href="https://github.com/joboufra"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 hover:text-accent transition"
            aria-label="GitHub Jose Boullosa"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M12 2a10 10 0 0 0-3.162 19.49c.5.09.683-.217.683-.48 0-.236-.01-1.022-.014-1.855-2.779.604-3.366-1.19-3.366-1.19-.454-1.153-1.11-1.46-1.11-1.46-.908-.62.07-.608.07-.608 1.003.071 1.531 1.03 1.531 1.03.892 1.529 2.341 1.088 2.91.833.09-.646.35-1.088.636-1.338-2.218-.253-4.555-1.109-4.555-4.94 0-1.091.39-1.984 1.029-2.682-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.025A9.564 9.564 0 0 1 12 6.844a9.56 9.56 0 0 1 2.506.337c1.909-1.295 2.748-1.025 2.748-1.025.545 1.378.202 2.397.099 2.65.64.698 1.028 1.59 1.028 2.682 0 3.841-2.34 4.685-4.566 4.933.359.31.678.92.678 1.854 0 1.338-.012 2.419-.012 2.747 0 .266.18.575.688.477A10 10 0 0 0 12 2Z"
                clipRule="evenodd"
              />
            </svg>
            GitHub
          </a>
          <a
            href="https://www.joboufra.es"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 hover:text-accent transition"
            aria-label="Portfolio Jose Boullosa"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z" />
              <path d="M3 12h18M12 3a15.3 15.3 0 0 1 4 9 15.3 15.3 0 0 1-4 9 15.3 15.3 0 0 1-4-9 15.3 15.3 0 0 1 4-9Z" />
            </svg>
            Portfolio
          </a>
          <a
            href="https://www.linkedin.com/in/jboullosa/"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 hover:text-accent transition"
            aria-label="LinkedIn Jose Boullosa"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor">
              <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.447-2.136 2.941v5.665H9.352V9h3.414v1.561h.049c.476-.9 1.637-1.85 3.37-1.85 3.602 0 4.268 2.37 4.268 5.455v6.286ZM5.337 7.433a2.062 2.062 0 1 1 0-4.125 2.062 2.062 0 0 1 0 4.125ZM3.56 20.452h3.556V9H3.56v11.452Z" />
            </svg>
            LinkedIn
          </a>
        </div>
      </footer>
    </main>
  );
}
