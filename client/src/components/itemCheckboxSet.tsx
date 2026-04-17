'use client'

import { getItemListingID } from '@/lib/items'
import { useEffect, useState } from 'react';

const Checkbox = ({
  outer_id,
  id,
  initialValue,
  isDisabled,
  onChecked,
  label,
  ref_id,
  isAsync = true
}) => {
  const [checked, setChecked] = useState(false)
  const [status, setStatus] = useState('none')

  useEffect(() => {
    if (label == 'positive') {
      setChecked(initialValue == 1)
    } else if (label == 'negative') {
      setChecked(initialValue === 0 && initialValue !== '' && initialValue !== null)
    } else {
      setChecked(initialValue == 1)
    }

    setStatus('none')
  }, [initialValue, label])

  const onChangeHandler = (e) => {
    if (isAsync) {
      setStatus('saving')
    }

    onChecked(e, ref_id)
    setChecked(JSON.parse(e.target.checked))
  }

  if (status == 'saving') {
    return (
      <p id={outer_id} key={outer_id}>
        <input type="checkbox" id={id} disabled={true} checked={checked} onChange={onChangeHandler}></input>
        <span id={id + '-checkbox-loading-icon'} className="spinner-border text-primary" role="status"></span>
      </p>
    )
  }

  return (
    <p id={outer_id} key={outer_id}>
      <input type="checkbox" id={id} disabled={isDisabled} checked={checked} onChange={onChangeHandler}></input>
    </p>
  )
}

const updateLabel = (itemContentId, checkboxStatus, onLabelsChanged, labelset_id, isExclude=false) => {

    const requestOptions = {
        method: 'POST',
        mode: 'cors',
        headers: {'Content-Type': 'application/json'}
    };    

    let params = {
      "labelset_id":labelset_id,
      "id": itemContentId
    }

    if (isExclude){
      params["exclude"]=checkboxStatus
    } else {
      params["checked"]=checkboxStatus
    }

    try {
      return fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/update_label?" + new URLSearchParams(params),requestOptions)
      .then(response => response.json())
      .then(
        res => {
          console.log(res)
          onLabelsChanged()
        }
      )
    } catch (e){
      console.log("ERROR")
      console.log(e)
    }
}

const updateExample = (itemContentId, checkboxStatus, onExamplesChanged, ref_id) => {
  onExamplesChanged(itemContentId, ref_id || null)
}

const ItemCheckboxSet = ({
  ref_id,
    checkbox_type,
    item_id, 
    itemLabels, 
    label,
    enableLabelling,
    onChange,
    isAsync=true
}) => {

    const onCheckboxChecked = (e, ref_id) =>{
      if (checkbox_type == "label"){
        updateLabel(e.target.id,e.target.checked,onChange,ref_id,false)
      } else if (checkbox_type == "example") {
        updateExample(e.target.id,e.target.checked,onChange,ref_id)
      } else if (checkbox_type == "local-example") {
        onChange(e.target.id,ref_id)
      } else if (checkbox_type == "sample") {
        onChange(e.target.id,ref_id)
      } else if (checkbox_type == "exclude") {
        updateLabel(e.target.id,e.target.checked,onChange,ref_id,true)
      }
    }

    if (itemLabels != undefined && itemLabels.length>0) {

        const checkbox_id = [label,"checkbox",getItemListingID(item_id,0)].join("-")
        const inner_checkbox_id = ["p",checkbox_id].join("-")
        const isDisabled = !enableLabelling
        let val = ""
        let styling_class = ""

        if ((checkbox_type == "exclude") && ('exclude' in itemLabels[0])){
          val = itemLabels[0]['exclude'].toString() == "true" ? 1 : 0
          styling_class = itemLabels[0]['exclude'].toString() == "true" ? "exclude" : ""
        } else if ('value' in itemLabels[0]){
          val = itemLabels[0]['value']
        } else {
          val = null
        }
        
        return (
            <span key={checkbox_id} className={styling_class}>
                <Checkbox 
                    key={inner_checkbox_id} 
                    inner_id={inner_checkbox_id} 
                    id={checkbox_id} 
                    initialValue={val}
                    isDisabled={isDisabled} 
                    onChecked={onCheckboxChecked} 
                    label={label} 
                    ref_id={ref_id}
                    isAsync={isAsync}
                />
            </span>
        )
    }

}

export default ItemCheckboxSet