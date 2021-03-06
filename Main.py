#!/usr/bin/python

'''
    ************************************************************************
    *   FILE NAME:      main.py
    *   AUTHOR:         Dylan Vogel, Peter Feng
    *   PURPOSE:        This file contains the script used to run the nanoimprinting process.
    *
    *
    *   EXTERNAL REFERENCES:    time, sys, dataLog, thmcouple, heater, PID
    *
    *
    *   NOTES:          Script can be safely closed using Ctrl-C.
    *
    *
    *   REVISION HISTORY:
    *
    *                   2017-05-22: Created file.
    *                   2017-05-23: Added PWM scriping and functions related to PID controller.
    *                   2017-05-24: Added waiting time after initial heating before PID controller
    *                               activates. Adjusted PID settings based on trials.
    *                   2017-05-25: Reorganized function structure and added comments for readability.
    *                               Moved all setup values to one section and labelled them for easy adjustment.
    *                               Added a limiting Kp value that the PID controller switches to within 15 C
    *                               of the target temp.
    *                               Moved most of the main script inside the try ... except statement for
    *                               consistent logging and proper script closure.
    *                               Added an exception handler that catches non-KeyboardInterrupt exceptions, prints
    *                               them to console, and safely exits the script.
    *                               Changed the clamping mechanism to work on the edge and center elements separately.



'''

# System functions
import time
import sys
import traceback


# User functions
import dataLog as log
import thmcouple as thm
import heater
import PID
import controller
################################################################################
''' EDIT THESE; THESE ARE THE PID COEFFICIENTS '''

'''

def pid_setup_center(work_temp, P, I, D): #change

    # Written as (Kp, Ki, Kd)
    pid_center = PID.PID(P, I, D)

    # Windup to prevent integral term from going too high/low.
    pid_center.setWindup(1)

    # Sample time, pretty self-explanatory.
    pid_center.setSampleTime(0.5)
    pid_center.SetPoint = work_temp

    return pid_center

def pid_setup_edge(work_temp, P, I, D): #change

    pid_edge = PID.PID(P, I, D)

    pid_edge.setWindup(1)
    pid_edge.setSampleTime(0.5)
    pid_edge.SetPoint = work_temp

    return pid_edge
'''

