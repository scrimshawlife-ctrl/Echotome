import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Echotome v3.1',
  description: 'Ritual Cryptography Engine',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header style={{ borderBottom: '1px solid var(--border)', padding: '1rem 2rem' }}>
          <nav className="flex flex-between flex-center">
            <a href="/" style={{ fontSize: '1.25rem', fontWeight: 700 }}>
              Echotome <span style={{ color: 'var(--text-secondary)', fontWeight: 400 }}>v3.1</span>
            </a>
            <div className="flex gap-2">
              <a href="/vaults">Vaults</a>
              <a href="/sessions">Sessions</a>
            </div>
          </nav>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
