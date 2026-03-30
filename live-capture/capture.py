#live capture 
# capture.py
from scapy.all import sniff, IP, TCP, UDP, ICMP
import time
import threading

packet_buffer = []
buffer_lock = threading.Lock()

def process_packet(packet):
    if IP not in packet:
        return

    record = {
        "timestamp": time.time(),
        "src_ip":    packet[IP].src,
        "dst_ip":    packet[IP].dst,
        "length":    len(packet),
        "protocol":  packet[IP].proto,
        "src_port":  None,
        "dst_port":  None,
        "tcp_flags": None,
    }

    if TCP in packet:
        record["src_port"]  = packet[TCP].sport
        record["dst_port"]  = packet[TCP].dport
        record["tcp_flags"] = packet[TCP].flags
    elif UDP in packet:
        record["src_port"] = packet[UDP].sport
        record["dst_port"] = packet[UDP].dport

    with buffer_lock:
        packet_buffer.append(record)

def start_capture(interface="eth0", packet_count=0):
    print(f"[capture] Starting on interface: {interface}")
    sniff(
        iface=interface,
        prn=process_packet,
        store=False,
        count=packet_count
    )

def get_and_clear_buffer():
    with buffer_lock:
        data = packet_buffer.copy()
        packet_buffer.clear()
    return data