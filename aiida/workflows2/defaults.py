# -*- coding: utf-8 -*-
import os.path
import uritools
import aiida.common.setup as setup
import aiida.settings as settings
from plum.engine.serial import SerialEngine
import plum.class_loader
from plum.engine.parallel import MultithreadedEngine
from aiida.workflows2.class_loader import ClassLoader
from aiida.workflows2.process_registry import ProcessRegistry

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."

# Have globals that can be used by all of AiiDA
class_loader = plum.class_loader.ClassLoader(ClassLoader())
registry = ProcessRegistry()
parallel_engine = MultithreadedEngine()
serial_engine = SerialEngine()

parts = uritools.urisplit(settings.REPOSITORY_URI)
if parts.scheme == u'file':
    import aiida.workflows2.persistence
    WORKFLOWS_DIR = os.path.expanduser(
        os.path.join(parts.path, setup.WORKFLOWS_SUBDIR))
    storage = aiida.workflows2.persistence.Persistence(
        auto_persist=False,
        running_directory=os.path.join(WORKFLOWS_DIR, 'running'),
        finished_directory=os.path.join(WORKFLOWS_DIR, 'finished'),
        failed_directory=os.path.join(WORKFLOWS_DIR, 'failed'))