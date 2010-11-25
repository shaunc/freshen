from freshen import *
from nose.tools import eq_

def get_person( p ):
    people = scc.people = scc.people or {}
    return people.setdefault( p, [] )

@When('^(\w+) likes (\w+)$')
def likes( a, b ):
    person = get_person( b )
    person.append( a )
    
@NamedTransform( '{int}', '(\d+)', '(\d+)' )
def transform_int( n ):
    return int( n )
    
@Then('^(\w+) is liked by {int} people')
def check_liked_by( p, n ):
    person = get_person( p )
    eq_( len( person ), n, 'person %s liked by %d' % ( p, len( person ) ) )
    
@When( 'these pairs like c:' )
def pairs_like_c( table ):
    for row in table.iterrows():
        likes( row[ 'a' ], row[ 'c' ] )
        likes( row[ 'b' ], row[ 'c' ] )
        
  
