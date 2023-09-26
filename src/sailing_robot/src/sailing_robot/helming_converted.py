import time
import collections
import numpy as np
import random
import sys

from sailing_robot.sail_table import SailTable, SailData

from sailing_robot.pid_data import PID_Data
import sailing_robot.pid_control as _PID
from sailing_robot.navigation import angle_subtract

from sailing_robot.sample_data_generator import SampleDataGenerator

# Define constants for sheet control
WIND = object()
SHEET_IN = object()
SHEET_OUT = object()

# Define constants for rudder control
PID_GOAL_HEADING = object()
PID_ANGLE_TO_WIND = object()
RUDDER_FULL_LEFT = object()
RUDDER_FULL_RIGHT = object()


#######
# rudder, sailsheet and dbg_helming are published here
#######


data = PID_Data()

# should get this from defaults.yaml file:
rudder = {'control': {'Kp': 0.5, 'Ki': 0.0, 'Kd': 0.0}, 'maxAngle': 30, 'initialAngle': 0,}

controller = _PID.PID(rudder['control']['Kp'], rudder['control']['Ki'], rudder['control']['Kd'],rudder['maxAngle'], -rudder['maxAngle'])
remote_control = False

# should get this from defaults.yaml file:
sail_table_dict = {0: 0.5, 45: 0.5, 90: 0.5, 135: 0.5, 180: 0.5, 225: 0.5, 270: 0.5, 315: 0.5}

sail_table = SailTable(sail_table_dict)
sail_data = SailData(sail_table)

TIMEOUT = 15
EXPLORE_COEF = 0.1

def set_sail(sheet_control, offset=0.0):
    if sheet_control is WIND:
        sheet_normalized = sail_data.calculate_sheet_setting() + offset
    
    elif sheet_control is SHEET_IN:
        sheet_normalized = 0

    elif sheet_control is SHEET_OUT:
        sheet_normalized = 1

    elif sheet_control is float:
        sheet_normalized = sheet_control

    # be sure we don't print values above 1 and below 0
    sheet_normalized = np.clip(sheet_normalized, 0, 1)
    # TODO: PUB_sailsheet.publish(sheet_normalized) to xmf
    print("Sheet setting: " + str(sheet_normalized))

def set_rudder(state, angle_to_wind=0):
    if state is PID_GOAL_HEADING:
        rawangle = -controller.update_PID(angle_subtract(data.heading, data.goal_heading))
        angle = _PID.saturation(rawangle,-rudder['maxAngle'], rudder['maxAngle'])

    elif state is PID_ANGLE_TO_WIND:
        rawangle = -controller.update_PID(angle_subtract(angle_to_wind, sail_data.wind_direction_apparent)) 
        angle = _PID.saturation(rawangle,-rudder['maxAngle'], rudder['maxAngle'])

    elif state is RUDDER_FULL_LEFT:
        angle = rudder['maxAngle']

    elif state is RUDDER_FULL_RIGHT:
        angle = -rudder['maxAngle']

    # TODO: PUB_rudder.publish(int(angle)) to xmf
    print("Rudder angle: " + str(angle))

class ProcedureBase(object):
    def __init__(self, sailing_state, timeout=TIMEOUT):
        self.start_time = time.time()
        self.timeout = timeout
        self.sailing_state = sailing_state

    def has_failed(self):
        """
        Am I out of time?
        Am I failing?
        """
        current_time = time.time()
        return self.enlapsed_time() > self.timeout

    def enlapsed_time(self):
        current_time = time.time()
        return current_time - self.start_time
    
    def __str__(self):
        return self.__class__.__name__

class TackBasic(ProcedureBase):
    """
    Basic tack procedure
    """
    def __init__(self, sailing_state, timeout=TIMEOUT):
        super(TackBasic, self).__init__(sailing_state, timeout) 

    def loop(self):
        set_sail(WIND)
        if self.sailing_state == "switch_to_port_tack":
            set_rudder(RUDDER_FULL_RIGHT) 
        else:
            set_rudder(RUDDER_FULL_LEFT)

