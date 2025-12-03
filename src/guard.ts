export async function selfIntegrityCheck(expectedHex: string) {
  const el = document.querySelector('script[type="module"][src^="/src/main"]') as HTMLScriptElement | null;
  if (!el) return true;

  const res = await fetch(el.src, { cache: 'no-store' });
  const buf = new Uint8Array(await res.arrayBuffer());
  const sha = new Uint8Array(await crypto.subtle.digest('SHA-256', buf));
  const hex = [...sha].map((b) => b.toString(16).padStart(2, '0')).join('');
  return hex === expectedHex;
}

export function devtoolsOpen(): boolean {
  return window.outerWidth - window.innerWidth > 160 || window.outerHeight - window.innerHeight > 160;
}
