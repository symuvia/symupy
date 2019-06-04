import os
from ctypes import cdll, create_string_buffer, c_int, byref, c_bool, c_double
from lxml import etree
from datetime import datetime

from symupy.utils import SymupyLoadLibraryError
from symupy.utils import SymupyFileLoadError
from symupy.utils import SymupyVehicleCreationError
from symupy.utils import SymupyDriveVehicleError
from symupy.utils import SimulatorRequest
from symupy.utils import SymupyWarning
from symupy.utils import timer_func
from symupy.utils import constants as ct

import typing


class Simulation(object):

    def __init__(self, file_name: str) -> None:
        if os.path.exists(file_name):
            self._file_name = file_name
        else:
            raise SymupyFileLoadError("File not found", file_name)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.filename})"

    def load_xml_tree(self) -> None:
        """ Load XML file_name
        """
        # TODO: Add validation with DTD
        tree = etree.parse(self._file_name)
        root = tree.getroot()
        self._xml_tree = root

    def get_simulation_parameters(self) -> tuple:
        """ Get simulation parameters

        :return: tuple with XML dictionary containing parameters
        :rtype: tuple
        """
        self.load_xml_tree()
        branch_tree = 'SIMULATIONS'
        sim_params = self._xml_tree.xpath(branch_tree)[0].getchildren()
        return tuple(par.attrib for par in sim_params)

    def get_vehicletype_information(self) -> tuple:
        """ Get the vehicle parameters

        :return: tuple of dictionaries containing vehicle parameters
        :rtype: tuple
        """
        self.load_xml_tree()
        branch_tree = 'TRAFICS/TRAFIC/TYPES_DE_VEHICULE'
        vehicle_types = self._xml_tree.xpath(branch_tree)[0].getchildren()
        return tuple(v.attrib for v in vehicle_types)

    def get_network_endpoints(self) -> tuple:
        """ Get networks endpoint names

        :return: tuple containing endpoint names
        :rtype: tuple
        """
        self.load_xml_tree()
        branch_tree = 'TRAFICS/TRAFIC/EXTREMITES'
        end_points = self._xml_tree.xpath(branch_tree)[0].getchildren()
        return tuple(ep.attrib['id'] for ep in end_points)

    def get_network_links(self) -> tuple:
        """ Get network link names

        :return: tuple containing link names 
        :rtype: tuple
        """
        self.load_xml_tree()
        branch_tree = 'TRAFICS/TRAFIC/TRONCONS'
        links = self._xml_tree.xpath(branch_tree)[0].getchildren()
        return tuple(ep.attrib['id'] for ep in links)

    def get_simulation_steps(self, simid: int = 0) -> range:
        """Get simulation steps for an simulation. specify the simulation id  via an integer value

        :param simid: simulation id , defaults to 0
        :type simid: int, optional
        :return:
        :rtype: range
        """
        t1 = datetime.strptime(
            self.get_simulation_parameters()[simid].get('debut'), ct.HOUR_FORMAT)
        t2 = datetime.strptime(
            self.get_simulation_parameters()[simid].get('fin'), ct.HOUR_FORMAT)
        t = t2 - t1
        n = t.seconds / \
            float(self.get_simulation_parameters()
                  [simid].get('pasdetemps'))
        return range(int(n))

    def __contains__(self, value: tuple) -> bool:
        # REVIEW: Implement? in method? maybe useful
        raise NotImplementedError

    @property
    def get_xml(self):
        return self._xml_tree

    @property
    def filename(self):
        return self._file_name

    @property
    def filename_enc(self):
        return self._file_name.encode('UTF8')

# FIXME: This should be a property simid is something that cannot be totally controlled via api
    def sampling_time(self, simid: int = 0):
        return float(self.get_simulation_parameters()[simid].get('pasdetemps'))


