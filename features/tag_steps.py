# -*- coding: utf-8 -*-
'''
.. _tag_steps:

:mod:`tag_steps`
======================================================

Step definitions (for `freshen`_ )

.. _freshen: http://github.com/shaunc/freshen/

'''
from nose.tools import *
from freshen import *
from freshen.checks import *

# ----------------------------------------------------------
# Scenario:
# ----------------------------------------------------------
def _push_tag( name, order, context ):
    if order == 0:
        assert not context.tag_stack
        context.tag_stack = []
    else:
        eq_( len( context.tag_stack ), order )
    context.tag_stack.append( name )
     
def _pop_tag( name, order, context ):
    eq_( len( context.tag_stack ), order )
    eq_( context.tag_stack.pop(), name )
     
@Before( '@first_feature_tag' )
def before_first_feature_tag( feature ):
    _push_tag( 'first_feature_tag', 0, ftc )
    _push_tag( 'first_feature_tag', 0, scc )
    
@Before( '@second_feature_tag' )
def before_second_feature_tag( feature ):
    _push_tag( 'second_feature_tag', 1, ftc )
    _push_tag( 'second_feature_tag', 1, scc )
    
@Before( '@first_scenario_tag' )
def before_first_scenario_tag( scenario ):
    _push_tag( 'first_scenario_tag', 2, scc )
    
@Before( '@second_scenario_tag' )
def before_second_scenario_tag( scenario ):
    _push_tag( 'second_scenario_tag', 3, scc )

@When( 'this is executed, tag hooks are wrapped around in lifo order' )
def tag_hooks_lifo():
    expected = [
        'first_feature_tag',
        'second_feature_tag',
        'first_scenario_tag',
        'second_scenario_tag',
        ]
    eq_( len( scc.tag_stack ), len( expected ) )
    eq_( len( ftc.tag_stack ), 2 )
    
    for a, b in zip( scc.tag_stack, expected ):
        eq_( a, b )
    for a, b in zip( ftc.tag_stack, expected ):
        eq_( a, b )
            
@After( '@second_scenario_tag' )
def after_second_scenario_tag( scenario ):
    _pop_tag( 'second_scenario_tag', 4, scc )            

@After( '@first_scenario_tag' )
def after_first_scenario_tag( scenario ):
    _pop_tag( 'first_scenario_tag', 3, scc )
            
@After( '@second_feature_tag' )
def after_second_feature_tag( feature ):
    _pop_tag( 'second_feature_tag', 2, ftc )
    _pop_tag( 'second_feature_tag', 2, scc )

@After( '@first_feature_tag' )
def after_first_feature_tag( feature ):
    _pop_tag( 'first_feature_tag', 1, ftc )
    _pop_tag( 'first_feature_tag', 1, scc )
    
    
    
