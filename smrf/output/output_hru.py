"""
Functions to output the gridded data for a HRU
"""

import logging
import os

import numpy as np
import pandas as pd


class output_hru():
    """
    Class output_hru() to output values to a HRU dataframe, then to a file
    """

    fmt = '%Y-%m-%d %H:%M:%S'
    date_cols = ["year", "month", "day", "hour", "minute", "second"]

    def __init__(self, variable_list, topo, date_time, config):
        """
        Initialize the output_hru() class

        Args:
            variable_list: list of dicts, one for each variable
            topo: loadTopo instance
            date_time: smrf.date_time, array of dates for the SMRF run
            config: configuration for the output
        """

        self._logger = logging.getLogger(__name__)
        self.config = config

        # check some defaults based on the output type
        self.prms_flag = False
        if config['output_type'] == 'csv':
            ext = '.csv'
            self.delimiter = ','

        elif config['output_type'] == 'prms':
            ext = '.data'
            self.prms_flag = True
            if not os.path.isfile(self.config['hru_file']):
                raise Exception('HRU file does not exist')
            self.delimiter = ' '

        # go through the variable list and make full file names
        for v in variable_list:
            if not variable_list[v]['out_location'].endswith(ext):
                variable_list[v]['file_name'] = \
                    variable_list[v]['out_location'] + ext
            else:
                variable_list[v]['file_name'] = \
                    variable_list[v]['out_location']

            try:
                os.remove(variable_list[v]['file_name'])
            except OSError:
                pass

        self.variable_list = variable_list

        # process the time section
        self.out_frequency = int(config['frequency'])
        self.date_time = date_time
        self.idx = 0

        # read in the HRU file
        self._logger.debug('Reading HRU ascii {}'
                           .format(self.config['hru_file']))

        hru = np.loadtxt(self.config['hru_file'], skiprows=6)
        hru_max = int(np.max(hru))
        self._logger.debug("Number of HRU's: {}".format(hru_max))

        self.hru = hru
        self.hru_max = hru_max

        self.IND = {}
        for h in range(hru_max):
            self.IND[h] = hru == h+1

        self.hru_idx = [str(i+1) for i in range(self.hru_max)]

        # create an empty dataframe
        if self.prms_flag:
            cols = self.date_cols + self.hru_idx
            hru_data = pd.DataFrame(index=range(len(self.date_time)),
                                    columns=cols)

            yrs = np.array([
                [y.year, y.month, y.day, y.hour, y.minute, y.second]
                for y in self.date_time])
            hru_data['year'] = yrs[:, 0]
            hru_data['month'] = yrs[:, 1]
            hru_data['day'] = yrs[:, 2]
            hru_data['hour'] = yrs[:, 3]
            hru_data['minute'] = yrs[:, 4]
            hru_data['second'] = yrs[:, 5]

            hru_data.loc[:, self.hru_idx] = \
                hru_data.loc[:, self.hru_idx].apply(pd.to_numeric)

            # lets start the output file
            self.generate_prms_header()

        else:
            cols = ["date_time"] + self.hru_idx
            hru_data = pd.DataFrame(index=range(len(self.date_time)),
                                    columns=cols)
            hru_data['date_time'] = self.date_time

        self.hru_data = hru_data

#     def generate_csv_header(self, hru_data):
#         """
#         Generate the header for the csv file
#         """
#
#         for v in self.variable_list:
#
#             with open(self.variable_list[v]['file_name'],'w') as f:
#
#
#                 hdr.to_csv(f, self.delimiter, index=False, header=True)

    def generate_prms_header(self):
        """
        Generate the header for the PRMS output file
        """

        for v in self.variable_list:

            with open(self.variable_list[v]['file_name'], 'w') as f:
                # Append the PRMS expected Header
                f.write("File Generated using SMRF distributed forcing data\n")
                f.write("{0} {1}\n".format(v, self.hru_max))

                f.write("########################################\n")
                f.close()

    def output(self, variable, data, date_time):
        """
        Output a time step

        Args:
            variable: variable name that will index into variable list
            data: the variable data
            date_time: the date time object for the time step
        """

        self._logger.debug('{} Writing variable {} to {} file'
                           .format(
                               date_time,
                               variable,
                               self.config['output_type']))

        # loop through the HRU
        m_hru = np.zeros((self.hru_max,))
        for h in range(self.hru_max):
            m_hru[h] = np.nanmean(data[self.IND[h]])

#             self.hru_data.loc[self.idx, (str(h+1))] = m_hru[h]

        if self.func == 'mm2in':
            m_hru /= 25.4
        elif self.func == 'C2F':
            m_hru = m_hru * 9/5 + 32

        self.hru_data.loc[self.idx, self.hru_idx] = m_hru

        # open the file and write the row of data
        with open(self.variable_list[variable]['file_name'], 'a') as f:

            row = self.hru_data.iloc[self.idx].to_frame().T

            # change the dates columns back to int
            if self.prms_flag:
                row[self.date_cols] = row[self.date_cols].astype(int)

            hdr = None
            if (self.idx == 0) & (not self.prms_flag):
                hdr = True

            row.to_csv(f, sep=self.delimiter,
                       header=hdr,
                       index=False,
                       float_format='%.3f')

            f.close()

        self.idx += 1
