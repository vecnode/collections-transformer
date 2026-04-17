import Head from 'next/head'
import React, {useEffect, useState} from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from "@/_contexts/AuthContext";
import { withAuth } from "@/_components/withAuth";
import StatusBox from '@/_components/statusBox';
import { useSearchParams } from 'next/navigation'



import OverviewAnalyser from '@/_components/overviewanalyser';


import ErrorBox from '@/_components/errorBox';

import { getFilterErrorString } from '@/lib/errors/contentFilter';


const Analyser = () => {
  const { user } = useAuth();

  const title = "Collections Transformer - Analyser Creator"

  const [model_source, setModelSource] = useState("")
  const [analyser_id, setAnalyserId] = useState("")
  const [analyser, setAnalyser] = useState({})
  const [analyser_name, setAnalyserName] = useState("")

  const [test_sample_ids, setTestSampleIds] = useState([])
  const [test_sample_predictions, setTestSamplePredictions] = useState([])
  const [unlabelledTestData, setUnlabelledTestData] = useState("")

  const [sample_ids, setSampleIds] = useState([])
  const [results, setResults] = useState({
    text:{}
  })

  const [analyserStatus, setAnalyserStatus] = useState("Unknown")
  const [errorStatus, setErrorStatus] = useState({
    text:"",
    type:""
  })

  const [tabIndex, setTabIndex] = useState(0);
  const [tabsDisabled, setTabsDisabled] = useState({
    0:false,
    1:true,
    2:true,
    3:true,
    4:true,
  })

  const router = useRouter()
  var params = useSearchParams()

  const getModelSource = () => {
    const requestOptions = {
      method: 'GET',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'}
    };

    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/model_source?" + new URLSearchParams({
    }), requestOptions)
    .then(
      response =>  response.json()
    ).then(
      res => {
        console.log(res)
        if (res.status == 200)
          setModelSource(res.data)
      }
    )
  }

  const getAnalyser = (id) => {

    const requestOptions = {
      method: 'GET',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'}
    };

    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/analyser?" + new URLSearchParams({
      analyser_id:id,
      include_names:true,
      include_versions:true
    }), requestOptions)
    .then(res => res.json()).then((res) => {
      if (res.status == "200"){
        let analyser=res.data
        setAnalyser(analyser)
        setTabsDisabled({
          0:false,
          1:!((analyser['dataset_id'].length>0 && analyser['labelset_id'].length>0) && (analyser.owner == user.user_id || user.sub)),
          2:!(("predictions" in analyser && analyser['predictions'].length>0) && ("accuracy" in analyser && analyser['accuracy'].toString().length>0)),
          3:!(("accuracy" in analyser) && (analyser['accuracy'].toString().length>0)), //TODO Store target accuracy & only enable Use tab if accuracy is high enough
          4:true
        })
        if ("predictions" in analyser){
          setTestSamplePredictions(analyser['predictions'])
        }
        if ("sample_ids" in analyser) {
          setTestSampleIds(analyser['sample_ids'])
        }
      } else {
        setErrorStatus({
          text:res.error,
          type:"error"
        })
      }
    })
  }

  const getPredictions = (analyserid, dataset_config, sampleids, example_ids) => {

    console.log("get predictions")

    let pred_type = "dataset_id" in dataset_config && dataset_config['dataset_id']!= null ? "use" : "test"

    console.log(pred_type)

    const requestOptions = {
      method: 'GET',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'},
    };

    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/llm_predictions?"+ new URLSearchParams({
      analyser_id:analyserid,
      dataset_id:"dataset_id" in dataset_config ? dataset_config['dataset_id'] : null,
      num_predictions:"num_predictions" in dataset_config ? dataset_config['num_predictions'] : 0,
      start:"preds_start_index" in dataset_config ? dataset_config["preds_start_index"] : 0,
      end:"preds_end_index" in dataset_config ? dataset_config["preds_end_index"] : 0,
      auto_select_sample:"auto_select_sample" in dataset_config ? dataset_config["auto_select_sample"] : null,
      sample_ids: sampleids
    }), requestOptions)
    .then(response => response.json())
    .then(res => {
      if (res.status == "200" && res.data.predictions!=null){
        //check if every item triggered the content filter
        let preds = res.data.predictions.map(a => Object.values(a)).flat()
        let all_triggered = preds.every((val, i, arr) => val === 'content_filter')
        if (all_triggered===false) {
          let result_string = "Predicted results for " + res.data.predictions.length + " items."
          if (res.data.status=="filtered_success"){
            setErrorStatus({
              text:getFilterErrorString(res.data.errors, false),
              type:"warning"
            })
          }
          setAnalyserStatus(result_string)
          if (pred_type == "use"){
            setResults(res.data.predictions)
            if (dataset_config["auto_select_sample"] == 'true'){
              setSampleIds(res.data.sample_ids)
            }
          } else {
            setTestSamplePredictions(res.data.predictions)
            setTestSampleIds(res.data.sample_ids)
            setUnlabelledTestData(res.data.unlabelledTestData)
          }
        } else {
          setAnalyserStatus("Error: Analyser predictions failed (see details below)")
          setErrorStatus({
            text:getFilterErrorString(res.data.errors, true),
            type:"error"
          })
        }
      } else {
        setAnalyserStatus("Error: Analyser predictions failed (see details below)")
        setErrorStatus({
          text:res.error,
          type:"error"
        })
      }
    }).then(() => {
      getAnalyser(analyser_id)
    })
  }

  const createAnalyser = (config, data) => {
    setAnalyserStatus("Creating analyser...")
    const requestOptions = {
      method: 'GET',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'},
    };

    console.log(config)

    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/analyser_new?"+ new URLSearchParams({
      user_id:user.user_id || user.sub,
      name:data.analyser_name,
      task_description:data.task_description,
      analyser_type:data.chosen_analyser_type,
      labelling_guide:data.labelling_guide,
      dataset_id:data.chosen_dataset_id,
      category_id:data.chosen_category_id,
      labelset_id:data.chosen_labelset_id,
      example_ids:JSON.stringify(data.example_ids),
      auto_select_examples:'auto_select_examples' in config ? config['auto_select_examples'] : false,
      num_examples:'num_examples' in config ? config['num_examples'] : 0,
      example_start_index:'examples_start_index' in config ? config['examples_start_index'] : 0,
      example_end_index:'examples_end_index' in config ? config['examples_end_index'] : 0
    }), requestOptions)
    .then(response => response.json())
    .then(res => {
      setAnalyserStatus("")
      console.log(res)
      setAnalyserId(res.data.analyser_id)
      router.push("/analyser?" + new URLSearchParams({
        analyser_id:res.data.analyser_id
      }))
      return res.data.analyser_id
    })
  }


  const handleSave = (config, data) => {
    createAnalyser(config, data)
  }

  const handleSetupUpdate = () => {
    setAnalyserStatus("Analyser updated")
  }

  
  
 
  
  

  const handleError = (error_text) => {
    if (error_text.length>0){
      console.log("ERROR")
      console.log(error_text)
      setAnalyserStatus("Error: Action Failed (see details below)")
    }
    setErrorStatus({
      text:error_text,
      type:"error"
    })
  }

  const handleWarning = (warning_text) => {
    setAnalyserStatus("")
    if (warning_text.length>0){
      console.log("WARNING")
      console.log(warning_text)
    }
    setErrorStatus({
      text:warning_text,
      type:"warning"
    })
  }


  

  useEffect(() => {
    getModelSource()
  }, [model_source])

  useEffect(() => {
    if (analyser_id!= ""){
      getAnalyser(analyser_id)
    }
  }, [analyser_id])

  useEffect(() => {
    let id = params.get('analyser_id')
    if (id!= "" && id!=null){
      setAnalyserId(id)
      getAnalyser(id)
    } else {
      setAnalyserId("")
      setTabsDisabled({
        0:false,
        1:true,
        2:true,
        3:true,
        4:true,
      })
      setAnalyser({})
      setTabIndex(0)
    }
  }, [params])
    
  return (
      <>
      <Head>
        <title>{title}</title>
      </Head>
      <main>
        <div className="container">
          
        <h1>Model</h1>

        <hr/>

          <div className="overview-content">
            <OverviewAnalyser
              user={user} 
              analyser_id={analyser_id}
              analyser={analyser}
              showPredictions={false}
              accordionLabels={[
                "Details",
                "Knowledge Source"
              ]}
              getAnalyser={getAnalyser}
              onUpdate={handleSetupUpdate}
              onComplete={handleSave}
              onError={handleError}
              onWarning={handleWarning}
            ></OverviewAnalyser>
          </div>

          {analyserStatus != "Unknown" ? (
            <StatusBox text={analyserStatus}></StatusBox>
          ) : (<></>)}
          <ErrorBox status={errorStatus}></ErrorBox>

      </div>
      </main>
      </>
  )
}


export default withAuth(Analyser);

