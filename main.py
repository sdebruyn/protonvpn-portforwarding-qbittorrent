import logging
import os
import sys
from time import sleep
from time import time
import qbittorrentapi
from natpmp.NATPMP import map_port, NATPMP_PROTOCOL_TCP, NATPMP_PROTOCOL_UDP

DEBUG_LOGGING = os.getenv("DEBUG_LOGGING", "false").lower() == "true"
default_logging_level = logging.DEBUG if DEBUG_LOGGING else logging.INFO

logger = logging.getLogger(__name__)


qbt_client = qbittorrentapi.Client()


def configure_logger(log_level: int|None = None) -> None:
    logging.basicConfig(
        level=log_level or default_logging_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def send_port_to_qbittorrent(port: int) -> None:
    logger.debug(f"Setting qBittorrent listen port to {port}")
    data = {"listen_port": port}
    qbt_client.app_set_preferences(prefs=data)
    logger.debug(f"Successfully updated qBittorrent port to {port}")


def request_single_port(protocol: int, gateway: str) -> int:
    protocol_name = "TCP" if protocol == NATPMP_PROTOCOL_TCP else "UDP"
    logger.debug(f"Requesting {protocol_name} port mapping from gateway {gateway}")
    response = map_port(protocol, 1, 0, 60, gateway_ip=gateway)
    if response.result != 0:
        logger.error(f"Failed to map {protocol_name} port: {response.result}")
        raise Exception(f"Failed to map port: {response.result}")
    logger.debug(
        f"Successfully mapped {protocol_name} with public port {response.public_port} and private port {response.private_port}"
    )
    return response.public_port


def request_proton_ports(proton_gateway: str) -> int:
    requested_tcp_port = request_single_port(NATPMP_PROTOCOL_TCP, proton_gateway)
    requested_udp_port = request_single_port(NATPMP_PROTOCOL_UDP, proton_gateway)

    if requested_tcp_port != requested_udp_port:
        raise Exception("TCP and UDP ports do not match")
    return requested_tcp_port


def store_current_timestamp_in_file() -> None:
    timestamp_file = "/app/last_updated"
    with open(timestamp_file, "w") as f:
        f.write(str(int(time())))
    logger.debug(f"Stored current timestamp in {timestamp_file}")


def main():
    logger.info("Starting ProtonVPN port forwarding service")
    interval = int(os.getenv("REQUEST_INTERVAL", 45))
    proton_gateway = os.getenv("PROTON_GATEWAY", "10.2.0.1")
    logger.info(f"Configuration: interval={interval}s, gateway={proton_gateway}")

    while True:
        try:
            logger.debug("Requesting new port mappings from ProtonVPN")
            requested_port = request_proton_ports(proton_gateway)
            logger.debug(
                f"Port {requested_port} successfully mapped, updating qBittorrent"
            )
            send_port_to_qbittorrent(requested_port)
            store_current_timestamp_in_file()
            logger.debug(f"Sleeping for {interval} seconds before next request")
            configure_logger()
        except Exception as e:
            configure_logger(logging.DEBUG)
            logger.error(f"Error in main loop: {e}")
            logger.info(f"Retrying in {interval} seconds")
        finally:
            sleep(interval)


if __name__ == "__main__":
    main()
