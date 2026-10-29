use robot_runtime::proto::robot_runtime_server::RobotRuntimeServer;
use robot_runtime::proto::Pose2D;
use robot_runtime::{RobotMode, RuntimeService};
use tonic::transport::Server;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args().skip(1);
    let address: std::net::SocketAddr = args.next().unwrap_or_else(|| "127.0.0.1:50051".to_owned()).parse()?;
    let robot_id = args.next().unwrap_or_else(|| "robot-1".to_owned());
    let service = match args.next().as_deref() {
        None => RuntimeService::new(robot_id, RobotMode::Ready),
        Some("--simulate") => {
            if !address.ip().is_loopback() {
                return Err("software demo runtime must bind loopback".into());
            }
            let x: f64 = args.next().unwrap_or_else(|| "0".to_owned()).parse()?;
            let y: f64 = args.next().unwrap_or_else(|| "0".to_owned()).parse()?;
            if !x.is_finite() || !y.is_finite() || x.abs() > 10000.0 || y.abs() > 10000.0 {
                return Err("invalid simulation starting pose".into());
            }
            RuntimeService::simulated(robot_id, Pose2D { x, y, yaw: 0.0 })
        }
        Some(_) => return Err("expected --simulate or no extra argument".into()),
    };
    println!("READY {address}");
    Server::builder().add_service(RobotRuntimeServer::new(service)).serve(address).await?;
    Ok(())
}
