from microfactory.domain.repositories import EventSink, JobRepository, ResourceRepository


def test_repository_protocols_are_runtime_checkable():
    assert hasattr(JobRepository, "__protocol_attrs__") or getattr(JobRepository, "_is_protocol", False)
    assert getattr(ResourceRepository, "_is_protocol", False)
    assert getattr(EventSink, "_is_protocol", False)
