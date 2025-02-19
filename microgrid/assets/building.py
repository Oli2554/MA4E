import datetime
import os
import pandas as pd
import numpy as np
from random import randint


class Building:
    @staticmethod
    def random():
        return Building(site=randint(1, 3), scenario=randint(1, 30))

    def __init__(self, site=1, scenario=1):
        self.site = site
        self.scenario = scenario
        self.data = pd.read_csv(os.path.join(os.path.dirname(__file__), f'scenarios/industrial/data.csv'), delimiter=';')

    def reset(self):
        self.scenario = randint(1, 30)

    def get_power(self, when: datetime.datetime, start: datetime.datetime):
        pdt = (when - datetime.datetime.fromordinal(start.date().toordinal())) // datetime.timedelta(minutes=30)
        scenario = self.scenario
        if pdt == 48:
            scenario = scenario % 30 + 1
        return self.data.query(f'site_id == {self.site} and scenario == {scenario} and time_slot == {pdt % 48 + 1}')['cons (kW)'].values[0]

    def get_conso_prevision(self, datetimes: [datetime.datetime]):
        res = []
        if len(datetimes) > 0:
            start = datetimes[0]
            res = np.array(list(map(lambda x: self.get_power(x, start), datetimes)))
            pdt = (start - datetime.datetime.fromordinal(start.date().toordinal())) // datetime.timedelta(minutes=15)
            if pdt == 24*4-1:
                self.scenario = self.scenario % 30 + 1
        return res


if __name__ == '__main__':
    b = Building(site=1)
    print(b.get_power(datetime.datetime.now()))
    print(b.get_conso_prevision([datetime.datetime.now(), datetime.datetime.now()+datetime.timedelta(minutes=15)]))
