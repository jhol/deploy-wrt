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

from dataclasses import dataclass
import dataclasses as dc
import logging as lg
import os
import os.path as osp
import subprocess as sp
import shutil
import sys
from tempfile import TemporaryDirectory
import yaml


@dataclass
class NodeConfig:
    host: str
    config_dir: str
    user: str


class ConfigLoadError(Exception):
    pass


def _load_node_config(args):
    file_cfg = {}
    try:
        with open(args.profile, "r") as f:
            file_cfg.update(yaml.safe_load(f)[args.HOST])

    except FileNotFoundError:
        pass
    except KeyError:
        raise ConfigLoadError(f'"{args.HOST}" not found in {args.profile}')

    file_config_dir = file_cfg.get('config_dir')
    if file_config_dir is not None and not osp.isabs(file_config_dir):
        file_config_dir = osp.join(osp.dirname(osp.abspath(args.profile)), file_config_dir)

    return NodeConfig(
        host=file_cfg.get('host') or args.HOST,
        config_dir=args.config_dir or file_config_dir or args.HOST,
        user=args.user or file_cfg.get('user') or 'root'
    )


def pull(host, config_dir, user="root"):
    with TemporaryDirectory() as temp_dir:
        # /etc/apk/world is backed up separately until https://github.com/openwrt/openwrt/issues/16947 is resolved
        ssh_cmd = [
            'ssh',
            f'{user}@{host}',
            'sysupgrade -b -; tar -czf - /etc/apk/world']
        gzip_cmd = ['gzip', '-c', '-d']
        tar_cmd = ['tar', '-C', temp_dir, '-xif', '-']

        lg.debug(f"Running: {' '.join(ssh_cmd)} | {' '.join(gzip_cmd)} | {' '.join(tar_cmd)}")

        ssh = sp.Popen(ssh_cmd, stdout=sp.PIPE)
        gzip = sp.Popen(gzip_cmd, stdin=ssh.stdout, stdout=sp.PIPE)
        tar = sp.Popen(tar_cmd, stdin=gzip.stdout)

        tar.wait()

        dest_etc = osp.join(config_dir, 'etc')
        os.makedirs(config_dir, exist_ok=True)
        if osp.exists(dest_etc):
            shutil.rmtree(dest_etc)

        shutil.move(osp.join(temp_dir, 'etc'), config_dir)

        shutil.rmtree(temp_dir)


def _pull_cmd(args):
    pull(**dc.asdict(_load_node_config(args)))


def push(host, config_dir, user="root", reboot=False):
    if not osp.exists(osp.join(config_dir, 'etc')):
        raise RuntimeError(f'{config_dir} does not appear to contain OpenWRT configuration')

    remote_cmds = (
            [
                'sysupgrade -r -',
                'apk update',
                'apk add'
            ] +
            (['reboot'] if reboot else [])
        )

    tar_cmd = ['tar', '-C', config_dir, '-czf', '-', 'etc']
    ssh_cmd = [
        'ssh',
        f'{user}@{host}',
        ' && '.join(remote_cmds)]

    lg.debug(f"Running: {' '.join(tar_cmd)} | {' '.join(ssh_cmd)}")

    tar = sp.Popen(tar_cmd, stdout=sp.PIPE)
    ssh = sp.Popen(ssh_cmd, stdin=tar.stdout)

    ssh.wait()


def _push_cmd(args):
    push(reboot=args.reboot, **dc.asdict(_load_node_config(args)))


def main_cli():
    import argparse

    parser = argparse.ArgumentParser(description="Tool for remote configuration of OpenWRT machines")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('-P', '--profile', default=".deploy-wrt.yml", help="File to open")

    subparsers = parser.add_subparsers(dest='command', help="Available commands")

    pull = subparsers.add_parser('pull', help="Pull the configuration from a machine")
    pull.add_argument('-u', '--user', type=str, help="SSH user name")
    pull.add_argument('-d', '--config-dir', type=str, help="Destination configuration directory")
    pull.add_argument('HOST', type=str, help="Host machine")
    pull.set_defaults(func=_pull_cmd)

    push = subparsers.add_parser('push', help="Push the configuration to a machine")
    push.add_argument('-u', '--user', type=str, help="SSH user name")
    push.add_argument('-d', '--config-dir', type=str, help="Source configuration directory")
    push.add_argument('HOST', type=str, help="Host machine")
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
