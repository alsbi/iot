#!/usr/bin/env python3
import socket
import time
from logging import getLogger

logger = getLogger(__name__)


class Switch:
    def __init__(self, relay, index, state):
        self.__relay = relay
        self.__index = index
        self.__state = state

    @property
    def state(self):
        return self.__state

    @state.setter
    def state(self, value):
        self.__state = value

    @property
    def power(self):
        return self.state

    @power.setter
    def power(self, value):
        logger.info(f'Set power: {value} for switch {self.__index}')
        operation = 'on' if value else 'off'
        command = f"{operation}{self.__index}"
        self.__relay.execute(command)
        self.state = value

    def timer(self, timeout):
        logger.info(f'Set power: True for switch {self.__index} timeout: {timeout}')
        command = f"on{self.__index}:{timeout}"
        self.__relay.execute(command)
        self.state = True

    def __repr__(self):
        return f'<Switch {self.__index}, power state {self.power}>'


class Relay:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.s.connect((self.ip, self.port))

        status = self._parse_status(self.execute('read'))
        self._switch = {index: Switch(self, index, state) for index, state in status}

    def execute(self, c):
        time.sleep(0.1)
        c = str(c).encode()
        self.s.send(c)
        data = self.s.recv(8192)
        return data.decode()

    def __getitem__(self, item):
        return self._switch[item]

    @staticmethod
    def _parse_status(data):
        return [[index + 1, bool(int(state))] for index, state in
                enumerate(reversed(data.split('relay')[1]))]

    def _update_status(self, status):
        for i, s in status:
            self._switch[i].state = s

    def status(self):
        data = self.execute('read')
        status = self._parse_status(data)
        self._update_status(status)
        return status

    def state(self, state: bool, switch=None):
        if not switch:
            command = str(int(state)) * len(self._switch)
            data = self.execute(f'all{command}')
            status = self._parse_status(data)
            self._update_status(status)

        else:
            self._switch[switch].power = state

    def __repr__(self):
        return str([s for s in self._switch.values()])

    def __del__(self):
        self.s.close()
