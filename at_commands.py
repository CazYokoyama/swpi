###########################################################################
#     Sint Wind PI
#     Copyright 2012 by Tonino Tarsi <tony.tarsi@gmail.com>
#     Modem comunications based on Slawek Ligus pyhumod-0.03 module
#   
#     Please refer to the LICENSE file for conditions 
#     Visit http://www.vololiberomontecucco.it
# 
##########################################################################
"""Classes and methods for handling AT commands."""


import re
import errors
from warnings import warn
from TTLib import *

# Deprecated decorator.
def deprecated(dep_func):
    """Decorator used to mark functions as deprecated."""
    def warn_and_run(*args, **kwargs):
        """Print warning and run the function."""
        warn('%r is deprecated and scheduled for removal.' % \
             dep_func.__name__)
        return dep_func(*args, **kwargs)
    return warn_and_run

class Command(object):
    """Class defining generic perations performed on AT commands."""

    def __init__(self, modem, cmd, prefixed=True):
        """Constructor for Command class."""
        self.cmd = cmd
        self.modem = modem
        self.prefixed = prefixed

    def run(self):
        r"""Send the AT command followed by the '\r' character to the modem.
        
        Returns:
            List of strings.
        """
        self.modem.ctrl_port.read_waiting()
        return self.modem.ctrl_port.send_at(self.cmd, '', self.prefixed)
        

    def get(self):
        r"""Send the AT command followed by the '?\r' characters to the modem.
        
        Returns:
            List of strings.
        """
        self.modem.ctrl_port.read_waiting()
        return self.modem.ctrl_port.send_at(self.cmd, '?', self.prefixed)

    def set(self, value):
        r"""Send the 'AT<+CMD>=<value>\r' string to the modem.
        
        Returns:
            List of strings.
        """
        self.modem.ctrl_port.read_waiting()
        return self.modem.ctrl_port.send_at(self.cmd, '=%s' % value,
                                         self.prefixed)

    def dsc(self):
        r"""Send the AT command followed by the '=?\r' characters to the modem.
        
        Returns:
            List of strings.
        """
        self.modem.ctrl_port.read_waiting()
        return self.modem.ctrl_port.send_at(self.cmd, '=?', self.prefixed)


def _common_run(modem, at_cmd, prefixed=True):
    """Boilerplate for most methods based on Command.run()."""
    info_cmd = Command(modem, at_cmd, prefixed)
    modem.ctrl_lock.acquire()
    try:
        data = info_cmd.run()
        return data
    finally:
        modem.ctrl_lock.release()

def _common_get(modem, at_cmd, prefixed=True):
    """Boilerplate for most methods based on Command.get()."""
    data_cmd = Command(modem, at_cmd, prefixed)
    modem.ctrl_lock.acquire()
    try:
        data = data_cmd.get()
        return data
    finally:
        modem.ctrl_lock.release()

def _common_dsc(modem, at_cmd, prefixed=True):
    """Boilerplate for most methods based on Command.dsc()."""
    data_cmd = Command(modem, at_cmd, prefixed)
    modem.ctrl_lock.acquire()
    try:
        data = data_cmd.dsc()
        return data
    finally:
        modem.ctrl_lock.release()

def _common_set(modem, at_cmd, value, prefixed=True):
    """Boilerplate for most methods based on Command.set()."""
    modem.ctrl_lock.acquire()
    try:
        data = Command(modem, at_cmd, prefixed).set(value)
        return data
    finally:
        modem.ctrl_lock.release()


