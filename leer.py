#!/usr/bin/env python

from sys import exit, stdout, stderr, argv
from subprocess import PIPE, Popen
from signal import SIGINT, SIGTERM, signal
from getopt import GetoptError, getopt
from re import sub, search, findall
from codecs import decode

Usage = """
usage: leer OPTIONS

Options:
  -p, --pid PID
  -d, --descriptors DESCRIPTOR[,...]
"""

WriteExpression = b'^.*write\(([0-9]+), "(.*)", [0-9]+\)[ ]+=[ ]+[0-9]+\n$'
Active = True 

def deactivate(signal=None, frame=None):
    global Active
    Active = False 

def parseParameters(arguments):
    parameters = {}
    options = getopt(arguments, "p:d:", ("pid=", "descriptors="))[0]

    for option, argument in options:
        if option in ("-p", "--pid"):
            parameters["pid"] = argument

        elif option in ("-d", "--descriptors"):
            parameters["descriptors"] = [int(d) for d in argument.split(",")]

    if not parameters:
        raise GetoptError(Usage)

    if "pid" not in parameters:
        raise GetoptError("Missing --pid")

    if "descriptors" not in parameters:
        raise GetoptError("Missing --descriptors")

    return parameters

def sample(parameters, line):
    arguments = findall(WriteExpression, line)
    if not arguments:
        return

    arguments = arguments[0]
    if not arguments:
        return

    descriptor = int(arguments[0])
    data = arguments[1]
 
    if descriptor in parameters.get("descriptors"):
        stdout.write(decode(data, "unicode_escape"))
 
def main(arguments):
    try:
        parameters = parseParameters(arguments) 

        signal(SIGINT, deactivate)
        signal(SIGTERM, deactivate)

        trace = Popen(["strace", "-q", "-ff",
                                 "-s", "65535",
                                 "-e", "trace=write",
                                 "-p", parameters.get("pid")],
                       stdout=PIPE,
                       stderr=PIPE)

        while Active:
            if trace.poll() is None:
                sample(parameters, trace.stderr.readline())
            else:
                deactivate() 
 
    except GetoptError as error:
        print(str(error))
        exit(2)

if __name__ == "__main__":
    main(argv[1:])
