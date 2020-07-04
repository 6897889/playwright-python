# Copyright (c) Microsoft Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import json
import os
import sys
from typing import Awaitable, Dict


class Transport:
  def __init__(self, input: asyncio.StreamReader, output: asyncio.StreamWriter, loop: asyncio.AbstractEventLoop) -> None:
    super().__init__()
    self._input = input
    self._output = output
    self.loop = loop
    self.on_message = lambda _: None
    loop.create_task(self._run())

  async def _run(self) -> None:
    while True:
      try:
        buffer = await self._input.readexactly(4)
        length = int.from_bytes(buffer, byteorder='little', signed=False)
        buffer = bytes(0)
        while length:
          to_read = min(length, 32768)
          data = await self._input.readexactly(to_read)
          length -= to_read
          if len(buffer):
            buffer = b''.join([buffer, data])
          else:
            buffer = data
        msg = buffer.decode('utf-8')
        obj = json.loads(msg)

        if 'DEBUGP' in os.environ:
          print('\x1b[33mRECV>\x1b[0m', json.dumps(obj, indent=2))
        if 'DEBUG' in os.environ:
          print('\x1b[33mRECV>\x1b[0m', obj.get('method'))
        self.on_message(obj)
      except asyncio.streams.IncompleteReadError:
        break
      await asyncio.sleep(0)

  def send(self, message: Dict) -> Awaitable:
    msg = json.dumps(message)
    if 'DEBUGP' in os.environ:
      print('\x1b[32mSEND>\x1b[0m', json.dumps(message, indent=2))
    if 'DEBUG' in os.environ:
      print('\x1b[32mSEND>\x1b[0m', message.get('method'))
    data = bytes(msg, 'utf-8')
    self._output.write(len(data).to_bytes(4, byteorder='little', signed=False))
    self._output.write(data)