if __name__ == "__main__":

    ################################################################################
    ''' EDIT THESE SETUP VARIABLES '''

    #change
    #work_temp = input('Enter a working temperature between 0-200 C: ')

    app = controller.QtWidgets.QApplication(sys.argv)
    window = controller.MainWindow()
    window.show()
    sys.exit(app.exec_())

    work_temp = window.temp
    P_center = window.P_center
    I_center = window.I_center
    D_center = window.D_center

    P_edge = window.P_edge
    I_edge = window.I_edge
    D_edge = window.D_edge



    '''
    #heat_time = input('Enter bonding time in seconds 0-3600s: ')

    # The frequency at which main.py will write to the console and log file.
    data_log_freq = 1

    # The PWM duty used for the initial heating. Generally around 50% for the
    # center and 100% for the edge seems to work. Should be adjusted based on
    # changes to the thermal volume based on empirical results.
    pwm_center = 40
    pwm_edge = 100

    # Used to suppress Kp as it approaches the setpoint.
    limited_kp =  1 #heater.calc_kp(work_temp)

    limited_kd = -0.2

    # Time to wait after initial heating for temp to settle
    wait_time = 30

    ################################################################################
    ''' DON'T EDIT THESE UNLESS YOU KNOW WHAT YOU'RE DOING '''

    log.setup("PID_cartridge_test")

    thm1 = thm.setup1()
    thm2 = thm.setup2()

    pwm_1 = heater.setup1()
    pwm_2 = heater.setup2()

    pid_edge = pid_setup_edge(work_temp, P_edge, I_edge, D_edge)
    pid_center = pid_setup_center(work_temp, P_center, I_center, D_center)

    pid_edge_val = pid_edge.getPID()
    pid_center_val = pid_center.getPID()

    # These variables will have current temp values written to them.
    t_center = thm.read(thm1)
    t_edge = thm.read(thm2)

    # These variables store the temperature averaged over the last two values.
    t_center_avg = t_center
    t_edge_avg = t_edge

    # Variables used for timekeeping and data plotting.
    start_t = time.time()
    curr_t = time.time()

    times = []
    cent_temps = []
    edge_temps = []


    print ("Setup completed, initial heating  ... ")
    
    try:
        # Function stored in heater.py. Algorithm based on empirical results.
        heat_time = heater.initial_heating_time(t_center, t_edge, work_temp, thm1, thm2)
        heater.change_duty(pwm_center, pwm_edge, pwm_1, pwm_2)
        # This is the initial heating.
        while ((time.time() - start_t) < heat_time):
            if ((time.time() - curr_t) >= data_log_freq):
                t_center = thm.read(thm1)
                t_edge = thm.read(thm2)

                curr_t = time.time()
                log.write_line_to_log(t_center, t_edge, pwm_center, pwm_edge, curr_t, start_t, cent_temps, edge_temps, times, window)

        # Update PWM values to zero.
        pwm_center = 0
        pwm_edge = 0
        heater.change_duty(pwm_center, pwm_edge, pwm_1, pwm_2)


        print('Initial heating finished...')
        log.write('LINE', round((time.time() - start_t), 2), 'Initial heating finished at: ')

        pid_start_t = time.time()

        # Wait for the temperature to settle.
        while ((time.time() - pid_start_t) < wait_time):
            if ((time.time() - curr_t) >= data_log_freq):
                t_center = thm.read(thm1)
                t_edge = thm.read(thm2)

                curr_t = time.time()
                log.write_line_to_log(t_center, t_edge, pwm_center, pwm_edge, curr_t, start_t, cent_temps, edge_temps, times, window)


        print('PID controller started ...')
        log.write('LINE', round((time.time() - start_t), 2), 'PID Controller started at: ')

        working = True
        limited = [[False, False], [False, False]]

        while working:
            t_center_last = t_center
            t_edge_last = t_edge
            t_center = thm.read(thm1)
            t_edge = thm.read(thm2)

            if ((time.time() - curr_t) >= data_log_freq):

                curr_t = time.time()
                log.write_line_to_log(t_center, t_edge, pwm_center, pwm_edge, curr_t, start_t, cent_temps, edge_temps, times, window)

            t_center_avg =  (t_center + t_center_last) / 2.0
            t_edge_avg =  (t_edge + t_edge_last) / 2.0

            pid_center.update(t_center_avg)
            pwm_center = pid_center.output
            pwm_center = heater.clamp(pwm_center, 0, 100)

            pid_edge.update(t_edge_avg)
            pwm_edge = pid_edge.output
            pwm_edge = heater.clamp(pwm_edge, 0, 100)

            heater.change_duty(pwm_center, pwm_edge, pwm_1, pwm_2)

            # Suppress Kp once the current temp nears the working temp.
            if ((limited[0][0] == False) and ((work_temp - t_center_avg) < 15)):
                print("Kp center suppressed ... ")
                log.write('LINE', 0, 'Kp center suppressed')
                pid_center.setKp(limited_kp)
                limited[0][0] = True

            if ((limited[1][0] == False) and ((work_temp - t_edge_avg) < 15)):
                print("Kp edge suppressed ... ")
                log.write('LINE', 0, 'Kp edge suppressed')
                pid_edge.setKp(limited_kp)
                limited[1][0] = True

            if ((limited[0][1] == False) and ((work_temp - t_center_avg) < 1)):
                print("Kd center suppressed ... ")
                log.write('LINE', 0, 'Kd center suppressed')
                pid_center.setKd(limited_kd)
                limited[0][1] = True

            if ((limited[1][1] == False) and ((work_temp - t_edge_avg) < 1)):
                print("Kd edge suppressed ... ")
                log.write('LINE', 0, 'Kd edge suppressed')
                pid_edge.setKd(limited_kd)
                limited[1][1] = True


    except KeyboardInterrupt:
        log.close()
        thm.close(thm1)
        thm.close(thm2)
        heater.close(pwm_1)
        heater.close(pwm_2)

        coefficients_center = pid_center.getPID()
        coefficients_edge = pid_edge.getPID()

        log.createPlot(times, cent_temps, edge_temps, heat_time, coefficients_center, coefficients_edge, pid_center_val, pid_edge_val)

        sys.exit()

    except:
        traceback.print_exc()
        log.close()
        thm.close(thm1)
        thm.close(thm2)
        heater.close(pwm_1)
        heater.close(pwm_2)

        sys.exit()
    
    '''

