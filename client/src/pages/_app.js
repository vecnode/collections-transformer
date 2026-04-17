import '@/styles/globals.css';
import RootLayout from '@/_components/layout';
import { AuthProvider } from '@/_contexts/AuthContext';

export default function App({ Component, pageProps }) {
  return (
    <AuthProvider>
      <RootLayout>
        <Component {...pageProps} />
      </RootLayout>
    </AuthProvider>
  )
}
