import Head from 'next/head'
import React, {useEffect} from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from "@/contexts/AuthContext";
import Link from 'next/link';


const Home = () => {
    const { user, isLoading } = useAuth();
    const router = useRouter();
    
    useEffect(() => {
        if (!isLoading && !user) {
            router.push('/login');
        }
    }, [user, isLoading, router]);
    
    if (isLoading || !user) {
        return <div>Loading...</div>;
    }

    const title = "Collections Transformer (TaNC UAL)"
    const jumpLinks = [
      {
        href: '/workspace',
        label: 'Dashboard',
        description: 'Review datasets, agents, analysis and history.'
      },
      {
        href: '/newagent',
        label: 'New Agent',
        description: 'Create agents and configure analysis.'
      },
      {
        href: '/dataset',
        label: 'Upload',
        description: 'Upload and prepare datasets for analysis workflows.'
      },
      {
        href: '/tasks',
        label: 'Analysis',
        description: 'Track and execute active analysis runs in one place.'
      },
      {
        href: '/user',
        label: 'Profile',
        description: 'Inspect your account information and context.'
      },
      {
        href: '/settings',
        label: 'Settings',
        description: 'Adjust environment and platform options for your workspace.'
      }
    ]

    return (

      <>
      <Head>
        <title>{title}</title>
      </Head>
        <main>
            <div className="container home-shell">
              <section className="home-hero">
                <p className="home-kicker">Operations Console</p>
                <h1>Collections Transformer</h1>
                <p className="home-subtitle">
                    Agent-based platform for multimodal analysis of datasets in the GLAM sector.
                </p>
              </section>

              <section className="home-command-center">
                <div className="home-command-header">
                  <h2>Console</h2>
                  <p>Welcome {user.username || user.name}. Start from any task below.</p>
                </div>

                <div className="home-jump-grid">
                  {jumpLinks.map((entry) => (
                    <Link key={entry.href} href={entry.href} className="home-jump-card">
                      <span className="home-jump-label">{entry.label}</span>
                      <span className="home-jump-description">{entry.description}</span>
                      <span className="home-jump-action">Open</span>
                    </Link>
                  ))}
                </div>
              </section>

              <section className="home-summary-strip">
                <div>
                  <h3>Clear workflow</h3>
                  <p>Upload datasets, create agents, run analysis, and review the outputs.</p>
                </div>
                <div>
                  <h3>Local Inference (Ollama)</h3>
                  <p>Swap LLMs and configure settings to use new language models.</p>
                </div>
              </section>
            </div>
        </main>
      </>
  )
}

export default Home
