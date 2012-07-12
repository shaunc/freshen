#-*- coding: utf8 -*-

import unittest
import sys
import os
import logging
import re
import traceback
from new import instancemethod

from pyparsing import ParseException

from nose.plugins import Plugin
from nose.plugins.skip import SkipTest
from nose.plugins.errorclass import ErrorClass, ErrorClassPlugin
from nose.selector import TestAddress
from nose.failure import Failure
from nose.util import isclass

from freshen.core import TagMatcher, load_language, load_feature, StepsRunner
from freshen.context import *
from freshen.prettyprint import FreshenPrettyPrint
from freshen.stepregistry import StepImplLoader, StepImplRegistry
from freshen.stepregistry import UndefinedStepImpl, StepImplLoadException

try:
    # use colorama for cross-platform colored text, if available
    import colorama
    colorama.init()
except ImportError:
    colorama = None

log = logging.getLogger( 'nose.plugins.freshen' )

# This line ensures that frames from this file will not be shown in tracebacks
__unittest = 1

class ExceptionWrapper( Exception ):

    def __init__( self, e, step ):
        self.e = e
        self.step = step

    def __str__( self ):
        return "".join( traceback.format_exception( *self.e ) )

class FeatureSuite( object ):
    '''
    Grouping context for nosetests.
    
    Provide access to filename loaded from and list of tests for
    the benefit of other nose plugins.
    '''

    def __init__( self, filename, indexes ):
        self.filename = filename
        self.indexes = indexes
        self.tests = []

    def add_test( self, test ):
        self.tests.append( test )

    def setUp( self ):
        #log.debug("Clearing feature context")
        ftc.clear()

class FreshenTestCase( unittest.TestCase ):

    start_live_server = True
    database_single_transaction = True
    database_flush = True
    selenium_start = False
    no_database_interaction = False
    make_translations = True
    required_sane_plugins = ["django", "http"]
    django_plugin_started = False
    http_plugin_started = False
    last_step = None

    test_type = "http"

    def __init__( self, step_runner, step_registry, feature, scenario, feature_suite ):
        self.feature = feature
        self.scenario = scenario
        self.context = feature_suite
        self.step_registry = step_registry
        self.step_runner = step_runner

        self.description = feature.name + ": " + scenario.name
        feature_suite.add_test( self )
        super( FreshenTestCase, self ).__init__()

    def setUp( self ):
        #log.debug("Clearing scenario context")
        scc.clear()
        for hook_impl in self.step_registry.get_hooks( 'before', self.scenario.get_tags() ):
            hook_impl.run( self.scenario )

    def runTest( self ):
        for step in self.scenario.iter_steps():
            try:
                self.last_step = step
                self.step_runner.run_step( step )
            except ( AssertionError, UndefinedStepImpl, ExceptionWrapper ):
                raise
            except:
                raise ExceptionWrapper( sys.exc_info(), step )

            for hook_impl in reversed( self.step_registry.get_hooks( 'after_step', self.scenario.get_tags() ) ):
                hook_impl.run( self.scenario )
        self.last_step = None

    def tearDown( self ):
        for hook_impl in reversed( self.step_registry.get_hooks( 'after', self.scenario.get_tags() ) ):
            hook_impl.run( self.scenario )

class FreshenErrorPlugin( ErrorClassPlugin ):

    enabled = True
    undefined = ErrorClass( UndefinedStepImpl,
                           label = "UNDEFINED",
                           isfailure = False )

    def options( self, parser, env ):
        # Forced to be on!
        pass


class StepsLoadFailure( Failure ):

    def __str__( self ):
        return "Could not load steps for %s" % self.address()

class ParseFailure( Failure ):

    def __init__( self, parse_exception, tb, filename ):
        self.parse_exception = parse_exception
        self.filename = filename
        super( ParseFailure, self ).__init__( parse_exception.__class__, parse_exception, tb )

    def __str__( self ):
        return "Could not parse %s" % ( self.filename )

