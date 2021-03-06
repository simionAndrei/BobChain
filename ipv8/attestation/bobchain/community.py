"""
The TrustChain Community is the first step in an incremental approach in building a new reputation system.
This reputation system builds a tamper proof interaction history contained in a chain data-structure.
Every node has a chain and these chains intertwine by blocks shared by chains.
"""
from __future__ import absolute_import

import hashlib
from binascii import unhexlify
from datetime import date, timedelta
from functools import wraps
from threading import RLock

from pyipv8 import NewCommunityCreatedEvent, PropertyBookedEvent
from pyipv8.ipv8.attestation.bobchain.settings import BobChainSettings
from pyipv8.ipv8.attestation.trustchain.block import ANY_COUNTERPARTY_PK
from pyipv8.ipv8.attestation.trustchain.community import TrustChainCommunity
from .block import BobChainBlock
from .database import BobChainDB
from ...peer import Peer
from twisted.internet.task import LoopingCall
from pyipv8.ipv8.community import Community


from pyipv8.ipv8.attestation.bobchain.listener import BoBListener

receive_block_lock = RLock()


# PROPERTY_TO_DETAILS_KEY = {}  # Maps property hash to (property details, keypair)

# try:
#     with open('property_to_key_mappings.json', 'r') as file:
#         json_file = json.load(file)
#         for property in json_file:
#             with open("keys/" + property[1] + ".pem", 'r') as key:
#                 key_content = key.read()
#                 PROPERTY_TO_DETAILS_KEY[property[1]] = (property[0], ECCrypto().key_from_private_bin(key_content))
# except IOError:
#     with open('property_to_key_mappings.json', 'w') as file:
#         json.dump([], file)
# PUBLIC_KEY = [b'0' * 74,
#               b'4jpvnlpbnesusvlkxh7d34u8mfq1gxc0la4usd54oooeulraw7dwv72d4nfn7czhaulen9fjbn',
#               b'xtkbp3zv88ruj2k63rizkelbhzg58gzcp09od1pt867ksn8i5xrn2zafqjfzua8hhdzhgp7376',
#               b'vvt6ng10p1w50jg9rmyy10tqqmmemrw59uf0ifa22odjg9hfuxoxx8ngv2apd7w6rlzh3cjfbu',
#               b'3f0xw1jtns6heuk478h58k3dburaeig6s2bt5vo5oz3bz2dfvel85g0edt3qsmgn06npr0we5s',
#               b'ev46dkjzfrc7vjywv7i3h0qcxpquuj9v5xit9z0lshzz53t6exb3vblrtnthupulthstdi7svh']


def synchronized(f):
    """
    Due to database inconsistencies, we can't allow multiple threads to handle a received_half_block at the same time.
    """

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        with receive_block_lock:
            return f(self, *args, **kwargs)

    return wrapper


