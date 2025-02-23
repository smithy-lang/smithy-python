# Copyright 2014 Ian Cordasco, Rackspace

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module vended from rfc3986 ``abnf_rexexp.py`` and ``misc.py``.

https://github.com/python-hyper/rfc3986/blob/main/src/rfc3986/abnf_regexp.py
https://github.com/python-hyper/rfc3986/blob/main/src/rfc3986/misc.py
"""
import re

# #########################
# Start abnf_regexp.py
# #########################

# Escape the '*' for use in regular expressions
SUB_DELIMITERS_RE = r"!$&'()\*+,;="
# We need to escape the '-' in this case:
UNRESERVED_RE = r"A-Za-z0-9._~\-"

# Percent encoded character values
PERCENT_ENCODED = PCT_ENCODED = "%[A-Fa-f0-9]{2}"
PCHAR = "([" + UNRESERVED_RE + SUB_DELIMITERS_RE + ":@]|%s)" % PCT_ENCODED

# #########################
# Authority Matcher Section
# #########################

# Host patterns, see: http://tools.ietf.org/html/rfc3986#section-3.2.2
# The pattern for a regular name, e.g.,  www.google.com, api.github.com
REGULAR_NAME_RE = REG_NAME = "((?:{}|[{}])*)".format(
    "%[0-9A-Fa-f]{2}", SUB_DELIMITERS_RE + UNRESERVED_RE
)
# The pattern for an IPv4 address, e.g., 192.168.255.255, 127.0.0.1,
IPv4_RE = r"([0-9]{1,3}\.){3}[0-9]{1,3}"
# Hexadecimal characters used in each piece of an IPv6 address
HEXDIG_RE = "[0-9A-Fa-f]{1,4}"
# Least-significant 32 bits of an IPv6 address
LS32_RE = "({hex}:{hex}|{ipv4})".format(hex=HEXDIG_RE, ipv4=IPv4_RE)
# Substitutions into the following patterns for IPv6 patterns defined
# http://tools.ietf.org/html/rfc3986#page-20
_subs = {"hex": HEXDIG_RE, "ls32": LS32_RE}

# Below: h16 = hexdig, see: https://tools.ietf.org/html/rfc5234 for details
# about ABNF (Augmented Backus-Naur Form) use in the comments
variations = [
    #                            6( h16 ":" ) ls32
    "(%(hex)s:){6}%(ls32)s" % _subs,
    #                       "::" 5( h16 ":" ) ls32
    "::(%(hex)s:){5}%(ls32)s" % _subs,
    # [               h16 ] "::" 4( h16 ":" ) ls32
    "(%(hex)s)?::(%(hex)s:){4}%(ls32)s" % _subs,
    # [ *1( h16 ":" ) h16 ] "::" 3( h16 ":" ) ls32
    "((%(hex)s:)?%(hex)s)?::(%(hex)s:){3}%(ls32)s" % _subs,
    # [ *2( h16 ":" ) h16 ] "::" 2( h16 ":" ) ls32
    "((%(hex)s:){0,2}%(hex)s)?::(%(hex)s:){2}%(ls32)s" % _subs,
    # [ *3( h16 ":" ) h16 ] "::"    h16 ":"   ls32
    "((%(hex)s:){0,3}%(hex)s)?::%(hex)s:%(ls32)s" % _subs,
    # [ *4( h16 ":" ) h16 ] "::"              ls32
    "((%(hex)s:){0,4}%(hex)s)?::%(ls32)s" % _subs,
    # [ *5( h16 ":" ) h16 ] "::"              h16
    "((%(hex)s:){0,5}%(hex)s)?::%(hex)s" % _subs,
    # [ *6( h16 ":" ) h16 ] "::"
    "((%(hex)s:){0,6}%(hex)s)?::" % _subs,
]

IPv6_RE = "(({})|({})|({})|({})|({})|({})|({})|({})|({}))".format(*variations)

IPv_FUTURE_RE = r"v[0-9A-Fa-f]+\.[%s]+" % (UNRESERVED_RE + SUB_DELIMITERS_RE + ":")

# RFC 6874 Zone ID ABNF
ZONE_ID = "(?:[" + UNRESERVED_RE + "]|" + PCT_ENCODED + ")+"

IPv6_ADDRZ_RFC4007_RE = IPv6_RE + "(?:(?:%25|%)" + ZONE_ID + ")?"
IPv6_ADDRZ_RE = IPv6_RE + "(?:%25" + ZONE_ID + ")?"

IP_LITERAL_RE = r"\[({}|{})\]".format(
    IPv6_ADDRZ_RFC4007_RE,
    IPv_FUTURE_RE,
)

# Pattern for matching the host piece of the authority
HOST_RE = HOST_PATTERN = "({}|{}|{})".format(
    REG_NAME,
    IPv4_RE,
    IP_LITERAL_RE,
)

# #########################
# End abnf_regexp.py
# #########################


# #########################
# Start misc.py
# #########################

# These are enumerated for the named tuple used as a superclass of
# URIReference

HOST_MATCHER = re.compile("^" + HOST_RE + "$")
IPv4_MATCHER = re.compile("^" + IPv4_RE + "$")
IPv6_MATCHER = re.compile(r"^\[" + IPv6_ADDRZ_RFC4007_RE + r"\]$")

# Used by host validator
IPv6_NO_RFC4007_MATCHER = re.compile(r"^\[%s\]$" % (IPv6_ADDRZ_RE))

# #########################
# End misc.py
# #########################
