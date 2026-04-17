'use client'
 
import Link from 'next/link';
import { dateFromObjectId } from '@/_helpers/utills';

const AgentList = ({
  user_id,
  agents=[{
    _id:"Loading...",
    name:" "}], 
  onDeleteHandler
}) => {

  console.log(agents)

  agents.sort(function(a,b){
    if ((a!= null) && (b != null)){
      let a_date = 'created_at' in a ? new Date(a['created_at']) : (("_id" in a) ? dateFromObjectId(a._id) : "")
      let b_date = 'created_at' in b ? new Date(b['created_at']) : (("_id" in b) ? dateFromObjectId(b._id) : "")
      return b_date - a_date;
    } else {
      return 0
    }
  });

  return (
    <table id="agents" className="table table-striped" style={{ borderLeft: '1px solid black', borderRight: '1px solid black', borderBottom: '1px solid black' }}>
    <thead>
      <tr>
        <th>Name</th>
        <th>Description</th>
        <th>Created</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {agents.map(function(agent) {
        if (agent!= null){
          return (
            <tr key={"agent-" + (agent._id != undefined ? agent._id : "")}>
              <td>
                { agent.name && agent.name.length>0 ? agent.name : "* Untitled *" }
              </td>
              <td 
                style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                title={agent.description || ""}
              >
                { agent.description || "" }
              </td>
              <td>
                { 'created_at' in agent ? (new Date(agent['created_at']).toLocaleString()) : (("_id" in agent) ? dateFromObjectId(agent._id).toLocaleString() : "") }
              </td>
              <td>
              { 'owner' in agent && agent.owner == user_id ? (
                <button 
                  onClick={() => onDeleteHandler(agent)}
                  style={{
                    padding: '4px 8px',
                    backgroundColor: 'white',
                    color: 'black',
                    border: '1px solid black',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '12px',
                  }}
                  onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
                  onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
                >
                  Delete
                </button>
              ) : (
                <></>
              )}

              </td>
            </tr>
          )
        } else {
          return
        }
      })}
    </tbody>
    </table>
  );
}

export default AgentList;
