import datetime
from microgrid.environments.charging_station.charging_station import ChargingStationEnv


class ChargingStationAgent:
    def __init__(self, env: ChargingStationEnv):
        self.env = env

    def take_decision(self, state):
        return self.env.action_space.sample()


if __name__ == "__main__":
    delta_t = datetime.timedelta(minutes=15)
    time_horizon = datetime.timedelta(days=1)
    N = time_horizon // delta_t
    evs_config = [
        {
            'capacity': 50,
            'pmax': 7,
        }
    ]
    env = ChargingStationEnv(evs_config=evs_config, nb_pdt=N)
    agent = ChargingStationAgent(env)
    cumulative_reward = 0
    now = datetime.datetime.now()
    state = env.reset(now, delta_t)
    for i in range(N*2):
        action = agent.take_decision(state)
        state, reward, done, info = env.step(action)
        cumulative_reward += reward
        if done:
            break
        print(f"action: {action}, reward: {reward}, cumulative reward: {cumulative_reward}")
        print("State: {}".format(state))
        print("Info: {}".format(action.sum(axis=0)))