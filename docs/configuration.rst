.. _using-configs:

=========================
Using Configuration Files
=========================

SMRF simulation details are managed using configuration files. The python
package inicheck is used to manage and interpret the configuration files. Each
configuration file is broken down into sections containing items and each item
is assigned a value.

A brief description of the syntax is:

* Sections are noted by being in a line by themselves and are bracketed.
* Items are denoted by colon ( **:** ).
* Values are simply written in, and values that are lists are comma separated.
* Comments are preceeded by a **#**

For more information regarding inicheck syntax and utilities refer to the
`inicheck documentation`_.

.. _inicheck documentation: http://inicheck.readthedocs.io/en/latest/


Understanding Configuration Files
----------------------------------

The easiest way to get started is to look at one of the config files
in the repo already. A simple case to use is our reynolds mountain east test
which can be view easily here_.

.. _here: https://github.com/USDA-ARS-NWRC/SMRF/blob/develop/examples/reynolds_mountain_east/config.ini

Take a look at the "topo" section from the config file show below

.. literalinclude:: ../examples/reynolds_mountain_east/config.ini
   :lines: 20-29
   :language: none

This section describes all the topographic information required for SMRF to run.
At the top of the section there is comment that describes the section.
The section name "topo" is bracketed to show it is a section and the items
underneath are assigned values by using the colon.

Editing/Checking Configuration Files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use any text editor to make changes to a config file. We like to use atom_ with
the .ini syntax package installed.

.. _atom: https://atom.io/

If you are unsure of what to use various entries in your config file refer to
the :ref:`config-file-reference` or use the inicheck command for command line help.
Below is an example of how to use the inicheck details option to figure out what
options are available for the topo section type item.

.. code-block:: console

  inicheck --details topo type -m smrf

The output is:

.. code-block:: console

  Providing details for section topo and item type...

  Section      Item    Default    Options                   Description
  ==========================================================================================
  topo         type    netcdf     ['netcdf', 'ipw']         Specifies the input file type


Creating Configuration Files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Not all items and options need to be assigned, if an item is left blank
it will be assigned a default. If it is a required filename or something it
will be assigned a none value and SMRF will throw an error until it is assigned.

To make an up to date config file use the following command to generate a fully
populated list of options.

.. code-block:: console

  inicheck -f config.ini -m smrf -w

This will create a config file using the same name but call "config_full.ini"
at the end.

.. _core-config:

Core Configuration File
-----------------------

Each configuration file is checked against the core configuration file stored
./smrf/framework/core_config.ini and various scenarios are guided by the a recipes
file that is stored in ./smrf/framework/recipes.ini. These files work together
to guide the outcomes of the configuration file.

To learn more about syntax and how to contribute to a Core or Master configuration
file see `Master Configuration Files`_ in inicheck.

.. _Master Configuration Files: http://inicheck.readthedocs.io/en/latest/master_config.html
