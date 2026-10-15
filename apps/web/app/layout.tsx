import type { Metadata } from "next";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "DocPilot — AI Workspace Assistant",
  description:
    "Answer questions from your own documents with citations (RAG), take actions with agent tools, and prove quality with built-in evals.",
  keywords: ["AI assistant", "RAG", "enterprise search", "citations", "agent tools"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-['Plus_Jakarta_Sans',sans-serif] bg-background text-foreground min-h-screen">
        {children}
      </body>
    </html>
  );
}
