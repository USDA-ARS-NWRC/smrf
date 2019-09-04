"""
Create classes for running on multiple threads

20160323 Scott Havens
"""

from queue import Queue, Empty, Full

import numpy as np
import threading
from time import time as _time
import logging
import sys

class DateQueue_Threading(Queue):
    """
    DateQueue extends Queue.Queue module
    Stores the items in a dictionary with date_time keys
    When values are retrieved, it will not remove them and will
    require cleaning at the end to not have to many values

    20160323 Scott Havens
    """

    def __init__(self, maxsize=0, timeout=None, name=None):
        # extend the base class
        Queue.__init__(self, maxsize)
        self.timeout = timeout

        logger_name = __name__
        if name is not None:
            logger_name = '{}.{}'.format(logger_name, name)

        self._logger = logging.getLogger(logger_name)


    # The following override the methods in Queue to use
    # a date approach to the queue

    # Initialize the queue representation
    def _init(self, maxsize):
        self.queue = {}

    def _qsize(self, len=len):
        return len(self.queue)

    # Put a new item in the queue
    def _put(self, item):
        # self.queue.append(item)
        self.queue.update({item[0]: item[1]})

    # Get an item from the queue
    def _get(self, index):
        return self.queue[index]

    def clean(self, index):
        """
        Need to clean it out so mimic the original get
        """
        self.not_empty.acquire()
        try:
            if index in self.queue:
                del self.queue[index]
                self.not_full.notifyAll()
        except Exception as e:
            self._logger.error('Error cleaning {} - {}'.format(index, e))
        finally:
            self.not_empty.release()

    def get(self, index, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until an item is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the Empty exception if no item was available within that time.
        Otherwise ('block' is false), return an item if one is immediately
        available, else raise the Empty exception ('timeout' is ignored
        in that case).

        This is from queue.Queue but with modifcation for supplying what to get
        """
        timed_out = False
        # see if timeout was passed
        if timeout is not None:
            self.timeout = timeout

        self.not_empty.acquire()
        try:
            if not block:
                if not self._qsize():
                    raise Empty

            elif self.timeout is None:
                while index not in self.queue.keys():
                    self.not_empty.wait()
            else:
                endtime = _time() + self.timeout

                while index not in self.queue.keys():
                    remaining = endtime - _time()

                    # Time out has occurred
                    if remaining <= 0.0:
                        self._logger.error("{} - Timeout occurred while removing"
                                            " an item from queue".format(index))
                        timed_out = True
                        raise Empty

                    self.not_empty.wait(remaining)
            item = self._get(index)
            self.not_full.notifyAll()
            return item

        except Exception as e:
            self._logger.error('{} - {}'.format(index, e))

        finally:
            self.not_empty.release()
            if timed_out:
                sys.exit()

    def put(self, item, block=True, timeout=None):
        """Put an item into the queue.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until a free slot is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the Full exception if no free slot was available within that time.
        Otherwise ('block' is false), put an item on the queue if a free slot
        is immediately available, else raise the Full exception ('timeout'
        is ignored in that case).
        """
        timed_out = False
        # see if timeout was passed
        timeout = None
        if timeout is not None:
            self.timeout = timeout

        self.not_full.acquire()
        try:
            if self.maxsize > 0:
                if not block:
                    if self._qsize() == self.maxsize:
                        raise Full
                elif self.timeout is None:
                    while self._qsize() == self.maxsize:
                        self.not_full.wait()
                else:
                    endtime = _time() + self.timeout

                    while self._qsize() == self.maxsize:
                        remaining = endtime - _time()
                        if remaining <= 0.0:
                            self._logger.error("{} - Timeout occurred in while"
                                               " putting an item in the queue".format(item[0]))
                            timed_out=True
                            raise Full

                        self.not_full.wait(remaining)
            self._put(item)
            self.unfinished_tasks += 1
            self.not_empty.notifyAll()

        except Exception as e:
            self._logger.error('{} - {}'.format(item[0], e))

        finally:
            self.not_full.release()
            if timed_out:
                sys.exit()

class QueueCleaner(threading.Thread):
    """
    QueueCleaner that will go through all the queues and check
    if they all have a date in common.  When this occurs, all the
    threads will have processed that time step and it's not longer needed
    """

    def __init__(self, date_time, queue):
        """
        Args:
            date_time: array of date_time
            queue: dict of the queue
        """
        threading.Thread.__init__(self, name='cleaner')
        self.queues = queue
        self.date_time = date_time

        self._logger = logging.getLogger(__name__)
        self._logger.debug('Initialized cleaner thread')

    def run(self):
        """
        Go through the date times and look for when all the queues
        have that date_time
        """

        for t in self.date_time:

            # first do a get on all the data, this will ensure that
            # there is data there to be had
            for v in self.queues.keys():
                # self._logger.debug('Clean checking %s -- %s' % (t, v))
                self.queues[v].get(t)

            # now that we know there is data in all of the queues
            # that have the same time, clean up those times
            for v in self.queues.keys():
                # self._logger.debug('Clean cleaning %s -- %s' % (t, v))
                self.queues[v].clean(t)

            self._logger.debug('%s Cleaned from queues' % t)


class QueueOutput(threading.Thread):
    """
    Takes values from the queue and outputs using 'out_func'
    """

    def __init__(self, queue, date_time, out_func, out_frequency, nx, ny):
        """
        Args:
            date_time: array of date_time
            queue: dict of the queue
        """

        threading.Thread.__init__(self, name='output')
        self.queues = queue
        self.date_time = date_time
        self.out_func = out_func
        self.out_frequency = out_frequency
        self.nx = nx
        self.ny = ny

        self._logger = logging.getLogger(__name__)
        self._logger.debug('Initialized output thread')

    def run(self):
        """
        Output the desired variables to a file.

        Go through the date times and look for when all the queues
        have that date_time
        """

        for output_count, t in enumerate(self.date_time):

            # output at the frequency and the last time step
            if (output_count % self.out_frequency == 0) or \
               (output_count == len(self.date_time)):

                # get the output variables then pass to the function
                for v in self.out_func.variable_list.values():
                    if v['variable'] in self.queues.keys():
                        data = self.queues[v['variable']].get(t)

                        if data is None:
                            data = np.zeros((self.ny, self.nx))

                        # output the time step
                        self.out_func.output(v['variable'], data, t)

                    else:
                        self._logger.warning('{0} Output variable {1} not in queue'
                                             .format(t, v['variable']))

                # put the value into the output queue so clean knows it's done
                self.queues['output'].put([t, True])

                self._logger.debug('%s Variables output from queues' % t)
