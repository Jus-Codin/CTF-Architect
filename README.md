# CTF-Architect

![Static Badge](https://img.shields.io/badge/python-3.11-blue)

A tool for managing challenges for CTFs.

NOTE: this tool is still a work in progress, bugs are to be expected.

I'm just a single person making this tool, so please be patient. 😇

## Installation

Note: This tool only supports python 3.11 and above.

### Installing from PyPI
To install from PyPI, run the following command:

```bash
# Linux and MacOS
python3 -m pip install ctf-architect

# Windows
py -3 -m pip install ctf-architect
```

### Installing from source

Git clone the repository, and pip install it
  
```bash
git clone https://github.com/Jus-Codin/CTF-Architect
cd CTF-Architect

# Linux and MacOS
python3 -m pip install .

# Windows
py -3 -m pip install .
```

If the installation is successful, you should be able to run the following commands:

```bash
ctf-architect --help

chall-architect --help
```

If, after installation, you get an error saying that the command is not found, you may need to add the python scripts folder to your PATH environment variable.

## Usage

### Creating a new challenge collection
To create a new CTF challenge collection, run the following command:

```bash
ctf-architect init
```

Follow the prompts to create a new challenge collection.

### Packaging a challenge for submission
To package a challenge for submission, run the following command:

```bash
chall-architect
```

Follow the prompts, and a folder will be created with the packaged challenge in your current directory.

### ⚠️ Warning ⚠️
This command will overwrite any files you have if they have the same name as the challenge you are packaging.