#!/usr/bin/env python
import curses

import global_mod as g

def draw_window(state, window):
    window.clear()
    window.refresh()
    win_header = curses.newwin(4, 75, 0, 0)

    if 'peerinfo' in state:
        color = curses.color_pair(1)
        if 'testnet' in state:
            if state['testnet']: color = curses.color_pair(2)
        win_header.addstr(0, 1, "bitcoind-ncurses " + g.version + " [peer view] (press 'P' to refresh)", color + curses.A_BOLD)

        window_height = state['y'] - 3

        if len(state['peerinfo']) > window_height:
            win_header.addstr(1, 1, "connected peers: " + str(len(state['peerinfo'])).ljust(10) + "                        (UP/DOWN: scroll)", curses.A_BOLD)
        else:
            win_header.addstr(1, 1, "connected peers: " + str(len(state['peerinfo'])), curses.A_BOLD)

        win_header.addstr(3, 1, "  Node IP                      Version                Recv      Sent", curses.A_BOLD + curses.color_pair(5))

        draw_peers(state)

    else:
        win_header.addstr(0, 1, "peer info not loaded (this should not happen!)", curses.A_BOLD)
        win_header.addstr(1, 1, "press 'M' to return to monitor window", curses.A_BOLD)

    win_header.refresh()

def draw_peers(state):
    window_height = state['y'] - 4
    win_peers = curses.newwin(window_height, 75, 4, 0)

    offset = state['peerinfo_offset']

    for index in xrange(offset, offset+window_height):
        if index < len(state['peerinfo']):
            peer = state['peerinfo'][index]
            if (index == offset+window_height-1) and (index+1 < len(state['peerinfo'])):
                win_peers.addstr(index-offset, 3, "... " + peer['addr'])
            elif (index == offset) and (index > 0):
                win_peers.addstr(index-offset, 3, "... " + peer['addr'])
            else:
                if peer['inbound']:
                    win_peers.addstr(index-offset, 1, 'I')
                elif 'syncnode' in peer:
                    if peer['syncnode']: # syncnodes are outgoing only
                        win_peers.addstr(index-offset, 1, 'S')
                win_peers.addstr(index-offset, 3, peer['addr'])
                win_peers.addstr(index-offset, 32, peer['subver'].strip("/"))

                mbrecv = "% 7.1f" % ( float(peer['bytesrecv']) / 1048576 )
                mbsent = "% 7.1f" % ( float(peer['bytessent']) / 1048576 )

                win_peers.addstr(index-offset, 50, mbrecv + 'MB')
                win_peers.addstr(index-offset, 60, mbsent + 'MB')

    win_peers.refresh()
