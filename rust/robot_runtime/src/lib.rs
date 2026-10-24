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
            | (Idle, Homing) | (Idle, Ready) | (Idle, Offline) | (Idle, EStop)
            | (Homing, Ready) | (Homing, Faulted) | (Homing, EStop)
            | (Ready, Executing) | (Ready, Paused) | (Ready, Faulted) | (Ready, EStop) | (Ready, Offline)
            | (Executing, Ready) | (Executing, Paused) | (Executing, Faulted) | (Executing, EStop)
            | (Paused, Ready) | (Paused, Executing) | (Paused, Faulted) | (Paused, EStop)
            | (Faulted, Idle) | (Faulted, EStop) | (Faulted, Offline)
            | (EStop, Idle) | (EStop, Offline)
    )
}

pub fn transition(from: RobotMode, to: RobotMode) -> Result<RobotMode, TransitionError> {
    if can_transition(from, to) {
        Ok(to)
    } else {
        Err(TransitionError { from, to })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn valid_execution_path() {
        assert_eq!(transition(RobotMode::Ready, RobotMode::Executing), Ok(RobotMode::Executing));
        assert_eq!(transition(RobotMode::Executing, RobotMode::Ready), Ok(RobotMode::Ready));
    }

    #[test]
    fn estop_cannot_jump_to_executing() {
        assert!(transition(RobotMode::EStop, RobotMode::Executing).is_err());
    }
}