class InteractiveCommands(object):
    """SIM interactive commands."""
    ctrl_lock = None
    ctrl_port = None
    
    def sms_send(self, number, contents):
        """Send a text message from the modem.
        
        Arguments:
            number -- string with reciepent number,
            contents -- text message body.
        
        Returns:
            Sent text message number since last counter reset.
        """
        self.ctrl_lock.acquire()
        try:
            self.ctrl_port.write('AT+CMGS="%s"\r\n' % number)
            # Perform a SIM test first.
            self.ctrl_port.write(contents+chr(26))
            result = self.ctrl_port.return_data()
            # A text number is an integer number, returned in the
            # last returned entry of the result, just after the ": " part.
            text_number = int(result[-1].split(': ')[1])
            return text_number
        finally:
            self.ctrl_lock.release()

    def sms_list(self, message_type='ALL'):
        """List messages by type.
        
        Arguments:
            message_type -- one of the following strings:
                'ALL' -- all messages,
                'REC READ' -- read messages,
                'REC UNREAD' -- unread messages,
                'STO SENT' -- stored sent messages,
                'STO UNSENT' -- stored unsent messages.
        Returns:
            list of string lists representing message headers.
        """
        self.ctrl_lock.acquire()
        try:
            message_lister = Command(self, '+CMGL')
            messages_data = message_lister.set('"%s"' % message_type)
            return _enlist_data(messages_data, 4)
        finally:
            self.ctrl_lock.release()

    def sms_read(self, message_num):
        """Read one message from the SIM.
        
        Arguments:
            message_num -- number of a message to read.
        Returns:
            message body (string) or None if the message isn't found.
        """
        self.ctrl_lock.acquire()
        try:
            message_reader = Command(self, '+CMGR', prefixed=False)
            message = message_reader.set(message_num)
            # Slicing out the header.
            return '\n'.join(message[1:])
        finally:
            self.ctrl_lock.release()

    def sms_del(self, message_num):
        """Delete message from the SIM."""
        msg_num_str = '%d' % message_num
        _common_set(self, '+CMGD', msg_num_str)

    @deprecated
    def del_message(self, message_num):
        """Deprecated equivalent of sms_del."""
        return self.sms_del(message_num)

    @deprecated
    def read_message(self, message_num):
        """Deprecated equivalent of sms_read."""
        return self.sms_read(message_num)

    @deprecated
    def send_text(self, number, contents):
        """Deprecated equivalent of sms_send."""
        return self.sms_send(number, contents)

    @deprecated
    def list_messages(self, message_type='ALL'):
        """Deprecated equivalent of sms_list."""
        return self.sms_list(message_type)

    def hangup(self):
        """Hang up."""
        log( "Hang up")
        _common_run(self, '+CHUP', prefixed=False)
		
    def answer (self):
        """answer  up."""
        log( "answering ...")
        _common_run(self, 'A', prefixed=False)		

    def pbent_read(self, start_index, end_index=None):
        """Read phonebook entries."""
        return_range = True
        if not end_index:
            end_index = start_index
            return_range = False
        index_range = '%d,%d' % (start_index, end_index)
        entries = _common_set(self, '+CPBR', index_range)
        if start_index > end_index:
            entries.reverse()
        entries_list = _enlist_data(entries)
        if return_range:
            return entries_list
        return entries_list[0]

    def pbent_find(self, query=''):
        """Find phonebook entries matching a query string."""
        entries = _common_set(self, '+CPBF', '"%s"' % query)
        return _enlist_data(entries)

    def pbent_write(self, index, number, text, numtype=145):
        """Write a phonebook entry."""
        param = '%d,"%s",%d,"%s"' % (index, number, numtype, text)
        _common_set(self, '+CPBW', param)

    def pbent_del(self, index):
        """Clear out a phonebook entry."""
        _common_set(self, '+CPBW', '%d' % index)

    @deprecated
    def find_pbent(self, query=''):
        """Deprecated equivalent of pbent_find."""
        return self.pbent_find(query)

    @deprecated
    def read_pbent(self, start_index, end_index=None):
        """Deprecated equivalent of pbent_list."""
        return self.pbent_read(start_index, end_index)

    @deprecated
    def del_pbent(self, index):
        """Deprecated equivalent of pbent_del."""
        return self.pbent_del(index)

    @deprecated
    def write_pbent(self, index, number, text, numtype=145):
        """Deprecated equivalent of pbent_write."""
        return self.pbent_write(index, number, text, numtype)

class ShowCommands(object):
    """Show methods extract static read-only data."""

    def show_status(self):
        """Show Activity status of the mobile phone."""
        return _common_run(self, '+CPAS', prefixed=True)[0]

    def show_imei(self):
        """Show IMEI serial number."""
        return _common_run(self, '+GSN', prefixed=False)[0]

    def show_sn(self):
        """Show serial number."""
        return _common_run(self, '^SN', prefixed=True)[0]

    def show_manufacturer(self):
        """Show manufacturer name."""
        return _common_run(self, '+GMI', prefixed=False)[0]

    def show_model(self):
        """Show device model name."""
        return _common_run(self, '+GMM', prefixed=False)[0]
        
    def show_revision(self):
        """Show device revision."""
        return _common_run(self, '+GMR', prefixed=False)[0]

    def show_hardcoded_operators(self):
        """List operators hardcoded on the device."""
        hard_ops_list = _common_run(self, '+COPN')
        data = dict()
        for entry in hard_ops_list:
            num, op_name = [item[1:-1] for item in entry.split(',', 1)] 
            data[num] = op_name
        return data

    def show_who_locked(self):
        """Show which network operator has locked the device."""
        locker_info = _common_dsc(self, '^CARDLOCK', prefixed=True)
        if locker_info:
            # Slice brackets off.
            locker_info = locker_info[0][1:-1].split(',')
        return locker_info

