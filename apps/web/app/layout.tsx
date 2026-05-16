import type { Metadata } from "next";

import "@/app/globals.css";

export const metadata: Metadata = {
  title: "MedNexa",
  description: "Clinical intelligence workspace",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans">{children}</body>
    </html>
  );
}
