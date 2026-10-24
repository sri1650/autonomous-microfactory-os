use std::sync::Arc;

use tokio::sync::Mutex;
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
        let request = request.into_inner();
        if request.robot_id != self.robot_id {
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
        Ok(Response::new(ProtoCommandAck {
            command_id: ack.command_id,
            disposition: disposition.into(),
            reason: ack.reason,
        }))
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
