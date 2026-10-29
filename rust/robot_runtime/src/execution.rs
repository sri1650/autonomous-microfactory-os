//! Explicit software-only route execution, enabled only by the demo CLI flag.
//! No hardware adapter or physical robot command is provided here.
use std::collections::BTreeMap;
use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use serde::Deserialize;
use tokio::sync::Mutex;
use tonic::Status;

use crate::proto::{Pose2D, RobotCommand as WireCommand};
use crate::{CommandResult, CommandTerminalState, RobotRuntimeState};

#[derive(Debug)]
pub(crate) struct ExecutionBook {
    pub requests: BTreeMap<String, WireCommand>,
    pub steps: BTreeMap<String, u64>,
    pub pose: Pose2D,
    pub session_id: String,
}

impl ExecutionBook {
    pub fn new(pose: Pose2D) -> Self {
        let nanos = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_nanos();
        Self {
            requests: BTreeMap::new(),
            steps: BTreeMap::new(),
            pose,
            session_id: format!("software-runtime-{}-{nanos}", std::process::id()),
        }
    }
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct SimulationRoute {
    pub waypoints: Vec<[f64; 2]>,
    pub step_ms: u64,
    #[serde(default)]
    pub fail_after_steps: Option<usize>,
}

pub(crate) fn validate_route(command: &WireCommand, pose: &Pose2D) -> Result<SimulationRoute, Status> {
    if command.kind != "MOVE" {
        return Err(Status::invalid_argument("software executor supports MOVE routes only"));
    }
    if command.payload_json.len() > 65536 {
        return Err(Status::invalid_argument("route payload exceeds 64 KiB"));
    }
    let route: SimulationRoute = serde_json::from_slice(&command.payload_json)
        .map_err(|_| Status::invalid_argument("invalid typed simulation route"))?;
    if route.waypoints.is_empty() || route.waypoints.len() > 4096
        || route.step_ms == 0 || route.step_ms > 1000
        || route.step_ms.saturating_mul(route.waypoints.len() as u64) > 30000
    {
        return Err(Status::invalid_argument("simulation route exceeds bounded execution limits"));
    }
    if route.waypoints.iter().flatten().any(|v| !v.is_finite() || v.abs() > 10000.0) {
        return Err(Status::invalid_argument("non-finite or out-of-range route coordinate"));
    }
    if (route.waypoints[0][0] - pose.x).abs() > 1e-8
        || (route.waypoints[0][1] - pose.y).abs() > 1e-8
    {
        return Err(Status::failed_precondition("route start differs from observed runtime pose"));
    }
    if route.waypoints.windows(2).any(|p| {
        let manhattan = (p[1][0] - p[0][0]).abs() + (p[1][1] - p[0][1]).abs();
        manhattan > 1.00000001
    }) {
        return Err(Status::invalid_argument("route contains a non-adjacent grid step"));
    }
    if route.fail_after_steps.is_some_and(|n| n >= route.waypoints.len()) {
        return Err(Status::invalid_argument("fault-injection step is outside the route"));
    }
    let deadline = command.deadline.as_ref()
        .ok_or_else(|| Status::invalid_argument("simulation command requires a deadline"))?;
    if deadline.seconds < 0 || !(0..1_000_000_000).contains(&deadline.nanos) {
        return Err(Status::invalid_argument("invalid command deadline"));
    }
    if expired(command) {
        return Err(Status::deadline_exceeded("command deadline already expired"));
    }
    Ok(route)
}

pub(crate) fn expired(command: &WireCommand) -> bool {
    let Some(deadline) = command.deadline.as_ref() else { return false; };
    let now = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default();
    now.as_secs() > deadline.seconds.max(0) as u64
        || (now.as_secs() == deadline.seconds.max(0) as u64
            && now.subsec_nanos() >= deadline.nanos.max(0) as u32)
}

pub(crate) async fn execute_route(
    state: Arc<Mutex<RobotRuntimeState>>,
    book: Arc<Mutex<ExecutionBook>>,
    command: WireCommand,
    route: SimulationRoute,
) {
    let mut terminal = CommandTerminalState::Succeeded;
    let mut explanation = "software route completed";
    for (index, point) in route.waypoints.iter().enumerate() {
        tokio::time::sleep(Duration::from_millis(route.step_ms)).await;
        if state.lock().await.terminal_result(&command.command_id).is_some() {
            return; // Explicit cancellation/result is terminal; never overwrite it.
        }
        if expired(&command) {
            terminal = CommandTerminalState::TimedOut;
            explanation = "command deadline elapsed before the route completed";
            break;
        }
        if route.fail_after_steps == Some(index) {
            terminal = CommandTerminalState::Failed;
            explanation = "explicit simulated route fault";
            break;
        }
        let mut execution = book.lock().await;
        // Cancellation uses the same book -> state lock order.
        if state.lock().await.terminal_result(&command.command_id).is_some() {
            return;
        }
        execution.pose = Pose2D { x: point[0], y: point[1], yaw: 0.0 };
        execution.steps.insert(command.command_id.clone(), (index + 1) as u64);
    }
    let execution = book.lock().await;
    let steps = execution.steps.get(&command.command_id).copied().unwrap_or(0);
    let detail = serde_json::json!({
        "scope": "SOFTWARE_SIMULATION", "reason": explanation,
        "steps_executed": steps, "route_points": route.waypoints.len(),
        "final_pose": [execution.pose.x, execution.pose.y],
        "runtime_session_id": execution.session_id,
    }).to_string();
    let mut core = state.lock().await;
    if core.terminal_result(&command.command_id).is_none() {
        // Unknown/rejected commands cannot enter this worker. A terminal
        // conflict is still handled explicitly instead of panicking.
        let _ = core.finish_command(CommandResult {
            command_id: command.command_id, state: terminal, detail,
        });
    }
}