class FreshenNosePlugin( Plugin ):

    name = "freshen"

    # This makes it so that freshen's formatFailure gets called before capture
    # and logcapture - those plugins replace and obscure the true exception value
    score = 1000

    def options( self, parser, env ):
        super( FreshenNosePlugin, self ).options( parser, env )

        parser.add_option( '--tags', action = 'store',
                          dest = 'tags',
                          default = env.get( 'NOSE_FRESHEN_TAGS' ),
                          help = "Run only those scenarios and features which "
                               "match the given tags. Should be a comma-separated "
                               "list. Each tag can be prefixed with a ~ to negate "
                               "[NOSE_FRESHEN_TAGS]" )
        parser.add_option( '--language',
                          action = "store",
                          dest = 'language',
                          default = 'en',
                          help = 'Change the language used when reading the feature files' )
        parser.add_option( '--list-undefined',
                          action = "store_true",
                          default = env.get( 'NOSE_FRESHEN_LIST_UNDEFINED' ) == '1',
                          dest = "list_undefined",
                          help = "Make a report of all undefined steps that "
                               "freshen encounters when running scenarios. "
                               "[NOSE_FRESHEN_LIST_UNDEFINED]" )

    def configure( self, options, config ):
        super( FreshenNosePlugin, self ).configure( options, config )
        all_tags = options.tags.split( "," ) if options.tags else []
        self.tagmatcher = TagMatcher( all_tags )
        self.language = load_language( options.language )
        self.impl_loader = StepImplLoader()
        if not self.language:
            print >> sys.stderr, "Error: language '%s' not available" % options.language
            exit( 1 )
        if options.list_undefined:
            self.undefined_steps = []
        else:
            self.undefined_steps = None

    def wantDirectory( self, dirname ):
        if not os.path.exists( os.path.join( dirname, ".freshenignore" ) ):
            return True
        return None

    def wantFile( self, filename ):
        return filename.endswith( ".feature" ) or None

    def loadTestsFromFile( self, filename, indexes = [] ):
        log.debug( "Loading from file %s" % filename )

        step_registry = StepImplRegistry( TagMatcher )
        try:
            feat = load_feature( filename, self.language )
            path = os.path.dirname( filename )
        except ParseException, e:
            ec, ev, tb = sys.exc_info()
            yield ParseFailure( e, tb, filename )
            return

        try:
            self.impl_loader.load_steps_impl( step_registry, path, feat.use_step_defs )
        except StepImplLoadException, e:
            yield StepsLoadFailure( *e.exc, address = TestAddress( filename ) )
            return

        cnt = 0
        ctx = FeatureSuite( filename, indexes )
        for i, sc in enumerate( feat.iter_scenarios() ):
            if ( not indexes or ( i + 1 ) in indexes ):
                if self.tagmatcher.check_match( sc.tags + feat.tags ):
                    yield FreshenTestCase( StepsRunner( step_registry ), step_registry, feat, sc, ctx )
                    cnt += 1

        if not cnt:
            yield False

    def loadTestsFromName( self, name, _ = None ):
        log.debug( "Loading from name %s" % name )

        if not self._is_file_with_indexes( name ):
            return # let nose take care of it

        name_without_indexes, indexes = self._split_file_in_indexes( name )

        if not os.path.exists( name_without_indexes ):
            return

        if os.path.isfile( name_without_indexes ) \
           and name_without_indexes.endswith( ".feature" ):
            for tc in self.loadTestsFromFile( name_without_indexes, indexes ):
                yield tc

    def _is_file_with_indexes( self, name ):
        drive, tail = os.path.splitdrive( name )
        if ":" not in tail:
            return False
        else:
            return True

    def _split_file_in_indexes( self, name_with_indexes ):
        drive, tail = os.path.splitdrive( name_with_indexes )
        parts = tail.split( ":" )
        name_without_indexes = drive + parts.pop( 0 )
        indexes = []
        try:
            indexes = set( int( p ) for p in parts )
        except ValueError:
            pass
        return ( name_without_indexes, indexes )

    def describeTest( self, test ):
        if isinstance( test.test, FreshenTestCase ):
            return test.test.description

    def formatFailure( self, test, err ):
        if hasattr( test, 'test' ) and isinstance( test.test, FreshenTestCase ):
            ec, ev, tb = err
            if ec is ExceptionWrapper and isinstance( ev, Exception ):
                orig_ec, orig_ev, orig_tb = ev.e
                message = "%s\n\n%s" % ( str( orig_ev ), self._formatSteps( test, ev.step ) )
                return ( orig_ec, message, orig_tb )
            elif not ec is UndefinedStepImpl and hasattr( test.test, 'last_step' ):
                message = "%s\n\n%s" % ( str( ev ), self._formatSteps( test, test.test.last_step ) )
                return ( ec, message, tb )

    formatError = formatFailure

    def prepareTestResult( self, result ):
        # Patch the result handler with an addError method that saves
        # UndefinedStepImpl exceptions for reporting later.
        if self.undefined_steps is not None:
            plugin = self
            def _addError( self, test, err ):
                ec, ev, tb = err
                if isclass( ec ) and issubclass( ec, UndefinedStepImpl ):
                    plugin.undefined_steps.append( ( test, ec, ev, tb ) )
                self._old_addError( test, err )
            result._old_addError = result.addError
            result.addError = instancemethod( _addError, result, result.__class__ )

    def report( self, stream ):
        if self.undefined_steps:
            stream.write( "======================================================================\n" )
            stream.write( "Tests with undefined steps\n" )
            stream.write( "----------------------------------------------------------------------\n" )
            for test, ec, ev, tb in self.undefined_steps:
                stream.write( self._formatSteps( test, ev.step, False ) + "\n\n" )
            stream.write( "You can implement step definitions for the missing steps with these snippets:\n\n" )
            uniq_steps = set( s[2].step for s in self.undefined_steps )
            for step in uniq_steps:
                stream.write( '@%s(r"^%s$")\n' % ( self.language.words( step.step_type )[0],
                                                 step.match ) )
                stream.write( 'def %s_%s():\n' % ( step.step_type,
                                                 re.sub( '[^\w]', '_', step.match ).lower() ) )
                stream.write( '    # code here\n\n' )

    def _formatSteps( self, test, failed_step, failure = True ):
        ret = []
        ret.append( FreshenPrettyPrint.feature( test.test.feature ) )
        ret.append( FreshenPrettyPrint.scenario( test.test.scenario ) )
        found = False
        for step in test.test.scenario.iter_steps():
            if step == failed_step:
                found = True
                if failure:
                    ret.append( FreshenPrettyPrint.step_failed( step ) )
                else:
                    ret.append( FreshenPrettyPrint.step_undefined( step ) )
            elif found:
                ret.append( FreshenPrettyPrint.step_notrun( step ) )
            else:
                ret.append( FreshenPrettyPrint.step_passed( step ) )
        return "\n".join( ret )

