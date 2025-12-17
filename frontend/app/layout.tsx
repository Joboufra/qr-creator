import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "QR Creator",
  description: "Genera tus códigos QR",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-night text-white font-body antialiased">{children}</body>
    </html>
  );
}

