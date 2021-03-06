"""
Copyright (C) 2018
Giovanni -iGio90- Rocca, Vincenzo -rEDSAMK- Greco

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program. If not, see https://www.gnu.org/licenses/
"""

import codecs
import os

import frida
import sys


class Target(object):
    def __init__(self, target):
        self.target = target
        self.target_module = 'null'
        self.on_message_cb = None
        self.script = ''
        self.start_delay = 0

    def set_frida_message_callback(self, cb):
        self.on_message_cb = cb

    def set_start_delay(self, delay):
        self.start_delay = delay

    def set_script(self, script):
        self.script = script

    def set_script_path(self, script_path):
        with codecs.open(script_path, 'r', 'utf-8') as f:
            s = f.read()
        self.script = s

    def set_target_module(self, target_module):
        self.target_module = target_module


class FridaSec(object):
    def __init__(self, target):
        self.target = target
        self.device = frida.get_usb_device()
        self.script = None

    def enumerate_applications(self):
        return self.enumerate_applications()

    def enumerate_processes(self):
        return self.device.enumerate_processes()

    def get_script(self):
        return self.script

    def run(self):
        bundle_identifier = None
        pid = None
        for application in self.device.enumerate_applications():
            if self.target.target == application.name:
                bundle_identifier = application.identifier
                pid = application.pid
            elif self.target.target == application.identifier:
                bundle_identifier = application.identifier
                pid = application.pid
        if bundle_identifier is None:
            print('[*] App not found')
            sys.exit(0)

        # attach and inject frida script
        print("[*] Attaching to target process")
        if pid == 0:
            pid = self.device.spawn([bundle_identifier])
        else:
            try:
                self.device.resume(pid)
            except:
                pass

        process = self.device.attach(pid)

        print("[*] Injecting script")
        with codecs.open(os.path.dirname(os.path.abspath(__file__)) + '/api.js', 'r', 'utf-8') as f:
            source = f.read()

        source = source.replace('%%target%%', self.target.target_module)
        source = source.replace('%%script%%', self.target.script)
        source = source.replace('%%delay%%', str(self.target.start_delay))

        self.script = process.create_script(source)
        self.script.on('message', self._on_message)
        print("[*] All done. Good luck!")
        self.script.load()
        sys.stdin.read()

    def _on_message(self, message, data):
        if self._handle_message(message, data):
            # just pass. it's handled
            pass
        elif self.target.on_message_cb is not None:
            self.target.on_message_cb(message, data)

    @staticmethod
    def _handle_message(message, data):
        if 'payload' in message:
            p = message['payload']
            if 'fscmd' in p:
                cmd = p['fscmd']
                if cmd == 'dump':
                    fn = p['fn']
                    with open(fn, 'wb') as f:
                        f.write(data)
                return True

        return False
