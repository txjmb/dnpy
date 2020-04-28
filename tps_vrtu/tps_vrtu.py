import logging
import sys
import os
import cppyy
import setup_cppyy
import confuse
import asyncio
import time
import IPython as ip
from io import StringIO
import signal
import pika
import sys
from lxml import etree
from lxml.etree import fromstring
import pdb

from cppyy.gbl import opendnp3, openpal, asiopal, asiodnp3

LOG_LEVELS = opendnp3.levels.NORMAL #| opendnp3.levels.ALL_COMMS
LOCAL_IP = "0.0.0.0"
PORT = 20000

app = None
connection = None

stdout_stream = logging.StreamHandler(sys.stdout)
stdout_stream.setFormatter(logging.Formatter('%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'))

_log = logging.getLogger(__name__)
_log.addHandler(stdout_stream)
_log.setLevel(logging.DEBUG)

template = {
    'message_sources': confuse.Sequence(
        {
            'message_source_id': int,
            'desc': str,
            'source_type': confuse.OneOf('rabbitmq', 'activemq'),
            'source_uri': str,
            'topics': confuse.Sequence(
                {
                    'topic_id': int,
                    'name': str,
                    'source_message_type': confuse.OneOf('xml', 'json')
                }
            ),
        }
    ),
    'outstations': confuse.Sequence(
        {
            'outstation_id': int,
            'station_id': int,
            'master_id':int,
            'desc': str,
            'points': 
                {
                    'analogs': confuse.Sequence(
                        {
                            'point_id': int,
                            'desc': str,
                            'point_type': confuse.OneOf('analog','float'),
                            'scaling': int,
                            'message_source_id': int,
                            'message_topic_id': int,
                            'point_path': str
                        }),
                    'binaries': confuse.Sequence(
                        {
                            'point_id': int,
                            'desc': str,
                            'point_type': confuse.OneOf('binary'),
                            'message_source_id': int,
                            'message_topic_id': int,
                            'point_path': str
                        })
                }
        }
    )
}


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    global connection
    connection.close()

    #sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


