from enum import Enum


class Environment(Enum):
    PONG_v0 = 'Pong-v0'
    PONG_v4 = 'Pong-v4'
    PONG_DETERMINISTIC_v0 = 'PongDeterministic-v0'
    PONG_DETERMINISTIC_v4 = 'PongDeterministic-v4'
    PONG_NO_FRAMESKIP_v0 = 'PongNoFrameskip-v0'
    PONG_NO_FRAMESKIP_v4 = 'PongNoFrameskip-v4'

    BREAKOUT_V0 = 'Breakout-v0'

    SPACE_INVADERS_V0 = 'SpaceInvaders-v0'

    CART_POLE_v0 = 'CartPole-v0'
