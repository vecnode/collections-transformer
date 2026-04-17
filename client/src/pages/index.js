import Head from 'next/head'
import React, {useEffect, useState} from 'react'
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

    return (

      <>
      <Head>
        <title>{title}</title>
      </Head>
        <main>
            <div className="container">
              <h1>Collections Transformer</h1>
              <hr/>

              <div className='feature-box intro'>
                <div>
                  
                  <u><strong>Welcome {user.username || user.name}</strong>!</u> <br></br>
                  
                </div>
                
              
              </div>

            </div>

            
        </main>
      </>
  )
}

export default Home
