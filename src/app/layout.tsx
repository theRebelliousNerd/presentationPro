import type {Metadata} from 'next';
import { Toaster } from "@/components/ui/toaster"
import './globals.css';
import { Montserrat, Roboto, Inter, Source_Sans_3 } from 'next/font/google'
import FontApply from '@/components/app/FontApply'

export const metadata: Metadata = {
  title: 'Next-Gen Presentation Studio',
  description: 'Next-Gen Engineering and Research Development - Professional Presentation Creation Platform',
};

const montserrat = Montserrat({ subsets: ['latin'], variable: '--font-montserrat' })
const roboto = Roboto({ subsets: ['latin'], weight: ['300','400','500','700'], variable: '--font-roboto' })
const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const sourceSans3 = Source_Sans_3({ subsets: ['latin'], variable: '--font-source' })

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className={`${montserrat.variable} ${roboto.variable} ${inter.variable} ${sourceSans3.variable}`}>
      <head></head>
      <body className="font-body antialiased" style={{
        // defaults
        ['--font-headline' as any]: 'var(--font-montserrat)',
        ['--font-body' as any]: 'var(--font-roboto)'
      }}>
        <FontApply />
        {children}
        <Toaster />
      </body>
    </html>
  );
}
