import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "QR Creator",
  description: "Genera códigos QR desde FastAPI + Next.js",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-night text-white font-body antialiased">{children}</body>
    </html>
  );
}

