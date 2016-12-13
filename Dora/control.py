import time
import global_vars as gv


# Constants for IR sensors in list
forward_sensor = 0
backward_sensor = 1


class PID():
    """
    Kp, Ki and Kd must be >=0
    
    """

    def __init__(self, setpoint = 0.0, Kp = 0.0, Ki = 0.0, Kd = 0.0):
        # Target value
        self.setpoint = setpoint
        
        # PID constants
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        
        # Sum of all errors (for integral part)
        self.error_sum = 0
        self.last_time = time.time()
        
        # Limits on the output value
        self.min = 0
        self.max = 100
        
        # If the output should be reversed
        self.reversed = False
        
        # Turn PID control on or off
        self.enabled = True
        
    def compute(self, input):
        # input is taken as a list of 6 IR-values
        
        if not self.enabled:
            return 0

        if isinstance(input, float):
            error = self.setpoint - input
        else:
            with input.get_lock():
                # test this code:
                dist  = float(input[forward_sensor])
                
            error = float(self.setpoint) - dist
            
        # Add to current error to total error sum
        current_time = time.time()
        self.error_sum += self.Ki * error * (current_time - self.last_time)
        self.last_time = current_time
        
        # Adjust integral term to limits
        if self.error_sum < self.min:
            self.error_sum = self.min
        elif self.error_sum > self.max:
            self.error_sum = self.max
            
        # Compute the PID output
        if isinstance(input, float):
            output = self.Kp * error + self.error_sum
        else:
            with input.get_lock():
                output = self.Kp * error + self.error_sum - self.Kd * (int(input[forward_sensor]) - int(input[backward_sensor]))
            
        # Adjust output to be within the bounds
        if output < self.min:
            output = self.min
        elif output > self.max:
            output = self.max
            
        if self.reversed:
            output = -output
            
        return output
    
    # Method for settings the max and min values of the output
    def set_output_limits(self, out_min, out_max):
        if out_min > out_max:
            return
        
        self.min = out_min
        self.max = out_max

    # Method for enabling or disabling the PID
    def enable(self, turn_on):
        # Check if we are switching the PID on
        if turn_on and not self.enabled:
            self.error_sum = 0
            if self.error_sum < self.min:
                self.error_sum = self.min
            elif self.error_sum > self.max:
                self.error_sum = self.max

        self.enabled = turn_on
