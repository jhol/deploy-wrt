deploy-wrt
==========

`deploy_wrt` is a tool and Python module that facilitates remote deployment and
configuration of OpenWRT machines. 

The tool works primarily by running `sysupgrade` through an SSH connection to
backup and restore system state. It also allows the list of installed packages
to be snapshotted and restored with APK package manager.


Installation
------------

### With PIP

```
 $ pip install git+https://github.com/jhol/deploy-wrt.git
```

### With Nix Flakes

```
 $ nix shell github:jhol/deploy-wrt
```


Quick Start
-----------

This is an example workflow where deploy-wrt is used together with Git to track
and modifiy the configuration of an OpenWRT machine: `mywrt`.

### Set-up

 1. Create a new Git repository:

    ```
     $ git init
    ```

 2. Create the `.deploy-wrt.yml` configuration YAML file. This file contains
    configuration profiles for each machine that will be managed through
    OpenWRT:

    ```
    mywrt:
        host: 192.168.1.1
    ```

 3. Commit the configuration file into Git:

    ```
     $ git add .deply-wrt.yml
     $ git commit -m"Added deploy-wrt config file"
    ```

### Snapshot

 1. Pull the current configuration from the machine. The `mywrt` profile is
    used from the `.deploy-wrt.yml` configuration file.

    ```
     $ deploy_wrt pull mywrt
    ```

    A new directory `mywrt/` has been created containing a snapshot of the
    current OpenWRT system configuration.

 2. Save the configuration in Git:

    ```
     $ git add mywrt/
     $ git commit -m"mywrt: Initial state import"
    ```

### Modification

The system configuration can now be modified either server-side i.e. through
normal OpenWRT configuration, or client-side i.e. making changes to the local
configuration.

#### Server Side

If the configuration is modified server-side, each change can be snapshotted
with `deploy_wrt pull` and Git commits.

#### Client Side

The configuration can be modified client-side by making changes to the
files in `mywrt/etc` which corresponds to the contents of the `/etc`
directory on the OpenWRT system.

APK packages can be added or removed by modifying the contents of the
`mywrt/etc/apk/world` file.

To apply the configuration to the machine the configuration should be applied
with the push command:

```
 $ deploy_wrt push mywrt
```


deploy-wrt Configuration
------------------------

The `.deply-wrt.yml` configuration file can contain one or more configuration
profiles:

  * Host Name
      * `host` - the address of network name of the OpenWRT machine.
      * `configuration_dir` - the directory where configuration files will be
        located. By default, if no value is set, the host name is used.
      * `user` - the user name to connect to SSH with. By default, if no value
        is set, the user name is set to `root`.


License
-------

The project is licensed under the terms of the GPL-v3 license.
