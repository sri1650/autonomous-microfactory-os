use robot_runtime::proto::robot_runtime_client::RobotRuntimeClient;
use robot_runtime::proto::robot_runtime_server::RobotRuntimeServer;
use robot_runtime::proto::{CommandDisposition, RobotCommand, RobotMode as ProtoRobotMode};
use robot_runtime::{RobotMode, RuntimeService};
use tokio::net::TcpListener;
use tokio_stream::wrappers::TcpListenerStream;
use tonic::transport::Server;

#[tokio::test]
async fn grpc_round_trip_is_idempotent() {
    let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
    let address = listener.local_addr().unwrap();
    let service = RuntimeService::new("robot-1", RobotMode::Ready);
    let server = tokio::spawn(async move {
        Server::builder()
            .add_service(RobotRuntimeServer::new(service))
            .serve_with_incoming(TcpListenerStream::new(listener))
            .await
            .unwrap();
    });

    let mut client = RobotRuntimeClient::connect(format!("http://{address}"))
        .await
        .unwrap();
    let command = RobotCommand {
        command_id: "cmd-network-1".to_owned(),
        correlation_id: "trace-network-1".to_owned(),
        robot_id: "robot-1".to_owned(),
        kind: "MOVE".to_owned(),
        deadline: None,
        payload_json: Vec::new(),
    };
    let first = client
        .submit_command(command.clone())
        .await
        .unwrap()
        .into_inner();
    let duplicate = client.submit_command(command).await.unwrap().into_inner();
    assert_eq!(first, duplicate);
    assert_eq!(first.disposition, CommandDisposition::Accepted as i32);

    let status = client
        .get_status(robot_runtime::proto::RobotStatusRequest {
            robot_id: "robot-1".to_owned(),
        })
        .await
        .unwrap()
        .into_inner();
    assert_eq!(status.mode, ProtoRobotMode::Executing as i32);
    assert_eq!(status.active_command_id, "cmd-network-1");

    server.abort();
}
