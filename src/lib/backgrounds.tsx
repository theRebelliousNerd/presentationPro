export type BgPattern = 'gradient' | 'shapes' | 'grid' | 'dots' | 'wave' | 'topography' | 'hexagons' | 'diagonal' | 'overlap';

export function getTheme(): 'brand' | 'muted' | 'dark' {
  if (typeof window === 'undefined') return 'brand';
  try { return (localStorage.getItem('app.theme') as any) || 'brand'; } catch { return 'brand'; }
}

export function getBgPattern(): BgPattern {
  if (typeof window === 'undefined') return 'gradient';
  try { return (localStorage.getItem('app.bgPattern') as BgPattern) || 'gradient'; } catch { return 'gradient'; }
}

export function getTypeScale(): 'normal' | 'large' {
  if (typeof window === 'undefined') return 'normal';
  try { return (localStorage.getItem('app.typeScale') as any) || 'normal'; } catch { return 'normal'; }
}

// Build Tailwind utility strings based on theme
export function backgroundContainerClasses(theme: ReturnType<typeof getTheme>, pattern: BgPattern): string {
  // background gradient base per theme
  const brandA = theme === 'dark'
    ? 'from-secondary/40 via-muted/20 to-primary/30'
    : theme === 'muted'
    ? 'from-muted/30 via-muted/10 to-secondary/20'
    : 'from-primary/30 via-accent/20 to-secondary/30';
  const brandB = theme === 'dark'
    ? 'from-secondary/40 via-secondary/20 to-primary/30'
    : theme === 'muted'
    ? 'from-muted/20 via-muted/10 to-accent/20'
    : 'from-secondary/30 via-muted/10 to-primary/20';
  switch (pattern) {
    case 'gradient':
      return `w-full h-full bg-gradient-to-br ${brandA}`;
    case 'shapes':
      return `w-full h-full bg-gradient-to-tr ${brandB}`;
    case 'grid':
      return `w-full h-full bg-gradient-to-bl ${brandA}`;
    case 'dots':
      return `w-full h-full bg-gradient-to-br ${brandB}`;
    case 'wave':
      return `w-full h-full bg-gradient-to-bl ${brandA}`;
    case 'topography':
      return `w-full h-full bg-gradient-to-br ${brandA}`;
    case 'hexagons':
      return `w-full h-full bg-gradient-to-tr ${brandB}`;
    case 'diagonal':
      return `w-full h-full bg-gradient-to-br ${brandA}`;
    case 'overlap':
      return `w-full h-full bg-gradient-to-tr ${brandB}`;
  }
}

export function renderPatternSvg(pattern: BgPattern) {
  switch (pattern) {
    case 'gradient':
      return null; // pure gradient
    case 'shapes':
      return (
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="g1" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="rgba(255,255,255,0.2)" />
              <stop offset="100%" stopColor="rgba(255,255,255,0)" />
            </linearGradient>
          </defs>
          <circle cx="15%" cy="20%" r="120" fill="url(#g1)" />
          <rect x="70%" y="60%" width="260" height="260" fill="rgba(255,255,255,0.05)" rx="16" />
        </svg>
      );
    case 'topography':
      // Simple topography-like path pattern
      return (
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
          <defs>
            <pattern id="topo" width="160" height="120" patternUnits="userSpaceOnUse">
              <path d="M0,60 C40,40 120,80 160,60" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
              <path d="M0,90 C30,70 130,110 160,90" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="1"/>
              <path d="M0,30 C50,20 110,40 160,30" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#topo)" />
        </svg>
      );
    case 'hexagons':
      // Simple hexagon tiling pattern
      return (
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="hex" width="40" height="34.64" patternUnits="userSpaceOnUse" patternTransform="translate(0,0)">
              <polygon points="20,0 40,10 40,24.64 20,34.64 0,24.64 0,10" fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#hex)" />
        </svg>
      );
    case 'diagonal':
      return (
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="diag" width="20" height="20" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <rect width="10" height="20" fill="rgba(255,255,255,0.06)" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#diag)" />
        </svg>
      );
    case 'overlap':
      return (
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <g fill="rgba(255,255,255,0.06)">
            <circle cx="20%" cy="30%" r="140" />
            <circle cx="35%" cy="40%" r="120" />
            <circle cx="70%" cy="60%" r="180" />
          </g>
        </svg>
      );
    case 'grid':
      return (
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      );
    case 'dots':
      return (
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <g fill="rgba(255,255,255,0.06)">
            {Array.from({ length: 60 }).map((_, i) => (
              <circle key={i} cx={(i * 80) % 1280} cy={(i * 50) % 720} r={3} />
            ))}
          </g>
        </svg>
      );
    case 'wave':
      return (
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <path d="M0,420 C320,320 560,520 1280,380 L1280,720 L0,720 Z" fill="rgba(255,255,255,0.08)" />
          <path d="M0,520 C320,420 560,620 1280,480 L1280,720 L0,720 Z" fill="rgba(255,255,255,0.05)" />
        </svg>
      );
  }
}


