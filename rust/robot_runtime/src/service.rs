use std::sync::Arc;

use opentelemetry::global;
use opentelemetry::propagation::Extractor;
use opentelemetry::trace::{
    Span, SpanContext, SpanId, TraceContextExt, TraceFlags, TraceId, TraceState, Tracer,
};
use opentelemetry::{Context, KeyValue};
use opentelemetry_sdk::propagation::TraceContextPropagator;
use opentelemetry_sdk::trace::TracerProvider;
use tokio::sync::Mutex;
use tonic::metadata::MetadataMap;
use tonic::{Request, Response, Status};

use crate::proto::robot_runtime_server::RobotRuntime;
use crate::proto::{
    CommandAck as ProtoCommandAck, CommandDisposition as ProtoCommandDisposition,
    RobotCommand as ProtoRobotCommand, RobotMode as ProtoRobotMode, RobotStatus,
    RobotStatusRequest,
};
use crate::{CommandDisposition, RobotCommand, RobotMode, RobotRuntimeState};

#[derive(Debug, Clone)]
pub struct RuntimeService {
    robot_id: String,
    state: Arc<Mutex<RobotRuntimeState>>,
}

impl RuntimeService {
    pub fn new(robot_id: impl Into<String>, mode: RobotMode) -> Self {
        initialize_tracing();
        Self {
            robot_id: robot_id.into(),
            state: Arc::new(Mutex::new(RobotRuntimeState::new(mode))),
        }
    }

    pub fn shared_state(&self) -> Arc<Mutex<RobotRuntimeState>> {
        Arc::clone(&self.state)
    }
}

#[tonic::async_trait]
impl RobotRuntime for RuntimeService {
    async fn submit_command(
        &self,
        request: Request<ProtoRobotCommand>,
    ) -> Result<Response<ProtoCommandAck>, Status> {
        let parent_context = extract_parent_context(request.metadata());
        let parent_span_context = parent_context.span().span_context().clone();
        let request = request.into_inner();
        let mut span = global::tracer("robot_runtime")
            .start_with_context("runtime.submit_command", &parent_context);
        span.set_attribute(KeyValue::new(
            "microfactory.robot_id",
            self.robot_id.clone(),
        ));
        span.set_attribute(KeyValue::new(
            "microfactory.command_id",
            request.command_id.clone(),
        ));
        let span_context = span.span_context().clone();
        if request.robot_id != self.robot_id {
            span.end();
            return Err(Status::not_found("robot_id does not match this runtime"));
        }
        let ack = self.state.lock().await.submit_command(RobotCommand {
            command_id: request.command_id,
            correlation_id: request.correlation_id,
            kind: request.kind,
        });
        let disposition = match ack.disposition {
            CommandDisposition::Accepted => ProtoCommandDisposition::Accepted,
            CommandDisposition::Rejected => ProtoCommandDisposition::Rejected,
        };
        let mut response = Response::new(ProtoCommandAck {
            command_id: ack.command_id,
            disposition: disposition.into(),
            reason: ack.reason,
        });
        if span_context.is_valid() {
            response.metadata_mut().insert(
                "x-microfactory-trace-id",
                span_context.trace_id().to_string().parse().unwrap(),
            );
            response.metadata_mut().insert(
                "x-microfactory-span-id",
                span_context.span_id().to_string().parse().unwrap(),
            );
        }
        if parent_span_context.is_valid() {
            response.metadata_mut().insert(
                "x-microfactory-parent-trace-id",
                parent_span_context.trace_id().to_string().parse().unwrap(),
            );
        }
        span.end();
        Ok(response)
    }

    async fn get_status(
        &self,
        request: Request<RobotStatusRequest>,
    ) -> Result<Response<RobotStatus>, Status> {
        if request.into_inner().robot_id != self.robot_id {
            return Err(Status::not_found("robot_id does not match this runtime"));
        }
        let state = self.state.lock().await;
        Ok(Response::new(RobotStatus {
            robot_id: self.robot_id.clone(),
            mode: proto_mode(state.mode()).into(),
            pose: None,
            battery_fraction: 1.0,
            active_command_id: state.active_command_id().unwrap_or_default().to_owned(),
            faults: Vec::new(),
            heartbeat_time: None,
        }))
    }
}

