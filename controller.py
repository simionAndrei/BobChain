import glob
import hashlib
import json
import os
from collections import defaultdict
from os.path import join

from twisted.internet import reactor

from pyipv8.events import NewCommunityCreatedEvent, NewCommunityRegisteredEvent, NewRegulationCommunityCreatedEvent
from pyipv8.ipv8.attestation.bobchain.community import BOBChainCommunity
from pyipv8.ipv8.attestation.bobchain.database import BobChainDB
from pyipv8.ipv8.keyvault.crypto import ECCrypto
from pyipv8.ipv8.peer import Peer
from pyipv8.ipv8.peerdiscovery.discovery import EdgeWalk, RandomWalk


def construct_communities():
    return defaultdict(construct_communities)


communities = construct_communities()
regulations_community = []

_WALKERS = {
    'EdgeWalk': EdgeWalk,
    'RandomWalk': RandomWalk
}


class Controller:
    """
    The controller is the "middle-ware" between the GUI and the trustchain code. This controller class contains methods
    that are convenient to use for the Booked-on-Blockchain use-case and acts as an abstraction layer
    """
    controller = None

    def __init__(self, ipv8):
        self.ipv8 = ipv8
        Controller.controller = self
        NewCommunityCreatedEvent.event.append(self.register_existing_community)
        NewRegulationCommunityCreatedEvent.event.append(self.register_regulations_community)

    def get_communities(self):
        """
        Returns a dictionary of communities, mapped by [country][state][city][street][number]
        """
        return communities

    def get_regulations(self):
        return regulations_community[0].get_regulations()

    def get_bookings(self, property_details):
        """
        Returns a list of dictionaries ("start_day", "end_day", "
        """
        country = property_details["country"]
        state = property_details["state"]
        city = property_details["city"]
        street = property_details["street"]
        number = property_details["number"]
        return communities[country][state][city][street][number].get_bookings()

    def add_regulation_category(self, name, nightcap):
        regulations_community[0].add_regulation_category(name, nightcap)

    def register_existing_community(self, community):
        communities[community.country][community.state][community.city][community.street][community.number] = community
        NewCommunityRegisteredEvent.event()

    def register_regulations_community(self, community):
        regulations_community.append(community)

    def create_community(self, regulation_category, country, state, city, street, number):
        property_details = {"regulation_category": regulation_category,
                            "country": country,
                            "state": state,
                            "city": city,
                            "street": street,
                            "number": number}
        community_key = ECCrypto().generate_key(u"medium")
        community_peer = Peer(community_key)
        community = BOBChainCommunity(community_peer, self.ipv8.endpoint, self.ipv8.network, **property_details)
        self.ipv8.overlays.append(community)
        for walker in [{
            'strategy': "EdgeWalk",
            'peers': 20,
            'init': {
                'edge_length': 4,
                'neighborhood_size': 6,
                'edge_timeout': 3.0
            }
        }]:
            strategy_class = _WALKERS.get(walker['strategy'],
                                          community.get_available_strategies().get(walker['strategy']))
            args = walker['init']
            target_peers = walker['peers']
            self.ipv8.strategies.append((strategy_class(community, **args), target_peers))
        for config in [('started',)]:
            reactor.callWhenRunning(getattr(community, config[0]), *config[1:])
        communities[country][state][city][street][number] = community

        community_key_hash = hashlib.sha224(json.dumps(property_details)).hexdigest()
        with open(join("keys", str(community_key_hash) + ".pem"), 'w') as f:
            f.write(community_key.key_to_bin())

        with open('property_to_key_mappings.json', 'w') as file:
            l = []
            for country, states in communities.items():
                for state, cities in states.items():
                    for city, streets in cities.items():
                        for street, numbers in streets.items():
                            for number in numbers:
                                l.append([{
                                    "regulation_category": numbers[number].regulation_category,
                                    "country": country,
                                    "state": state,
                                    "city": city,
                                    "street": street,
                                    "number": number,
                                }, community_key_hash])
            json.dump(l, file)

    def book_apartment(self, property_details, start_day, end_day):
        country = property_details["country"]
        state = property_details["state"]
        city = property_details["city"]
        street = property_details["street"]
        number = property_details["number"]
        regulation_category = property_details["regulation_category"]
        nightcap = regulations_community[0].get_nightcap(regulation_category)
        return communities[country][state][city][street][number].book_apartment(start_day, end_day, nightcap)

    def remove_all_created_blocks(self):
        db = BobChainDB("", "bobchain")
        blocks = db.get_all_blocks()
        for block in blocks:
            db.remove_block(block)

        db2 = BobChainDB("", "bobchainregulations")
        blocks = db2.get_all_blocks()
        for block in blocks:
            db2.remove_block(block)

        for f in glob.glob(join("keys", "*")):
            os.remove(f)

        with open('property_to_key_mappings.json', 'w') as file:
            json.dump([], file)
