""" 
Stream Parser 
=============
This module handles the Simulation response converting it into proper formats for querying data afterwards. 

The parser object converts a request from the simulator into the correct format for the 
"""

# ============================================================================
# STANDARD  IMPORTS
# ============================================================================

from xmltodict import parse
from xml.parsers.expat import ExpatError
from ctypes import create_string_buffer
from typing import Union, Dict, List, Tuple

# ============================================================================
# INTERNAL IMPORTS
# ============================================================================

from symupy.logic.publisher import Publisher
from symupy.components import Vehicle, VehicleList
import symupy.utils.constants as ct

# ============================================================================
# CLASS AND DEFINITIONS
# ============================================================================

vtypes = Union[float, int, str]
vdata = Tuple[vtypes]
vmaps = Dict[str, vtypes]
vlists = List[vmaps]


class SimulatorRequest(Publisher):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._str_response = create_string_buffer(ct.BUFFER_STRING)
        self._vehs = []

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __str__(self):
        return (
            "Sim Time: {}, VehInNetwork: {}".format(
                self.current_time, self.current_nbveh
            )
            if self.data_query
            else "Simulation has not started"
        )

    @property
    def query(self):
        """String response from the simulator"""
        return self._str_response

    @query.setter
    def query(self, response: str):
        self._str_response = response

    @property
    def data_query(self):
        try:
            dataveh = parse(self._str_response)
            # Transform ordered dictionary into new keys
            return dataveh
        except ExpatError:
            return {}
        except AttributeError:
            return {}

    # def parse_data(self, response: str = None) -> dict:
    #     """Parses response from simulator to data

    #     :param response: Simulator response
    #     :type response: str
    #     :return: Full simulator response
    #     :rtype: dict
    #     """
    #     self._str_response = response

    def get_vehicle_data(self) -> vlists:
        """ Extracts vehicles information from simulators response

            Returns:
                t_veh_data (list): list of dictionaries containing vehicle data with correct formatting

        """
        if self.data_query.get("INST", {}).get("TRAJS") is not None:
            veh_data = self.data_query.get("INST").get("TRAJS")
            if isinstance(veh_data["TRAJ"], list):
                return [SimulatorRequest.transform(d) for d in veh_data["TRAJ"]]
            return [SimulatorRequest.transform(veh_data["TRAJ"])]
        return []

    @staticmethod
    def transform(veh_data: dict):
        """ Transform vehicle data from string format to coherent format

            Args: 
                veh_data (dict): vehicle data as received from simulator

            Returns:
                t_veh_data (dict): vehicle data with correct formatting 


            Example: 
                As an example, for an input of the following style 

                >>> v = OrderedDict([('@abs', '25.00'), ('@acc', '0.00'), ('@dst', '25.00'), ('@id', '0'), ('@ord', '0.00'), ('@tron', 'Zone_001'), ('@type', 'VL'), ('@vit', '25.00'), ('@voie', '1'),('@z', '0')])
                >>> tv = SimulatorRequest.transform(v)
                >>> # Transforms into 
                >>> tv == {
                >>>     "abscissa": 25.0,
                >>>     "acceleration": 0.0,
                >>>     "distance": 25.0,
                >>>     "elevation": 0.0,
                >>>     "lane": 1,
                >>>     "link": "Zone_001",
                >>>     "ordinate": 0.0,
                >>>     "speed": 25.0,
                >>>     "vehid": 0,
                >>>     "vehtype": "VL",
                >>> },

        """
        
        return {
            ct.FIELD_DATA[key]: ct.FIELD_FORMAT[key](val)
            for key, val in veh_data.items()
        }

    def get_vehicles_property(self, property: str) -> vdata:
        """ Extracts a specific property and returns a tuple containing this 
            property for all vehicles in the buffer string

            Args: 
                property (str): 
                    one of the following options abscissa, acceleration, distance, elevation, lane, link, ordinate, speed, vehid, vehtype, 
            
            Returns:
                values (tuple):
                    tuple with corresponding values e.g (0,1), (0,),(None,)
        """
        return tuple(veh.get(property) for veh in self.get_vehicle_data())

    def filter_vehicle_property(self, property: str, *args):
        """ Filter out a property for a subset of vehicles
            
            Args:
                property (str): 
                    one of the following options abscissa, acceleration, distance, elevation, lane, link, ordinate, speed, vehid, vehtype, 

                vehids (int): 
                    separate the ``vehid`` via commas to get the corresponding property
        """
        if args:
            sargs = set(args)
            vehids = set(self.get_vehicles_property("vehid"))
            fin_ids = vehids.intersection(sargs)
            return tuple(
                veh.get(property)
                for veh in self.get_vehicle_data()
                if veh.get("vehid") in fin_ids
            )
        return self.get_vehicles_property(property)

    # def query_vehicle_link(self, vehid: str, *args) -> tuple:
    #     """ Extracts current vehicle link information from simulators response

    #     :param vehid: vehicle id multiple arguments accepted
    #     :type vehid: str
    #     :return: vehicle link in tuple form
    #     :rtype: tuple
    #     """
    #     vehids = set((vehid, *args)) if args else vehid
    #     vehid_pos = self.query_vehicle_data_dict("@tron", vehids)
    #     return tuple(vehid_pos.get(veh) for veh in vehids)

    # def query_vehicle_position(self, vehid: str, *args) -> tuple:
    #     """ Extracts current vehicle distance information from simulators response

    #     :param vehid: vehicle id multiple arguments accepted
    #     :type vehid: str
    #     :return: vehicle distance in link in tuple form
    #     :rtype: tuple
    #     """
    #     vehids = set((vehid, *args)) if args else vehid
    #     vehid_pos = self.query_vehicle_data_dict("@dst", vehids)
    #     return tuple(vehid_pos.get(veh) for veh in vehids)

    # def query_vehicle_data_dict(self, dataval: str, vehid: str, *args) -> dict:
    #     """ Extracts and filters vehicle data from the simulators response

    #         :param dataval: parameter to be extracted e.g. '@id', '@dst'
    #         :type dataval: str
    #         :param vehid: vehicle id, multiple arguments accepted
    #         :type vehid: str
    #         :return: dictionary where key is @id and value is dataval
    #         :rtype: dict
    #     """
    #     vehids = set((vehid, *args)) if args else set(vehid)
    #     data_vehs = [
    #         (veh.get("@id"), veh.get(dataval))
    #         for veh in self.get_vehicle_data()
    #         if veh.get("@id") in vehids
    #     ]
    #     return dict(data_vehs)

    def is_vehicle_in_network(self, vehid: str, *args) -> bool:
        """ True if veh id is in the network at current state, for multiple
            arguments. True if all veh ids are in the network.

            Args: 
                vehid (int): Integer of vehicle id, comma separated if testing for multiple 

            Returns: 
                present (bool): True if vehicle is in the network otherwise false.
  
        """
        all_vehs = self.get_vehicles_property("vehid")
        if not args:
            return vehid in all_vehs
        vehids = set((vehid, *args))
        return set(vehids).issubset(set(all_vehs))

    def vehicles_in_link(self, link: str, lane: int = 1) -> vdata:
        """ Returns a tuple containing vehicle ids traveling on the same 
            (link,lane) at current state

            Args: 
                link (str): link name 
                lane (int): lane number 

            Returns: 
                vehs (tuple): set of vehicles in link/lane

        """
        return tuple(
            veh.get("vehid")
            for veh in self.get_vehicle_data()
            if veh.get("link") == link and veh.get("lane") == lane
        )

    def is_vehicle_in_link(self, veh: int, link: str) -> bool:
        """ Returns true if a vehicle is in a link at current state
        
            Args: 
                vehid (int): vehicle id
                link (str): link name 

            Returns: 
                present (bool): True if veh is in link 

        """
        veh_ids = self.vehicles_in_link(link)
        return set(veh).issubset(set(veh_ids))

    def is_vehicle_driven(self, vehid: str) -> bool:
        """ Returns true if the vehicle state is exposed to a driven state

            Args:
                vehid (str):
                    vehicle id
        """
        if self.is_vehicle_in_network(vehid):

            forced = tuple(
                veh.get("@etat_pilotage") == "force (ecoulement respecte)"
                for veh in self.get_vehicle_data()
                if veh.get("@id") == vehid
            )
            return any(forced)
        return False

    def vehicle_downstream_of(self, vehid: str) -> tuple:
        """Get ids of vehicles downstream to vehid

        :param vehid: integer describing id of reference veh
        :type vehid: int
        :return: tuple with ids of vehicles ahead (downstream)
        :rtype: tuple
        """
        link = self.query_vehicle_link(vehid)[0]
        vehpos = self.query_vehicle_position(vehid)[0]

        vehids = set(self.vehicle_in_link(link))
        neigh = vehids.difference(set(vehid))

        neighpos = self.query_vehicle_position(*neigh)

        return tuple(
            nbh
            for nbh, npos in zip(neigh, neighpos)
            if float(npos) > float(vehpos)
        )

    def vehicle_upstream_of(self, vehid: str) -> tuple:
        """Get ids of vehicles upstream to vehid

        :param vehid: integer describing id of reference veh
        :type vehid: int
        :return: tuple with ids of vehicles behind (upstream)
        :rtype: tuple
        """
        link = self.query_vehicle_link(vehid)[0]
        vehpos = self.query_vehicle_position(vehid)[0]

        vehids = set(self.vehicle_in_link(link))
        neigh = vehids.difference(set(vehid))

        neighpos = self.query_vehicle_position(*neigh)

        return tuple(
            nbh
            for nbh, npos in zip(neigh, neighpos)
            if float(npos) < float(vehpos)
        )

    def create_vehicle_list(self):
        """Initialize 
        """
        if not self._vehs:
            self._vehs = VehicleList.from_request(self.get_vehicle_data())
            return

    def update_vehicle_list(self):
        """ Construct and or update vehicle data
        """
        if self._vehs:
            self._vehs.update_list(self.get_vehicle_data())
            return
        self.create_vehicle_list()

    def __contains__(self, elem: Vehicle) -> bool:
        return elem in self._vehs

    @property
    def vehicles(self):
        self.update_vehicle_list()
        return self._vehs

    @property
    def current_time(self) -> str:
        return self.data_query.get("INST").get("@val")

    @property
    def current_nbveh(self) -> int:
        return self.data_query.get("INST").get("@nbVeh")
