# Packaging Challenges

!!! note
    This guide assumes that you have successfully installed CTF-Architect. If you have not, please refer to the [installation guide](./installation.md).

## Download ctf_config.toml
Download the relavant `ctf_config.toml` file for the CTF. If you do not have this file, contact the CTF organizers for it.

## Prepare Your Files
Prepare the following files for your challenge:

- **Solution Files**: The writeup or solution files for the challenge.
- **Challenge Files**: The files that the participants will interact with to solve the challenge.
- **Service Folders**: If your challenge requires a service, create a folder for the service. This folder should contain the files required to run the service and a `Dockerfile`.

## Packaging a Challenge
To package a challenge for submission, run the following command:

```bash
chall-architect

# or

python3 -m ctf_architect.chall_architect # Linux and MacOS
py -3 -m ctf_architect.chall_architect # Windows
```

<div class="termy">

```console
$ chall-architect
────────────────── ⚙ CTF Config ⚙ ───────────────────
# Please select the CTF config file.$                                     
╭──────────────── YCEP 2024 Config ─────────────────╮
│ Categories:                                       │
│   - Web                                           │
│   - Forensics                                     │
│   - Crypto                                        │
│   - Misc                                          │
│   - Re                                            │
│   - Pwn                                           │
│   - Osint                                         │
│                                                   │
│ Difficulties:                                     │
│   - Easy (1000)                                   │
│   - Medium (1000)                                 │
│   - Hard (1000)                                   │
│   - Insane (1000)                                 │
│                                                   │
│ Extra Fields:                                     │
│   - discord                                       │
│                                                   │
│ Starting Port: 8000                               │
╰───────────────────────────────────────────────────╯
# Is this the correct config? [y/n]:$ y
───────────── 🚀 Challenge Creation 🚀 ──────────────
# 🚀 [1/6] Please enter the challenge name(case-insensitive):$ Gimme Cookie
🚀 [2/6] Please enter the challenge description.
Press Ctrl+D (or Ctrl+Z on Windows) on an empty line
to finish.
# >>>$ I want cookies!
# >>>$ ^Z

Categories:
1. Web
2. Forensics
3. Crypto
4. Misc
5. Re
6. Pwn
7. Osint

# 🚀 [3/6] Please choose the challenge category [1-7]:$ 1
Category selected: Web

Difficulties:
1. Easy (1000)
2. Medium (1000)
3. Hard (1000)
4. Insane (1000)

# 🚀 [4/6] Please choose the challenge difficulty [1-4]:$ 1
Difficulty selected: Easy


# 🚀 [5/6] Please enter your name:$ JusCodin

# 🚀 [6/6] Please enter info for discord:$ juscodin
Discord: juscodin
# ─ 📁 Please select the source files for the challe… ─$                                     
Source files selected:
  C:\Users\Admin\Git\Gryphons\YCEP-Challenges-2024\ch
allenges\web\Gimme Cookie\service\gimme-cookie\app.py
  C:\Users\Admin\Git\Gryphons\YCEP-Challenges-2024\ch
allenges\web\Gimme
Cookie\service\gimme-cookie\Dockerfile
# ─ 📁 Please select the solution files for the chal… ─$                                     
Solution files selected:
  C:\Users\Admin\Git\Gryphons\YCEP-Challenges-2024\ch
allenges\web\Gimme Cookie\solution\writeup.md
─────────────── 🚩 Challenge Flags 🚩 ───────────────
# 🚩 Is the flag a regex flag? [y/n]:$ n
# 🚩 Is the flag case-sensitive? [y/n]:$ y
# 🚩 Enter the flag:$ YCEP24{v3Ry_EZ_C0oK1e_MAn1pU1@t!0N}
# Do you want to add another flag? [y/n]:$ n
─────────────── 💡 Challenge Hints 💡 ───────────────
# 💡 Does the challenge have hints? [y/n]:$ n
─────────────── 📁 Challenge Files 📁 ───────────────
# 📁 Does the challenge have files to give to players? [y/n]:$ y

# 📁 Are there any files from URLs? [y/n]:$ n

# 📁 Are there any files from the local system? [y/n]:$ y
$                                     
Files selected:
-
C:\Users\Admin\Git\Gryphons\YCEP-Challenges-2024\chal
lenges\web\Gimme
Cookie\service\gimme-cookie\Dockerfile
────────────── ⚙ Challenge Services ⚙ ───────────────
# ⚙ Does the challenge have services? [y/n]:$ y

# ⚙ Please enter the service name:$ gimme-cookie
# ⚙ Please enter the service port:$ 1337
⚙ Please enter the service type
# [web/nc/ssh/secret/internal]:$ web
# ⚙ Please select the service folder...$                                     
# ⚙ Does the service have any extra fields? [y/n]:$ n
# Do you want to add another service? [y/n]:$ n
🚀 Does the service(s) need a Docker Compose file?
# [y/n]:$ n

──────────── ⚙ Challenge Requirements ⚙ ─────────────
# ⚙ Does the challenge have requirements? [y/n]:$ n
╭──────────────── Challenge Details ────────────────╮
│ Name: Gimme Cookie                                │
│ Description: I want cookies!                      │
│ Category: Web                                     │
│ Difficulty: Easy                                  │
│ Author: JusCodin                                  │
│                                                   │
│ Extra Fields:                                     │
│ Discord: juscodin                                 │
│ None                                              │
│                                                   │
│ Solution Files:                                   │
│ -                                                 │
│ C:/Users/Admin/Git/Gryphons/YCEP-Challenges-2024/ │
│ challenges/web/Gimme Cookie/solution/writeup.md   │
│                                                   │
│ Flags: YCEP24{v3Ry_EZ_C0oK1e_MAn1pU1@t!0N}        │
│                                                   │
│ Hints:                                            │
│ None                                              │
│                                                   │
│ Files:                                            │
│ -                                                 │
│ C:/Users/Admin/Git/Gryphons/YCEP-Challenges-2024/ │
│ challenges/web/Gimme                              │
│ Cookie/service/gimme-cookie/Dockerfile            │
│                                                   │
│ Services:                                         │
│ - gimme-cookie (web)                              │
│                                                   │
│ Docker Compose:                                   │
│ None                                              │
│ Requirements:                                     │
│ None                                              │
│                                                   │
╰───────────────────────────────────────────────────╯
# Do you want to create the challenge? [y/n]:$ y
Successfully created challenge `Gimme Cookie` at
`C:\Users\Admin\Gimme Cookie`
```

</div>

## Submitting a Challenge
If everything goes well, your challenge should be nicely packaged in a folder. You can now **zip** the folder and submit it. 

!!! warning
    Ensure that it is a **.zip** file, and not a **.rar** or **.7z** file.