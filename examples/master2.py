import logging
import sys
import time
import cppyy
import setup_cppyy
from cppyy.gbl import opendnp3, openpal, asiopal, asiodnp3
#import pdb
#import cppyy.ll
#cppyy.ll.set_signals_as_exception(True)

# from cppyy.gbl.asiodnp3 import DNP3Manager, IChannelListener, PrintingCommandCallback, MasterStackConfig, ConsoleLogger, PrintingChannelListener, PrintingSOEHandler, DefaultMasterApplication
# from cppyy.asiopal import ChannelRetry
# from cppyy.opendnp3 import ClassField, levels, TaskConfig, ISOEHandler, IMasterApplication
# from cppyy.openpal import TimeDuration, ILogHandler
#from visitors import *

FILTERS = opendnp3.levels.NORMAL | opendnp3.levels.ALL_COMMS
HOST = "127.0.0.1"
LOCAL = "0.0.0.0"
PORT = 20000

stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)

class MyMaster:
    """
        Interface for all master application callback info except for measurement values.

        DNP3 spec section 5.1.6.1:
            The Application Layer provides the following services for the DNP3 User Layer in a master:
                - Formats requests directed to one or more outstations.
                - Notifies the DNP3 User Layer when new data or information arrives from an outstation.

        DNP spec section 5.1.6.3:
            The Application Layer requires specific services from the layers beneath it.
                - Partitioning of fragments into smaller portions for transport reliability.
                - Knowledge of which device(s) were the source of received messages.
                - Transmission of messages to specific devices or to all devices.
                - Message integrity (i.e., error-free reception and transmission of messages).
                - Knowledge of the time when messages arrive.
                - Either precise times of transmission or the ability to set time values
                  into outgoing messages.
    """
    def __init__(self):
        self.manager = asiodnp3.DNP3Manager(1,  asiodnp3.ConsoleLogger.Create())
        self.channel = self.manager.AddTCPClient("tcpclient", FILTERS, asiopal.ChannelRetry(openpal.TimeDuration.Milliseconds(1000),openpal.TimeDuration.Milliseconds(300000)), [asiopal.IPEndpoint("127.0.0.1", 20000)],
                                        "0.0.0.0", asiodnp3.PrintingChannelListener.Create())
        
        self.stackConfig = asiodnp3.MasterStackConfig()
        self.stackConfig.master.responseTimeout = openpal.TimeDuration.Seconds(2)
        self.stackConfig.master.disableUnsolOnStartup = True

        self.stackConfig.link.LocalAddr = 1
        self.stackConfig.link.RemoteAddr = 10

        self.master = self.channel.AddMaster("master",                           # id for logging
                                     asiodnp3.PrintingSOEHandler.Create(),       # callback for data processing
                                     asiodnp3.DefaultMasterApplication.Create(), # master application instance
                                     self.stackConfig)                           # stack configuration

        #self.integrityScan = self.master.AddClassScan(opendnp3.ClassField.AllClasses(), openpal.TimeDuration.Minutes(1))
        #self.exceptionScan = self.master.AddClassScan(opendnp3.ClassField(opendnp3.ClassField.CLASS_1), openpal.TimeDuration.Seconds(2))

        _log.debug('Enabling the master. At this point, traffic will start to flow between the Master and Outstations.')
        
        self.master.Enable()
        self.channelCommsLoggingEnabled = True
        self.masterCommsLoggingEnabled = True

    def shutdown(self):
        del self.integrityScan
        del self.exceptionScan
        del self.master
        del self.channel
        self.manager.Shutdown()

def main():
    app = MyMaster()

    _log.debug('Initialization complete. In command loop.')

    time.sleep(5)

    app.shutdown()
    _log.debug('Exiting.')
    exit()


if __name__ == '__main__':
    main()




        
