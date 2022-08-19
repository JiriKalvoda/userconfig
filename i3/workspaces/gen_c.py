#!/usr/bin/env python3
import io

import i3_workspace_util as util
import i3_workspace_help as help
from i3_workspace_constants import *
from i3_workspace_main_functions import main_functions_list, EnumString

def escape_char(c):
    return {
            '\n': '\\n',
            '\t': '\\t',
            '"': '\\"',
            }.get(c,c)

def c(x):
    if x is None:
        return "NULL"
    if type(x) == bytes:
        return x.decode()
    if type(x) == str:
        return '"' + "".join(escape_char(c) for c in x) + '"'
    if type(x) == int:
        return str(x)
    if type(x) == tuple or type(x) == list:
        return "{" + ",".join(map(c,x)) +"}"

def char(s):
    return {
            '\n': b"'\\n'",
            '\t': b"'\\t'",
            '\'': b"'\\''",
        }.get(c,f"'{s}'".encode())


print("const char *USAGE =", c(help.client_usage),";")
print("const char *LICENSE =", c(help.LICENSE_ALL),";")

SUBCOMMANDS_HELP = []

print('static void check(int argc, char ** argv)')
print('{')
for f in main_functions_list:
    parser = util.ArgumentParserNoFail(add_help=False)
    for (args, kvargs) in f.args:
        parser.add_argument(*args, **kvargs)
    help_io = io.StringIO()
    parser.print_help(help_io)
    help_io.seek(0)
    help_str = "\n".join("   "+x for x in (f.help.split("\n") if f.help else []) + help_io.read().split("\n")[2:-1])
    module_help = "/".join(f.names) + ":\n"+help_str
    if f.help is not None:
        SUBCOMMANDS_HELP.append(module_help)

    print('if(', " || ".join(f"!strcmp(argv[1], {c(name)})" for name in f.names), ")")
    print('{')
    print(f'const char * module_help = {c(module_help)};')
    switch= []
    short_opts = []
    long_opts = []
    for args, kvargs in f.args:
        need_argument = "action" not in kvargs
        short = args[0][1:]
        long = args[1][2:]
        short_opts.append(args[0][1:] + ":" if need_argument else "")
        long_opts.append((long, b"required_argument" if need_argument else b"no_argument", None, char(short)))
        def assert_in(l):
            switch.append(f"case {c(char(short))}: {{")
            switch.append(f"char *list[] = {c(l)};")
            switch.append(f"IS_IN(optarg, list, \"-{short}/--{long}\");")
            switch.append("} break;")
        if "type" in kvargs and issubclass(kvargs["type"], EnumString):
            assert_in(kvargs["type"]().options())

    print(f"struct option long_opts[] = {c(long_opts + [(None, 0, None, 0)])};")
    print("int opt;")
    print(f'while ((opt = getopt_long(argc-1, argv+1, {c("".join(short_opts))}, long_opts, NULL)) >= 0)')
    print('{')
    print('if(opt==\'?\') die("%s", module_help);')
    print("switch (opt)")
    print('{')
    for s in switch:
        print(s)
    print('}')
    print('}')
    print('if (optind < argc-1) die("Positional argument is unsupported.\\n%s", module_help);')
    print('return;')
    print('}')
    
print('die_help("Command %s not found.", argv[1]);')
print('}')

SUBCOMMANDS_HELP.append(
f"""
WORKSPACE must be name (mostly number) of workspace
SLAVE must be number between {MIN_MASTER} and {MAX_MASTER} or command from next list:
    - next/prev            next/previous master from actual
                           after all masters, shared slaves will be iterated
    - next-skip/prev-skip  next/previous used master from actual
    - alloc                first unused master
SLAVE must be number between {MIN_SLAVE} and {MAX_SLAVE} or command from next list:
    - next-limit/prev-limit              next/previous slave from actual master
    - next-limit-skip/prev-limit-skip    next/previous used slave from actual master
    - next-limit/prev-limit/next-limit-skip/prev-limit-skip
                The same as with limit, but if there is no more slave,
                next master will be used and after all slaves will be shared slaves.
    - alloc                first unused slave on this master
"""[1:-1]
)

print("const char *SUBCOMMANDS_HELP =", c("   " + "\n\n".join(SUBCOMMANDS_HELP).replace('\n', '\n   ')),";")
