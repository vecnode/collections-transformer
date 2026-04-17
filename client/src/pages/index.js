import Head from 'next/head'
import React, {useEffect} from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from "@/_contexts/AuthContext";
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
        label: 'Workspace',
        description: 'Review datasets, analysers, labelsets and operational history.'
      },
      {
        href: '/newagent',
        label: 'New Agent',
        description: 'Create focused analysis agents and configure behavior quickly.'
      },
      {
        href: '/uploaddataset',
        label: 'New Dataset',
        description: 'Upload and prepare source material for analysis workflows.'
      },
      {
        href: '/tasks',
        label: 'Tasks',
        description: 'Track and execute active processing tasks in one place.'
      },
      {
        href: '/user',
        label: 'Profile',
        description: 'Inspect your account information and latest usage context.'
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
                <p className="home-kicker">Collections Operations Console</p>
                <h1>Collections Transformer</h1>
                <p className="home-subtitle">
                    Professional tooling for structured analysis, dataset management, and supervised transformation flows.
                </p>
              </section>

              <section className="home-command-center">
                <div className="home-command-header">
                  <h2>Jump To Function</h2>
                  <p>Welcome {user.username || user.name}. Start from any core area below.</p>
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
                  <p>Ingest datasets, build agents, run analyses, and review outputs without context switching.</p>
                </div>
                <div>
                  <h3>Serious visual mode</h3>
                  <p>A restrained palette, high contrast text, and precise spacing for focused operation.</p>
                </div>
              </section>
            </div>
        </main>
      </>
  )
}

export default Home
