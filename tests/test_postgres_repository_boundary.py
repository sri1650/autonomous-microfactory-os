from microfactory.adapters.postgres import PostgresJobRepository
from microfactory.domain.models import JobRecord,TaskDefinition,TaskRecord

class Cursor:
    def __init__(self,script=None):
        self.script=script or []
        self.executed=[]
        self.last=""
    def __enter__(self): return self
    def __exit__(self,*a): return False
    def execute(self,q,p=None): self.executed.append((q,p)); self.last=q
    def fetchone(self):
        if "FROM jobs" in self.last: return ("j",3,"RUNNING")
        return None
    def fetchall(self):
        return [("j","a","MOVE","mover",[],{},"READY",0,None)]

class Conn:
    def __init__(self): self.cur=Cursor(); self.commits=0; self.rollbacks=0
    def cursor(self): return self.cur
    def commit(self): self.commits+=1
    def rollback(self): self.rollbacks+=1

def test_get_rehydrates_job():
    c=Conn(); repo=PostgresJobRepository(lambda:c)
    job=repo.get("j")
    assert job.job_id=="j"
    assert job.tasks["a"].definition.required_resource_type=="mover"

def test_save_emits_transactional_sql():
    c=Conn(); repo=PostgresJobRepository(lambda:c)
    job=JobRecord("j",1,{"a":TaskRecord(TaskDefinition("a","MOVE","mover"))})
    repo.save(job)
    assert c.commits==1 and c.rollbacks==0
    text="\n".join(q for q,_ in c.cur.executed)
    assert "INSERT INTO jobs" in text
    assert "INSERT INTO tasks" in text
