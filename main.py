import asyncio
import logging
import os
import sys
from time import sleep
import qbittorrentapi
from natpmp.NATPMP import map_port, NATPMP_PROTOCOL_TCP, NATPMP_PROTOCOL_UDP


# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


qbt_client = qbittorrentapi.Client()


async def send_port_to_qbittorrent(port: int) -> None:
    logger.info(f"Setting qBittorrent listen port to {port}")
    data = {"listen_port": port}
    await asyncio.to_thread(qbt_client.app_set_preferences, prefs=data)
    logger.info(f"Successfully updated qBittorrent port to {port}")


def request_single_port(protocol: int, gateway: str) -> int:
    protocol_name = "TCP" if protocol == NATPMP_PROTOCOL_TCP else "UDP"
    logger.info(f"Requesting {protocol_name} port mapping from gateway {gateway}")
    response = map_port(protocol, 1, 0, 60, gateway_ip=gateway)
    if response.result != 0:
        logger.error(f"Failed to map {protocol_name} port: {response.result}")
        raise Exception(f"Failed to map port: {response.result}")
    logger.info(f"Successfully mapped {protocol_name} port {response.private_port}")
    return response.private_port


def request_proton_ports(proton_gateway: str) -> int:
    requested_tcp_port = request_single_port(NATPMP_PROTOCOL_TCP, proton_gateway)
    requested_udp_port = request_single_port(NATPMP_PROTOCOL_UDP, proton_gateway)

    if requested_tcp_port != requested_udp_port:
        raise Exception("TCP and UDP ports do not match")
    return requested_tcp_port


def main():
    logger.info("Starting ProtonVPN port forwarding service")
    background_tasks = set()
    interval = int(os.getenv("REQUEST_INTERVAL", 45))
    proton_gateway = os.getenv("PROTON_GATEWAY", "10.2.0.1")
    logger.info(f"Configuration: interval={interval}s, gateway={proton_gateway}")

    while True:
        try:
            logger.info("Requesting new port mappings from ProtonVPN")
            requested_port = request_proton_ports(proton_gateway)
            logger.info(
                f"Port {requested_port} successfully mapped, updating qBittorrent"
            )
            task = asyncio.create_task(send_port_to_qbittorrent(requested_port))
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)
            logger.info(f"Sleeping for {interval} seconds before next request")
            sleep(interval)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            logger.info(f"Retrying in {interval} seconds")
            sleep(interval)


if __name__ == "__main__":
    main()
