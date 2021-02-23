""" 
    This module explains a data extractor class to process output xml files, from symuvia. Initially it is intended to manipulate simulation data in an easy way via data manipulation tools.
"""

# ============================================================================
# STANDARD  IMPORTS
# ============================================================================

from lxml import etree
import pandas as pd

# ============================================================================
# INTERNAL IMPORTS
# ============================================================================

from symupy.utils.constants import TRJDATA_TYPE

# ============================================================================
# CLASS AND DEFINITIONS
# ============================================================================


def vehicle_data(XMLfilename: str) -> pd.DataFrame:
    """ This function imports data from a defined absolute path to an xml 
        output file and converts in particular trajectory data into  

        Args:
            XMLfilename(str): absolute path to output XML

        Returns:
            Df (DataFrame): Dataframe where columns: trajectory data, index:time step. 

    """

    # Get tree elements
    tree = etree.parse(XMLfilename)
    root = tree.getroot()
    # Time slots
    timeslot = root.xpath("SIMULATION/INSTANTS/INST")

    dfs = []
    for instant in timeslot:
        current_t = float(instant.get("val"))
        trajs = instant.xpath("TRAJS")[0].xpath("TRAJ")
        if trajs:
            trjdata = [dict(zip(x.keys(), x.values())) for x in trajs]
            dfs.append(
                pd.DataFrame(data=trjdata, index=[current_t] * len(trajs))
            )
        # else:
        #     # Declare empty roads when network is empty
        #     dfs.append(pd.DataFrame(columns=TRJDATA_TYPE.keys(), index=[current_t]))

    # Fuse all
    df = pd.concat(dfs)

    # Parse into dict -> df when no time  info is required
    # trajs = root.xpath("SIMULATION/INSTANTS/INST/TRAJS/TRAJ")
    # trajs_dct = [dict(zip(x.keys(), x.values())) for x in trajs]
    # df = pd.DataFrame(trajs_dct)

    # Parsing types

    df = df.astype(TRJDATA_TYPE)

    return df
