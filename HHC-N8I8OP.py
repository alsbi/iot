#!/usr/bin/env python3
import socket
import time
from logging import getLogger

logger = getLogger(__name__)


class Switch:
    def __init__(self, relay, index, state):
        self.__relay = relay
        self.__index = index
        self.state = state

    def on(self, timer):
        if not self.state:
            logger.info(f'On switch {self.__index}')
            self.__relay.command(f"on{self.__index}")
            self.state = True

    def off(self, timer):
        if self.state:
            logger.info(f'Off switch {self.__index}')
            self.__relay.command(f"off{self.__index}")
            self.state = False

    def __repr__(self):
        return f'<Index {self.__index}, state {self.state}>'


class Relay:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.s.connect((self.ip, self.port))

        self.switch = {index: Switch(self, index, state) for index, state in self._get_state()}

    def _get_state(self, data=None):
        data = data or self.command('read')
        for index, state in enumerate(reversed(data.split('relay')[1])):
            yield index + 1, bool(int(state))

    def _update_state(self, data=None):
        for index, state in self._get_state(data=data):
            self.switch[index].state = state

    def command(self, c):
        c = str(c).encode()
        self.s.send(c)
        data = self.s.recv(8192)
        time.sleep(0.3)
        return data.decode()

    def on(self, index, timer=None):
        return self.switch[index].on(timer)

    def off(self, index, timer=None):
        return self.switch[index].off(timer)

    def on_all(self):
        if any(not s.state for s in self.switch.values()):
            logger.info(f'ON ALL switch')
            switch = '1' * len(self.switch)
            self._update_state(self.command(f'all{switch}'))

    def off_all(self):
        if any(s.state for s in self.switch.values()):
            logger.info(f'OFF ALL switch')
            switch = '0' * len(self.switch)
            self._update_state(self.command(f'all{switch}'))

    def __repr__(self):
        return str([s for s in self.switch.values()])

    def __del__(self):
        self.s.close()
