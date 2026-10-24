use std::collections::BTreeMap;

#[allow(clippy::result_large_err)]
pub mod proto {
    tonic::include_proto!("microfactory.v1");
}

mod service;
pub use service::RuntimeService;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RobotMode {
    Offline,
    Idle,
    Homing,
    Ready,
    Executing,
    Paused,
    Faulted,
    EStop,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TransitionError {
    pub from: RobotMode,
    pub to: RobotMode,
}

pub fn can_transition(from: RobotMode, to: RobotMode) -> bool {
    use RobotMode::*;
    matches!(
        (from, to),
        (Offline, Idle)
            | (Idle, Homing)
            | (Idle, Ready)
            | (Idle, Offline)
            | (Idle, EStop)
            | (Homing, Ready)
            | (Homing, Faulted)
            | (Homing, EStop)
            | (Ready, Executing)
            | (Ready, Paused)
            | (Ready, Faulted)
            | (Ready, EStop)
            | (Ready, Offline)
            | (Executing, Ready)
            | (Executing, Paused)
            | (Executing, Faulted)
            | (Executing, EStop)
            | (Paused, Ready)
            | (Paused, Executing)
            | (Paused, Faulted)
            | (Paused, EStop)
            | (Faulted, Idle)
            | (Faulted, EStop)
            | (Faulted, Offline)
            | (EStop, Idle)
            | (EStop, Offline)
    )
}

pub fn transition(from: RobotMode, to: RobotMode) -> Result<RobotMode, TransitionError> {
    if can_transition(from, to) {
        Ok(to)
    } else {
        Err(TransitionError { from, to })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RobotCommand {
    pub command_id: String,
    pub correlation_id: String,
    pub kind: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CommandDisposition {
    Accepted,
    Rejected,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CommandAck {
    pub command_id: String,
    pub disposition: CommandDisposition,
    pub reason: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CommandTerminalState {
    Succeeded,
    Failed,
    TimedOut,
    Cancelled,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CommandResult {
    pub command_id: String,
    pub state: CommandTerminalState,
    pub detail: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct CommandRecord {
    command: RobotCommand,
    ack: CommandAck,
    result: Option<CommandResult>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CommandLifecycleError {
    UnknownCommand(String),
    CommandWasRejected(String),
    ConflictingTerminalResult {
        existing: CommandResult,
        requested: CommandResult,
    },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum WatchdogState {
    AwaitingHeartbeat,
    Healthy,
    Expired,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum WatchdogError {
    ZeroTimeout,
    NonMonotonicTime { previous_ms: u64, observed_ms: u64 },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HeartbeatWatchdog {
    timeout_ms: u64,
    last_heartbeat_ms: Option<u64>,
}

impl HeartbeatWatchdog {
    pub fn new(timeout_ms: u64) -> Result<Self, WatchdogError> {
        if timeout_ms == 0 {
            return Err(WatchdogError::ZeroTimeout);
        }
        Ok(Self {
            timeout_ms,
            last_heartbeat_ms: None,
        })
    }

    pub fn last_heartbeat_ms(&self) -> Option<u64> {
        self.last_heartbeat_ms
    }

    pub fn record_heartbeat(&mut self, now_ms: u64) -> Result<(), WatchdogError> {
        if let Some(previous_ms) = self.last_heartbeat_ms {
            if now_ms < previous_ms {
                return Err(WatchdogError::NonMonotonicTime {
                    previous_ms,
                    observed_ms: now_ms,
                });
            }
        }
        self.last_heartbeat_ms = Some(now_ms);
        Ok(())
    }

    pub fn state_at(&self, now_ms: u64) -> Result<WatchdogState, WatchdogError> {
        let Some(previous_ms) = self.last_heartbeat_ms else {
            return Ok(WatchdogState::AwaitingHeartbeat);
        };
        if now_ms < previous_ms {
            return Err(WatchdogError::NonMonotonicTime {
                previous_ms,
                observed_ms: now_ms,
            });
        }
        if now_ms - previous_ms >= self.timeout_ms {
            Ok(WatchdogState::Expired)
        } else {
            Ok(WatchdogState::Healthy)
        }
    }
}

#[derive(Debug, Clone)]
pub struct RobotRuntimeState {
    mode: RobotMode,
    active_command_id: Option<String>,
    commands: BTreeMap<String, CommandRecord>,
}

impl RobotRuntimeState {
    pub fn new(mode: RobotMode) -> Self {
        Self {
            mode,
            active_command_id: None,
            commands: BTreeMap::new(),
        }
    }

    pub fn mode(&self) -> RobotMode {
        self.mode
    }

    pub fn active_command_id(&self) -> Option<&str> {
        self.active_command_id.as_deref()
    }

    pub fn submit_command(&mut self, command: RobotCommand) -> CommandAck {
        if let Some(record) = self.commands.get(&command.command_id) {
            return record.ack.clone();
        }

        let (disposition, reason) = if command.command_id.is_empty() {
            (CommandDisposition::Rejected, "command_id is required")
        } else if self.mode != RobotMode::Ready {
            (
                CommandDisposition::Rejected,
                "robot must be READY to accept a command",
            )
        } else {
            (CommandDisposition::Accepted, "")
        };

        let ack = CommandAck {
            command_id: command.command_id.clone(),
            disposition,
            reason: reason.to_owned(),
        };
        if disposition == CommandDisposition::Accepted {
            self.mode = RobotMode::Executing;
            self.active_command_id = Some(command.command_id.clone());
        }
        self.commands.insert(
            command.command_id.clone(),
            CommandRecord {
                command,
                ack: ack.clone(),
                result: None,
            },
        );
        ack
    }

    pub fn terminal_result(&self, command_id: &str) -> Option<&CommandResult> {
        self.commands
            .get(command_id)
            .and_then(|record| record.result.as_ref())
    }

    pub fn finish_command(
        &mut self,
        result: CommandResult,
    ) -> Result<CommandResult, CommandLifecycleError> {
        let record = self
            .commands
            .get_mut(&result.command_id)
            .ok_or_else(|| CommandLifecycleError::UnknownCommand(result.command_id.clone()))?;
        if record.ack.disposition == CommandDisposition::Rejected {
            return Err(CommandLifecycleError::CommandWasRejected(
                result.command_id.clone(),
            ));
        }
        if let Some(existing) = &record.result {
            return if existing == &result {
                Ok(existing.clone())
            } else {
                Err(CommandLifecycleError::ConflictingTerminalResult {
                    existing: existing.clone(),
                    requested: result,
                })
            };
        }

        record.result = Some(result.clone());
        if self.active_command_id.as_deref() == Some(result.command_id.as_str()) {
            self.active_command_id = None;
            self.mode = RobotMode::Ready;
        }
        Ok(result)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn valid_execution_path() {
        assert_eq!(
            transition(RobotMode::Ready, RobotMode::Executing),
            Ok(RobotMode::Executing)
        );
        assert_eq!(
            transition(RobotMode::Executing, RobotMode::Ready),
            Ok(RobotMode::Ready)
        );
    }

    #[test]
    fn estop_cannot_jump_to_executing() {
        assert!(transition(RobotMode::EStop, RobotMode::Executing).is_err());
    }

    fn command(command_id: &str) -> RobotCommand {
        RobotCommand {
            command_id: command_id.to_owned(),
            correlation_id: "trace-1".to_owned(),
            kind: "MOVE".to_owned(),
        }
    }

    #[test]
    fn accepted_command_is_idempotent_and_becomes_active() {
        let mut runtime = RobotRuntimeState::new(RobotMode::Ready);
        let first = runtime.submit_command(command("cmd-1"));
        let duplicate = runtime.submit_command(command("cmd-1"));

        assert_eq!(first.disposition, CommandDisposition::Accepted);
        assert_eq!(duplicate, first);
        assert_eq!(runtime.active_command_id(), Some("cmd-1"));
        assert_eq!(runtime.mode(), RobotMode::Executing);
    }

    #[test]
    fn busy_runtime_rejects_new_command_and_replays_rejection() {
        let mut runtime = RobotRuntimeState::new(RobotMode::Executing);
        let first = runtime.submit_command(command("cmd-2"));
        let duplicate = runtime.submit_command(command("cmd-2"));

        assert_eq!(first.disposition, CommandDisposition::Rejected);
        assert_eq!(duplicate, first);
        assert_eq!(runtime.active_command_id(), None);
    }

    #[test]
    fn terminal_result_is_idempotent_but_cannot_change() {
        let mut runtime = RobotRuntimeState::new(RobotMode::Ready);
        runtime.submit_command(command("cmd-3"));
        let result = CommandResult {
            command_id: "cmd-3".to_owned(),
            state: CommandTerminalState::Succeeded,
            detail: "complete".to_owned(),
        };

        assert_eq!(runtime.finish_command(result.clone()), Ok(result.clone()));
        assert_eq!(runtime.finish_command(result.clone()), Ok(result));
        assert_eq!(runtime.mode(), RobotMode::Ready);
        assert_eq!(runtime.active_command_id(), None);

        let conflicting = CommandResult {
            command_id: "cmd-3".to_owned(),
            state: CommandTerminalState::Failed,
            detail: "late failure".to_owned(),
        };
        assert!(matches!(
            runtime.finish_command(conflicting),
            Err(CommandLifecycleError::ConflictingTerminalResult { .. })
        ));
    }

    #[test]
    fn watchdog_expires_at_the_timeout_boundary() {
        let mut watchdog = HeartbeatWatchdog::new(1_000).unwrap();
        assert_eq!(watchdog.state_at(10), Ok(WatchdogState::AwaitingHeartbeat));
        watchdog.record_heartbeat(100).unwrap();
        assert_eq!(watchdog.state_at(1_099), Ok(WatchdogState::Healthy));
        assert_eq!(watchdog.state_at(1_100), Ok(WatchdogState::Expired));
    }

    #[test]
    fn heartbeat_refreshes_watchdog_and_rejects_time_reversal() {
        let mut watchdog = HeartbeatWatchdog::new(500).unwrap();
        watchdog.record_heartbeat(1_000).unwrap();
        watchdog.record_heartbeat(1_200).unwrap();
        assert_eq!(watchdog.state_at(1_600), Ok(WatchdogState::Healthy));
        assert_eq!(
            watchdog.record_heartbeat(1_199),
            Err(WatchdogError::NonMonotonicTime {
                previous_ms: 1_200,
                observed_ms: 1_199,
            })
        );
    }

    #[test]
    fn zero_timeout_is_invalid() {
        assert_eq!(HeartbeatWatchdog::new(0), Err(WatchdogError::ZeroTimeout));
    }
}
