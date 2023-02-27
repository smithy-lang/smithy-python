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

"""Module vended from rfc3986 ``abnf_rexexp.py``, ``misc.py`` and ``validators.py``."""
import re

# #########################
# Start abnf_regexp.py
# #########################

# https://tools.ietf.org/html/rfc3986#page-13
GEN_DELIMS = GENERIC_DELIMITERS = ":/?#[]@"
GENERIC_DELIMITERS_SET = set(GENERIC_DELIMITERS)
# https://tools.ietf.org/html/rfc3986#page-13
SUB_DELIMS = SUB_DELIMITERS = "!$&'()*+,;="
SUB_DELIMITERS_SET = set(SUB_DELIMITERS)
# Escape the '*' for use in regular expressions
SUB_DELIMITERS_RE = r"!$&'()\*+,;="
RESERVED_CHARS_SET = GENERIC_DELIMITERS_SET.union(SUB_DELIMITERS_SET)
ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
DIGIT = "0123456789"
# https://tools.ietf.org/html/rfc3986#section-2.3
UNRESERVED = UNRESERVED_CHARS = ALPHA + DIGIT + r"._!-~"
UNRESERVED_CHARS_SET = set(UNRESERVED_CHARS)
NON_PCT_ENCODED_SET = RESERVED_CHARS_SET.union(UNRESERVED_CHARS_SET)
# We need to escape the '-' in this case:
UNRESERVED_RE = r"A-Za-z0-9._~\-"

# Percent encoded character values
PERCENT_ENCODED = PCT_ENCODED = "%[A-Fa-f0-9]{2}"
PCHAR = "([" + UNRESERVED_RE + SUB_DELIMITERS_RE + ":@]|%s)" % PCT_ENCODED

# NOTE(sigmavirus24): We're going to use more strict regular expressions
# than appear in Appendix B for scheme. This will prevent over-eager
# consuming of items that aren't schemes.
SCHEME_RE = "[a-zA-Z][a-zA-Z0-9+.-]*"
_AUTHORITY_RE = "[^\\\\/?#]*"
_PATH_RE = "[^?#]*"
_QUERY_RE = "[^#]*"
_FRAGMENT_RE = ".*"

# Extracted from http://tools.ietf.org/html/rfc3986#appendix-B
COMPONENT_PATTERN_DICT = {
    "scheme": SCHEME_RE,
    "authority": _AUTHORITY_RE,
    "path": _PATH_RE,
    "query": _QUERY_RE,
    "fragment": _FRAGMENT_RE,
}

# See http://tools.ietf.org/html/rfc3986#appendix-B
# In this case, we name each of the important matches so we can use
# SRE_Match#groupdict to parse the values out if we so choose. This is also
# modified to ignore other matches that are not important to the parsing of
# the reference so we can also simply use SRE_Match#groups.
URL_PARSING_RE = (
    r"(?:(?P<scheme>{scheme}):)?(?://(?P<authority>{authority}))?"
    r"(?P<path>{path})(?:\?(?P<query>{query}))?"
    r"(?:#(?P<fragment>{fragment}))?"
).format(**COMPONENT_PATTERN_DICT)


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
USERINFO_RE = "^([" + UNRESERVED_RE + SUB_DELIMITERS_RE + ":]|%s)+" % (PCT_ENCODED)
PORT_RE = "[0-9]{1,5}"

# ####################
# Path Matcher Section
# ####################

# See http://tools.ietf.org/html/rfc3986#section-3.3 for more information
# about the path patterns defined below.
segments = {
    "segment": PCHAR + "*",
    # Non-zero length segment
    "segment-nz": PCHAR + "+",
    # Non-zero length segment without ":"
    "segment-nz-nc": PCHAR.replace(":", "") + "+",
}

# Path types taken from Section 3.3 (linked above)
PATH_EMPTY = "^$"
PATH_ROOTLESS = "%(segment-nz)s(/%(segment)s)*" % segments
PATH_NOSCHEME = "%(segment-nz-nc)s(/%(segment)s)*" % segments
PATH_ABSOLUTE = "/(%s)?" % PATH_ROOTLESS
PATH_ABEMPTY = "(/%(segment)s)*" % segments
PATH_RE = "^({}|{}|{}|{}|{})$".format(
    PATH_ABEMPTY,
    PATH_ABSOLUTE,
    PATH_NOSCHEME,
    PATH_ROOTLESS,
    PATH_EMPTY,
)

