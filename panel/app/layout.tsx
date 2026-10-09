import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Contesta — Panel del dueño",
  description: "Llamadas, citas recuperadas y conversión de tu recepcionista 24/7",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
