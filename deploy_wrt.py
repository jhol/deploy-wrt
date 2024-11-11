#!/usr/bin/env python3
'''
This file is part of the deploy-wrt project.

Copyright (C) 2024 Joel Holdsworth <joel@airwebreathe.org.uk>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import logging as lg
import os
import os.path as osp
import subprocess as sp
import shutil
import sys
from tempfile import TemporaryDirectory


def pull(host, destination, user="root"):
    with TemporaryDirectory() as temp_dir:
        ssh_cmd = [
            'ssh',
            f'{user}@{host}',
            'sysupgrade -k -b -']
        tar_cmd = ['tar', '-C', temp_dir, '-xzf', '-']

        lg.debug(f"Running: {' '.join(ssh_cmd)} | {' '.join(tar_cmd)}")

        ssh = sp.Popen(ssh_cmd, stdout=sp.PIPE)
        tar = sp.Popen(tar_cmd, stdin=ssh.stdout)

        tar.wait()

        dest_etc = osp.join(destination, 'etc')
        os.makedirs(destination, exist_ok=True)
        if osp.exists(dest_etc):
            shutil.rmtree(dest_etc)
        
        shutil.move(osp.join(temp_dir, 'etc'), destination)

        shutil.rmtree(temp_dir)


def _pull_cmd(args):
    pull(args.HOST, args.DEST, args.user)


def push(host, source, user="root", reboot=False):
    if not osp.exists(osp.join(source, 'etc')):
        raise RuntimeError(f'{source} does not appear to contain OpenWRT configuration')

    remote_cmd = f'sysupgrade -r -{"; reboot" if reboot else ""}'

    tar_cmd = ['tar', '-C', source, '-czf', '-', 'etc']
    ssh_cmd = [
        'ssh',
        f'{user}@{host}',
        remote_cmd]

    lg.debug(f"Running: {' '.join(tar_cmd)} | {' '.join(ssh_cmd)}")

    tar = sp.Popen(tar_cmd, stdout=sp.PIPE)
    ssh = sp.Popen(ssh_cmd, stdin=tar.stdout)

    ssh.wait()


def _push_cmd(args):
    push(args.HOST, args.SRC, args.user, args.reboot)


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(description="Tool for remote configuration of OpenWRT machines")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')

    subparsers = parser.add_subparsers(dest='command', help="Available commands")

    pull = subparsers.add_parser('pull', help="Pull the configuration from a machine")
    pull.add_argument('-u', '--user', type=str, default='root')
    pull.add_argument('HOST', type=str, help="Host machine")
    pull.add_argument('DEST', type=str, help="Destination configuration directory")
    pull.set_defaults(func=_pull_cmd)

    push = subparsers.add_parser('push', help="Push the configuration to a machine")
    push.add_argument('--user', '-u', type=str, default='root')
    push.add_argument('HOST', type=str, help="Host machine")
    push.add_argument('SRC', type=str, help="Source configuration directory")
    push.add_argument('-r', '--reboot', action="store_true", help="Reboot machine after import")
    push.set_defaults(func=_push_cmd)

    args = parser.parse_args()

    lg.basicConfig(level=lg.DEBUG if args.verbose else lg.INFO)

    if hasattr(args, 'func'):
        try:
            args.func(args)
            return 0
        except Exception as e:
            sys.stderr.write(f'Error: {e}\n')
            return 1
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main_cli())
