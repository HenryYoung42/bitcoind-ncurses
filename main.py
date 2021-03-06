#!/usr/bin/env python

###############################################################################
# bitcoind-ncurses by Amphibian
# thanks to jgarzik for bitcoinrpc
# wumpus and kylemanna for configuration file parsing
# all the users for their suggestions and testing
# and of course the bitcoin dev team for that bitcoin gizmo, pretty neat stuff
###############################################################################

from gevent import monkey
monkey.patch_all()
import gevent
import gevent.queue

import argparse, signal

import rpc2
import block_store
import block_viewer
import interface
import config

def interrupt_signal(signal, frame):
    s = {'stop': "Interrupt signal caught"}
    response_queue.put(s)

def mainfn(window):
    # initialise queues
    response_queue = gevent.queue.Queue()
    rpc_queue = gevent.queue.Queue()

    # parse commandline arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config",
                        help="path to config file [bitcoin.conf]",
                        default="bitcoin.conf")
    parser.add_argument("-m", "--mode",
                        help="initial mode",
                        default=None)
    args = parser.parse_args()

    # parse config file
    try:
        cfg = config.read_file(args.config)
    except IOError:
        cfg = {}
        s = {'stop': "configuration file [" + args.config + "] does not exist or could not be read"}
        response_queue.put(s)

    # initialise interrupt signal handler (^C)
    signal.signal(signal.SIGINT, interrupt_signal)

    bstore = block_store.BlockStore()
    bviewer = block_viewer.BlockViewer(bstore, window)

    bstore._on_block = bviewer.on_block

    # start RPC thread
    rpcc = rpc2.BitcoinRPCClient(
        response_queue=response_queue, # TODO: refactor this
        block_store=bstore,
        rpcuser=cfg["rpcuser"],
        rpcpassword=cfg["rpcpassword"],
        rpcip=(cfg["rpcip"] if "rpcip" in cfg else "localhost"),
        rpcport=(cfg["rpcport"] if "rpcport" in cfg else 18332 if "testnet" in cfg else 8332),
        protocol=(cfg["protocol"] if "protocol" in cfg else "http"),
    )
    connected = rpcc.connect()
    if not connected:
        print "RPCC failed to connect"
        sys.exit(1)

    rpc2_process = gevent.spawn(rpcc.run)

    poller = rpc2.Poller(rpcc)
    poller_process = gevent.spawn(poller.run)

    if args.mode is not None:
        initial_mode = args.mode
    elif "mode" in cfg:
        initial_mode = cfg["mode"]
    else:
        initial_mode = None

    # main loop
    try:
        interface.main(bviewer, window, response_queue, rpcc, poller, initial_mode)
    finally:
        rpcc.stop()
        rpc2_process.join()

if __name__ == '__main__':
    window = interface.init_curses()
    try:
        mainfn(window)
    finally:
        import curses
        curses.nocbreak()
        curses.endwin()
