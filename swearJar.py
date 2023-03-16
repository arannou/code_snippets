import os
import json
from os import sys
import re

from hashlib import blake2b
from click import prompt

MY_HASH = b'36c0ef2d9163d01150df0b1a76e6c3e2fda60b9779820909f19c89fd453b53cb8c7849d138feb572ecf8cc391bc32d017bc4b8abf9818a47ea1051b17cfc1201'

class bcolors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    ENDC = '\033[0m'

def showHelp():
    print(bcolors.GREEN + "Welcome to the SwearJar 2.0" + bcolors.ENDC)
    print("\t<names> <amount?> \tAdd <amount> swears to each <names> (space separated). Default amount is 1")
    print("\t--help \t\t\tDisplay this help")
    print("\t--show \t\t\tDisplay all scores")
    print("\t--add <name> \t\tAdd someone to the jar with name <name> with score of 1")
    print("\t--remove <name> \tRemove someone of the jar")

def showScores(j):
    for s in sorted(j.items(), key=lambda kv: kv[1], reverse=True):
        print(str(s[1]) + "\t" + bcolors.BLUE + s[0] + bcolors.ENDC)

def authent():
    pwd = prompt("Password", hide_input=True)
    h = blake2b()
    h.update(pwd.encode('utf-8'))
    return h.hexdigest().encode('utf-8') == MY_HASH

# open file
file = os.path.join("/home/arannou/swearJarData.json")
with open(file, "r") as f:
    j = json.load(f)
f.close()

if '--help' in sys.argv :
    showHelp()

if '--show' in sys.argv :
    showScores(j)

amount = 1
# search for specified amount
for i in range(len(sys.argv)):
    if re.search('[0-9]+', sys.argv[i]):
        amount = int(sys.argv[i])

    if sys.argv[i] == '--add':
        if authent():
            try:
                j[sys.argv[i+1]] = 0
                print(bcolors.GREEN + "Success: New user added!"+ bcolors.ENDC)
            except:
                print(bcolors.RED + "Error: Please provide a name to add!"+ bcolors.ENDC)
        else:
            print(bcolors.RED + "Error: Wrong password!"+ bcolors.ENDC)

    if sys.argv[i] == '--remove':
        if authent():
            try:
                del j[sys.argv[i+1]]
                print(bcolors.GREEN + "Success: User removed!"+ bcolors.ENDC)
            except:
                print(bcolors.RED + "Error: Please provide a name to remove!"+ bcolors.ENDC)
        else:
            print(bcolors.RED + "Error: Wrong password!"+ bcolors.ENDC)

modified = False
for arg in sys.argv:
    # add amount for each name
    if arg in j.keys():
        j[arg] += amount
        modified = True

# write new file
with open(file, 'w') as outfile:
    json.dump(j, outfile)
    outfile.close()

if modified:
    showScores(j)
