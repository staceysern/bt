"""
The TrackerProxy contacts the tracker specified in the supplied Metainfo object
and provides information about peers upon request.  During initialization, the
TrackerProxy raises a TrackerError if the tracker can't be contacted or
returns an invalid response.

This blocking TrackerProxy should be made non-blocking.

Right now, this client doesn't support multiple trackers specified by
announce-list in the Metainfo object.


The TrackerProxy should periodically report progress back to the tracker and
notify it when it has downloaded the entire torrent.  If the peer list is
exhausted, it should also get more peers from the tracker.
"""

import bencode
import logging
import requests
import sys

logger = logging.getLogger('bt.trackerproxy')


class TrackerError(Exception):
    pass


class TrackerProxy(object):
    def __init__(self, metainfo, port, peer_id):
        self._metainfo = metainfo
        self._port = port
        self._peer_id = peer_id

        params = {'info_hash': self._metainfo.info_hash,
                  'peer_id': self._peer_id,
                  'port': self._port,
                  'uploaded': 0,
                  'downloaded': 0,
                  'left': sum([pair[1] for pair in self._metainfo.files]),
                  'compact': 1,
                  'event': 'started'}

        try:
            response = requests.get(self._metainfo.announce, params=params)
        except requests.ConnectionError:
            raise TrackerError("Can't connect to the tracker at {}"
                               .format(self._metainfo.announce))

        response = bencode.bdecode(response.content)

        if 'failure reason' in response:
            raise TrackerError("Failure reason: {}"
                               .format(response['failure reason']))

        if 'warning message' in response:
            logger.warning("Warning: {}".format(response['warning message']))
            print >> sys.stderr, ("Warning: {}"
                                  .format(response['warning message']))

        try:
            self._min_interval = response.get('min interval', 0)
            if 'tracker id' in response:
                self._tracker_id = response['tracker id']

            self._interval = response['interval']
            self._complete = response['complete']
            self._incomplete = response['incomplete']

            if isinstance(response['peers'], list):
                self._peers = response['peers']
            else:
                self._peers = []
                peers = response['peers']
                for offset in xrange(0, len(peers), 6):
                    self._peers.append({'ip': "{}.{}.{}.{}"
                                        .format(str(ord(peers[offset])),
                                                str(ord(peers[offset+1])),
                                                str(ord(peers[offset+2])),
                                                str(ord(peers[offset+3]))),
                                        'port': (ord(peers[offset+4])*256 +
                                                 ord(peers[offset+5]))})
        except Exception:
            raise TrackerError("Invalid tracker response")

    def get_peers(self, n):
        if (len(self._peers) <= n):
            n = len(self._peers)

        peers = self._peers[:n]
        self._peers = self._peers[n:]
        return peers