class JibeBasic(ProcedureBase):
    """
    Basic Jibe procedure
    """
    def __init__(self, sailing_state, timeout=TIMEOUT):
        super(JibeBasic, self).__init__(sailing_state, timeout) 

    def loop(self):
        # sheet out a bit more than what is given by the look up table
        set_sail(WIND, offset=+0.2)
        if self.sailing_state == "switch_to_port_tack":
            set_rudder(RUDDER_FULL_LEFT) 
        else:
            set_rudder(RUDDER_FULL_RIGHT)

class TackSheetOut(ProcedureBase):
    """
    Tack procedure where we sheet out a bit

    When sheeted in completely the jib has too much power and tacking becomes impossible
    in some strong conditions. Hence sheeting out is needed, however if the sails are out
    too much the boat will not have enough power to tack 
    """
    def __init__(self, sailing_state, timeout=TIMEOUT):
        super(TackSheetOut, self).__init__(sailing_state, timeout) 

    def loop(self):
        # sheet out a bit more than what is given by the look up table
        set_sail(WIND, offset=+0.2)
        if self.sailing_state == "switch_to_port_tack":
            set_rudder(RUDDER_FULL_RIGHT) 
        else:
            set_rudder(RUDDER_FULL_LEFT)

class Tack_IncreaseAngleToWind(ProcedureBase):
    """
    More advance Tack procedure, building speed for 5s by going less upwind
    """
    def __init__(self, sailing_state, timeout=TIMEOUT):
        super(Tack_IncreaseAngleToWind, self).__init__(sailing_state, timeout) 
        self.beating_angle = 80

    def loop(self):
        set_sail(WIND)
        if self.enlapsed_time() < 4:
            if self.sailing_state == "switch_to_port_tack":
                set_rudder(PID_ANGLE_TO_WIND, angle_to_wind = self.beating_angle)
            else:
                set_rudder(PID_ANGLE_TO_WIND, angle_to_wind = 360-self.beating_angle)  
        else:
            if self.sailing_state == "switch_to_port_tack":
                set_rudder(RUDDER_FULL_RIGHT) 
            else:
                set_rudder(RUDDER_FULL_LEFT)

###############################################################################################################

class ProcedureHandle():
    """
        Class to handle a list of procedure and the priority based on weights
        after each tack attempt weight based on time taken by the procedure
        are given to each procedure for the future.
    """
    def __init__(self, ProcedureList):

        self.ProcedureList = [{"Procedure": Procedure, 
                                "TimeList": collections.deque(maxlen=10), 
                                "InitPos": i} for i, Procedure in enumerate(ProcedureList)]
        self.currentProcedureId = 0
        self.currentProcedure = None

    def ProcedureInProgress(self):
        return (self.currentProcedure is not None)

    def FirstProcedure(self):
        self.OrderList()
        self.currentProcedureId = 0

    def NextProcedure(self):
        self.currentProcedureId = (self.currentProcedureId + 1) % len(self.ProcedureList)

    def OrderList(self):
        def get_weight(x):
            if x['TimeList']:
                return np.mean(x['TimeList'])
            else:
                if random.random() < (EXPLORE_COEF / sum([not x['TimeList'] for x in self.ProcedureList])):
                    print("Random procedure picked")
                    # Add some randomness in choice for untested procedures
                    return 0.1 * random.random()
                else:
                    # Just to keep the order given at first if the procedure was not tested yet
                    return TIMEOUT + x['InitPos'] * 0.01 * TIMEOUT

        self.ProcedureList = sorted(self.ProcedureList, key=get_weight)

    def MarkSuccess(self):
        if not remote_control:
            # TODO: PUB_dbg_helming.publish("success " + str(self.currentProcedure)) to xmf
            print("Success " + str(self.currentProcedure))
            self.ProcedureList[self.currentProcedureId]['TimeList'].append(self.currentProcedure.enlapsed_time())
        self.currentProcedure = None

    def MarkFailure(self):
        if not remote_control:
            # TODO: PUB_dbg_helming.publish("fail " + str(self.currentProcedure)) to xmf
            print("Fail " + str(self.currentProcedure))
            self.ProcedureList[self.currentProcedureId]['TimeList'].append(1.5 * TIMEOUT)
        self.currentProcedure = None

    def StartProcedure(self, sailing_state):
        self.currentProcedure = self.ProcedureList[self.currentProcedureId]['Procedure'](sailing_state)
        # TODO: PUB_dbg_helming.publish("start " + str(self.currentProcedure)) to xmf
        print("Start " + str(self.currentProcedure))