FRAGMENT_RE = QUERY_RE = (
    "^([/?:@" + UNRESERVED_RE + SUB_DELIMITERS_RE + "]|%s)*$" % PCT_ENCODED
)

# ##########################
# Relative reference matcher
# ##########################

# See http://tools.ietf.org/html/rfc3986#section-4.2 for details
RELATIVE_PART_RE = "(//{}{}|{}|{}|{})".format(
    COMPONENT_PATTERN_DICT["authority"],
    PATH_ABEMPTY,
    PATH_ABSOLUTE,
    PATH_NOSCHEME,
    PATH_EMPTY,
)

# See http://tools.ietf.org/html/rfc3986#section-3 for definition
HIER_PART_RE = "(//{}{}|{}|{}|{})".format(
    COMPONENT_PATTERN_DICT["authority"],
    PATH_ABEMPTY,
    PATH_ABSOLUTE,
    PATH_ROOTLESS,
    PATH_EMPTY,
)

# #########################
# End abnf_regexp.py
# #########################


# #########################
# Start misc.py
# #########################

# These are enumerated for the named tuple used as a superclass of
# URIReference
URI_COMPONENTS = ["scheme", "authority", "path", "query", "fragment"]

important_characters = {
    "generic_delimiters": GENERIC_DELIMITERS,
    "sub_delimiters": SUB_DELIMITERS,
    # We need to escape the '*' in this case
    "re_sub_delimiters": SUB_DELIMITERS_RE,
    "unreserved_chars": UNRESERVED_CHARS,
    # We need to escape the '-' in this case:
    "re_unreserved": UNRESERVED_RE,
}

URI_MATCHER = re.compile(URL_PARSING_RE)

SUBAUTHORITY_MATCHER = re.compile(
    (
        "^(?:(?P<userinfo>{})@)?"  # userinfo
        "(?P<host>{})"  # host
        ":?(?P<port>{})?$"  # port
    ).format(USERINFO_RE, HOST_PATTERN, PORT_RE)
)

HOST_MATCHER = re.compile("^" + HOST_RE + "$")
IPv4_MATCHER = re.compile("^" + IPv4_RE + "$")
IPv6_MATCHER = re.compile(r"^\[" + IPv6_ADDRZ_RFC4007_RE + r"\]$")

# Used by host validator
IPv6_NO_RFC4007_MATCHER = re.compile(r"^\[%s\]$" % (IPv6_ADDRZ_RE))

# Matcher used to validate path components
PATH_MATCHER = re.compile(PATH_RE)


# ##################################
# Query and Fragment Matcher Section
# ##################################

QUERY_MATCHER = re.compile(QUERY_RE)

FRAGMENT_MATCHER = QUERY_MATCHER

# Scheme validation, see: http://tools.ietf.org/html/rfc3986#section-3.1
SCHEME_MATCHER = re.compile(f"^{SCHEME_RE}$")

RELATIVE_REF_MATCHER = re.compile(
    r"^%s(\?%s)?(#%s)?$"
    % (
        RELATIVE_PART_RE,
        QUERY_RE,
        FRAGMENT_RE,
    )
)

# See http://tools.ietf.org/html/rfc3986#section-4.3
ABSOLUTE_URI_MATCHER = re.compile(
    r"^%s:%s(\?%s)?$"
    % (
        COMPONENT_PATTERN_DICT["scheme"],
        HIER_PART_RE,
        QUERY_RE[1:-1],
    )
)
# #########################
# End misc.py
# #########################


# #########################
# Start validators.py
# #########################


def valid_ipv4_host_address(host: str) -> bool:
    """Determine if the given host is a valid IPv4 address."""
    # If the host exists, and it might be IPv4, check each byte in the
    # address.
    return all([0 <= int(byte, base=10) <= 255 for byte in host.split(".")])


# #########################
# End validators.py
# #########################


def is_port_valid(port: int) -> bool:
    """Determine if the given port is valid."""
    return 0 <= port <= 65535
