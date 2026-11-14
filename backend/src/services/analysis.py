import hashlib,json
from src.services.cpm import cpm
from src.services.pert import simulate
from src.services.rcps import schedule

def analyze(snapshot,scenario):
 tasks=snapshot['package']['tasks'];edges=[[e['predecessor'],e['successor']] for e in snapshot['dependencies']]
 crews=snapshot.get('crews') or [];dispatch=snapshot.get('dispatch') or []
 baseline=cpm({t['task_id']:t['m'] for t in tasks},edges);risk=simulate(tasks,edges,scenario.samples,scenario.seed,scenario.deadline,crews,dispatch)
 data={'snapshot':snapshot,'samples':scenario.samples,'seed':scenario.seed,'deadline':scenario.deadline}
 assumptions=['单位为小时；依赖仅零等待finish-start，多源多汇及孤立任务通过虚拟源/汇的共同边界统一。','CPM使用最可能m工期。每次模拟重新计算依赖最大完工与总时差；所有LF以该次实际项目完工为基准，不用外部deadline。','Beta-PERT lambda=4；alpha=1+4(m-a)/(b-a)，beta=1+4(b-m)/(b-a)，a=m=b为点质量，不调用Beta。','任务工期相互独立；固定seed与ID顺序复现。关键度为总时差<=1e-8小时的次数/全部样本数；不把基线关键集合套到每次模拟。']
 if crews:
  assumptions+=['班组容量、任务占用与派工优先级随情景快照冻结；每个任务须配置派工，超容量需求在情景冻结时拒绝。','串行派工：任务全部前置完工后就绪；同一时刻可就绪的任务按(优先级,任务ID)依次占用班组，先开工的先占用，工期内不抢占；资源等待=开工-前置全部就绪时刻。','每次模拟完工为班组受限完工；延期=班组受限完工-同样本无约束CPM完工；达标比较为班组受限完工<=deadline+1e-8小时，有限样本比例不是工期保证。','未模拟天气共因、日历、班组内人员差异与班组间替代；确定性派工规则不保证资源最优，输出仅供模拟工务计划人工复核。']
 else:
  assumptions+=['达标比较为每次项目完工<=deadline+1e-8小时，仅消除浮点边界误差；有限样本比例不是工期保证，也不是资源约束排程。','未模拟天气共因、共享人员设备、日历与资源竞争；模型输出仅供模拟工务计划人工复核。']
 result={'baseline':baseline,'risk':risk,'tasks':tasks,'edges':edges,'checksum':hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'assumptions':assumptions}
 if crews:result['resource']={'crews':risk['resource']['crews'],'dispatch':risk['resource']['dispatch'],'baseline_schedule':schedule({t['task_id']:t['m'] for t in tasks},edges,crews,dispatch)}
 return result
