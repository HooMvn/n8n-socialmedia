import type { ReactNode } from 'react';

export const metadata = {
  title: 'Risheh Engage',
  description: 'AI Content & Customer Engagement Platform',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fa" dir="rtl">
      <body>{children}</body>
    </html>
  );
}
