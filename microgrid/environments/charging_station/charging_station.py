from typing import Optional, Union, Tuple

import gym
import numpy as np
from gym import spaces
from gym.core import ObsType, ActType

import datetime

from microgrid.assets.battery import BatteryState
from microgrid.assets.ev import EV


class ChargingStationEnv(gym.Env):
    def __init__(self, evs_config: [dict], nb_pdt=24, seed: Optional[int] = None):
        self.evs_config = evs_config
        self.nb_pdt = nb_pdt
        self.nb_evs = len(evs_config)
        self.evs = [EV(**ev_config) for ev_config in evs_config]

        self.observation_space = spaces.Dict(
            {
                'datetime': spaces.Space[datetime.datetime]((), np.datetime64, seed),
                'manager_signal': spaces.Box(low=-np.inf, high=np.inf, shape=(nb_pdt,)),
                'soc': spaces.Box(low=0.0, high=np.array([ev.battery.capacity for ev in self.evs]), shape=(self.nb_evs, )),
                'is_plugged_prevision': spaces.Box(low=0.0, high=1.0, shape=(self.nb_evs, nb_pdt)),
            }
        )
        low = np.array([[ev.battery.pmin for ev in self.evs] for _ in range(nb_pdt)]).transpose()
        high = np.array([[ev.battery.pmax for ev in self.evs] for _ in range(nb_pdt)]).transpose()
        self.action_space = spaces.Box(low=low, high=high, shape=(self.nb_evs, nb_pdt))
        self.now = None
        self.delta_t = None
        self.n_coord_step = None

    def step(self, action: ActType) -> Tuple[ObsType, float, bool, dict]:
        effective_powers = []
        penalties = []
        socs = []
        for ev, action_ev in zip(self.evs, action[0, :]):
            soc, effective_power, penalty = ev.charge(action_ev, delta_t=self.delta_t)
            socs.append(soc)
            effective_powers.append(effective_power)
            penalties.append(penalty)
        self.now += self.delta_t
        return self._step_common(effective_powers, penalties)

    def try_step(self, action: ActType) -> Tuple[ObsType, float, bool, dict]:
        effective_powers = []
        penalties = []
        for ev, action_ev in zip(self.evs, action[0, :]):
            effective_power, penalty = ev.check_power(action_ev, delta_t=self.delta_t)
            effective_powers.append(effective_power)
            penalties.append(penalty)
        return self._step_common(effective_powers, penalties)

    def _step_common(self, effective_powers, penalties) -> Tuple[ObsType, float, bool, dict]:
        state = {
            'datetime': self.now,
            'manager_signal': np.zeros(self.nb_pdt),
            'soc': np.array([ev.get_soc(self.now) for ev in self.evs]),
            'is_plugged_prevision': np.array([ev.get_is_plugged_prevision([self.now + i * self.delta_t for i in range(self.nb_pdt)]) for ev in self.evs]),
        }
        reward = 0 if all(penalty == BatteryState.OK for penalty in penalties) else -1e5
        return state, reward, False, {'reward': reward, 'penalties': penalties, 'effective_action': effective_powers, 'soc': [ev.battery.soc for ev in self.evs], 'datetime': self.now}

    def reset(self, *args, seed: Optional[int] = None, return_info: bool = False, options: Optional[dict] = None)\
            -> Union[ObsType, Tuple[ObsType, dict]]:
        self.now, self.delta_t = tuple(args)
        for ev in self.evs:
            ev.reset()
        state = {
            'datetime': self.now,
            'manager_signal': np.zeros(self.nb_pdt),
            'soc': np.array([ev.get_soc(self.now) for ev in self.evs]),
            'is_plugged_prevision': np.array([ev.get_is_plugged_prevision([self.now + i * self.delta_t for i in range(self.nb_pdt)]) for ev in self.evs]),
        }
        return state

    def get_consumption(self, _: ObsType,  action: ActType) -> np.ndarray:
        return action.sum(axis=0)

    def render(self, mode="human"):
        pass

