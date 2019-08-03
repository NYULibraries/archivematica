# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

# @package Archivematica
# @subpackage MCPServer
# @author Joseph Perry <joseph@artefactual.com>

from linkTaskManager import LinkTaskManager
from taskGroup import TaskGroup

import archivematicaFunctions
from dicts import ReplacementDict

from taskGroupRunner import TaskGroupRunner


class linkTaskManagerDirectories(LinkTaskManager):
    def __init__(self, jobChainLink, unit):
        super(linkTaskManagerDirectories, self).__init__(jobChainLink, unit)
        config = self.jobChainLink.link.config
        filterSubDir = config["filter_subdir"]
        standardOutputFile = config["stdout_file"]
        standardErrorFile = config["stderr_file"]
        execute = config["execute"]
        arguments = config["arguments"]

        # Used by ``TaskGroup._log_task``.
        self.execute = config["execute"]

        # Apply passvar replacement values
        if self.jobChainLink.passVar is not None:
            if isinstance(self.jobChainLink.passVar, list):
                for passVar in self.jobChainLink.passVar:
                    if isinstance(passVar, ReplacementDict):
                        arguments, standardOutputFile, standardErrorFile = passVar.replace(
                            arguments, standardOutputFile, standardErrorFile
                        )
            elif isinstance(self.jobChainLink.passVar, ReplacementDict):
                arguments, standardOutputFile, standardErrorFile = self.jobChainLink.passVar.replace(
                    arguments, standardOutputFile, standardErrorFile
                )

        # Apply unit (SIP/Transfer) replacement values
        commandReplacementDic = unit.get_replacement_mapping(
            filter_subdir_path=filterSubDir
        )
        # Escape all values for shell
        for key, value in commandReplacementDic.items():
            escapedValue = archivematicaFunctions.escapeForCommand(value)
            if arguments is not None:
                arguments = arguments.replace(key, escapedValue)
            if standardOutputFile is not None:
                standardOutputFile = standardOutputFile.replace(key, escapedValue)
            if standardErrorFile is not None:
                standardErrorFile = standardErrorFile.replace(key, escapedValue)

        group = TaskGroup(self, execute)
        group.addTask(
            arguments,
            standardOutputFile,
            standardErrorFile,
            commandReplacementDic=commandReplacementDic,
        )
        group.logTaskCreatedSQL()
        TaskGroupRunner.runTaskGroup(group, self.taskGroupFinished)

    def taskGroupFinished(self, finishedTaskGroup):
        finishedTaskGroup.write_output()

        self.jobChainLink.linkProcessingComplete(
            finishedTaskGroup.calculateExitCode(), self.jobChainLink.passVar
        )
