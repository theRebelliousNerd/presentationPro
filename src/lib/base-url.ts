const LOCAL_GATEWAY = 'http://localhost:18088';
const INTERNAL_GATEWAY = 'http://api-gateway:8088';

function normalize(url?: string | null): string | undefined {
  if (!url) return undefined;
  const trimmed = url.trim();
  if (!/^https?:\/\//i.test(trimmed)) return undefined;
  return trimmed.replace(/\/+$/, '');
}

function isLocalhostHost(hostname: string): boolean {
  return ['localhost', '127.0.0.1', '::1', '[::1]'].includes(hostname.toLowerCase());
}

export function resolveAdkBaseUrl(): string {
  const envBrowser = normalize(process.env.NEXT_PUBLIC_ADK_BASE_URL);
  const envServer = normalize(process.env.ADK_BASE_URL);

  if (typeof window !== 'undefined') {
    if (envBrowser) return envBrowser;
    const { protocol, hostname, port } = window.location;
    if (isLocalhostHost(hostname)) {
      if (!port || port === '3000') {
        return `${protocol}//${hostname}:18088`;
      }
      return `${protocol}//${hostname}${port ? `:${port}` : ''}`;
    }
    if (port) {
      return `${protocol}//${hostname}:${port}`;
    }
    return `${protocol}//${hostname}`;
  }

  if (envServer) return envServer;
  if (envBrowser) return envBrowser;
  return process.env.NODE_ENV === 'production' ? INTERNAL_GATEWAY : LOCAL_GATEWAY;
}

export function resolveVisionBaseUrl(): string {
  const base = resolveAdkBaseUrl();
  if (base.includes('api-gateway')) {
    return base;
  }
  return base || LOCAL_GATEWAY;
}