class Simulator(object):

    def __init__(self, path: str) -> None:
        self._path = path

    def __repr__(self):
        return f"{self.__class__.__name__}({self.libraryname})"

    def load_symuvia(self) -> None:
        """ load SymuVia shared library """
        try:
            lib_symuvia = cdll.LoadLibrary(self._path)
        except OSError:
            raise SymupyLoadLibraryError("Library not found", self._path)
        self._library = lib_symuvia

    def load_network(self) -> None:
        """ load SymuVia Simulation File """
        if not hasattr(self, '_sim'):
            raise SymupyFileLoadError("File not provided", "")
        self._library.SymLoadNetworkEx(self._sim.filename_enc)

    def init_simulation(self) -> None:
        """ Initializes conditions for a step by step simulation"""
        # Pointers
        self._s_response = create_string_buffer(ct.BUFFER_STRING)
        self._b_end = c_int()
        self._b_trace = c_bool(False)
        # self._b_force = c_int(1)
        self.data = SimulatorRequest()

    @timer_func
    def run_simulation(self, sim_object: Simulation) -> None:
        """ Run simulation in a single shot

        Args:
            sim_object (Simulation): Valid simulation scenario

        Returns:
            None: No returns provided, only internal updates
        """
        self.register_simulation(sim_object)
        self.load_symuvia()
        self._library.SymRunEx(self._sim.filename_enc)

    def register_simulation(self, sim_object: Simulation) -> None:
        """Register simulation file within the simulator

        :param sim_object: Simulation scenario to register
        :type sim_object: Simulation
        :return: No value is returned
        :rtype: None
        """
        self._sim = sim_object

    def request_answer(self):
        """Request simulator answer and maps the data locally
        """
        self._bContinue = self._library.SymRunNextStepEx(self._s_response,
                                                         self._b_trace,
                                                         byref(self._b_end)
                                                         )
        self.data.parse_data(self.s_response_dec)

    def run_step(self) -> int:
        """ Run simulation step by step

        :return: iteration step
        :rtype: int
        """
        try:
            self.request_answer()
            self._c_iter = next(self._n_iter)
            print(f"Step: {self._c_iter}")
            return self._c_iter
        except StopIteration:
            self._bContinue = False
            return -1

    def stop_step(self):
        """Stop current current step of running simulation
        """
        self._bContinue = False

    def create_vehicle(self, vehtype: str,
                       origin: str,
                       destination: str,
                       lane: int = 1,
                       simid: int = 0) -> int:
        """Creates a vehicle within the network

        :param vehtype: vehicle type according to simulation definitions
        :type vehtype: str
        :param origin: network endpoint nodeaccording to simulation
        :type origin: str
        :param destination: network endpoint nodeaccording to simulation
        :type destination: str
        :param lane: vehicle lane number, defaults to 1
        :type lane: int, optional
        :param simid: simulation id, defaults to 0
        :type simid: int, optional
        :raises SymupyVehicleCreationError: Exception handling for invalid vehicle types or invalid network points
        :return: Vehicle id of the vehicle created >0
        :rtype: int
        """
        endpoints = self._sim.get_network_endpoints()
        veh_data = self._sim.get_vehicletype_information()
        dbTime = self._sim.sampling_time(simid)
        veh_id = tuple(v['id'] for v in veh_data)
        if(vehtype not in veh_id):
            raise SymupyVehicleCreationError(
                "Unexisting Vehicle Class in File: ", self._sim.filename)

        if (origin not in endpoints) or (destination not in endpoints):
            raise SymupyVehicleCreationError(
                "Unexisting Network Endpoint File: ", self._sim.filename)

        veh_id = self._library.SymCreateVehicleEx(vehtype.encode('UTF8'),
                                                  origin.encode('UTF8'),
                                                  destination.encode('UTF8'),
                                                  c_int(lane),
                                                  c_double(dbTime))
        return veh_id

    def drive_vehicle(self, veh_id: int, new_pos: float,
                      destination: str = None, lane: str = 1) -> None:
        """ Modifies the position of a vehicle
        :param pos: [description]
        :type pos: float
        :return: [description]
        :rtype: None
        """
        links = self._sim.get_network_links()

        if not destination:
            destination = self.data.query_vehicle_link(veh_id)[0]

        if (destination not in links):
            raise SymupyDriveVehicleError(
                "Unexisting Network Endpoint File: ", self._sim.filename)

        # TODO: Validate that position do not overpass the max pos
        dr_state = self._library.SymDriveVehicleEx(c_int(veh_id),
                                                   destination.encode('UTF8'),
                                                   c_int(lane),
                                                   c_double(new_pos),
                                                   1)
        self.request_answer()
        return dr_state

    def __enter__(self) -> None:
        """ Implementation as a context manager
            FIXME: Implement state machine ???
        """
        self.load_symuvia()
        self.load_network()
        self.init_simulation()
        self._n_iter = iter(self._sim.get_simulation_steps())
        self._c_iter = 0
        self._bContinue = True
        return self

    def __exit__(self, type, value, traceback) -> bool:
        return False

    @property
    def s_response_dec(self):
        """ Obtains instantaneous data from simulator

        :return: last query from simulator
        :rtype: str
        """
        return self._s_response.value.decode('UTF8')

    @property
    def do_next(self) -> bool:
        return self._bContinue

    @property
    def get_request(self) -> dict:
        return self.data.data_query

    @property
    def libraryname(self) -> str:
        return self._path