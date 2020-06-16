from collections import deque
from enum import Enum

import cv2
import gym
import numpy as np
from gym import spaces

class EnvironmentWrapper(Enum):
    KEEP_ORIGINAL_OBSERVATION = "keep-original-observation"

    ATARI = "atari", # Contains NOOP_RESET and MAX_AND_SKIP
    NOOP_RESET = "noop-reset-env",
    MAX_AND_SKIP = "max-and-skip-env",

    DEEP_MIND = "deep-mind", # Contains EPISODIC_LIFE, FIRE_RESET, WARP_FRAME and CLIP_REWARD
    EPISODIC_LIFE = "episodic-life",
    FIRE_RESET = "fire-reset",
    WARP_FRAME = "warp-frame",
    CLIP_REWARD = "clip-reward",
    FRAME_STACK = "frame-stack",

    PYTORCH = "pytorch" # Contains IMAGE_TO_PYTORCH
    IMAGE_TO_PYTORCH = "image-to-pytorch"


class EnvironmentBuilder:
    """
    Builds environment and wraps it optionally
    See https://github.com/openai/baselines/blob/master/baselines/common/atari_wrappers.py
    """

    def make_environment(environment_id):
        return gym.make(environment_id)

    def make_environment_with_wrappers(environment_id, wrappers):
        env = gym.make(environment_id)

        for w in wrappers:
            if w == EnvironmentWrapper.KEEP_ORIGINAL_OBSERVATION:
                env = KeepOriginalObservationEnv(env)

            if w == EnvironmentWrapper.ATARI:
                env = NoopResetEnv(env, noop_max=30)
                env = MaxAndSkipEnv(env, skip=4)
            if w == EnvironmentWrapper.NOOP_RESET:
                env = NoopResetEnv(env, noop_max=30)
            if w == EnvironmentWrapper.MAX_AND_SKIP:
                env = MaxAndSkipEnv(env, skip=4)

            if w == EnvironmentWrapper.DEEP_MIND:
                env = EpisodicLifeEnv(env)
                if 'FIRE' in env.unwrapped.get_action_meanings():
                    env = FireResetEnv(env)
                env = WarpFrameEnv(env)
                env = ClipRewardEnv(env)
                env = FrameStack(env, k=4)
            if w == EnvironmentWrapper.EPISODIC_LIFE:
                env = EpisodicLifeEnv(env)
            if w == EnvironmentWrapper.FIRE_RESET:
                if 'FIRE' in env.unwrapped.get_action_meanings():
                    env = FireResetEnv(env)
            if w == EnvironmentWrapper.WARP_FRAME:
                env = WarpFrameEnv(env)
            if w == EnvironmentWrapper.CLIP_REWARD:
                env = ClipRewardEnv(env)
            if w == EnvironmentWrapper.FRAME_STACK:
                env = FrameStack(env, k=4)

            if w == EnvironmentWrapper.PYTORCH:
                env = ImageToPyTorchEnv(env)
            if w == EnvironmentWrapper.IMAGE_TO_PYTORCH:
                env = ImageToPyTorchEnv(env)

        return env

class KeepOriginalObservationEnv(gym.ObservationWrapper):
    """
    Keeps original observation which may be distorted in other environment wrappers
    """
    def __init__(self, env):
        gym.ObservationWrapper.__init__(self, env)

    def observation(self, observation):
        self.original_observation = observation
        return observation

class NoopResetEnv(gym.Wrapper):
    def __init__(self, env, noop_max=30):
        """Sample initial states by taking random number of no-ops on reset.
        No-op is assumed to be action 0.
        """
        gym.Wrapper.__init__(self, env)
        self.noop_max = noop_max
        self.override_num_noops = None
        self.noop_action = 0
        assert env.unwrapped.get_action_meanings()[0] == 'NOOP'

    def reset(self, **kwargs):
        """ Do no-op action for a number of steps in [1, noop_max]."""
        self.env.reset(**kwargs)
        if self.override_num_noops is not None:
            noops = self.override_num_noops
        else:
            noops = self.unwrapped.np_random.randint(1, self.noop_max + 1)  # pylint: disable=E1101
        assert noops > 0
        obs = None
        for _ in range(noops):
            obs, _, done, _ = self.env.step(self.noop_action)
            if done:
                obs = self.env.reset(**kwargs)
        return obs

    def step(self, ac):
        return self.env.step(ac)

class MaxAndSkipEnv(gym.Wrapper):
    def __init__(self, env, skip=4):
        """Return only every `skip`-th frame"""
        gym.Wrapper.__init__(self, env)
        # most recent raw observations (for max pooling across time steps)
        self._obs_buffer = np.zeros((2,) + env.observation_space.shape, dtype=np.uint8)
        self._skip = skip

    def reset(self):
        return self.env.reset()

    def step(self, action):
        """Repeat action, sum reward, and max over last observations."""
        total_reward = 0.0
        done = None
        for i in range(self._skip):
            obs, reward, done, info = self.env.step(action)
            if i == self._skip - 2: self._obs_buffer[0] = obs
            if i == self._skip - 1: self._obs_buffer[1] = obs
            total_reward += reward
            if done:
                break
        # Note that the observation on the done=True frame
        # doesn't matter
        max_frame = self._obs_buffer.max(axis=0)

        return max_frame, total_reward, done, info

    def reset(self, **kwargs):
        return self.env.reset(**kwargs)

