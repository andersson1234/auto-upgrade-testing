#
# Ubuntu Upgrade Testing
# Copyright (C) 2015 Canonical
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from upgrade_testing.provisioning import backends


class ProvisionSpecification:
    def __init__(self):
        raise NotImplementedError()

    @property
    def system_states(self):
        # Note: Rename from releases
        raise NotImplementedError()

    @property
    def initial_state(self):
        """Return the string indicating the required initial system state."""
        raise NotImplementedError()

    @property
    def final_state(self):
        """Return the string indicating the required final system state."""
        raise NotImplementedError()

    @staticmethod
    def from_testspec(spec):
        backend_name = spec['provisioning']['backend']
        spec_type = get_specification_type(backend_name)
        return spec_type(spec['provisioning'])

    @staticmethod
    def from_provisionspec(spec):
        # A provision spec is almost the same as a testdef provision spec
        # except it doesn't have the parent stanza.
        backend_name = spec['backend']
        spec_type = get_specification_type(backend_name)
        return spec_type(spec)


def get_specification_type(spec_name):
    __spec_map = dict(
        lxc=LXCProvisionSpecification,
        device=DeviceProvisionSpecification
    )
    return __spec_map[spec_name]


class LXCProvisionSpecification(ProvisionSpecification):
    def __init__(self, provision_config):
        # Defaults to ubuntu
        self.distribution = provision_config.get('distribution', 'ubuntu')
        self.releases = provision_config['releases']

        self.backend = backends. LXCBackend(
            self.initial_state,
            self.distribution
        )

    @property
    def system_states(self):
        # Note: Rename from releases
        return self.releases

    @property
    def initial_state(self):
        """Return the string indicating the required initial system state."""
        return self.releases[0]

    @property
    def final_state(self):
        """Return the string indicating the required final system state."""
        return self.releases[-1]

    def __repr__(self):
        return '{classname}(backend={backend}, distribution={dist}, releases={releases})'.format(  # NOQA
            classname=self.__class__.__name__,
            backend=self.backend,
            dist=self.distribution,
            releases=self.releases
        )


class DeviceProvisionSpecification(ProvisionSpecification):
    def __init__(self, provision_config):
        try:
            self.channel = provision_config['channel']
            self.revisions = provision_config['revisions']
        except KeyError as e:
            raise ValueError('Missing config detail: {}'.format(str(e)))

        serial = provision_config.get('serial', None)
        password = provision_config.get('password', None)
        self.backend = backends.DeviceBackend(
            self.channel,
            self.initial_state,
            password,
            serial,
        )

    def _construct_state_string(self, rev):
        return '{channel}:{rev}'.format(channel=self.channel, rev=rev)

    @property
    def system_states(self):
        return [self._construct_state_string(r) for r in self.revisions]

    @property
    def initial_state(self):
        """Return the string indicating the required initial system state."""
        return self._construct_state_string(self.revisions[0])

    @property
    def final_state(self):
        """Return the string indicating the required final system state."""
        return self._construct_state_string(self.revisions[-1])

    def __repr__(self):
        return '{classname}(backend={backend}, channel={channel}, revisions={revisions})'.format(  # NOQA
            classname=self.__class__.__name__,
            backend=self.backend,
            channel=self.channel,
            revisions=self.system_states
        )
