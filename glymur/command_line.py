"""
Entry point for console script jp2dump.
"""
import argparse
import os
import warnings

from . import Jp2k, set_printoptions, set_parseoptions, lib, tif2jp2, core


def tif2jp2_cmd():
    """
    Entry point for console script tif2jp2
    """
    kwargs = {'description': 'Convert TIFF to JPEG2000',
              'formatter_class': argparse.ArgumentDefaultsHelpFormatter}
    parser = argparse.ArgumentParser(**kwargs)
    parser.add_argument('-n', '--num-resolutions',
                        help='number of resolution',
                        dest='num_res',
                        default=6,
                        type=int)
    parser.add_argument('-p', '--progression-order',
                        help='progression order',
                        dest='progression_order',
                        default='LRCP',
                        choices=['LRCP', 'RPCL', 'RLCP', 'PCRL', 'CPRL'])
    parser.add_argument('-t', '--tile-size',
                        help='shape of tiles',
                        metavar=('NRows', 'NCols'),
                        nargs=2,
                        type=int,
                        default=None)
    parser.add_argument('input_tiff', type=str)
    parser.add_argument('output_jp2', type=str)
    args = parser.parse_args()

    tif2jp2(args.input_tiff, args.output_jp2,
            num_res=args.num_res,
            tilesize=args.tile_size,
            prog=args.progression_order)


def main():
    """
    Entry point for console script jp2dump
    """

    kwargs = {'description': 'Print JPEG2000 metadata.',
              'formatter_class': argparse.ArgumentDefaultsHelpFormatter}
    parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument('-x', '--noxml',
                        help='suppress XML',
                        action='store_true')
    parser.add_argument('-s', '--short',
                        help='only print box id, offset, and length',
                        action='store_true')

    chelp = 'Level of codestream information.  0 suppresses all details, '
    chelp += '1 prints the main header, 2 prints the full codestream.'
    parser.add_argument('-c', '--codestream',
                        help=chelp,
                        metavar='LEVEL',
                        nargs=1,
                        type=int,
                        default=[1])

    parser.add_argument('filename')

    args = parser.parse_args()
    if args.noxml:
        set_printoptions(xml=False)
    if args.short:
        set_printoptions(short=True)

    codestream_level = args.codestream[0]
    if codestream_level not in [0, 1, 2]:
        raise ValueError("Invalid level of codestream information specified.")

    if codestream_level == 0:
        set_printoptions(codestream=False)
    elif codestream_level == 2:
        set_parseoptions(full_codestream=True)

    filename = args.filename

    with warnings.catch_warnings(record=True) as wctx:

        # JP2 metadata can be extensive, so don't print any warnings until we
        # are done with the metadata.
        jp2 = Jp2k(filename)
        if jp2._codec_format == lib.openjp2.CODEC_J2K:
            if codestream_level == 0:
                print('File:  {0}'.format(os.path.basename(filename)))
            elif codestream_level == 1:
                print(jp2)
            elif codestream_level == 2:
                print('File:  {0}'.format(os.path.basename(filename)))
                print(jp2.get_codestream(header_only=False))
        else:
            print(jp2)

        # Re-emit any warnings that may have been suppressed.
        if len(wctx) > 0:
            print("\n")
        for warning in wctx:
            print("{0}:{1}: {2}: {3}".format(warning.filename,
                                             warning.lineno,
                                             warning.category.__name__,
                                             warning.message))