class FrameStack(gym.Wrapper):
    def __init__(self, env, k):
        """Stack k last frames.
        Returns lazy array, which is much more memory efficient.
        See Also
        --------
        baselines.lib.atari_wrappers.LazyFrames
        """
        gym.Wrapper.__init__(self, env)
        self.k = k
        self.frames = deque([], maxlen=k)
        shp = env.observation_space.shape
        self.observation_space = spaces.Box(low=0, high=255, shape=(shp[0], shp[1], shp[2] * k), dtype=np.uint8)

    def reset(self):
        ob = self.env.reset()
        for _ in range(self.k):
            self.frames.append(ob)
        return self._get_ob()

    def step(self, action):
        ob, reward, done, info = self.env.step(action)
        self.frames.append(ob)
        return self._get_ob(), reward, done, info

    def _get_ob(self):
        assert len(self.frames) == self.k
        return LazyFrames(list(self.frames))

class LazyFrames(object):
    def __init__(self, frames):
        """This object ensures that lib frames between the observations are only stored once.
        It exists purely to optimize memory usage which can be huge for DQN's 1M frames replay
        buffers.
        This object should only be converted to numpy array before being passed to the output.
        You'd not believe how complex the previous solution was."""
        self._frames = frames
        self._out = None

    def _force(self):
        if self._out is None:
            self._out = np.concatenate(self._frames, axis=2)
            self._frames = None
        return self._out

    def __array__(self, dtype=None):
        out = self._force()
        if dtype is not None:
            out = out.astype(dtype)
        return out

    def __len__(self):
        return len(self._force())

    def __getitem__(self, i):
        return self._force()[i]

    def count(self):
        frames = self._force()
        return frames.shape[frames.ndim - 1]

    def frame(self, i):
        return self._force()[..., i]

class EpisodicLifeEnv(gym.Wrapper):
    def __init__(self, env):
        """Make end-of-life == end-of-episode, but only reset on true game over.
        Done by DeepMind for the DQN and co. since it helps value estimation.
        """
        gym.Wrapper.__init__(self, env)
        self.lives = 0
        self.was_real_done = True

    def step(self, action):
        obs, reward, done, info = self.env.step(action)
        self.was_real_done = done
        # check current lives, make loss of life terminal,
        # then update lives to handle bonus lives
        lives = self.env.unwrapped.ale.lives()
        if lives < self.lives and lives > 0:
            # for Qbert sometimes we stay in lives == 0 condtion for a few frames
            # so its important to keep lives > 0, so that we only reset once
            # the environment advertises done.
            done = True
        self.lives = lives
        return obs, reward, done, info

    def reset(self, **kwargs):
        """Reset only when lives are exhausted.
        This way all states are still reachable even though lives are episodic,
        and the learner need not know about any of this behind-the-scenes.
        """
        if self.was_real_done:
            obs = self.env.reset(**kwargs)
        else:
            # no-op step to advance from terminal/lost life state
            obs, _, _, _ = self.env.step(0)
        self.lives = self.env.unwrapped.ale.lives()
        return obs

class FireResetEnv(gym.Wrapper):
    def __init__(self, env):
        """Take action on reset for environments that are fixed until firing."""
        gym.Wrapper.__init__(self, env)
        assert env.unwrapped.get_action_meanings()[1] == 'FIRE'
        assert len(env.unwrapped.get_action_meanings()) >= 3

    def reset(self, **kwargs):
        self.env.reset(**kwargs)
        obs, _, done, _ = self.env.step(1)
        if done:
            self.env.reset(**kwargs)
        obs, _, done, _ = self.env.step(2)
        if done:
            self.env.reset(**kwargs)
        return obs

    def step(self, ac):
        return self.env.step(ac)

class WarpFrameEnv(gym.ObservationWrapper):
    def __init__(self, env):
        """Warp frames to 84x84 as done in the Nature paper and later work."""
        gym.ObservationWrapper.__init__(self, env)
        self.width = 84
        self.height = 84
        self.observation_space = spaces.Box(low=0, high=255,
                                            shape=(self.height, self.width, 1), dtype=np.uint8)

    def observation(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_AREA)
        return frame[:, :, None]

class ClipRewardEnv(gym.RewardWrapper):
    def __init__(self, env):
        gym.RewardWrapper.__init__(self, env)

    def reward(self, reward):
        """Bin reward to {+1, 0, -1} by its sign."""
        return np.sign(reward)

class ImageToPyTorchEnv(gym.ObservationWrapper):
    """
    Image shape to num_channels x weight x height
    """

    def __init__(self, env):
        super(ImageToPyTorchEnv, self).__init__(env)
        old_shape = self.observation_space.shape
        self.observation_space = gym.spaces.Box(low=0.0, high=1.0, shape=(old_shape[-1], old_shape[0], old_shape[1]),
                                                dtype=np.uint8)

    def observation(self, observation):
        return np.swapaxes(observation, 2, 0)