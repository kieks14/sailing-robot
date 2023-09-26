# -*- coding: utf-8 -*-
"""
template to interact with the XMF main file. 

There are some reasons that can make the interaction go wrong. This especially happens
if you run the file multiple times.

- the socket is not closed. Then you have to close it manually:
    sockReceive.close()
    sockSend.close()

- XMF is still running in the background. Close it in the Task Manager (its name starts with 'MARIN')

- The subprocess is still running on the background
    A.terminate()

Most of the time, I just to them all, and then it will work out ok. A clear indicator
that something goes wrong is if you get a lot of time outs. Getting one or two is not a 
problem, but if this continues you have to kill em all.

@author: BDuz
"""
import numpy as np
import matplotlib.pyplot as plt
import socket
import struct
import sys
import subprocess
import os


# set the location where xSimulation is located
xPath = r'D:\Apps\xsimulation\xsimulation-eoe-tag-2023.02.0\eoe'
assert(os.path.isdir(xPath))

# some of the parameters
Tfinal = 0.5
dt = 0.05
t = np.arange(0, Tfinal + dt, dt)
N = len(t)

#  setup the communication with the model via UDP
# adresses of the connections
UDP_IP_S = "127.0.0.1"
UDP_IP_R = "127.0.0.1"

# the ports
UDP_PORT_S = 10004
UDP_PORT_R = 10003

# We do need to known the number of doubles we receive (hardcoded!)
# receive = [globalPosition, globalOrientation, bodyFixedVelocity, bodyFixedRotation]
# send = [telegraph_SB, telegraph_PS, rudder_SB, rudder_PS]
received_doubles = 21
# fs_rec = f'{received_doubles}d'
fs_rec = f'<I3d{received_doubles}d'
fs_send = '<I3d'

# make sockets
sockReceive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sockSend = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# set the option so that we can reconnect without timeout things (otherwise wait long....)
sockReceive.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sockSend.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# bind the receiver (sender not needed !) Use a long timeout: xmf needs time to start
sockReceive.settimeout(15)
sockReceive.bind((UDP_IP_R, UDP_PORT_R))

# allocate data for logging
logX = np.zeros((N, 25))
logA = np.zeros((N, 4))

# %% write the run file
fid = open('_runXMF.cmd', 'w')
fid.write('ECHO OFF\n')
fid.write(f'path={xPath}; %path%')
fid.write('\n')
fid.write(r'call setpath')
fid.write('\n')
fid.write(f'ft -c input.xmf -l {Tfinal}')
fid.close()

# %% here we go to run
A = subprocess.Popen('_runXMF.cmd', shell=True)

# start by sending, to avoid deadlock
# might be needed if the timeout in the UDP node in XMF is incorrect. Prefer not to use it.
"""
if False:
    u = [0.0, 0.0, 0.0, 0.0]
    data = struct.pack(fs_send, *u)
    for _ in range(10):
        _ = sockSend.sendto(data, (UDP_IP_S, UDP_PORT_S))
"""

# Receive the the initial condition from the basin
for n in range(3):
    if True:
        data = []
        try:
            data = sockReceive.recv(4096)
            data_length = int(sys.getsizeof(data))
            print(data_length)

            # only continue if we got data.
            if len(data) > 0:

                # unpack to normal format
                """
                state = struct.unpack('i', data[:4])[0]
                data_unp = struct.unpack(fs_rec, data[4:received_doubles * 8 + 4])

                time = data_unp[0]
                dt = data_unp[1]
                time_scale = data_unp[2]
                LineLength = data_unp[3]
                RudderAngle = data_unp[4]
                BallastPos = data_unp[5]
                print(state, time, dt, LineLength, RudderAngle, BallastPos)
                """

                data_unp = struct.unpack(fs_rec, data)
                state = data_unp[0]
                time = data_unp[1]
                dt = data_unp[2]
                time_scale = data_unp[3]
                LineLength = data_unp[4]
                RudderAngle = data_unp[5]
                BallastPos = data_unp[6]
                print(state, time, time_scale, LineLength, RudderAngle, BallastPos)

        except Exception as e:
            print(e)
            data_unp = np.zeros((1, received_doubles))

# log the initial condition
logX[0, :] = data_unp

# Actions
Status = 0  # 0 = continue,  1 = request from agent for basin to terminate episode,  2 = request from agent for simulation to terminate episode
actionLineLength = 0.5
actionRudderAngle = 1
actionBallastPos = 0.5

minLineLength, maxLineLength, LineRate = 0.73, 1.32, 0.4
minRudderAngle, maxRudderAngle, RudderRate = np.deg2rad(-65.0), np.deg2rad(65.0), np.deg2rad(30.0)
minBallastPos, maxBallastPos, BallastRate = -0.45, 0.45, 0.2
for n in range(N-1):
    
    RudderAngle = RudderAngle + actionRudderAngle * RudderRate * dt
    RudderAngle = min(max(RudderAngle, -maxRudderAngle), maxRudderAngle)

    LineLength = LineLength + actionLineLength * LineRate * dt
    LineLength = min(max(LineLength, minLineLength), maxLineLength)

    BallastPos = BallastPos + actionBallastPos * BallastRate * dt
    BallastPos = min(max(BallastPos, minBallastPos), maxBallastPos) 
    
    # send something back
    u = [Status, LineLength, RudderAngle, BallastPos]

    # pack it
    data = struct.pack(fs_send, *u)

    # send it to the XMF
    bsend = sockSend.sendto(data, (UDP_IP_S, UDP_PORT_S))

    # wait for data
    data = []
    try:
        data = sockReceive.recv(4096)
        data_length = int(sys.getsizeof(data))

        # only continue if we got data.
        if len(data) > 0:

            # unpack to normal format
            # state = struct.unpack('i', data[:4])[0]
            # data_unp = struct.unpack(fs_rec, data[4:received_doubles * 8 + 4])

            data_unp = struct.unpack(fs_rec, data)

    except Exception as e:
        print(e)
        data_unp = np.zeros((1, received_doubles))

    print(data_unp[0], data_unp[1], u[1], data_unp[4], u[2], data_unp[5], u[3], data_unp[6])

    logX[n+1, :] = data_unp
    logA[n, :] = u  

# close the socket
A.terminate()
sockReceive.close()
sockSend.close()

# plot to show that we got something
#fig, ax = plt.subplots(2, 1)
#ax[0].plot(t, logX[:, 5])  # yaw
#ax[1].plot(t, logX[:, 6])  # surge
#ax[0].set(ylabel='yaw [rad]')
#ax[1].set(ylabel='speed [m/s]', xlabel='time [s]')

np.savetxt("logX.csv", logX, delimiter=",")
np.savetxt("logA.csv", logA, delimiter=",")