class Helming():
    def __init__(self):
        self.rate = 10  # Set the rate (adjust as needed)

        # Initialize your data objects and parameters here
        self.data = PID_Data()
        rudder = {'control': {'Kp'
        : 0.5, 'Ki': 0.0, 'Kd': 0.0}, 'maxAngle': 30, 'initialAngle': 0,} # TODO: get this from defaults.yaml file
        self.controller = _PID.PID(rudder['control']['Kp'], rudder['control']['Ki'], rudder['control']['Kd'],rudder['maxAngle'], -rudder['maxAngle'])
        self.remote_control = False
        self.sail_table_dict = {0: 0.5, 45: 0.5, 90: 0.5, 135: 0.5, 180: 0.5, 225: 0.5, 270: 0.5, 315: 0.5}  # TODO: get this from defaults.yaml file
        self.sail_table = SailTable(self.sail_table_dict)
        self.sail_data = SailData(self.sail_table)
        self.TIMEOUT = 30  # Set the timeout value (adjust as needed)
        self.EXPLORE_COEF = 0.1  # Set the exploration coefficient (adjust as needed)
        
        procedureList = [TackBasic, TackSheetOut, Tack_IncreaseAngleToWind, JibeBasic]
        
        self.Proc = ProcedureHandle(procedureList)
        self.Runner()
    
    def Runner(self):
        while True:
            if self.data.sailing_state == 'normal':
                if self.Proc and self.Proc.ProcedureInProgress():
                    # Ending a procedure because it is finished according to the high-level
                    print("Procedure success " + str(self.Proc.currentProcedure) +
                          " in " + '{:.2f}'.format(self.Proc.currentProcedure.enlapsed_time()) + "s")
                    self.Proc.MarkSuccess()

                set_rudder(PID_GOAL_HEADING)
                set_sail(WIND)
            else:
                # Continuing a procedure
                self.runProcedure()

            time.sleep(1.0 / 10)

    def runProcedure(self):
        if (not self.Proc.ProcedureInProgress()) or (self.data.sailing_state != self.Proc.currentProcedure.sailing_state):
            # No procedure has been started (= we just decided to switch tack)
            self.Proc.FirstProcedure()
            self.Proc.StartProcedure(self.data.sailing_state)
            #print("Run procedure     " + str(self.Proc.currentProcedure))
            print("DEBUG: Run procedure {} initiated".format(self.Proc.currentProcedure), file=sys.stderr)

        elif self.Proc.currentProcedure.has_failed():
            print("Procedure failed  " + str(self.Proc.currentProcedure))
            self.Proc.MarkFailure()
            # If timeout, we start the next procedure in the list
            self.Proc.NextProcedure()
            self.Proc.StartProcedure(self.data.sailing_state)
            #print("Run procedure     " + str(self.Proc.currentProcedure))
            print("DEBUG: Run procedure {} initiated".format(self.Proc.currentProcedure), file=sys.stderr)

        # We advance to the next time step
        self.Proc.currentProcedure.loop()

# if __name__ == '__main__':
#     try:
#         Helming()
#     except KeyboardInterrupt:
#         pass