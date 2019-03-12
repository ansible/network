from ansible.module_utils.argspec.base import ArgspecBase


class ConfigBase(ArgspecBase):

    def search_obj_in_list(self, name, lst):
        for o in lst:
            if o['name'] == name:
                return o
        return None
