"""
The TrustChain Community is the first step in an incremental approach in building a new reputation system.
This reputation system builds a tamper proof interaction history contained in a chain data-structure.
Every node has a chain and these chains intertwine by blocks shared by chains.
"""
from __future__ import absolute_import

import hashlib
from binascii import unhexlify
from functools import wraps
from threading import RLock

from twisted.internet.defer import succeed

from pyipv8 import NewCommunityCreatedEvent, PropertyBookedEvent
from .block import BobChainBlock
from .database import BobChainDB
from .settings import BobChainSettings
from ..trustchain.block import ANY_COUNTERPARTY_PK, ValidationResult
from ...community import Community
from ...peer import Peer

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


class BOBChainCommunity(Community):
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

        # initialize the database:
        working_directory = kwargs.pop('working_directory', '')
        db_name = kwargs.pop('db_name', self.DB_NAME)
        self.settings = kwargs.pop('settings', BobChainSettings())

        super(BOBChainCommunity, self).__init__(*args)
        self.persistence = self.DB_CLASS(working_directory, db_name)
        self.country = kwargs["country"]
        self.state = kwargs["state"]
        self.city = kwargs["city"]
        self.street = kwargs["street"]
        self.number = kwargs["number"]
        NewCommunityCreatedEvent.event(self)
        self.block_type_property = hashlib.sha224(
            self.country + self.state + self.city + self.street + self.number).hexdigest()

    def book_apartment(self, start_day, end_day):
        start_day_split = start_day.split("-")
        end_day_split = end_day.split("-")
        start_day_tuple = (int(start_day_split[0]), int(start_day_split[1]), int(start_day_split[2]))
        end_day_tuple = (int(end_day_split[0]), int(end_day_split[1]), int(end_day_split[2]))
        blocks = self.persistence.get_latest_blocks(self.my_peer.public_key.key_to_bin(), limit=99999)
        for block in blocks:
            if block.is_genesis:
                continue
            block_start_day_split = block.transaction["start_day"].split("-")
            block_end_day_split = block.transaction["end_day"].split("-")
            block_start_day_tuple = (
            int(block_start_day_split[0]), int(block_start_day_split[1]), int(block_start_day_split[2]))
            block_end_day_tuple = (
            int(block_end_day_split[0]), int(block_end_day_split[1]), int(block_end_day_split[2]))
            if not (block_end_day_tuple <= start_day_tuple or block_start_day_tuple >= end_day_tuple):
                print "Overbooking!"
                return False

        source_block = self.persistence.get_latest(self.my_peer.public_key.key_to_bin())
        self.create_link(
            source=source_block,
            block_type=self.block_type_property,
            additional_info=
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
        print "Number of linked blocks:", len(self.persistence.get_all_linked(source_block))
        print "Booked property"
        return True

    def get_bookings(self):
        result = []
        for block in self.persistence.get_latest_blocks(self.my_peer.public_key.key_to_bin(), limit=99999):
            if block.is_genesis:
                continue
            result.append(block.transaction)
        return result

    def create_genesis_block(self):
        """
        Create a genesis block without any initial counterparty to sign.

        :param block_type: The type of the block to be constructed, as a string
        :param transaction: A string describing the interaction in this block
        :param public_key: A string of 74 characters that is a public key
        :return: A deferred that fires with a (block, None) tuple
        """
        return self.sign_block(peer=None,
                               public_key=ANY_COUNTERPARTY_PK,
                               block_type=self.block_type_property,
                               transaction={"country": self.country,
                                            "state": self.state,
                                            "city": self.city,
                                            "street": self.street,
                                            "number": self.number})

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

    def print_blocks(self):
        blocks = self.persistence.get_all_blocks()
        i = 0
        for block in blocks:
            print "block number: ", i, " is_genesis: ", block.is_genesis
            print "transaction", block.transaction
            print "has id: ", block.block_id
            print "linked_block_id: ", block.linked_block_id
            i += 1

    def started(self):
        if len(self.persistence.get_blocks_with_type(self.block_type_property)) == 0:
            self.create_genesis_block()
        # self.register_task("print_peers", LoopingCall(print_peers)).start(5.0, True)
        # self.register_task("print_blocks", LoopingCall(wrapper_create_and_remove_blocks)).start(5.0, True)

    @synchronized
    def sign_block(self, peer, public_key, block_type, transaction=None, linked=None,
                   additional_info=None):
        """
        Create, sign, persist and send a block signed message
        :param peer: The peer with whom you have interacted, as a IPv8 peer
        :param public_key: The public key of the other party you transact with
        :param block_type: The type of the block to be constructed, as a string
        :param transaction: A string describing the interaction in this block
        :param linked: The block that the requester is asking us to sign
        :param additional_info: Stores additional information, on the transaction
        """

        # TODO:
        # Should add assertion checks below that makes sense for the BOBChain
        # check the trustchain/community sign_block() to get an idea of what are good assertions
        assert transaction is None or isinstance(transaction, dict), "Transaction should be a dictionary"
        assert additional_info is None or isinstance(additional_info, dict), "Additional info should be a dictionary"

        # TODO:
        # Check below should be implemented, this check makes sure that the latest block in the chain
        # can be validated, otherwise the database needs to be sanitized
        # self.persistence_integrity_check()

        # TODO:
        # Add linkage logic
        # if linked and linked.link_public_key != ANY_COUNTERPARTY_PK:
        #     block_type = linked.type

        # TODO
        # Fix input for the get_block_class, this should not be a static string
        block = self.get_block_class(self.block_type_property).create(block_type,
                                                                      transaction,
                                                                      self.persistence,
                                                                      public_key=self.my_peer.public_key.key_to_bin(),
                                                                      link=linked,
                                                                      additional_info=additional_info,
                                                                      link_pk=public_key)

        block.sign(self.my_peer.key)

        # TODO
        # Write validation logic

        # Add block to database:
        if not self.persistence.contains(block):
            self.persistence.add_block(block)
            # self.notify_listeners(block)

        # This is a source block with no counterparty
        if not peer and public_key == ANY_COUNTERPARTY_PK:
            # TODO figure this out
            # if self.settings.broadcast_blocks:
            #     self.send_block(block)
            return succeed((block, None))

        # TODO
        # No Counter party is ever needed, see how we need to handle this
        # If there is a counterparty to sign, we send it
        # self.send_block(block, address=peer.address)

        # TODO
        # Find logic when we broadcast the block
        # Probably when we think it is validated
        # We broadcast the block in the network if we initiated a transaction
        # if self.settings.broadcast_blocks and not linked:
        #     self.send_block(block)

        # Self signed block, this seems to be the situation
        if peer == self.my_peer:
            # We created a self-signed block
            # TODO figure out how to send this
            # if self.settings.broadcast_blocks:
            #     self.send_block(block)

            return succeed((block, None)) if public_key == ANY_COUNTERPARTY_PK else succeed((block, linked))
        # elif not linked:
        #     # We keep track of this outstanding sign request.
        #     sign_deferred = Deferred()
        #     self.request_cache.add(HalfBlockSignCache(self, block, sign_deferred, peer.address))
        #     return sign_deferred
        # else:
        #     # We return a deferred that fires immediately with both half blocks.
        #     if self.settings.broadcast_blocks:
        #         self.send_block_pair(linked, block)
        #
        #     return succeed((linked, block))

    def create_link(self, source, block_type, additional_info, public_key=None):
        """
        Create a Link Block to a source block

        :param source: The source block which had no initial counterpary to sign
        :param block_type: The type of the block to be constructed, as a string
        :param additional_info: a dictionary with supplementary information concerning the transaction
        :param public_key: The public key of the counterparty (usually of the source's owner)
        :return: None
        """
        public_key = source.public_key if public_key is None else public_key

        return self.sign_block(self.my_peer, additional_info=additional_info, linked=source, public_key=public_key,
                               block_type=block_type)

    def validate_persist_block(self, block):
        """
        Validate a block and if it's valid, persist it. Return the validation result.
        :param block: The block to validate and persist.
        :return: [ValidationResult]
        """
        validation = block.validate(self.persistence)
        if validation[0] == ValidationResult.invalid:
            pass
        elif not self.persistence.contains(block):
            self.persistence.add_block(block)
            self.notify_listeners(block)

        return validation

    def get_block_class(self, block_type):
        """
        Get the block class for a specific block type.
        """
        assert block_type == self.block_type_property, "Wrong type of block is being created"

        return BobChainBlock

    def persistence_integrity_check(self):
        """
        Perform an integrity check of our own chain. Recover it if needed.
        """
        block = self.persistence.get_latest(self.my_peer.public_key.key_to_bin())
        if not block:
            return

        # TODO
        # validation = self.validate_persist_block(block)
        # if validation[0] != ValidationResult.partial_next and validation[0] != ValidationResult.valid:
        #     self.logger.error("Our chain did not validate. Result %s", repr(validation))
        #     self.sanitize_database()
