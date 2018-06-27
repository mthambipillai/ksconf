""" SUBCOMMAND:  ksconf check <CONF>

Usage example:   (Nice pre-commit script)

    find . -name '*.conf' | ksconf check -

"""
from __future__ import absolute_import
from __future__ import unicode_literals
import os
from collections import Counter

from ksconf.conf.parser import parse_conf, PARSECONF_STRICT_NC, ConfParserException
from ksconf.consts import EXIT_CODE_SUCCESS, EXIT_CODE_BAD_CONF_FILE, EXIT_CODE_INTERNAL_ERROR
from ksconf.util.file import _stdin_iter
from ksconf.commands import KsconfCmd, dedent
from ksconf.util.completers import conf_files_completer




class CheckCmd(KsconfCmd):
    help = "Perform basic syntax and sanity checks on .conf files"
    description = dedent("""
        Provide basic syntax and sanity checking for Splunk's .conf
        files.  Use Splunk's builtin 'btool check' for a more robust
        validation of keys and values.

        Consider using this utility as part of a pre-commit hook.""")

    def register_args(self, p):
        p.add_argument("conf", metavar="FILE", nargs="+",
                       help="One or more configuration files to check.  If the special value of "
                            "'-' is given, then the list of files to validate is read from "
                            "standard input"
                         ).completer = conf_files_completer
        p.add_argument("--quiet", "-q", default=False, action="store_true",
                         help="Reduce the volume of output.")
        ''' # Do we really need this?
        p.add_argument("--max-errors", metavar="INT", type=int, default=0,
                         help="Abort check if more than this many files fail validation.  Useful
                         for a pre-commit hook where any failure is unacceptable.")
        '''

    def run(self, args):
        # Should we read a list of conf files from STDIN?
        if len(args.conf) == 1 and args.conf[0] == "-":
            confs = _stdin_iter()
        else:
            confs = args.conf
        c = Counter()
        exit_code = EXIT_CODE_SUCCESS
        for conf in confs:
            c["checked"] += 1
            if not os.path.isfile(conf):
                self.stderr.write("Skipping missing file:  {0}\n".format(conf))
                c["missing"] += 1
                continue
            try:
                parse_conf(conf, profile=PARSECONF_STRICT_NC)
                c["okay"] += 1
                if not args.quiet:
                    self.stdout.write("Successfully parsed {0}\n".format(conf))
                    self.stdout.flush()
            except ConfParserException as e:
                self.stderr.write("Error in file {0}:  {1}\n".format(conf, e))
                self.stderr.flush()
                exit_code = EXIT_CODE_BAD_CONF_FILE
                # TODO:  Break out counts by error type/category (there's only a few of them)
                c["error"] += 1
            except Exception as e:  # pragma: no cover
                self.stderr.write("Unhandled top-level exception while parsing {0}.  "
                                  "Aborting.\n{1}\n".format(conf, e))
                exit_code = EXIT_CODE_INTERNAL_ERROR
                c["error"] += 1
                break
        if True:  # show stats or verbose
            self.stdout.write("Completed checking {0[checked]} files.  rc={1} Breakdown:\n"
                              "   {0[okay]} files were parsed successfully.\n"
                              "   {0[error]} files failed.\n".format(c, exit_code))
        return exit_code
