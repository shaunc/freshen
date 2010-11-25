Using step definitions from: "combination_steps"

Feature: combinatorial testing
  In order to test combinations of test parameters
  As a python developer
  I want to join tables together to test all cross-products of their rows
  

# runs twice
Scenario Outline: normal scenario outline
  When <a> likes <b>
  And <c> likes <b>
  Then <b> is liked by 2 people
Examples:
  | a    | b       | c   |
  | bob  | alice   | sam |
  | jill | theresa | sue |

# runs 4 times

Scenario Outline: all-pairs testing
  When <a> likes <c>
  And <b> likes <c>
  Then <c> is liked by 2 people
Examples:
  | a    | b       |
  | bob  | alice   |
  | jill | theresa |
Joined With:
  | c     |
  | sam   |
  | sue   |


# runs 8 times
  
Scenario Outline: triples testing
  When <a> likes <c>
  And <b> likes <c>
  Then <c> is liked by 2 people
Examples:
  | a    |
  | bob  |
  | jill |
Joined With:
  | b       |
  | alice   |
  | theresa |
Joined With:
  | c     |
  | sam   |
  | sue   |

Scenario: joins are also possible with inline tables
  When these pairs like c:
  | a    | b       |
  | bob  | alice   |
  | jill | theresa |
  Joined With:
  | c     |
  | sam   |
  | sue   |
  Then sam is liked by 4 people
  Then sue is liked by 4 people
  