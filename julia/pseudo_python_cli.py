"""
Pseudo Python command line interface.

It tries to mimic a subset of Python CLI:
https://docs.python.org/3/using/cmdline.html
"""

import argparse
import code
import runpy
import sys
import traceback


def python(module, command, script, script_args, interactive):
    if command:
        sys.argv[0] = "-c"
    elif script:
        sys.argv[0] = script
    sys.argv[1:] = script_args

    banner = ""
    try:
        if command:
            scope = {}
            exec(command, scope)
        elif module:
            scope = runpy.run_module(
                module,
                run_name="__main__",
                alter_sys=True)
        elif script == "-":
            source = sys.stdin.read()
            exec(compile(source, "<stdin>", "exec"), scope)
        elif script:
            scope = runpy.run_path(
                script,
                run_name="__main__")
        else:
            interactive = True
            scope = None
            banner = None  # show banner
    except Exception:
        if not interactive:
            raise
        traceback.print_exc()

    if interactive:
        code.interact(banner=banner, local=scope)


class CustomFormatter(argparse.RawDescriptionHelpFormatter,
                      argparse.ArgumentDefaultsHelpFormatter):
    pass


def make_parser(description=__doc__):
    parser = argparse.ArgumentParser(
        prog=None if sys.argv[0] else "python",
        usage="%(prog)s [option] ... [-c cmd | -m mod | script | -] [args]",
        formatter_class=CustomFormatter,
        description=description)

    parser.add_argument(
        "-i", dest="interactive", action="store_true",
        help="""
        inspect interactively after running script.
        """)
    parser.add_argument(
        "--version", "-V", action="version",
        version="Python {0}.{1}.{2}".format(*sys.version_info),
        help="""
        print the Python version number and exit.
        -VV is not supported.
        """)

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-c", dest="command",
        help="""
        Execute the Python code in COMMAND.
        """)
    group.add_argument(
        "-m", dest="module",
        help="""
        Search sys.path for the named MODULE and execute its contents
        as the __main__ module.
        """)

    parser.add_argument(
        "script", nargs="?",
        help="path to file")

    return parser


def split_args(args):
    """
    Split arguments to Python and `sys.argv[1:]` to be used inside "script".

    >>> split_args(["-i", "script.py", "arg"])
    (['-i', 'script.py'], ['arg'])
    >>> split_args(["-c", "1/0"])
    (['-c', '1/0'], [])
    >>> split_args(["-mjson.tool", "-h"])
    (['-mjson.tool'], ['-h'])
    """
    it = iter(args)
    py_args = []
    for a in it:
        if a in ("-c", "-m"):
            py_args.append(a)
            try:
                a = next(it)
            except StopIteration:
                break
            py_args.append(a)
            break
        elif a == "-":
            py_args.append(a)
            break
        elif a.startswith("-"):
            py_args.append(a)
            if a[1] in ("c", "m"):
                break
        else:  # script
            py_args.append(a)
            break
    return py_args, list(it)


def parse_args(args):
    parser = make_parser()
    py_args, script_args = split_args(args)
    ns = parser.parse_args(py_args)
    ns.script_args = script_args
    return ns


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    try:
        ns = parse_args(args)
        python(**vars(ns))
    except SystemExit as err:
        return err.code
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