class SetCommands(object):
    """Set methods write user settings that are kept permanently."""

    # pylint: disable-msg=R0913
    def set_pdp_context(self, num, proto='IP', apn='', ip_addr='', d_comp=0,
                        h_comp=0):
        """Set Packet Data Protocol context."""
        pdp_context_str = '%d,"%s","%s","%s",%d,%d' % (num, proto, apn, 
                                                       ip_addr, d_comp, h_comp)
        _common_set(self, '+CGDCONT', pdp_context_str)

    def	set_destination_port(self,port):
        _common_set(self, '^DDSETEX', port)



    def set_service_center(self, sca, tosca=145):
        """Set Service Center address and type.
        
        Args:
          sca -- String with service center address,
          tosca -- Integer with SC type.
        Raises:
          AtCommandError -- if tosca contains an unknown value for SC type,
          TypeError -- if SC type is not an integer.
        """
        # Possible type of SC values:
        #  128: unknown
        #  129: national
        #  145: international
        #  161: national 
        if tosca not in (128, 129, 145, 161):
            raise errors.AtCommandError('Unknown SC type: %i.' % tosca)
        sca_str = '"%s",%i' % (sca, tosca)
        _common_set(self, '+CSCA', sca_str)

class EnterCommands(object):
    """Enter methods write user settings that are kept until modem restarts."""

    def enter_pin(self, pin, new_pin=None):
        """Enter or set new PIN."""
        if new_pin:
            set_arg = '"%d","%d"' % (pin, new_pin)
        else:
            set_arg = '"%d"' % pin
        
        return _common_set(self, '+CPIN', set_arg)

    def _common_enable(self, command, active, inactive, status, 
                       active_set=None, inactive_set=None):
        """Enable, disable or check status of a setting."""
        if not active_set: 
            active_set = active
        if not inactive_set:
            inactive_set = inactive

        if status is None:
            result = _common_get(self, command)[0]
            return result == active
        if status is True:
            _common_set(self, command, active_set)
        else:
            _common_set(self, command, inactive_set)

    def enable_nmi(self, status=None):
        """Enable, disable or check status on new message indications."""
        return self._common_enable('+CNMI', '2,1,0,2,1', '0,0,0,0,0', status)

    def enable_clip(self, status=None):
        """Enable, disable or check status of calling line identification."""
        return self._common_enable('+CLIP', '1,1', '0,1', status, '1', '0')

    def enable_textmode(self, status=None):
        """Enable, disable or find out about current mode."""
        return self._common_enable('+CMGF', '1', '0', status)

    @deprecated
    def enter_text_mode(self):
        """Enter text mode."""
        _common_set(self, '+CMGF', '1')

    @deprecated
    def enter_pdu_mode(self):
        """Enter PDU mode."""
        _common_set(self, '+CMGF', '0')

class GetCommands(object):
    """Get methods read dynamic or user-set data."""

    def get_networks(self):
        """Scan for networks."""
        active_ops = _common_dsc(self, '+COPS')
        bracket_group = re.compile('\(.+?\)')
        if active_ops:
            data = list()
            network_data_list = bracket_group.findall(active_ops[0])
            for network_data_set in network_data_list:
                unbracketed_set = network_data_set[1:-1]
                items = unbracketed_set.split(',')
                if len(items) == 5:
                    transformed_set = [_transform(ni) for ni in items]
                    data.append(transformed_set)
            return data

    def get_clock(self):
        """Return internal modem clock."""
        return _common_get(self, '+CCLK')[0]

    def get_service_center(self):
        """Show service center number."""
        sc_data = _common_get(self, '+CSCA')[0].split(',', 1)
        service_center, sc_type_num = [_transform(item) for item in sc_data]
        return service_center, sc_type_num

    def get_detailed_error(self):
        """Print detailed error message."""
        return _common_run(self, '+CEER')[0]

    def get_rssi(self):
        """Show RSSI level."""
        rssi_info = _common_run(self, '+CSQ')[0]
        rssi = rssi_info.split(',', 1)
        return int(rssi[0])

    def get_pin_status(self):
        """Inform about PIN status.
        
        Returns:
            'READY' -- sim card ready to use,
            'SIM PIN' -- PIN required,
            'SIM PUK' -- PUK required.
        """
        pin_info = _common_get(self, '+CPIN')[0]
        return pin_info

    def get_pdp_context(self):
        """Read PDP context entries."""
        pdp_context_data = _common_get(self, '+CGDCONT')
        data = _enlist_data(pdp_context_data)
        return data

    @deprecated
    def get_mode(self):
        """Get current mode.
        
        Returns:
            0 -- PDU mode,
            1 -- Text mode.
        """
        current_mode = _common_get(self, '+CMGF')[0]
        return int(current_mode)


def _transform(pdp_item):
    """Return a string if pdp_item starts with quotes or integer otherwise."""
    if pdp_item:
        if pdp_item.startswith('"'):
            return pdp_item[1:-1]
        else:
            return int(pdp_item)
    else:
        return ''

def _enlist_data(string_list, max_split=None):
    """Transform data strings into data lists and return them."""
    entries_list = list()
    if max_split:
        for entry in string_list:
            entry_list = [_transform(item) for item 
                          in entry.split(',', max_split)]
            entries_list.append(entry_list)
    else:
        for entry in string_list:
            entry_list = [_transform(item) for item in entry.split(',')]
            entries_list.append(entry_list)
    return entries_list
