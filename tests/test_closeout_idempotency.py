"""Completion gates for command identity: content changes cannot replay success."""
from copy import deepcopy
import pytest
from microfactory.adapters.memory import InMemoryEventSink, InMemoryJobRepository
from microfactory.orchestrator import Orchestrator
from microfactory.domain.models import JobRecord, TaskRecord, TaskDefinition


def job():
    return JobRecord('job-closeout', 5, {'move': TaskRecord(TaskDefinition('move','MOVE','mover',payload={'target':[1,2]}))})


@pytest.mark.parametrize('field',['payload','priority'])
def test_changed_submit_content_cannot_reuse_successful_command_id(field):
    service=Orchestrator(InMemoryJobRepository(),InMemoryEventSink())
    original=job()
    service.submit_job(original,command_id='unique-command')
    changed=deepcopy(original)
    if field == 'priority': changed.priority=999
    else: changed.tasks['move'].definition.payload['target']=[99,99]
    with pytest.raises(ValueError,match='different operation'):
        service.submit_job(changed,command_id='unique-command')
    # Correct identical retransmission remains a read-only replay.
    assert service.submit_job(original,command_id='unique-command').replayed is True
    assert service.get_job(original.job_id).tasks['move'].definition.payload['target']==[1,2]


def test_empty_command_identity_never_mutates_repository():
    repository=InMemoryJobRepository()
    service=Orchestrator(repository,InMemoryEventSink())
    with pytest.raises(ValueError,match='command_id'):
        service.submit_job(job(),command_id='')
    assert repository.get('job-closeout') is None
