Feature: befriending many

    Scenario: befriending many people
        When user duane befriends user adelaide
        And user duane befriends user hazel
        And user hazel befriends user adelaide
        Then these users should be friends: users duane, hazel and adelaide

    Scenario: befriending a list of people
 		When user adelaide befriends: user paxton, hazel and duane
        Then user adelaide should be friends with user paxton
        And user adelaide should be friends with user hazel
        And user adelaide should be friends with user duane
