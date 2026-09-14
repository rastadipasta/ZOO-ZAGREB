import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Zoo Zagreb · Interaktivna 3D karta",
  description: "Istraži Zoološki vrt Zagreb u 3D: nastambe, usluge, zanimljivosti i tvoja lokacija na jednoj karti.",
  manifest: "/manifest.webmanifest",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="hr">
      <body className="antialiased">{children}</body>
    </html>
  );
}
