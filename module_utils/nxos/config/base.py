from ansible.module_utils.connection import Connection


class ConfigBase(object):

    _connection = None

    def __init__(self, module):
        self._module = module
        self._connection = self._get_connection()

    def _get_connection(self):
        if self._connection:
            return self._connection
        self._connection = Connection(self._module._socket_path)
        return self._connection
