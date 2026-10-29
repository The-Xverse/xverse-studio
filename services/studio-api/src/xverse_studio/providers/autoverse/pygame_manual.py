"""Own-process adapter around Autoverse's original public manual-control CLI.

Initialize only keyboard/display/font APIs. Physical joystick/wheel backends and
unrelated Zenoh discovery are outside this integration's admitted permissions.
The original companion script and its rendering/control algorithms stay intact.
"""
import argparse
import json
import os
from pathlib import Path
import runpy
import sys


class KeyboardOnlyJoysticks:
    @staticmethod
    def init(): pass
    @staticmethod
    def quit(): pass
    @staticmethod
    def get_init(): return False
    @staticmethod
    def get_count(): return 0
    @staticmethod
    def Joystick(*_args): raise RuntimeError('Physical wheel access is not admitted')


def configure_keyboard_only(pygame):
    def initialize():
        pygame.display.init()
        pygame.font.init()
        return (2, 0)
    pygame.init = initialize
    pygame.joystick = KeyboardOnlyJoysticks()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--ready-file', type=Path, required=True)
    args = parser.parse_args()
    import pygame
    import zenoh
    configure_keyboard_only(pygame)
    original_open = zenoh.open
    def confined_open(config):
        for key, value in {'mode': 'client', 'connect/endpoints': ['tcp/127.0.0.1:7447'],
            'listen/endpoints': [], 'scouting/multicast/enabled': False, 'scouting/gossip/enabled': False}.items():
            config.insert_json5(key, json.dumps(value))
        return original_open(config)
    zenoh.open = confined_open
    original_events = pygame.event.get
    reported = False
    def events(*values, **options):
        nonlocal reported
        if not reported:
            window = pygame.display.get_wm_info().get('window')
            caption = pygame.display.get_caption()[0]
            if type(window) is int and window > 0 and caption == 'Vehicle Manual Control':
                payload = {'pid': os.getpid(), 'windowId': window, 'title': caption, 'keyboardOnly': True}
                temporary = args.ready_file.with_suffix('.tmp')
                temporary.write_text(json.dumps(payload), encoding='utf-8')
                temporary.chmod(0o600)
                os.replace(temporary, args.ready_file)
                reported = True
        return original_events(*values, **options)
    pygame.event.get = events
    script = args.root.resolve() / 'bridges/carla/examples/vehicle_manual_control.py'
    sys.argv = [str(script), '--router', '127.0.0.1', '--signals-config', str(script.with_name('signals_config_manual_control.json'))]
    sys.path.insert(0, str(script.parent))
    runpy.run_path(str(script), run_name='__main__')


if __name__ == '__main__':
    main()
