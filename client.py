#!/usr/bin/env python

"""
The BitTorrentClient sets up necessary objects before creating a Reactor and
calling run on it to start the event loop.  From there all other functions of
the BitTorrent client are event driven and flow from calls from the Reactor.

Initially, the client chooses a peer_id and creates an Acceptor for incoming
connections.  Before starting the reactor, it schedules a call to
start_download which eventually creates a TorrentMgr for each torrent specified
on the command line.

Since uploading is not yet fully supported, the place of the Acceptor in the
system hasn't fully been thought out.  When the Acceptor presents an incoming
connection, a PeerProxy must be created with the connection and it should
handshake with the peer.  After the handshake, it can be determined which
torrent the peer wishes to upload and the PeerProxy can be added to the
appropriate torrent.  It's not clear whether this functionality belongs in the
BitTorrentClient or perhaps in an incoming connection manager.

Right now, nothing handles cleanup on program exit.  Files should be flushed
and closed and sockets should be closed ideally.
"""

import logging
import logging.config
import sys
import time

from acceptor import Acceptor
from reactor import Reactor
from torrentmgr import TorrentMgr
from torrentmgr import TorrentMgrError

_PORT_FIRST = 6881
_PORT_LAST = 6889

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('bt')


class BitTorrentClient(object):
    def __init__(self):
        self._peer_id = "-HS0001-"+str(int(time.time())).zfill(12)
        self._torrents = {}
        self._downloads = set()

        for self._port in range(_PORT_FIRST, _PORT_LAST+1):
            try:
                self._acceptor = Acceptor(("localhost", self._port), self)
                break
            except Exception as err:
                logger.debug(err)
                continue
        else:
            logger.critical(("Could not find free port in range {}-{} to "
                             "accept connections")
                            .format(_PORT_FIRST, _PORT_LAST))
            sys.exit(1)

        logger.info("Listening on port {}".format(self._port))

        Reactor().schedule_timer(.01, self.start_downloads)
        Reactor().run()

    def start_downloads(self):
        for filename in sys.argv[1:]:
            self.add_torrent(filename)

        if len(self._downloads) == 0:
            sys.exit(0)

    def add_torrent(self, filename):
        if filename not in self._downloads:
            try:
                torrent = TorrentMgr(self, filename, self._port, self._peer_id)
            except TorrentMgrError:
                return

            self._torrents[torrent.info_hash] = torrent
            self._downloads.add(filename)

    def download_complete(self, filename):
        if filename in self._downloads:
            self._downloads.remove(filename)
            if len(self._downloads) == 0:
                sys.exit(0)

    # Acceptor callback

    def accepted_connection(self, addr, connection):
        pass

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("usage: {0} file1 [file2 ...]".format(sys.argv[0]))
        print("    file1, file2, etc.: torrent files")
        sys.exit(1)

    logger.info("Starting BitTorrent Client")
    BitTorrentClient()