fn extract_parent_context(metadata: &MetadataMap) -> Context {
    let extracted = global::get_text_map_propagator(|propagator| {
        propagator.extract(&GrpcMetadataExtractor(metadata))
    });
    if extracted.span().span_context().is_valid() {
        return extracted;
    }

    let Some(header) = metadata
        .get("traceparent")
        .and_then(|value| value.to_str().ok())
    else {
        return extracted;
    };
    let parts: Vec<_> = header.split('-').collect();
    if parts.len() != 4 {
        return extracted;
    }
    let parsed = (
        TraceId::from_hex(parts[1]),
        SpanId::from_hex(parts[2]),
        u8::from_str_radix(parts[3], 16),
    );
    match parsed {
        (Ok(trace_id), Ok(span_id), Ok(flags)) => {
            Context::new().with_remote_span_context(SpanContext::new(
                trace_id,
                span_id,
                TraceFlags::new(flags),
                true,
                TraceState::default(),
            ))
        }
        _ => extracted,
    }
}

fn initialize_tracing() {
    static INIT: std::sync::Once = std::sync::Once::new();
    INIT.call_once(|| {
        global::set_text_map_propagator(TraceContextPropagator::new());
        global::set_tracer_provider(TracerProvider::builder().build());
    });
}

struct GrpcMetadataExtractor<'a>(&'a MetadataMap);

impl Extractor for GrpcMetadataExtractor<'_> {
    fn get(&self, key: &str) -> Option<&str> {
        self.0.get(key).and_then(|value| value.to_str().ok())
    }

    fn keys(&self) -> Vec<&str> {
        self.0
            .keys()
            .filter_map(|key| match key {
                tonic::metadata::KeyRef::Ascii(name) => Some(name.as_str()),
                tonic::metadata::KeyRef::Binary(_) => None,
            })
            .collect()
    }
}

fn proto_mode(mode: RobotMode) -> ProtoRobotMode {
    match mode {
        RobotMode::Offline => ProtoRobotMode::Offline,
        RobotMode::Idle => ProtoRobotMode::Idle,
        RobotMode::Homing => ProtoRobotMode::Homing,
        RobotMode::Ready => ProtoRobotMode::Ready,
        RobotMode::Executing => ProtoRobotMode::Executing,
        RobotMode::Paused => ProtoRobotMode::Paused,
        RobotMode::Faulted => ProtoRobotMode::Faulted,
        RobotMode::EStop => ProtoRobotMode::Estop,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn command(command_id: &str, robot_id: &str) -> ProtoRobotCommand {
        ProtoRobotCommand {
            command_id: command_id.to_owned(),
            correlation_id: "trace-1".to_owned(),
            robot_id: robot_id.to_owned(),
            kind: "MOVE".to_owned(),
            deadline: None,
            payload_json: Vec::new(),
        }
    }

    #[tokio::test]
    async fn submit_and_status_preserve_idempotency() {
        let service = RuntimeService::new("robot-1", RobotMode::Ready);
        let first = service
            .submit_command(Request::new(command("cmd-1", "robot-1")))
            .await
            .unwrap()
            .into_inner();
        let duplicate = service
            .submit_command(Request::new(command("cmd-1", "robot-1")))
            .await
            .unwrap()
            .into_inner();

        assert_eq!(first, duplicate);
        assert_eq!(first.disposition, ProtoCommandDisposition::Accepted as i32);
        let status = service
            .get_status(Request::new(RobotStatusRequest {
                robot_id: "robot-1".to_owned(),
            }))
            .await
            .unwrap()
            .into_inner();
        assert_eq!(status.active_command_id, "cmd-1");
        assert_eq!(status.mode, ProtoRobotMode::Executing as i32);
    }

    #[tokio::test]
    async fn rejects_requests_for_another_robot() {
        let service = RuntimeService::new("robot-1", RobotMode::Ready);
        let error = service
            .submit_command(Request::new(command("cmd-2", "robot-2")))
            .await
            .unwrap_err();
        assert_eq!(error.code(), tonic::Code::NotFound);
    }
}
