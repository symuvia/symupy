# ============================================================================
# STANDARD  IMPORTS
# ============================================================================

import pandas as pd
import os

# ============================================================================
# INTERNAL IMPORTS
# ============================================================================

from symupy.tsc.journey import Path, State, Trip
from symupy.utils.exceptions import SymupyWarning
from symupy.utils.time import Date
from symupy.abstractions.reader import AbstractTrafficDataReader

# ============================================================================
# CLASS AND DEFINITIONS
# ============================================================================



class SymuMasterPPathsReader(AbstractTrafficDataReader):
    _ext = 'csv'
    def __init__(self, ppaths, final_ppaths, distribution):
        self._file_ppaths = ppaths

        self.ppaths = pd.read_csv(self._file_ppaths, sep=';', index_col=False, header=None, engine='python')


    def get_OD(self, OD, period=None, loop=None, file='distribution'): #Both ppaths and distribution
        paths = list()
        for row in self.ppaths.iterrows():
            try:
                path = row[1][7].split('\\')
                readLine = True
                if 'Area Pattern' in path:
                    readLine &= path[2]==OD[0] and path[-3]==OD[1]
                    path = path[3:-3][::2]
                else:
                    readLine &= path[0]==OD[0] and path[-1]==OD[1]
                    path = path[1:-1][::2]

                if period is not None:
                    readLine &= int(row[1][0])==period

                if loop is not None:
                    readLine &= int(row[1][1])==loop[0] and int(row[1][2])==loop[1]

                if readLine:
                    p = Path(path)
                    paths.append(p)
            except AttributeError:
                pass

        return paths


class SymuMasterFinalPPathsReader(AbstractTrafficDataReader):
    _ext = 'csv'
    def __init__(self, final_ppaths):
        self._file_final_ppaths = final_ppaths
        self.final_ppaths = pd.read_csv(self._file_final_ppaths, sep=';', index_col=False, engine='python', header=None)

    def get_path(self, userid):
        row = self.final_ppaths[self.final_ppaths.iloc[:,3]==float(userid)]
        path = row[7].to_list()[0].split('\\')
        path = [p for p in path[1:-1][::2] if p!='Area Pattern']
        return Path(path[1:-1][::2])

    def get_trip(self, userid):
        row = self.final_ppaths[self.final_ppaths.iloc[:,3]==float(userid)]
        path = row[7].to_list()[0].split('\\')
        origin = path[0]
        dest = path[-1]
        departure_time = Date(row[4].to_list()[0])
        if row[5].to_list()[0] == 'Undefined':
            arrival_time = 'Undefined'
        else:
            arrival_time = Date(row[5].to_list()[0])

        return Trip(path=Path(path[1:-1][::2]),
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    origin=origin,
                    destination=dest,
                    vehicle=userid)



class SymuMasterDistributionReader(AbstractTrafficDataReader):
    _ext = 'csv'
    def __init__(self, distribution):
        self._file_distribution = distribution

        self.distribution = pd.read_csv(self._file_distribution, sep=';', index_col=False, engine='python', header=None, skiprows=1)


    def get_OD(self, OD, period=None, loop=None): #Both ppaths and distribution
        paths = list()

        mask = (self.distribution.iloc[:,4]==OD[0]) & (self.distribution.iloc[:,5]==OD[1]) & (self.distribution.iloc[:,8]!='Sum of user and minimum travel time for the OD')
        if period is not None:
            mask &= (self.distribution.iloc[:,0].astype(int)==period)
        if loop is not None:
            mask &= (self.distribution.iloc[:,1].astype(int)==loop[0]) & (self.distribution.iloc[:,2].astype(int)==loop[1])
        rows = self.distribution[mask]


        for row in rows.iterrows():
            p = Path(row[1][8].split("\\")[4:-4][::2])
            paths.append(p)

        return paths


if __name__ == '__main__':
    fileppaths = '/Users/florian.gacon/Work/data/LYON63V/default_PPaths.csv'
    filefinal = '/Users/florian.gacon/Work/data/LYON63V/default_final_PPaths.csv'
    filedistrib = '/Users/florian.gacon/Work/data/LYON63V/default_distribution.csv'

    reader = SymuMasterTrafficDataReader(fileppaths, filefinal, filedistrib)
    # reader.load_distribution()
    reader.load_ppaths()

    # t = reader.get_OD(('690340602', '692660103'))
    t = reader.get_OD(('C_702719926', 'C_82613196'), 0, file='ppaths')
