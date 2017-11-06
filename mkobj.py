#!/usr/bin/env python
# Contributors Listed Below - COPYRIGHT 2017
# [+] International Business Machines Corp.
#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""
mkobj is a D-Bus application that enables creation of arbitrary
D-Bus interfaces on arbitrary paths.  The intended use case is
for mocking of objects.

A typical usage pattern might be:

1 - Start the application
  ./mkobj.py

2 - Create an interface (xyz.openbmc_project.Testing.Interface on /xyz/openbmc_project/test_obj)
  busctl call xyz.openbmc_project.Testing \
          /xyz/openbmc_project/testing/create/object \
          xyz.openbmc_project.Testing.Object.Create \
          Create sas /xyz/openbmc_project/test_obj 1 xyz.openbmc_project.Testing.Interface

3 - Populate and set properties on the newly created interface
  busctl set-property xyz.openbmc_project.Testing \
          /xyz/openbmc_project/test_obj \
          xyz.openbmc_project.Interface \
          SomeProperty as 1 value
"""

import dbus
import dbus.service
import dbus.mainloop.glib
import gobject
import obmc.dbuslib.bindings
import sys

DBUS_NAME = 'xyz.openbmc_project.Testing'
CREATE_NAME = 'xyz.openbmc_project.Testing.Object.Create'
REMOVE_NAME = 'xyz.openbmc_project.Testing.Object.Delete'

class Object(obmc.dbuslib.bindings.DbusProperties):
    def __init__(self, manager, *a, **kw):
        super(Object, self).__init__(*a, **kw)
        self.path = kw.get('object_path')
        self.manager = manager
        self.unmask_signals()

    @dbus.service.method(REMOVE_NAME, '', '')
    def Delete(self):
        self.manager.remove(self.path)


def get_object_class(ifaces):
    name = '+'.join(['ObjectType'] + ifaces)
    cls = type(name, (Object,), {})
    obmc.dbuslib.bindings.add_interfaces_to_class(cls, ifaces)

    return cls


class ObjectFactory(dbus.service.Object):
    def __init__(self, *a, **kw):
        manager_path = kw.pop('manager_path')
        self.dbus_bus = kw.get('conn')
        super(ObjectFactory, self).__init__(*a, **kw)

        kw['object_path'] = manager_path
        self.manager = obmc.dbuslib.bindings.DbusObjectManager(*a, **kw)
        self.manager.unmask_signals()

    @dbus.service.method(CREATE_NAME, 'sas', '')
    def Create(self, path, ifaces):
        ifaces = [str(x) for x in ifaces]
        Obj = get_object_class(ifaces)
        o = Obj(self.manager, conn=self.dbus_bus, object_path=path)
        for iface in ifaces:
            o.properties[iface] = {}
        self.manager.add(path, o)


def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    dbus_bus = dbus.SystemBus()
    path = '/xyz/openbmc_project/testing/create/object'
    manager_path = '/xyz/openbmc_project'

    factory = ObjectFactory(
        manager_path=manager_path,
        conn=dbus_bus,
        object_path=path)
    name = dbus.service.BusName(DBUS_NAME, dbus_bus)

    loop = gobject.MainLoop()
    loop.run()


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
