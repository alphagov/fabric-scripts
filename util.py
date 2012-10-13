import random

from fabric.api import env

def use_random_host(role):
    """Use a randomly chosen host from the given role"""
    env.host_string = random.choice(env.roledefs[role])
