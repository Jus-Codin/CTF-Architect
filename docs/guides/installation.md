# Installation

## Installing from PyPI

To install from PyPI, run the following command:

```bash
# Linux and MacOS
python3 -m pip install -U ctf-architect

# Windows
py -3 -m pip install -U ctf-architect
```
!!! warning
    If the above command produces an error during installation, try running the command in a terminal with administrator privileges.


## Installing from Source

!!! warning
    Installing from source will pull the latest changes from the repository. This may include new features, bug fixes, or breaking changes. If you want to use a stable version, it is recommended to install from PyPI.

Git clone the repository, and pip install it
  
```bash
git clone https://github.com/Jus-Codin/CTF-Architect
cd CTF-Architect

# Linux and MacOS
python3 -m pip install .

# Windows
py -3 -m pip install .
```

## Post Installation

If the installation is successful, you should be able to run the following commands:

```bash
ctf-architect --help

chall-architect --help
```

!!! note
    If after installation, you get an error saying that the command is not found, you may need to add the python scripts folder to your PATH environment variable. See [this guide](https://realpython.com/add-python-to-path/) for more information.

Now that you have successfully installed CTF-Architect, read these guides to get started:

- [Packaging a challenge for submission](./packaging-challenges.md)
- [Setting up a challenge repository](./repository-setup.md)
