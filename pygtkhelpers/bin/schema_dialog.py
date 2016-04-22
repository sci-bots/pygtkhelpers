from argparse import ArgumentParser
import json
import logging
import re
import sys

from pygtkhelpers.schema import schema_dialog
import gtk


def parse_args(args=None):
    """Parses arguments, returns (options, args)."""

    if args is None:
        args = sys.argv

    parser = ArgumentParser(description='Barcode scanner based on GStreamer, '
                            'zbar, and gtk.')
    log_levels = ('critical', 'error', 'warning', 'info', 'debug', 'notset')

    parser.add_argument('-l', '--log-level', type=str, choices=log_levels,
                        default='info')
    parser.add_argument('-d', '--device-name', type=str, help='GStreamer video'
                        ' device name')
    parser.add_argument('-w', '--max-width', type=int,
                        help='Maximum video width')
    parser.add_argument('-f', '--max-fps', type=float, help='Maximum video '
                        'frame rate (frames/second)')
    parser.add_argument('schema', type=str, help='jsonschema schema')

    args = parser.parse_args()
    if hasattr(args, 'log_level'):
        args.log_level = getattr(logging, args.log_level.upper())
    return args


def main(args=None):
    gtk.threads_init()
    args = parse_args(args)

    schema = json.loads(args.schema)
    device_name = (re.split(r',\s+', args.device_name)
                   if args.device_name else None)

    try:
        results = schema_dialog(schema, device_name=device_name,
                                max_width=args.max_width, max_fps=args.max_fps)
    except ValueError, exception:
        print >> sys.stderr, 'Error: {}'.format(exception)
        raise SystemExit(-1)
    except KeyError, exception:
        print >> sys.stderr, 'Error: {}'.format(exception)
        raise SystemExit(-2)
    else:
        print json.dumps(results)


if __name__ == '__main__':
    main()
