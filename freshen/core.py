#-*- coding: utf8 -*-

# This line ensures that frames from this file will not be shown in tracebacks
__unittest = 1

import inspect
import os
import yaml

from freshen.context import *
from freshen.parser import parse_steps, parse_file


class StepsRunner( object ):

    def __init__( self, step_registry ):
        self.step_registry = step_registry

    def run_steps_from_string( self, spec, language_name = 'en' ):
        """ Called from within step definitions to run other steps. """

        caller = inspect.currentframe().f_back
        line = caller.f_lineno - 1
        fname = caller.f_code.co_filename

        steps = parse_steps( spec, fname, line, load_language( language_name ) )
        for s in steps:
            self.run_step( s )

    def run_step( self, step ):
        step_impl, args = self.step_registry.find_step_impl( step )
        if step.arg is not None:
            return step_impl.run( step.arg, *args )
        else:
            return step_impl.run( *args )


class TagMatcher( object ):
    '''
    matches hook tags with tags from scenario or feature.
    
    Note that the latter are :class:`freshen.parser.Tag` objects.
    '''

    def __init__( self, tags ):
        self.include_tags = set( t.lstrip( "@" ) for t in tags if not t.startswith( "~" ) )
        self.exclude_tags = set( t.lstrip( "~@" ) for t in tags if t.startswith( "~" ) )

    def get_matching_set( self, tagset ):
        tagset = set( tagset )
        if tagset & self.exclude_tags:
            return set()
        if not self.include_tags:
            return tagset
        # include_tags are strings, whereas tagset are Tags,
        # which we want to return, so we cant use set intersection
        return set( t for t in tagset if t in self.include_tags )

    def check_match( self, tagset ):
        '''
        check whether a concrete set of tags from feature or scenario
        match the ones of this TagMatcher.
        
        There is a match if, after excluding, the remaining
        tags are a superset of the include tags.
        '''
        if not tagset and not self.include_tags: return True
        return len( self.get_matching_set( tagset ) ) >= len( self.include_tags )

    def get_min_order( self, tagset ):
        '''
        return the minimal order from matching tags.
        
        Is an error if there are no matching tags.
        '''
        matching = self.get_matching_set( tagset )
        return min( tag.order for tag in matching )


class Language( object ):
    def __init__( self, mappings, default_mappings = None ):
        self.mappings = mappings
        self.default_mappings = default_mappings

    def words( self, key ):
        """
        Give all the synonymns of a word in the requested language 
        (or the default language if no word is available).
        """
        if self.default_mappings is not None and key not in self.mappings:
            return self.default_mappings[key].encode( 'utf' ).split( "|" )
        else:
            return self.mappings[key].encode( 'utf' ).split( "|" )


def load_feature( fname, language ):
    """ Load and parse a feature file. """

    fname = os.path.abspath( fname )
    feat = parse_file( fname, language )
    return feat

def load_language( language_name, default_language_name = "en" ):
    directory, _f = os.path.split( os.path.abspath( __file__ ) )
    language_path = os.path.join( directory, 'languages.yml' )
    languages = yaml.load( open( language_path ) )
    if language_name not in languages:
        return None
    return Language( languages[language_name], languages[default_language_name] )

def run_steps( spec, language = "en" ):
    """ Can be called by the user from within a step definition to execute other steps. """

    # The way this works is a little exotic, but I couldn't think of a better way to work around
    # the fact that this has to be a global function and therefore cannot know about which step
    # runner to use (other than making step runner global)

    # Find the step runner that is currently running and use it to run the given steps
    fr = inspect.currentframe()
    while fr:
        if "self" in fr.f_locals:
            f_self = fr.f_locals['self']
            if isinstance( f_self, StepsRunner ):
                return f_self.run_steps_from_string( spec, language )
        fr = fr.f_back



