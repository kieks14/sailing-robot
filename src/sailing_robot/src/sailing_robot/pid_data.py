#import rospy


class PID_Data:
    def __init__(self):
        self.tack_rudder = 0.
        self.sailing_state = 'normal'
        self.goal_heading = 0.
        self.heading = 0.

    def update_goal_heading(self, msg):
        """
        Update goal heading data from higher level controller for PID controller
        :param msg:
        """
        # TODO: receive goal_heading from xmf
        #self.goal_heading = msg.data
        self.goal_heading = 45

    def update_sailing_state(self, msg):
        """
        Update sailing state data from higher level controller
        """
        # TODO: receive sailing_state from xmf
        #self.sailing_state = msg.data
        self.sailing_state = 'normal'
        user_input = input("Enter new sailing state ('normal' or 'switch_to_port_tack' or 'switch_to_stbd_tack'): ")

        if user_input in ['normal', 'switch_to_port_tack', 'switch_to_stbd_tack']:
            self.sailing_state = user_input
        else:
            print("Invalid input. Sailing state remains unchanged.")

    def update_heading(self, msg):
        """
        Get continuous update of current heading from sensors
        :param msg:

        """
        # TODO: receive heading from xmf
        #self.heading = msg.data
        self.heading = 45

    def update_tack_rudder(self,msg):
        # TODO: receive tack rudder from xmf
        #self.tack_rudder = msg.data
        self.tack_rudder = 0.0
