## BitTorrent

A BitTorrent client written in Python.

This version of the client implements downloading but not uploading.  It can handle multiple torrents at a time but does not manage traffic load.  It uses a very simple strategy for determining which blocks to request and does not implement keep alives, pipelined requests or endgame strategy.

This BitTorrent client includes its own event loop.  Another version, which has been adapted to use Twisted, a Python networking library, can be found in the [bt-twisted](http://github.com/staceysern/bt-twisted) repo.

### Usage

```
python client.py file1 [file2 ...]
```
where file1, file2, etc. are names of torrent files

### Unit Tests

py.test is used for unit testing.  From the test directory run:

```
PYTHONPATH=..:${PYTHONPATH} py.test
```
