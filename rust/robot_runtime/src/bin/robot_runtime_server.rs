use robot_runtime::proto::robot_runtime_server::RobotRuntimeServer;
use robot_runtime::{RobotMode, RuntimeService};
use tonic::transport::Server;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args().skip(1);
    let address = args
        .next()
        .unwrap_or_else(|| "127.0.0.1:50051".to_owned())
        .parse()?;
    let robot_id = args.next().unwrap_or_else(|| "robot-1".to_owned());
    let service = RuntimeService::new(robot_id, RobotMode::Ready);
    println!("READY {address}");
    Server::builder()
        .add_service(RobotRuntimeServer::new(service))
        .serve(address)
        .await?;
    Ok(())
}
