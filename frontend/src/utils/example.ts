export function example(){return {name:'新检修工作包·4任务',source:'duochuan_new_package.json',tasks:[{task_id:'A',name:'交接定位',a:2,m:2,b:2},{task_id:'B',name:'支座检查',a:2,m:3,b:5},{task_id:'C',name:'锚固施工',a:3,m:5,b:7},{task_id:'D',name:'联合复检',a:1,m:1,b:1}]}}
export function crewExample(){return [{crew_id:'CR-A',capacity:4},{crew_id:'CR-B',capacity:2}]}
export function dispatchExample(tasks:{task_id:string}[]){return tasks.map((t,i)=>({task_id:t.task_id,priority:i?50:10,crews:i%3?{'CR-A':1}:{'CR-B':1}}))}
