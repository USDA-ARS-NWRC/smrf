
Configuration
=============

SMRF is configured using a configuration file and an extension of Pythons
`ConfigParser`_ (:mod:`smrf.framework.model_framework.MyParser`). See
``test_data/testConfig.ini`` for an example and read below for more information
on specific sections. All the entrys to a config file are governed by the
CoreConfig.ini in :mod:`smrf.framework.model_framework`. A couple of commandline
tools have provided to help get the config files generated correctly.

A brief introduction to a configuration file from the `ConfigParser`_ documentation: ::

   The configuration file consists of sections, led by a [section] header and followed
   by name: value entries, with continuations in the style of RFC 822 (see section
   3.1.1, “LONG HEADER FIELDS”); name=value is also accepted. Note that leading
   whitespace is removed from values. The optional values can contain format strings
   which refer to other values in the same section, or values in a special DEFAULT
   section. Additional defaults can be provided on initialization and retrieval. Lines
   beginning with '#' or ';' are ignored and may be used to provide comments.

   Configuration files may include comments, prefixed by specific characters (# and ;).
   Comments may appear on their own in an otherwise empty line, or may be entered in
   lines holding values or section names. In the latter case, they need to be preceded
   by a whitespace character to be recognized as a comment. (For backwards compatibility,
   only ; starts an inline comment, while # does not.)

Section and keys are case insensitive.

Notes:
1. Config file can have items in it that are not registered, they will simply be
ignored and SMRF will warn you at the beginning of the run. This should be used
to make sure you spelled things correctly.
2. The exception to the above, is station names. In some modules like wind,
have adjustment values can be added to the config file on a station by
station basis. SMRF will still warn that stations are not registered but they
are used when the code is reading it.
3. A config file can only have one data section. You can choose from mysql,
csv,gridded.


.. _ConfigParser: https://docs.python.org/2/library/configparser.html
.. _logging: https://docs.python.org/2/library/logging.html


.. toctree::
   :maxdepth: 4

   auto_config
   core_config
