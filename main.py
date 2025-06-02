import asyncio
import os
from time import sleep
import qbittorrentapi
from natpmp.NATPMP import map_port, NATPMP_PROTOCOL_TCP, NATPMP_PROTOCOL_UDP


qbt_client = qbittorrentapi.Client()


async def send_port_to_qbittorrent(port: int) -> None:
    data = {"listen_port": port}
    await asyncio.to_thread(qbt_client.app_set_preferences, prefs=data)


def request_single_port(protocol: int, gateway: str) -> int:
    response = map_port(protocol, 1, 0, 60, gateway_ip=gateway)
    if response.result != 0:
        raise Exception(f"Failed to map port: {response.result}")
    return response.private_port


def request_proton_ports(proton_gateway: str) -> int:
    requested_tcp_port = request_single_port(NATPMP_PROTOCOL_TCP, proton_gateway)
    requested_udp_port = request_single_port(NATPMP_PROTOCOL_UDP, proton_gateway)

    if requested_tcp_port != requested_udp_port:
        raise Exception("TCP and UDP ports do not match")
    return requested_tcp_port


def main():
    background_tasks = set()
    interval = int(os.getenv("REQUEST_INTERVAL", 45))
    proton_gateway = os.getenv("PROTON_GATEWAY", "10.2.0.1")

    while True:
        requested_port = request_proton_ports(proton_gateway)
        task = asyncio.create_task(send_port_to_qbittorrent(requested_port))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
        sleep(interval)


if __name__ == "__main__":
    main()
