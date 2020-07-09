import cppyy
import setup_cppyy
import pdb
from cppyy.gbl import opendnp3, openpal, asiopal, asiodnp3 , std
import cppyy.ll
import time
cppyy.ll.set_signals_as_exception(True)

FILTERS = opendnp3.levels.NORMAL | opendnp3.levels.ALL_COMMS
HOST = "127.0.0.1"
LOCAL = "0.0.0.0"
PORT = 20000

shortone = openpal.TimeDuration.Milliseconds(1000)
longone = openpal.TimeDuration.Milliseconds(300000)
retry = asiopal.ChannelRetry(openpal.TimeDuration.Milliseconds(1000), openpal.TimeDuration.Milliseconds(300000))
log_handler = asiodnp3.ConsoleLogger(False).Create()
manager = asiodnp3.DNP3Manager(1, log_handler)
listener = asiodnp3.PrintingChannelListener().Create()
channel = manager.AddTCPClient("tcpclient",
                                FILTERS,
                                retry,
                                HOST,
                                LOCAL,
                                PORT,
                                listener)

time.sleep(5)
    
