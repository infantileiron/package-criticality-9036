from pydantic import BaseModel,Field,ConfigDict
class CrewInput(BaseModel):
 model_config=ConfigDict(extra='forbid')
 crew_id:str=Field(min_length=1,max_length=24)
 capacity:int=Field(ge=1,le=1000000,strict=True)
class DispatchInput(BaseModel):
 model_config=ConfigDict(extra='forbid')
 task_id:str=Field(min_length=1,max_length=24)
 priority:int=Field(default=0,ge=0,le=1000000,strict=True)
 crews:dict[str,int]=Field(default_factory=dict,max_length=20)
class ScenarioInput(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
 name:str=Field(min_length=2,max_length=160)
 package_id:str
 deadline:float=Field(ge=0,le=1000000)
 samples:int=Field(ge=100,le=5000,strict=True)
 seed:int=Field(ge=0,le=2147483647,strict=True)
 crews:list[CrewInput]=Field(default_factory=list,max_length=20)
 dispatch:list[DispatchInput]=Field(default_factory=list,max_length=60)
