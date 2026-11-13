-- Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
-- SPDX-License-Identifier: Apache-2.0
--
-- Converts documentation for PandocWorker.java over stdin and stdout, so that a
-- whole generation shares one Pandoc process.
--
-- The first line written is "READY <pandoc version>", or "UNSUPPORTED" when this
-- Pandoc lacks pandoc.log.silence (added in Pandoc 3.2).
--
-- Request: <from format>\n<to format>\n<input byte count>\n<input bytes>
-- Reply:   "OK <output byte count>\n<output bytes>" for a conversion that logged
--          nothing, otherwise "FALLBACK\n". On FALLBACK the caller runs the pandoc
--          command line instead, which reproduces its own output, warnings and
--          errors exactly.

local stdin, stdout = io.stdin, io.stdout

local function send(...)
  stdout:write(...)
  stdout:flush()
end

-- Match the command line, which passes --columns=72 to both the reader and the
-- writer. Its --wrap=auto is already the writer default.
local supported, reader_options, writer_options = pcall(function ()
  return pandoc.ReaderOptions({columns = 72}), pandoc.WriterOptions({columns = 72})
end)
if not supported or type(pandoc.log) ~= 'table' or type(pandoc.log.silence) ~= 'function' then
  send('UNSUPPORTED\n')
  return
end

local function convert(input, from, to)
  return pandoc.write(pandoc.read(input, from, reader_options), to, writer_options)
end

send('READY ', tostring(PANDOC_VERSION), '\n')

while true do
  local from = stdin:read('l')
  local to = stdin:read('l')
  local size_line = stdin:read('l')
  local size = size_line and tonumber(size_line)
  if not (from and to and size) then
    break
  end
  -- read(0) would block until the next request arrives, so skip it.
  local input = size > 0 and stdin:read(size) or ''
  if input == nil or #input ~= size then
    break
  end

  local ok, messages, output = pcall(pandoc.log.silence, convert, input, from, to)
  if ok and #messages == 0 and type(output) == 'string' then
    send('OK ', tostring(#output), '\n', output)
  else
    send('FALLBACK\n')
  end
end