class OutstationApplication(opendnp3.IOutstationApplication):
    """
        Interface for all outstation callback info except for control requests.

        DNP3 spec section 5.1.6.2:
            The Application Layer provides the following services for the DNP3 User Layer in an outstation:
                - Notifies the DNP3 User Layer when action requests, such as control output,
                  analog output, freeze and file operations, arrive from a master.
                - Requests data and information from the outstation that is wanted by a master
                  and formats the responses returned to a master.
                - Assures that event data is successfully conveyed to a master (using
                  Application Layer confirmation).
                - Sends notifications to the master when the outstation restarts, has queued events,
                  and requires time synchronization.

        DNP3 spec section 5.1.6.3:
            The Application Layer requires specific services from the layers beneath it.
                - Partitioning of fragments into smaller portions for transport reliability.
                - Knowledge of which device(s) were the source of received messages.
                - Transmission of messages to specific devices or to all devices.
                - Message integrity (i.e., error-free reception and transmission of messages).
                - Knowledge of the time when messages arrive.
                - Either precise times of transmission or the ability to set time values
                  into outgoing messages.
    """

    outstations = []

    def __init__(self):
        config = confuse.Configuration("tps_vrtu")
        print('Config directory is: ', config.config_dir())

        config.set_file("tps_vrtu.yaml")

        self.config = config.get(template)

        super(OutstationApplication, self).__init__()

        _log.debug('Creating a DNP3Manager.')
        threads_to_allocate = 1
        # self.log_handler = MyLogger()
        self.log_handler = asiodnp3.ConsoleLogger(False).Create()              # (or use this during regression testing)
        self.manager = asiodnp3.DNP3Manager(threads_to_allocate, self.log_handler)
        self.server_accept_mode = opendnp3.ServerAcceptMode.CloseNew

        _log.debug('Creating the DNP3 channel, a TCP server.')
        self.retry_parameters = asiopal.ChannelRetry(openpal.TimeDuration.Seconds(1), openpal.TimeDuration.Seconds(300)).Default()
        #self.listener = std.make_shared[AppChannelListener]()
        self.listener = asiodnp3.PrintingChannelListener().Create()       # (or use this during regression testing)
        self.channel = self.manager.AddTCPServer("server",
                                                 LOG_LEVELS,
                                                 self.server_accept_mode,
                                                 LOCAL_IP,
                                                 PORT,
                                                 self.listener)

        _log.debug('Adding the outstations to the channel.')
        self.command_handler = OutstationCommandHandler()
        #self.load_stations()
        # self.command_handler =  opendnp3.SuccessCommandHandler().Create() # (or use this during regression testing)

    def load_stations(self):
        # Load all of the required stations
            
        for station in self.config.outstations:
            print(station.desc)
            _log.debug(f'Configuring the DNP3 stacks for station {station.desc}.')

            stack_config = self.configure_stack(station)
            new_outstation = self.channel.AddOutstation("outstation", self.command_handler, self, stack_config)

            _log.debug(f'Enabling the outstation {station.desc}. Traffic will now start to flow.')
            new_outstation.Enable()

            # Put the Outstation singleton in OutstationApplication so that it can be used to send updates to the Master.
            OutstationApplication.add_outstation(new_outstation)

    @staticmethod
    def configure_stack(station):
        """Set up the OpenDNP3 configuration."""
        #get counts
        numAnalog = len(list(elem for elem in station.points.analogs if elem.point_type == "analog"))
        numBinary = len(list(station.points.binaries))
        numFloat = len(list(elem for elem in station.points.analogs if elem.point_type == "float"))

        stack_config = asiodnp3.OutstationStackConfig(opendnp3.DatabaseSizes(numBinary, 0, numAnalog + numFloat, 0,0,0,0,0,0))

        # later, we'll add events, but for now we'll leave it empty
        stack_config.outstation.eventBufferConfig = opendnp3.EventBufferConfig(0,0,0,0,0,0,0,0)
        # make this configurable
        stack_config.outstation.params.allowUnsolicited = True
        stack_config.link.LocalAddr = station.master_id
        stack_config.link.RemoteAddr = station.station_id
        stack_config.link.KeepAliveTimeout = openpal.TimeDuration().Max()

        db_config = stack_config.dbConfig

        _log.debug(f'Configuring the outstation database for station {station.desc}.')

        for point in station.points.analogs:
            if point.point_type == "analog":
                db_config.analog[point.point_id].clazz = opendnp3.PointClass.Class2
                db_config.analog[point.point_id].svariation = opendnp3.StaticAnalogVariation.Group30Var1
            elif point.point_type == "float":
                db_config.analog[point.point_id].clazz = opendnp3.PointClass.Class2
                db_config.analog[point.point_id].svariation = opendnp3.StaticAnalogVariation.Group30Var5
            else:
                assert(False)

        for point in station.points.binaries:
                db_config.binary[point.point_id].clazz = opendnp3.PointClass.Class2
                db_config.binary[point.point_id].svariation = opendnp3.StaticBinaryVariation.Group1Var2
        #configure_database(stack_config.dbConfig, station)

        return stack_config

    @staticmethod
    def configure_database(db_config, station):
        """
            Configure the Outstation's database of input point definitions.

            Configure two Analog points (group/variation 30.1) at indexes 1 and 2.
            Configure two Binary points (group/variation 1.2) at indexes 1 and 2.
        """
        _log.debug(f'Configuring the outstation database for station {station.desc}.')

        for point in station.points:
            if point.point_type == "analog":
                db_config.analog[point.point_id].clazz = opendnp3.PointClass.Class2
                db_config.analog[point.point_id] = opendnp3.StaticAnalogVariation.Group30Var1
            elif point.point_type == "float":
                db_config.analog[point.point_id].clazz = opendnp3.PointClass.Class2
                db_config.analog[point.point_id] = opendnp3.StaticAnalogVariation.Group30Var5
            elif point.point_type == "binary":
                db_config.analog[point.point_id].clazz = opendnp3.PointClass.Class2
                db_config.analog[point.point_id] = opendnp3.StaticAnalogVariation.Group30Var1
            

    def shutdown(self):
        """
            Execute an orderly shutdown of the Outstation.

            The debug messages may be helpful if errors occur during shutdown.
        """
        # _log.debug('Exiting application...')
        # _log.debug('Shutting down outstation...')
        # OutstationApplication.set_outstation(None)
        # _log.debug('Shutting down stack config...')
        # self.stack_config = None
        # _log.debug('Shutting down channel...')
        # self.channel = None
        # _log.debug('Shutting down DNP3Manager...')
        # self.manager = None

        self.manager.Shutdown()

    @classmethod
    def get_outstations(cls):
        """Get the singleton instance of IOutstation."""
        return cls.outstations

    @classmethod
    def add_outstation(cls, outstn):
        """
            Set the singleton instance of IOutstation, as returned from the channel's AddOutstation call.

            Making IOutstation available as a singleton allows other classes (e.g. the command-line UI)
            to send commands to it -- see apply_update().
        """
        cls.outstations.append(outstn)

    # Overridden method
    def ColdRestartSupport(self):
        """Return a RestartMode enumerated value indicating whether cold restart is supported."""
        _log.debug('In OutstationApplication.ColdRestartSupport')
        return opendnp3.RestartMode.UNSUPPORTED

    # Overridden method
    def GetApplicationIIN(self):
        """Return the application-controlled IIN field."""
        application_iin = opendnp3.ApplicationIIN()
        application_iin.configCorrupt = False
        application_iin.deviceTrouble = False
        application_iin.localControl = False
        application_iin.needTime = False
        # Just for testing purposes, convert it to an IINField and display the contents of the two bytes.
        iin_field = application_iin.ToIIN()
        #_log.debug('OutstationApplication.GetApplicationIIN: IINField LSB={}, MSB={}'.format(iin_field.LSB,
        #                                                                                     iin_field.MSB))
        return application_iin

    # Overridden method
    def SupportsAssignClass(self):
        _log.debug('In OutstationApplication.SupportsAssignClass')
        return False

    # Overridden method
    def SupportsWriteAbsoluteTime(self):
        _log.debug('In OutstationApplication.SupportsWriteAbsoluteTime')
        return False

    # Overridden method
    def SupportsWriteTimeAndInterval(self):
        _log.debug('In OutstationApplication.SupportsWriteTimeAndInterval')
        return False

    # Overridden method
    def WarmRestartSupport(self):
        """Return a RestartMode enumerated value indicating whether a warm restart is supported."""
        _log.debug('In OutstationApplication.WarmRestartSupport')
        return opendnp3.RestartMode.UNSUPPORTED

    @classmethod
    def process_point_value(cls, command_type, command, index, op_type):
        """
            A PointValue was received from the Master. Process its payload.

        :param command_type: (string) Either 'Select' or 'Operate'.
        :param command: A ControlRelayOutputBlock or else a wrapped data value (AnalogOutputInt16, etc.).
        :param index: (integer) DNP3 index of the payload's data definition.
        :param op_type: An OperateType, or None if command_type == 'Select'.
        """
        _log.debug('Processing received point value for index {}: {}'.format(index, command))


    def apply_update(self, value, outstation_id, index):
        """
            Record an opendnp3 data value (Analog, Binary, etc.) in the outstation's database.

            The data value gets sent to the Master as a side-effect.

        :param value: An instance of Analog, Binary, or another opendnp3 data value.
        :param index: (integer) Index of the data definition in the opendnp3 database.
        """
        #breakpoint()
        _log.debug('Recording {} measurement, index={}, value={}'.format(type(value).__name__, index, value.value))
        builder = asiodnp3.UpdateBuilder()
        builder.Update(value, index)
        update = builder.Build()
        OutstationApplication.get_outstations()[outstation_id - 1].Apply(update)

    def pika_on_message_callback(self, channel, method, properties, body):
        _log.debug('Message Received')
        body_text = body.decode(encoding='UTF-8')
        _log.debug(f'{body_text}')
        consumer_tag_info = method.consumer_tag.split("-")
        #breakpoint()
        for station in self.config.outstations:
            for point in station.points.analogs:
                if point.message_source_id == int(consumer_tag_info[0]) and point.message_topic_id == int(consumer_tag_info[1]):
                    #breakpoint()
                    topic = next(t for t in \
                            next(f for f in self.config.message_sources \
                                if f.message_source_id==point.message_source_id).topics 
                                if t.topic_id==point.message_topic_id)

                    if topic.source_message_type == "xml":
                        value = self.processXml(body_text, point.point_path)
                        #breakpoint()
                        if point.point_type == "analog" or point.point_type == "float" :
                            #breakpoint()
                            self.apply_update(opendnp3.Analog(float(value[0])), station.outstation_id, point.point_id)
                    else:
                        assert(False)
        
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def processXml(self, text, xpath):
        #f = StringIO(text)
        xml = bytes(bytearray(text, encoding='utf-8'))
        tree = etree.XML(xml)
        retval = tree.xpath(xpath)
        #TODO: Add error handling...
        return retval


    def start_listening(self):
                # establish connection/channel/queue to RabbitMQ
        for connection_source in self.config.message_sources:
            #ip.embed()
            if connection_source.source_type == "rabbitmq":
                pika_connection_params = pika.ConnectionParameters(
                    host=connection_source.source_uri,
                    heartbeat=600,
                    blocked_connection_timeout=300,
                )
                global connection
                connection = pika.BlockingConnection(pika_connection_params)
                #global channel 
                channel = connection.channel()

                for topic in connection_source.topics:

                    result = channel.queue_declare(queue='', exclusive=True)
                    _log.debug(f'Queue name {result.method.queue}')

                    channel.queue_bind(exchange=topic.name,
                            queue=result.method.queue)

                    channel.basic_consume(queue=result.method.queue, on_message_callback=self.pika_on_message_callback, consumer_tag=f"{connection_source.message_source_id}-{topic.topic_id}")
                    channel.start_consuming()
                #ip.embed()


