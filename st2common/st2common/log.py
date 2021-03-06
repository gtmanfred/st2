# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import socket
import datetime
import logging
import logging.config
import logging.handlers
import os
import six
import sys
import traceback

from oslo.config import cfg

logging.AUDIT = logging.CRITICAL + 10
logging.addLevelName(logging.AUDIT, 'AUDIT')


def getLogger(name):
    logger_name = 'st2.{}'.format(name)
    return logging.getLogger(logger_name)


class FormatNamedFileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding=None, delay=False):
        # Include timestamp in the name.
        filename = filename.format(ts=str(datetime.datetime.utcnow()).replace(' ', '_'),
                                   pid=os.getpid())
        super(FormatNamedFileHandler, self).__init__(filename, mode, encoding, delay)


class ConfigurableSyslogHandler(logging.handlers.SysLogHandler):
    def __init__(self, address=None, facility=None, socktype=None):
        if not address:
            address = (cfg.CONF.syslog.host, cfg.CONF.syslog.port)
        if not facility:
            facility = cfg.CONF.syslog.facility
        if not socktype:
            protocol = cfg.CONF.syslog.protocol.lower()

            if protocol == 'udp':
                socktype = socket.SOCK_DGRAM
            elif protocol == 'tcp':
                socktype = socket.SOCK_STREAM
            else:
                raise ValueError('Unsupported protocol: %s' % (protocol))

        if socktype:
            super(ConfigurableSyslogHandler, self).__init__(address, facility, socktype)
        else:
            super(ConfigurableSyslogHandler, self).__init__(address, facility)


class ExclusionFilter(object):

    def __init__(self, exclusions):
        self._exclusions = set(exclusions)

    def filter(self, record):
        if len(self._exclusions) < 1:
            return True
        module_decomposition = record.name.split('.')
        exclude = len(module_decomposition) > 0 and module_decomposition[0] in self._exclusions
        return not exclude


class LoggingStream(object):

    def __init__(self, name, level=logging.ERROR):
        self._logger = getLogger(name)
        self._level = level

    def write(self, message):
        self._logger._log(self._level, message, None)


def _audit(logger, msg, *args, **kwargs):
    if logger.isEnabledFor(logging.AUDIT):
        logger._log(logging.AUDIT, msg, args, **kwargs)

logging.Logger.audit = _audit


def _add_exclusion_filters(handlers):
    for h in handlers:
        h.addFilter(ExclusionFilter(cfg.CONF.log.excludes))


def _redirect_stderr():
    # It is ok to redirect stderr as none of the st2 handlers write to stderr.
    if cfg.CONF.log.redirect_stderr:
        sys.stderr = LoggingStream('STDERR')


def setup(config_file, disable_existing_loggers=False):
    """Configure logging from file.
    """
    try:
        logging.config.fileConfig(config_file,
                                  defaults=None,
                                  disable_existing_loggers=disable_existing_loggers)
        handlers = logging.getLoggerClass().manager.root.handlers
        _add_exclusion_filters(handlers)
        _redirect_stderr()
    except Exception as exc:
        # revert stderr redirection since there is no logger in place.
        sys.stderr = sys.__stderr__
        # No logger yet therefore write to stderr
        sys.stderr.write('ERROR: %s' % traceback.format_exc())
        raise Exception(six.text_type(exc))
