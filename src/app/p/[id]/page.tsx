import AppRoot from '@/components/app/AppRoot';

export default async function SharePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AppRoot presentationIdOverride={id} />;
}
