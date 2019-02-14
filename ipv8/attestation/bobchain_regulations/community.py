"""
The TrustChain Community is the first step in an incremental approach in building a new reputation system.
This reputation system builds a tamper proof interaction history contained in a chain data-structure.
Every node has a chain and these chains intertwine by blocks shared by chains.
"""
from __future__ import absolute_import

from datetime import timedelta
from functools import wraps
from threading import RLock

from pyipv8.events import RegulationAddedEvent, NewRegulationCommunityCreatedEvent
from pyipv8.ipv8.attestation.bobchain.settings import BobChainSettings
from pyipv8.ipv8.attestation.trustchain.block import ANY_COUNTERPARTY_PK
from pyipv8.ipv8.attestation.trustchain.community import TrustChainCommunity
from .block import BOBChainRegulationsChainBlock
from .database import BOBChainRegulationsDB

receive_block_lock = RLock()

BLOCK_TYPE = "regulation"


def synchronized(f):
    """
    Due to database inconsistencies, we can't allow multiple threads to handle a received_half_block at the same time.
    """

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        with receive_block_lock:
            return f(self, *args, **kwargs)

    return wrapper


class BOBChainRegulationsCommunity(TrustChainCommunity):
    DB_CLASS = BOBChainRegulationsDB
    DB_NAME = 'bobchainregulations'

    def __init__(self, *args, **kwargs):
        super(BOBChainRegulationsCommunity, self).__init__(*args)
        # self.network.verified_peers.append(args[0])
        self.settings = kwargs.pop('settings', BobChainSettings())
        NewRegulationCommunityCreatedEvent.event(self)

    def add_regulation_category(self, name, nightcap):
        self.sign_block(
            peer=None,
            public_key=ANY_COUNTERPARTY_PK,
            block_type=BLOCK_TYPE,
            transaction=
            {
                b"name": name,
                b"nightcap": nightcap
            }
        )
        RegulationAddedEvent.event()
        print "Regulation added"

    def get_regulations(self):
        result = []
        genesis_block = True
        for block in self.persistence.get_blocks_with_type(BLOCK_TYPE):
            if genesis_block:
                genesis_block = False
                continue
            result.append(block.transaction)
        return result

    def get_nightcap(self, name):
        """
        Returns -1 when there's no nightcap set for the regulation category requested, the nightcap limit otherwise
        """
        nightcap = 999999
        genesis_block = True
        for block in self.persistence.get_blocks_with_type(BLOCK_TYPE):
            if genesis_block:
                genesis_block = False
                continue
            if block.transaction["name"] == name:
                nightcap = block.transaction["nightcap"]
        return timedelta(int(nightcap))

    def started(self):
        if len(self.persistence.get_blocks_with_type(BLOCK_TYPE)) == 0:
            self.create_source_block(block_type=BLOCK_TYPE, transaction={})

    def get_block_class(self, block_type=None):
        """
        Get the block class for a specific block type.
        """
        return BOBChainRegulationsChainBlock