class BOBChainCommunity(TrustChainCommunity):
    bobChainCommunity = None

    # TODO figure this out
    # Took the trustchain community values...
    master_peer = Peer(unhexlify("3081a7301006072a8648ce3d020106052b8104002703819200040672297aa47c7bb2648ba0385275bc"
                                 "8ade5aedc3677a615f5f9ca83b9b28c75e543342875f7f353bbf74baff7e3dae895ee9c9a9f80df023"
                                 "dbfb72362426b50ce35549e6f0e0a319015a2fd425e2e34c92a3fb33b26929bcabb73e14f63684129b"
                                 "66f0373ca425015cc9fad75b267de0cfb46ed798796058b23e12fc4c42ce9868f1eb7d59cc2023c039"
                                 "14175ebb9703"))

    DB_CLASS = BobChainDB
    DB_NAME = 'bobchain'

    def __init__(self, *args, **kwargs):
        super(BOBChainCommunity, self).__init__(*args)
        print "BoBChain args[0] %s" % args[0]

        #print "I am:", self.my_peer, "\nI know:", [str(p) for p in self.get_peers()]

        #self.network.verified_peers.append(args[0])
        self.settings = kwargs.pop('settings', BobChainSettings())
        self.country = kwargs["country"]
        self.state = kwargs["state"]
        self.city = kwargs["city"]
        self.street = kwargs["street"]
        self.number = kwargs["number"]
        NewCommunityCreatedEvent.event(self)
        self.block_type_property = hashlib.sha224(
            self.country + self.state + self.city + self.street + self.number).hexdigest()
        #self.register_task("print_peers", LoopingCall(self.print_peers)).start(5.0, True)
        self.add_listener(BoBListener(), [self.get_block_class()])

    def print_peers(self):
        print "I am:", self.my_peer, "\nI know:", [str(p) for p in self.get_peers()]


    def book_apartment(self, start_day, end_day):
        start_day_split = start_day.split("-")
        end_day_split = end_day.split("-")
        start_day_tuple = (int(start_day_split[0]), int(start_day_split[1]), int(start_day_split[2]))
        end_day_tuple = (int(end_day_split[0]), int(end_day_split[1]), int(end_day_split[2]))
        blocks = self.persistence.get_blocks_with_type(self.block_type_property)
        nightcap = timedelta(9)
        total_days_booked = date(end_day_tuple[0], end_day_tuple[1], end_day_tuple[2]) - date(start_day_tuple[0], start_day_tuple[1], start_day_tuple[2])
        for block in blocks:
            if block.is_genesis:
                continue
            block_start_day_split = block.transaction["start_day"].split("-")
            block_end_day_split = block.transaction["end_day"].split("-")
            block_start_day_tuple = (
                int(block_start_day_split[0]), int(block_start_day_split[1]), int(block_start_day_split[2]))
            block_end_day_tuple = (
                int(block_end_day_split[0]), int(block_end_day_split[1]), int(block_end_day_split[2]))
            total_days_booked += date(block_end_day_tuple[0], block_end_day_tuple[1], block_end_day_tuple[2]) - date(block_start_day_tuple[0], block_start_day_tuple[1], block_start_day_tuple[2])
            if not (block_end_day_tuple <= start_day_tuple or block_start_day_tuple >= end_day_tuple):
                print "Overbooking!"
                return 1
        if total_days_booked > nightcap:
            print "Nightcap exceeded!"
            return 2

        self.sign_block(
            peer=None,
            public_key=ANY_COUNTERPARTY_PK,
            block_type=self.block_type_property,
            transaction=
            {
                b"start_day": start_day,  # yyyy-mm-dd
                b"end_day": end_day  # yyyy-mm-dd
            }
        )
        PropertyBookedEvent.event({"country": self.country,
                                   "state": self.state,
                                   "city": self.city,
                                   "street": self.street,
                                   "number": self.number},
                                  start_day,
                                  end_day)
        print "Booked property"
        return 0

    def get_bookings(self):
        result = []
        for block in self.persistence.get_blocks_with_type(self.block_type_property):
            if block.is_genesis:
                continue
            result.append(block.transaction)
        return result

    # This function will remove all the created blocks in the bobchain community
    def remove_all_created_blocks(self):
        print "Going to remove all blocks"

        blocks = self.persistence.get_all_blocks()
        print "Number of blocks found: ", len(blocks)

        for block in blocks:
            self.persistence.remove_block(block)
        blocks = self.persistence.get_all_blocks()

        if len(blocks) == 0:
            print "All blocks have succesfully been removed"
        else:
            print "Not all blocks have been removed, number of blocks remaining: ", len(blocks)

    def started(self):
        if len(self.persistence.get_blocks_with_type(self.block_type_property)) == 0:
            self.create_source_block(block_type=self.block_type_property,
                                     transaction={"country": self.country,
                                                  "state": self.state,
                                                  "city": self.city,
                                                  "street": self.street,
                                                  "number": self.number})
        # self.register_task("print_peers", LoopingCall(print_peers)).start(5.0, True)
        # self.register_task("print_blocks", LoopingCall(wrapper_create_and_remove_blocks)).start(5.0, True)

    def get_block_class(self, block_type = None):
        """
        Get the block class for a specific block type.
        """
        return BobChainBlock
