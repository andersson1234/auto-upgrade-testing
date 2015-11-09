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

import logging
import os
import shutil
import tempfile
import pkg_resources

from collections import namedtuple
from contextlib import contextmanager
from textwrap import dedent

from upgrade_testing.preparation._testbed import get_testbed_storage_location

logger = logging.getLogger(__name__)


# Definition for the tempfiles that are created for a run and cleaned up
# afterwards.
TestrunTempFiles = namedtuple(
    'TestrunTempFiles', ['run_config_file', 'testrun_tmp_dir', 'unbuilt_dir']
)


@contextmanager
def prepare_test_environment(testsuite):
    """Return a TestrunTempFiles instance that is cleaned up once out of scope.

    Creates a temp directory an populates it with the required data structure
    to copy across to the testbed.
    Namely:
      - Test run config details
      - 'Dummy' debian/autopkgtest details for this run.

    :param testsuite: TestSpecification instance.

    """

    try:
        temp_dir = tempfile.mkdtemp()
        run_config_path = _write_run_config(testsuite, temp_dir)
        unbuilt_dir = _create_autopkg_details(temp_dir)
        logger.info('Unbuilt dir: {}'.format(unbuilt_dir))
        yield TestrunTempFiles(
            run_config_file=run_config_path,
            # Should we create a dir so that it won't interfer?
            unbuilt_dir=temp_dir,
            testrun_tmp_dir=temp_dir,
        )
    finally:
        _cleanup_dir(temp_dir)


def _cleanup_dir(dir):
    shutil.rmtree(dir)


def _write_run_config(testsuite, temp_dir):
    """Write a config file for this run of testing.

    Populates a config file with the details from the test config spec as well
    as the dynamic details produced each run (temp dir etc.).

    """
    run_config_file = tempfile.mkstemp(dir=temp_dir)[1]
    with open(run_config_file, 'w') as f:
        pre_tests = ' '.join(testsuite.pre_upgrade_scripts)
        post_tests = ' '.join(testsuite.post_upgrade_tests)
        config_string = dedent('''\
            # Auto Upgrade Test Configuration
            PRE_TEST_LOCATION="{testbed_location}/pre_scripts"
            POST_TEST_LOCATION="{testbed_location}/post_scripts"
        '''.format(testbed_location=get_testbed_storage_location()))
        f.write(config_string)
        f.write('PRE_TESTS_TO_RUN="{}"\n'.format(pre_tests))
        f.write('POST_TESTS_TO_RUN="{}"\n'.format(post_tests))
        # Need to store the expected pristine system and the post-upgrade
        # system
        # Note: This will only support one upgrade, for first -> final
        f.write(
            'INITIAL_SYSTEM_STATE="{}"\n'.format(
                testsuite.provisioning.initial_state
            )
        )
        f.write(
            'POST_SYSTEM_STATE="{}"\n'.format(
                testsuite.provisioning.final_state
            )
        )
    return run_config_file


def _create_autopkg_details(temp_dir):
    """Create a'dummy' debian dir structure for autopkg testing.

    Given a temp dir build the required dir tree and populate it with the
    needed files.

    The test file that is executed is already populated and part of this
    project.

    """
    dir_tree = os.path.join(temp_dir, 'debian')
    test_dir_tree = os.path.join(dir_tree, 'tests')
    os.makedirs(test_dir_tree)

    import upgrade_testing
    source_dir = pkg_resources.resource_filename(
        upgrade_testing.__name__, 'data'
    )

    def _copy_file(dest, name):
        """Copy a file from the source data dir to dest."""
        src = os.path.join(source_dir, name)
        dst = os.path.join(dest, name)
        shutil.copyfile(src, dst)

    _copy_file(test_dir_tree, 'control')
    _copy_file(test_dir_tree, 'upgrade')
    _copy_file(dir_tree, 'changelog')

    # Main control file can be empty
    dummy_control = os.path.join(dir_tree, 'control')
    open(dummy_control, 'a').close()

    return dir_tree
