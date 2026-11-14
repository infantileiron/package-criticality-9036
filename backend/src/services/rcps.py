"""Crew-capacity serial dispatch; non-preemptive; deterministic (priority, task_id) rule."""
import re,heapq
MAX_CAPACITY=1000000
MAX_PRIORITY=1000000
CREW_ID=re.compile(r'[A-Za-z][A-Za-z0-9_-]{0,23}')

def validate_crews(crews,dispatch,task_ids):
 """Normalize and validate crew capacities and per-task dispatch; raise ValueError on any violation."""
 if not isinstance(crews,list) or not isinstance(dispatch,list):raise ValueError('班组与派工配置须为列表')
 if len(crews)>20:raise ValueError('班组数量须不超过20')
 if len(dispatch)>60:raise ValueError('派工配置须不超过60任务')
 seen=set();norm_crews=[]
 for c in crews:
  cid=c.get('crew_id');cap=c.get('capacity')
  if not isinstance(cid,str) or not CREW_ID.fullmatch(cid):raise ValueError('班组ID须为英数短ID')
  if cid in seen:raise ValueError('班组ID须唯一: '+cid)
  if isinstance(cap,bool) or not isinstance(cap,int) or not 1<=cap<=MAX_CAPACITY:raise ValueError('班组容量须为1至1000000整数')
  seen.add(cid);norm_crews.append({'crew_id':cid,'capacity':cap})
 capacity={c['crew_id']:c['capacity'] for c in norm_crews}
 if not norm_crews and dispatch:raise ValueError('未配置班组容量，不能配置任务占用')
 norm_dispatch=[];seen_t=set()
 for d in dispatch:
  tid=d.get('task_id')
  if tid not in task_ids:raise ValueError('派工任务不在工作包内: '+str(tid))
  if tid in seen_t:raise ValueError('任务派工配置重复: '+tid)
  seen_t.add(tid)
  pr=d.get('priority',0)
  if isinstance(pr,bool) or not isinstance(pr,int) or not 0<=pr<=MAX_PRIORITY:raise ValueError('派工优先级须为0至1000000整数，数值小者先派工')
  needs=d.get('crews') or {}
  if not isinstance(needs,dict):raise ValueError('任务占用须为班组ID到占用数的映射')
  norm_needs={}
  for cid,u in needs.items():
   if cid not in capacity:raise ValueError('任务占用未定义的班组: '+str(cid))
   if isinstance(u,bool) or not isinstance(u,int) or u<1:raise ValueError('任务占用须为正整数')
   if u>capacity[cid]:raise ValueError(f'任务{tid}占用{u}超过班组{cid}容量{capacity[cid]}，超容量需求拒绝')
   norm_needs[cid]=u
  norm_dispatch.append({'task_id':tid,'priority':pr,'crews':dict(sorted(norm_needs.items()))})
 if norm_crews:
  missing=sorted(set(task_ids)-seen_t)
  if missing:raise ValueError('配置班组后每个任务都须派工，缺少: '+','.join(missing[:8])+('…' if len(missing)>8 else ''))
 norm_crews.sort(key=lambda c:c['crew_id']);norm_dispatch.sort(key=lambda d:d['task_id'])
 return norm_crews,norm_dispatch

def schedule(durations,edges,crews,dispatch):
 """Validate config, then run the serial dispatch. See schedule_validated for semantics."""
 crews,dispatch=validate_crews(crews,dispatch,set(durations))
 return schedule_validated(durations,edges,crews,dispatch)

def schedule_validated(durations,edges,crews,dispatch):
 """Serial dispatch over pre-validated crews/dispatch: at each decision time, eligible tasks (all
 predecessors finished) are dispatched in (priority, task_id) order while crew capacity allows; started
 tasks hold crews until finish (no preemption). Deterministic for any input order."""
 if not durations:raise ValueError('at least one task required')
 if not crews:raise ValueError('crew capacity required for resource-constrained scheduling')
 capacity={c['crew_id']:c['capacity'] for c in crews}
 priority={k:0 for k in durations};demand={k:{} for k in durations}
 for d in dispatch:priority[d['task_id']]=d['priority'];demand[d['task_id']]=dict(d['crews'])
 ids=sorted(durations);pred={k:[] for k in ids};succ={k:[] for k in ids}
 for edge in edges:
  if len(edge)!=2:raise ValueError('dependency requires predecessor and successor')
  a,b=edge
  if a not in durations or b not in durations:raise ValueError('unknown dependency endpoint')
  pred[b].append(a);succ[a].append(b)
 for k in ids:succ[k].sort()
 remaining={k:len(pred[k]) for k in ids};free=dict(capacity)
 eligible=[(priority[k],k) for k in ids if not remaining[k]];heapq.heapify(eligible)
 events=[];seq=0;start={};finish={};ready={k:0.0 for k in ids};t=0.0;completed=0;n=len(ids)
 while completed<n:
  deferred=[]
  while eligible:
   _,k=heapq.heappop(eligible)
   need=demand[k]
   if all(free[c]>=u for c,u in need.items()):
    start[k]=t;f=t+durations[k];finish[k]=f
    if durations[k]==0:
     completed+=1
     for j in succ[k]:
      ready[j]=max(ready[j],f);remaining[j]-=1
      if remaining[j]==0:heapq.heappush(eligible,(priority[j],j))
    else:
     for c,u in need.items():free[c]-=u
     seq+=1;heapq.heappush(events,(f,seq,k))
   else:deferred.append((priority[k],k))
  for item in deferred:heapq.heappush(eligible,item)
  if completed>=n:break
  if not events:raise ValueError('dependency graph contains a cycle')
  t=events[0][0]
  while events and events[0][0]==t:
   f,_,k=heapq.heappop(events);completed+=1
   for c,u in demand[k].items():free[c]+=u
   for j in succ[k]:
    ready[j]=max(ready[j],f);remaining[j]-=1
    if remaining[j]==0:heapq.heappush(eligible,(priority[j],j))
 rows=[{'task_id':k,'start':start[k],'finish':finish[k],'precedence_ready':ready[k],'resource_wait':start[k]-ready[k]} for k in ids]
 return {'project_finish':max(finish.values()),'tasks':rows,'crews':crews,'dispatch':dispatch,'dispatch_rule':'eligible tasks dispatched in (priority, task_id) order; first-started holds crews; non-preemptive'}
