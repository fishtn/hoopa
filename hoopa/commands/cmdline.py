import sys
import cProfile

from hoopa.exceptions import UsageError
from hoopa.commands.create import CreateCommand


def _pop_command_name(argv):
    i = 0
    for arg in argv[1:]:
        if not arg.startswith('-'):
            del argv[i]
            return arg
        i += 1


def _print_unknown_command(cmd_name):
    print("Unknown command: %s\n" % cmd_name)
    print('Use "hoopa" to see available commands')


def _run_print_help(parser, func, *a, **kw):
    try:
        func(*a, **kw)
    except UsageError as e:
        if str(e):
            parser.error(str(e))
        if e.print_help:
            parser.print_help()
        sys.exit(2)


def _run_command(cmd, args, opts):
    if opts.profile:
        _run_command_profiled(cmd, args, opts)
    else:
        cmd.run(args, opts)


def _run_command_profiled(cmd, args, opts):
    if opts.profile:
        sys.stderr.write("scrapy: writing cProfile stats to %r\n" % opts.profile)
    loc = locals()
    p = cProfile.Profile()
    p.runctx('cmd.run(args, opts)', globals(), loc)
    if opts.profile:
        p.dump_stats(opts.profile)


def _print_commands():
    # with open(join(dirname(dirname(__file__)), "VERSION"), "rb") as f:
    #     version = f.read().decode("ascii").strip()
    #
    # print("hoopa {}".format(version))
    print("Usage:")
    print("  hoopa <command> [options] [args]\n")
    print("Available commands:")
    cmd_list = {"create": "create project、spider、item and so on"}
    for cmd_name, cmd_class in sorted(cmd_list.items()):
        print("  %-13s %s" % (cmd_name, cmd_class))

    print('Use "hoopa <command> -h" to see more info about a command')


def execute(argv=None):
    if argv is None:
        argv = sys.argv

    if len(argv) < 2:
        _print_commands()
        return

    cmd_name = argv.pop(1)
    cmd_list = {
        "create": CreateCommand
    }

    if not cmd_name:
        _print_commands()
        sys.exit(0)
    elif cmd_name not in cmd_list:
        _print_unknown_command(cmd_name)
        sys.exit(2)

    cmd = cmd_list[cmd_name]()
    cmd.add_arguments()
    cmd.run_cmd()

    sys.exit()


if __name__ == '__main__':
    execute()

