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

import ast
import json
import logging

from st2client import formatters
from st2client.utils import jsutil
from st2client.utils import strutil


LOG = logging.getLogger(__name__)


class ExecutionResult(formatters.Formatter):

    @classmethod
    def format(cls, entry, *args, **kwargs):
        attrs = kwargs.get('attributes', [])
        key = kwargs.get('key', None)
        if key:
            output = jsutil.get_value(entry.result, key)
        else:
            output = ''
            for attr in attrs:
                value = getattr(entry, attr, None)
                if (isinstance(value, basestring) and len(value) > 0 and
                        value[0] in ['{', '['] and value[len(value) - 1] in ['}', ']']):
                    new_value = ast.literal_eval(value)
                    if type(new_value) in [dict, list]:
                        value = new_value
                if type(value) in [dict, list]:
                    value = ('\n' if isinstance(value, dict) else '') + json.dumps(value, indent=4)
                output += ('\n' if output else '') + '%s: %s' % (attr.upper(), value)
        return strutil.unescape(output)
