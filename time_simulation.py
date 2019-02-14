import os
import csv
import os
import sys
import thread
from datetime import datetime

from twisted.internet import reactor

from ota_infra import *
from pyipv8.controller import Controller
from pyipv8.ipv8.REST.rest_manager import RESTManager
from pyipv8.ipv8.attestation.bobchain_regulations.community import BOBChainRegulationsCommunity
from pyipv8.ipv8.keyvault.crypto import ECCrypto
from pyipv8.ipv8.messaging.interfaces.udp.endpoint import UDPEndpoint
from pyipv8.ipv8.peer import Peer
from pyipv8.ipv8.peerdiscovery.network import Network
from pyipv8.ipv8_service import IPv8

import socket
import time


def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


config = {
    'address': '0.0.0.0',
    'port': 8090,
    'keys': [],
    'logger': {
        'level': "INFO"
    },
    'walker_interval': 0.5,
    'overlays': []
}


def simulate(controller, nightcap):
    
    controller.remove_all_created_blocks()

    successfulBookings = 0
    overBookings = 0
    nightcapBookings = 0

    endpoint = UDPEndpoint(port=8090, ip='0.0.0.0')
    endpoint.open()
    network = Network()
    regulations_community = BOBChainRegulationsCommunity(Peer(ECCrypto().generate_key(u"medium")), endpoint, network)
    regulations_community.started()
    controller.add_regulation_category("a", nightcap)

    with open(os.path.join("pyipv8", "simulation", "bookings_500_per_50.csv"), 'r') as file:
        reader = csv.reader(file, delimiter=',')
        firstline = True
        init_time = datetime.now()
        for booking in reader:
            if firstline:
            	firstline = False
                continue
            status = booking[0]
            ota = booking[1]
            end_date = booking[2]
            address = {
                    "regulation_category": "a",
                    "country": booking[3].split("_")[1],
                    "state": booking[3].split("_")[1],
                    "city": booking[3].split("_")[1],
                    "street": booking[3].split("_")[1],
                    "number": booking[3].split("_")[1]
            }
            start_date = booking[4]
            row = booking[5]

            try:
                controller.get_bookings(address)
            except AttributeError:
                controller.create_community("a", address["country"], address["state"], address["city"],
                                                address["street"], address["number"])
            finally:
                result = controller.book_apartment(address, start_date, end_date)
                if result == 0:
                    successfulBookings += 1
                elif result == 1:
                    overBookings += 1
                elif result == 2:
                    nightcapBookings += 1

    return successfulBookings, overBookings, nightcapBookings



# Start the IPv8 service
ipv8 = IPv8.__new__(IPv8)
controller = Controller(ipv8)
ipv8.__init__(config)
rest_manager = RESTManager(ipv8)

if len(sys.argv) > 1:
    rest_manager.start(int(sys.argv[1]))
else:
    rest_manager.start(14410)



import numpy as np
for _ in range(10):
	time.sleep(0.1)
	start_time = time.time()
	successfulBookings, overBookings, nightcapBookings = simulate(controller, 9999999)
	crt_row  = []
	crt_row.append(time.time() - start_time)
	crt_row.append(successfulBookings) 
	crt_row.append(overBookings)
	crt_row.append(nightcapBookings)
	
	with open("results.csv", 'a') as fp:
		np.savetxt(fp, crt_row, delimiter = ",")






