'''
Test code for submitting issues to CPPYY if necessary.
'''


import sys
import cppyy

cppyy.cppdef("""
namespace opendnp3
{
struct LogLevel
{
public:
    LogLevel() = default;

    explicit LogLevel(int32_t level) : value(level) {}

    LogLevel next() const
    {
        return LogLevel(value << 1);
    }

    bool operator==(const LogLevel& other) const
    {
        return this->value == other.value;
    }

    int32_t value = 0;
};

class LogLevels
{
public:
    LogLevels() = default;

    explicit LogLevels(int32_t levels) : levels(levels) {}

    LogLevels(LogLevel level) : levels(level.value) {}

    static LogLevels none()
    {
        return LogLevels(0);
    }

    static LogLevels everything()
    {
        return LogLevels(~0);
    }

    inline bool is_set(const LogLevel& level) const
    {
        return (level.value & levels) != 0;
    }

    LogLevels operator~() const
    {
        return LogLevels(~this->levels);
    }

    LogLevels& operator|=(const LogLevel& other)
    {
        this->levels |= other.value;
        return *this;
    }

    LogLevels operator|(const LogLevel& other) const
    {
        return LogLevels(this->levels | other.value);
    }

    LogLevels& operator|=(const LogLevels& other)
    {
        this->levels |= other.levels;
        return *this;
    }

    LogLevels operator|(const LogLevels& other) const
    {
        return LogLevels(this->levels | other.levels);
    }

    inline int32_t get_value() const
    {
        return levels;
    }

private:
    int32_t levels = 0;
};


namespace flags
{


    // base filters
    const LogLevel EVENT = LogLevel(1);
    const LogLevel ERR = EVENT.next();
    const LogLevel WARN = ERR.next();
    const LogLevel INFO = WARN.next();
    const LogLevel DBG = INFO.next();

    // up-shift the custom dnp3 filters

    const LogLevel LINK_RX = DBG.next();
    const LogLevel LINK_RX_HEX = LINK_RX.next();

    const LogLevel LINK_TX = LINK_RX_HEX.next();
    const LogLevel LINK_TX_HEX = LINK_TX.next();

    const LogLevel TRANSPORT_RX = LINK_TX_HEX.next();
    const LogLevel TRANSPORT_TX = TRANSPORT_RX.next();

    const LogLevel APP_HEADER_RX = TRANSPORT_TX.next();
    const LogLevel APP_HEADER_TX = APP_HEADER_RX.next();

    const LogLevel APP_OBJECT_RX = APP_HEADER_TX.next();
    const LogLevel APP_OBJECT_TX = APP_OBJECT_RX.next();

    const LogLevel APP_HEX_RX = APP_OBJECT_TX.next();
    const LogLevel APP_HEX_TX = APP_HEX_RX.next();

} // namespace flags
namespace levels
{
    const LogLevels NOTHING = LogLevels::none();
    const LogLevels ALL = LogLevels::everything();
    const LogLevels NORMAL = NOTHING | flags::EVENT | flags::ERR | flags::WARN | flags::INFO;
    const LogLevels ALL_APP_COMMS = NOTHING | flags::APP_HEADER_RX | flags::APP_HEADER_TX | flags::APP_OBJECT_RX
        | flags::APP_OBJECT_TX | flags::APP_HEX_RX | flags::APP_HEX_TX;
    const LogLevels ALL_COMMS
        = ALL_APP_COMMS | flags::LINK_RX | flags::LINK_TX | flags::TRANSPORT_RX | flags::TRANSPORT_TX;
} // namespace levels
}
""")
print(cppyy.gbl.opendnp3.levels.NORMAL)
#from cppyy.gbl import CommandHandler
#from cppyy.gbl import Foo

#testCommand = CommandHandler()
#testFoo = Foo()
#print(testCommand.Foobar(testFoo))