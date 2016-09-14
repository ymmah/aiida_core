# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"

from test.util import DbTestCase

from aiida.workflows2.process import Process
from aiida.workflows2.defaults import registry
from aiida.workflows2.workfunction import workfunction
from aiida.common.lang import override
from aiida.workflows2.run import async
from aiida.orm.data.base import Int
import aiida.workflows2.util as util


class RegistryTester(Process):
    @override
    def _run(self):
        assert registry.current_pid == self.pid
        assert registry.current_calc_node is self.calc
        nested_tester()


@workfunction
def registry_tester():
    # Call a wf
    future = async(nested_tester)
    out = future.result()
    assert future.pid == out['pid']
    assert future.pid == out['node_pk']

    # Call a Process
    RegistryTester.run()

    return {'pid': Int(registry.current_pid),
            'node_pk': Int(registry.current_calc_node.pk)}


@workfunction
def nested_tester():
    return {'pid': Int(registry.current_pid),
            'node_pk': Int(registry.current_calc_node.pk)}


class TestProcessRegistry(DbTestCase):
    """
    These these check that the registry is giving out the right pid which when
    using storage is equal to the node pk.
    """
    def setUp(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_process_pid_and_calc(self):
        RegistryTester.run()

    def test_wf_pid_and_calc(self):
        future = async(registry_tester)
        out = future.result()

        self.assertEqual(out['pid'], future.pid)
        self.assertEqual(out['node_pk'], future.pid)





