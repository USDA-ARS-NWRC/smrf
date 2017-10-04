
Configuration
=============

SMRF is configured using a configuration file and an extension of Pythons
`ConfigParser`_ (:mod:`smrf.framework.model_framework.MyParser`). See
``test_data/testConfig.ini`` for an example and read below for more information
on specific sections.

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

*All values below are required except those with default values, shown in
parenthesis next to the variable.*

.. toctree::
   :maxdepth: 4

   auto_config
   core_config
