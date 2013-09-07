#!/usr/bin/python
import sys
import unittest

from gnats.tests import database_tests
from gnats.tests import server_tests
from gnats.tests import dbhandle_tests

modules = (
           server_tests,
           database_tests,
           dbhandle_tests,
           )

def run_all_suites(verbosity):
    results = []
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=verbosity)
    fail_classes = []
    error_classes = []
    for m in modules:
        if verbosity > 0:
            print "#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#=#\nModule: %s" % \
                m.__name__
        for cl in m.classes:
            if verbosity > 0:
                print "Class: %s - %s" % (cl.__name__, cl.__doc__)
            res = runner.run(unittest.makeSuite(cl, 'test'))
            results.append(res)
            if res.failures:
                fail_classes.append("%s.%s" % (m.__name__, cl.__name__))
            if res.errors:
                error_classes.append("%s.%s" % (m.__name__, cl.__name__))
            if verbosity > 0:
                print
    run = failed = errors = 0
    for res in results:
        run += res.testsRun
        failed += len(res.failures)
        errors += len(res.errors)
    print "%d tests run.  %d failures, %d errors" % (run, failed, errors)
    if failed:
        print "Failures in:\n  %s" % '\n  '.join(fail_classes)
    if errors:
        print "Errors in:\n%s" % '\n  '.join(error_classes)
    return (failed > 0 or errors > 0) and 1 or 0


if __name__ == '__main__':
    if len(sys.argv) > 1:
        verb = int(sys.argv[1])
    else:
        verb = 1
    exit_code = run_all_suites(verb)
    sys.exit(exit_code)
