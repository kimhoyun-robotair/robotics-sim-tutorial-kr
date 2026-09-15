"""Run in Script Editor after enabling MobilityGen Examples; registers a slower Jetbot."""
from isaacsim.replicator.mobility_gen.examples.robots import JetbotRobot
from isaacsim.replicator.mobility_gen.impl.robot import ROBOTS


@ROBOTS.register()
class TutorialSlowJetbot(JetbotRobot):
    keyboard_linear_velocity_gain = 0.12
    gamepad_linear_velocity_gain = 0.12
    path_following_speed = 0.12
