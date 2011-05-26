Using steps: 'tag_steps'

@first_feature_tag
@second_feature_tag
Feature: scenario and feature tags trigger before and after hooks in appropriate order
  In order to drive design and implementation by code behavior 
  As a freshen user
  I want tags to trigger before and after hooks in the apropriate order

@first_scenario_tag
@second_scenario_tag
Scenario: hooks are executed in appropriate order
  When this is executed, tag hooks are wrapped around in lifo order

@first_scenario_tag
@second_scenario_tag
Scenario: feature tag hooks are wrapped around each scenario
  When this is executed, tag hooks are wrapped around in lifo order