class OutstationCommandHandler(opendnp3.ICommandHandler):
    """
        Override ICommandHandler in this manner to implement application-specific command handling.

        ICommandHandler implements the Outstation's handling of Select and Operate,
        which relay commands and data from the Master to the Outstation.
    """

    def Start(self):
        _log.debug('In OutstationCommandHandler.Start')

    def End(self):
        _log.debug('In OutstationCommandHandler.End')

    def Select(self, command, index):
        """
            The Master sent a Select command to the Outstation. Handle it.

        :param command: ControlRelayOutputBlock,
                        AnalogOutputInt16, AnalogOutputInt32, AnalogOutputFloat32, or AnalogOutputDouble64.
        :param index: int
        :return: CommandStatus
        """
        OutstationApplication.process_point_value('Select', command, index, None)
        return opendnp3.CommandStatus.SUCCESS

    def Operate(self, command, index, op_type):
        """
            The Master sent an Operate command to the Outstation. Handle it.

        :param command: ControlRelayOutputBlock,
                        AnalogOutputInt16, AnalogOutputInt32, AnalogOutputFloat32, or AnalogOutputDouble64.
        :param index: int
        :param op_type: OperateType
        :return: CommandStatus
        """
        OutstationApplication.process_point_value('Operate', command, index, op_type)
        return opendnp3.CommandStatus.SUCCESS


class AppChannelListener(asiodnp3.IChannelListener):
    """
        Override IChannelListener in this manner to implement application-specific channel behavior.
    """

    def __init__(self):
        super(AppChannelListener, self).__init__()

    def OnStateChange(self, state):
        _log.debug('In AppChannelListener.OnStateChange: state={}'.format(state))


class MyLogger(openpal.ILogHandler):
    """
        Override ILogHandler in this manner to implement application-specific logging behavior.
    """

    def __init__(self):
        super(MyLogger, self).__init__()

    def Log(self, entry):
        filters = entry.filters.GetBitfield()
        location = entry.location.rsplit('/')[-1] if entry.location else ''
        message = entry.message
        _log.debug('Log\tfilters={}\tlocation={}\tentry={}'.format(filters, location, message))


def main():
    """The Outstation has been started from the command line. Execute ad-hoc tests if desired."""
    global app 
    app = OutstationApplication()
    app.load_stations()
    _log.debug('Initialization complete. In command loop.')

    app.start_listening()
    # while(True):
    #     time.sleep(5)

    # Ad-hoc tests can be inserted here if desired. See outstation_cmd.py for examples.

    app.shutdown()

    _log.debug('Exiting.')
    exit()


if __name__ == '__main__':
    main()
