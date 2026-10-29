//! Real Tokio execution results, not caller-injected success acknowledgements.
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use robot_runtime::proto::robot_runtime_server::RobotRuntime;
use robot_runtime::proto::{CommandDisposition, CommandResultRequest, CommandTerminalState,
    Pose2D, RobotCommand, RobotStatusRequest};
use robot_runtime::RuntimeService;
use tonic::Request;

fn command(id: &str, duration_ms: u64, fail_step: Option<usize>) -> RobotCommand {
    let deadline = SystemTime::now().duration_since(UNIX_EPOCH).unwrap() + Duration::from_secs(3);
    RobotCommand {
        command_id: id.to_owned(), correlation_id: "causal-test".to_owned(),
        robot_id: "test-robot".to_owned(), kind: "MOVE".to_owned(),
        deadline: Some(prost_types::Timestamp { seconds: deadline.as_secs() as i64,
            nanos: deadline.subsec_nanos() as i32 }),
        payload_json: serde_json::json!({"waypoints":[[0.0,0.0],[1.0,0.0],[2.0,0.0]],
            "step_ms":duration_ms,"fail_after_steps":fail_step}).to_string().into_bytes(),
    }
}
fn query(id: &str) -> CommandResultRequest {
    CommandResultRequest { robot_id: "test-robot".to_owned(), command_id: id.to_owned() }
}
fn service() -> RuntimeService {
    RuntimeService::simulated("test-robot", Pose2D { x: 0.0, y: 0.0, yaw: 0.0 })
}
async fn terminal(service: &RuntimeService, id: &str) -> robot_runtime::proto::CommandResult {
    for _ in 0..200 {
        let r = service.get_command_result(Request::new(query(id))).await.unwrap().into_inner();
        if r.state != CommandTerminalState::Unspecified as i32 { return r; }
        tokio::time::sleep(Duration::from_millis(5)).await;
    }
    panic!("simulation never produced a terminal result");
}

#[tokio::test]
async fn accepted_is_not_completed_and_actual_route_progress_drives_result() {
    let service = service();
    let cmd = command("move-1", 20, None);
    let ack = service.submit_command(Request::new(cmd.clone())).await.unwrap().into_inner();
    assert_eq!(ack.disposition, CommandDisposition::Accepted as i32);
    let initial = service.get_command_result(Request::new(query("move-1"))).await.unwrap().into_inner();
    assert_eq!(initial.state, CommandTerminalState::Unspecified as i32);
    let done = terminal(&service, "move-1").await;
    assert_eq!(done.state, CommandTerminalState::Succeeded as i32);
    let details: serde_json::Value = serde_json::from_str(&done.detail).unwrap();
    assert_eq!(details["steps_executed"], 3);
    assert_eq!(details["scope"], "SOFTWARE_SIMULATION");
    let retry = service.submit_command(Request::new(cmd)).await.unwrap().into_inner();
    assert_eq!(retry, ack);
    let status = service.get_status(Request::new(RobotStatusRequest{robot_id:"test-robot".to_owned()})).await.unwrap().into_inner();
    assert!(status.software_simulation);
    assert_eq!(status.pose.unwrap().x, 2.0);
    assert!(status.active_command_id.is_empty());
    assert!(!status.runtime_session_id.is_empty());
}

#[tokio::test]
async fn altered_wire_payload_does_not_replay_a_successful_identity() {
    let service = service();
    let cmd = command("identity", 10, None);
    service.submit_command(Request::new(cmd.clone())).await.unwrap();
    let mut changed = cmd;
    changed.payload_json = b"{}".to_vec();
    let denied = service.submit_command(Request::new(changed)).await.unwrap().into_inner();
    assert_eq!(denied.disposition, CommandDisposition::Rejected as i32);
    assert_eq!(terminal(&service, "identity").await.state, CommandTerminalState::Succeeded as i32);
}

#[tokio::test]
async fn injected_failure_is_a_real_terminal_failure_not_test_authored_success() {
    let service = service();
    service.submit_command(Request::new(command("fault", 5, Some(1)))).await.unwrap();
    let done = terminal(&service, "fault").await;
    assert_eq!(done.state, CommandTerminalState::Failed as i32);
    let details: serde_json::Value = serde_json::from_str(&done.detail).unwrap();
    assert_eq!(details["steps_executed"], 1);
}

#[tokio::test]
async fn deadline_expiry_during_execution_cannot_be_reported_success() {
    let service = service();
    let mut cmd = command("timeout", 100, None);
    let deadline = SystemTime::now().duration_since(UNIX_EPOCH).unwrap() + Duration::from_millis(30);
    cmd.deadline = Some(prost_types::Timestamp{seconds:deadline.as_secs() as i64,nanos:deadline.subsec_nanos() as i32});
    service.submit_command(Request::new(cmd)).await.unwrap();
    assert_eq!(terminal(&service, "timeout").await.state, CommandTerminalState::TimedOut as i32);
}

#[tokio::test]
async fn cancellation_remains_terminal_when_the_route_worker_wakes() {
    let service = service();
    service.submit_command(Request::new(command("cancel", 50, None))).await.unwrap();
    let cancelled = service.cancel_command(Request::new(query("cancel"))).await.unwrap().into_inner();
    assert_eq!(cancelled.state, CommandTerminalState::Cancelled as i32);
    tokio::time::sleep(Duration::from_millis(200)).await;
    assert_eq!(terminal(&service, "cancel").await, cancelled);
    let status=service.get_status(Request::new(RobotStatusRequest{robot_id:"test-robot".to_owned()})).await.unwrap().into_inner();
    assert_eq!(status.pose.unwrap().x, 0.0);
}
