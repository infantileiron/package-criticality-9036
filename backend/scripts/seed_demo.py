import json
from sqlalchemy import select,func
from src.config.database import Base,engine,Session
from src.models import User,WorkPackage,TaskDependency,DurationScenario,ScheduleRun,DeliveryReview,Report
from src.services.analysis import analyze
from src.utils.security import hash_password
from src.utils.time import now
from src.utils.serialization import serialize

def seed():
 Base.metadata.create_all(engine)
 with Session() as db:
  for role in ('admin','analyst','viewer'):
   if not db.get(User,role):db.add(User(id=role,email=role+'@duochuan.demo',password=hash_password('Schedule2026!'),role=role))
  names=['现场交接','区域围护','测量复核','工器具核验','基层清理','支座检查','连接件检测','电缆隔离','钻孔定位','锚固施工','边梁加固','排水修补','防护层修复','支架复验','承载复测','密封施工','绝缘复核','灌浆养护','界面验收','防护恢复','联合复检','现场交付','资料封版','独立备件盘点'];modes=[2,3,2,1,4,3,4,2,3,5,4,3,2,3,4,2,3,6,2,2,3,2,1,4]
  tasks=[{'task_id':f'T{i+1:02}','name':name,'a':float(m if i in (0,23) else round(m*.7,2)),'m':float(m),'b':float(m if i in (0,23) else round(m*1.7,2))} for i,(name,m) in enumerate(zip(names,modes))]
  if not db.get(WorkPackage,'demo-package'):db.add(WorkPackage(id='demo-package',name='铎川·检修通道加固工作包',source='duochuan_workpackage_20261112.json',tasks=tasks,created_at=now()));db.flush()
  edges=[(1,5),(1,6),(2,6),(2,7),(3,7),(4,8),(5,9),(6,10),(6,11),(7,11),(7,12),(8,13),(9,14),(10,14),(10,15),(11,15),(12,16),(13,17),(14,18),(15,18),(15,19),(16,19),(17,20),(18,21),(19,21),(19,22),(20,22),(20,23),(5,10),(12,17)]
  for i,(a,b) in enumerate(edges,1):
   if not db.get(TaskDependency,f'demo-edge-{i}'):db.add(TaskDependency(id=f'demo-edge-{i}',package_id='demo-package',predecessor=f'T{a:02}',successor=f'T{b:02}',created_at=now()))
  db.flush()
  if not db.get(DurationScenario,'demo-scenario'):
   snapshot={'package':serialize(db.get(WorkPackage,'demo-package')),'dependencies':[serialize(e) for e in db.scalars(select(TaskDependency).where(TaskDependency.package_id=='demo-package').order_by(TaskDependency.predecessor,TaskDependency.successor))]}
   db.add(DurationScenario(id='demo-scenario',name='通道加固·32小时交付风险基线',package_id='demo-package',version=1,deadline=32.,samples=1500,seed=2410,snapshot=snapshot,created_at=now()))
  db.flush()
  if not db.get(ScheduleRun,'demo-run'):db.add(ScheduleRun(id='demo-run',scenario_id='demo-scenario',status='completed',result=analyze(db.get(DurationScenario,'demo-scenario').snapshot,db.get(DurationScenario,'demo-scenario')),error='',created_at=now()));db.flush()
  if not db.get(DurationScenario,'demo-scenario-crews'):
   b_crew={'T03','T06','T07','T08','T14','T15','T17','T19'};heavy={'T10','T11','T18'};mid={'T10','T11','T12','T13','T14','T16'}
   prio={'T21':10,'T19':20,'T20':20,'T15':30,'T17':30,'T18':30,'T24':90}
   crews=[{'crew_id':'CR-A','capacity':4},{'crew_id':'CR-B','capacity':2}]
   dispatch=[{'task_id':t['task_id'],'priority':prio.get(t['task_id'],40 if t['task_id'] in mid else 50),'crews':{'CR-A':1,'CR-B':1} if t['task_id']=='T21' else {'CR-A':2} if t['task_id'] in heavy else {'CR-B':1} if t['task_id'] in b_crew else {'CR-A':1}} for t in tasks]
   snapshot={'package':serialize(db.get(WorkPackage,'demo-package')),'dependencies':[serialize(e) for e in db.scalars(select(TaskDependency).where(TaskDependency.package_id=='demo-package').order_by(TaskDependency.predecessor,TaskDependency.successor))],'crews':crews,'dispatch':dispatch}
   db.add(DurationScenario(id='demo-scenario-crews',name='通道加固·双班组受限32小时交付风险',package_id='demo-package',version=2,deadline=32.,samples=1500,seed=2410,snapshot=snapshot,created_at=now()))
  db.flush()
  if not db.get(ScheduleRun,'demo-run-crews'):db.add(ScheduleRun(id='demo-run-crews',scenario_id='demo-scenario-crews',status='completed',result=analyze(db.get(DurationScenario,'demo-scenario-crews').snapshot,db.get(DurationScenario,'demo-scenario-crews')),error='',created_at=now()));db.flush()
  if not db.get(DeliveryReview,'demo-review'):db.add(DeliveryReview(id='demo-review',run_id='demo-run',version=1,note='已核对FS依赖与基线时差，模拟每次重算关键度；独立工期未涵盖共享资源、天气共因，32小时达标比例不是交付保证。',decision='accepted',author='analyst@duochuan.demo',created_at=now()));db.flush()
  if not db.get(Report,'demo-report'):db.add(Report(id='demo-report',run_id='demo-run',review_id='demo-review',title='铎川通道加固·基线与风险复核',published_by='admin@duochuan.demo',created_at=now()))
  db.commit();return {m.__tablename__:db.scalar(select(func.count()).select_from(m)) for m in (User,WorkPackage,TaskDependency,DurationScenario,ScheduleRun,DeliveryReview,Report)}
if __name__=='__main__':print(json.dumps(seed(),ensure_ascii=False))
