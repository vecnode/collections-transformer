// @ts-nocheck
import Head from 'next/head'

import React, {useEffect, useRef, useState} from 'react'
import { useSearchParams } from 'next/navigation'
import { useAuth } from "@/contexts/AuthContext";
import { withAuth } from "@/components/withAuth";

import DatasetLabeller from '@/components/datasetLabeller';
import StatusBox from '@/components/statusBox';





const ViewDataset = () => {
    const { user } = useAuth();

    const title = "Collections Transformer - View Dataset"

    var params = useSearchParams()
    let param_dataset_id = params.get('dataset_id')

    const [dataset, setDataset] = useState({
      id:"",
      name:"",
      artworks:[]
    })

    const [datasetStatus, setDatasetStatus] = useState("")
    const [dataset_id, setDatasetId] = useState("")


    const getDataset = (dataset_id) => {

      const requestOptions = {
        method: 'GET',
        mode: 'cors',
        headers: {'Content-Type': 'application/json'}
      };
    
      try {
        fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/dataset?" + new URLSearchParams({
          dataset_id:dataset_id,
          include_items:true
        }),requestOptions)
        .then(response => response.json())
        .then(
          res => {
            console.log("in /dataset response")
            console.log(res.data)
            const artworkCount = res.data.artwork_count || (res.data.artworks ? res.data.artworks.length : 0)
            setDatasetStatus("Loaded "+artworkCount+" data records")
            setDataset(res.data)
          }
        )
      } catch (e){
        console.log("ERROR")
        console.log(e)
      }
    }

    const updateDataset = (dataset_id, data) => {

      console.log(data)
      console.log(dataset_id)
  
      const requestOptions = {
        method: 'GET',
        mode: 'cors',
        headers: {'Content-Type': 'application/json'}
      };
  
      try{
        fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/dataset_update?" + new URLSearchParams({
          dataset_id:dataset_id,
          data:JSON.stringify(data)
        }), requestOptions)
        .then(res => res.json()).then((res) => {
          console.log(res)
          if (res.status==200){
            getDataset(dataset_id)
          }
        })
      } catch (e){
        console.log("ERROR")
        console.log(e)
      }

    }




    useEffect(() => {
      if (dataset_id!= ""){
        setDatasetStatus("Loading dataset...")
        getDataset(dataset_id)
      }
    }, [dataset_id])



    useEffect(()=>{
      if(param_dataset_id!=undefined && dataset_id==""){
        setDatasetId(param_dataset_id)
      }
    },[])


    return (

      <>
      <Head>
        <title>{title}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-+0n0xVW2eSR5OomGNYDnhzAbDsOXxcvSN1TPprVMTNDbiYZCxYbOOl7+AMvyTG2x" crossOrigin="anonymous"/>
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.25/css/dataTables.bootstrap5.css"/>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.3.0/font/bootstrap-icons.css"/>
      </Head>

      <main>
          
        <div className="container">
        
          <h1>Dataset</h1>
          <hr/>
          <h3>{dataset.name}</h3>
          <hr/>
        </div>
        
      
        {dataset.artworks.length > 0 ? (
          <DatasetLabeller
            dataset={dataset} 
            labelset={{"_id":"", labels:[]}}
            showLabels={false}
            enableLabelling={false}
            onLabelsChanged={()=>{}}
          />) : null}

        
      

        <StatusBox text={datasetStatus}></StatusBox>

        <script type="text/javascript" charSet="utf8" src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script type="text/javascript" charSet="utf8" src="https://cdn.datatables.net/1.10.25/js/jquery.dataTables.js"></script>
        <script type="text/javascript" charSet="utf8" src="https://cdn.datatables.net/1.10.25/js/dataTables.bootstrap5.js"></script>
      
        

      </main>

      </>
  )
}

export default withAuth(ViewDataset)
