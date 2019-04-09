"""
This module consists of encapsulators that return threads
where each thread gets data from an external source and
puts the data into a queue. The scheduler reads data from
the queue and puts the data on to streams. Effectively,
these encapsulators put data from external sources on to
streams.

An external source could be a sensor or Twitter, or a
any function such as one that gets data from a time service
such as NTP or a random number generator.

This module also has a function that waits for data to arrive
at a queue, and when data arrives it is put on a stream.
Another function puts data from a function call into a queue.

A source function returns a thread. Each source is executed in a
separate thread. The source threads do not interfere with each other
or with the thread that executes the agent that carries out the
computation in a process.

Functions in the module:
   1. func_to_q: puts data called by a function into a queue.
   2. q_to_streams: Used in ../multiprocessing
        Waits for data to arrive in a queue and puts the data
        into streams. The arriving data in the queue specifies
        the recipient stream name
   3. q_to_streams_general: Used in ../multiprocessing
        Same as q_to_streams except for a more general description
        of the recipient streams.
   4. source_func_to_stream: Used in ../multiprocessing/multicore
        puts data generated by a function into the queue read
        by the scheduler.
   5. source_file_to_stream: puts data from a file into the queue read by the
        scheduler.
   6. source_list_to_stream: puts data from a list into the queue read by the
        scheduler. 
    

"""
import time
import threading

import sys
import os
sys.path.append(os.path.abspath("../helper_functions"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../agent_types"))
from check_agent_parameter_types import check_source_function_arguments
from check_agent_parameter_types import check_source_file_arguments
from recent_values import recent_values
from stream import Stream
    
def func_to_q(func, q, state=None, sleep_time=0, num_steps=None,
              name='source_to_q', *args, **kwargs):
    """
    Value returned by func is appended to the queue q

    ----------
        func: function on state (optional), args (optional), kwargs
              (optional) 
           Value returned by func is appended to the queue q
        q: Queue.Queue() or multiprocessing.Queue()
        sleep_time: int or float (optional)
           The thread sleeps for this amount of time (seconds) before
           successive calls to func.
        num_steps: int or None (optional)
           The number of calls to func before this thread
           terminates. If num_steps is None then this thread does not
           terminate.
        name: str (optional)
           Name of the string is helpful in debugging.
    Returns
    -------
        thread: threading.Thread()
            The thread that repeatedly calls function.
           
    """
    def thread_target(func, q, state, sleep_time, num_steps, args, kwargs):
        if num_steps is None:
            while True:
                output = func(*args, **kwargs) if state is None else \
                  func(state, *args, **kwargs)
                q.put(output)
                time.sleep(sleep_time)
        else:
            for _ in range(num_steps):
                output = func(*args, **kwargs) if state is None else \
                  func(state, *args, **kwargs)
                q.put(output)
                time.sleep(sleep_time)

    return (
        threading.Thread(
        target=thread_target,
        args=(func, q, state, sleep_time, num_steps, args, kwargs)))
                

def q_to_streams(q, out_streams, name='thread_q_to_streams'):
    """
    Parameters
    ----------
    q: Queue.Queue or multiprocessing.Queue
       messages arriving on q are tuples (stream_name, message content).
       The message content is appended to the stream with the specified
       name
    out_streams: list of Stream
       Each stream in this list must have a unique name. When a message
       (stream_name, message_content) arrives at the queue,
       message_content is placed on the stream with name stream_name.
    name: str (optional)
       The name of this thread. Useful for debugging.

    Variables
    ---------
    name_to_stream: dict. key: stream_name. value: stream
       
    """
    name_to_stream = {stream.name:stream for stream in out_streams}
    def thread_target(q, name_to_stream):
        while True:
            v = q.get()
            if v == '_close':
                break
            stream_name, new_data_for_stream = v
            stream = name_to_stream[stream_name]
            stream.append(new_data_for_stream)
        return
    
    return (
        threading.Thread(target=thread_target, args=(q, name_to_stream)))


def q_to_streams_general(q, func, name='thread_q_to_streams'):
    """
    Identical to q_to_streams except that a stream is identified by the
    descriptor attached to each message in the queue. The descriptor need
    not be a name; for instance, the descriptor could be a 2-tuple
    consisting of (1) the name of an array of streams and (2) an index
    into the array. Note that for q_to_streams the descriptor must be a
    name.

    func is a function that returns a stream given a stream
    descriptor. In the case of q_to_streams we don't need func because
    the stream is identified by its name.
    
    Parameters
    ----------
    q: Queue.Queue or multiprocessing.Queue
       messages arriving on q are tuples (stream_name, message content).
       The message content is appended to the stream with the specified
       name
    func: function
       function from stream_descriptor to a stream
    name: str (optional)
       The name of this thread. Useful for debugging.

       
    """
    def thread_target(q, name_to_stream):
        while True:
            v = q.get()
            if v == '_close':
                break
            # Each message is a tuple: (stream descriptor, msg content)
            stream_descriptor, new_data_for_stream = v
            stream = func(stream_descriptor)
            stream.append(new_data_for_stream)
        return
    return (
        threading.Thread(target=thread_target, args=(q, name_to_stream)))


def source_func_to_stream(
        func, out_stream, time_interval=0, num_steps=None, window_size=1,
        state=None, name='source_f', *args, **kwargs):
    """
    Puts (out_stream.name, v) on the scheduler queue where v is the value
    returned by func. The scheduler gets these pairs from the queue and
    appends v to out_stream. So, effectively, source_func_to_stream puts values
    returned by func into out_stream.
    
    Parameters
    ----------
       func: function on state, args, kwargs
          This function is called and the 2-tuple consisting of (1)
          the result of this function and (2) stream_name is
          appended to the queue of the scheduler.
       out_stream: Stream
          The stream to which elements will be appended.
       time_interval: float or int (optional), time in seconds
          An element is placed on the output stream every time_interval
          seconds.
       num_steps: int or None (optional)
          default is None
          source_func_to_stream terminates after num_steps: the number of steps.
          At each step a window_size number of elements is placed on the
          out_stream.
          If num_steps is None then source_func_to_stream terminates
          only when an exception is raised.
       window_size: int (optional)
          At each step a window_size number of elements is placed on the
          out_stream.
       state: object (optional)
          The state of the function; an argument of the parameter func.
       name: str or picklable, i.e., linearizable, object (optional)
           The name of the thread. Useful in debugging.
       args: list
          Positional arguments of func
       kwargs: dict
          Keyword arguments of func

    Returns: thread
    -------
          thread: threading.Thread
             The thread created by this function. The thread must
             be started and thread.join() may have to be called to
             ensure that the thread terminates execution.
          name: str
             The name of the thread
    """
    stream_name = out_stream.name
    check_source_function_arguments(
        func, stream_name, time_interval, num_steps, window_size,
        state, name)
    scheduler = Stream.scheduler

    def thread_target(
            func, stream_name, time_interval,
            num_steps, window_size, state, args, kwargs):
        """
        thread_target is the function executed by the thread.
        """

        #-----------------------------------------------------------------
        def get_output_list_and_next_state(state):
            """
            This function returns a list of length window_size and the
            next state.

            Parameters
            ----------
               state is the current state of the agent.
            Returns
            -------
               output_list: list
                 list of length window_size
               next_state: object
                 The next state after output_list is created.

            """
            output_list = []
            next_state = state
            # Compute the output list of length window_size
            for _ in range(window_size):
                if next_state is not None:
                    # func has a single argument, state,
                    # apart from *args, **kwargs
                    output_increment, next_state = func(
                        next_state, *args, **kwargs)
                else:
                    # func has no arguments apart from
                    # *args, **kwargs
                    output_increment = func(*args, **kwargs)
                output_list.append(output_increment)
            # Finished computing output_list of length window_size
            return output_list, next_state
        #-----------------------------------------------------------------
        # End of def get_output_list_and_next_state(state)
        #-----------------------------------------------------------------

        if num_steps is None:
            while True:
                output_list, state = get_output_list_and_next_state(state)
                for v in output_list:
                    scheduler.input_queue.put((stream_name, v))
                time.sleep(time_interval)
        else:
            for _ in range(num_steps):
                output_list, state = get_output_list_and_next_state(state)
                for v in output_list:
                    scheduler.input_queue.put((stream_name, v))
                time.sleep(time_interval)
        return

    #------------------------------------------------------------------------
    # End of def thread_target(...)
    #------------------------------------------------------------------------

    return (
        threading.Thread(
            target=thread_target,
            args=(func, stream_name, time_interval, num_steps,
              window_size, state, args, kwargs)))

def source_file_to_stream(
        func, out_stream, filename, time_interval=0,
        num_steps=None, window_size=1, state=None, name='source_file_to_stream',
        *args, **kwargs):
    
    """
    Applies function func to each line in the file with name filename
    and puts the pair (out_stream.name, v) on the scheduler input
    queue where v is the value returned by func.
    The scheduler gets the pair from the queue and appends ve to out_stream.
    So, effectively, source_file_to_stream puts values into out_stream.
    
    Parameters
    ----------
       func: function
          This function is applied to each line read from file with name
          filename, and the result of this function is placed on the
          scheduler's input queue. The scheduler then appends this value
          to out_stream.
          The arguments of func are a line of the file, the
          state if any, and *args, **kwargs.
       out_stream: The output stream to which elements are appended.
       filename: str
          The name of the file that is read.
       time_interval: float or int (optional)
          The next line of the file is read every time_interval seconds.
       num_steps: int (optional)
          file_to_stream terminates after num_steps taken.
          If num_steps is None then the
          file_to_stream terminates when the entire file is read.
        window_size: int (optional)
          At each step, window_size number of lines are read from the
          file and placed on out_stream after function is applied to them.
       state: object (optional)
          The state of the function; an argument of func.
       args: list
          Positional arguments of func
       kwargs: dict
          Keyword arguments of func
    
    Returns: thread
    -------
          thread: threading.Thread
             The thread created by this function. The thread must
             be started and thread.join() may have to be called to
             ensure that the thread terminates execution.
          name: str
             The name of the thread The thread must
             be started and thread.join() may have to be called to
             ensure that the thread terminates execution.

    """

    #-----------------------------------------------------------------
    stream_name = out_stream.name
    check_source_file_arguments(
        func, stream_name, filename, time_interval,
        num_steps, window_size, state, name)
    scheduler = Stream.scheduler

    def thread_target(func, stream_name, filename, time_interval,
                      num_steps, window_size, state,
                      args, kwargs):
        """
        This is the function executed by the thread.
        
        """
        num_lines_read_in_current_window = 0
        num_steps_taken = 0
        output_list_for_current_window = []
        with open(filename, 'r') as input_file:
            for line in input_file:
                # Append to the output list for the current window
                # the incremental output returned by a function call.
                # The function is passed the current line from the
                # file as an argument and the function returns the
                # increment and the next state.
                if state is not None:
                    output_increment, state = func(
                        line, state, *args, **kwargs)
                else:
                    output_increment = func(line, *args, **kwargs)
                output_list_for_current_window.append(output_increment)
                num_lines_read_in_current_window += 1
                if num_lines_read_in_current_window >= window_size:
                    # Put the entire window on the scheduler queue
                    # then re-initialize the window, and finally sleep.
                    for v in output_list_for_current_window:
                        scheduler.input_queue.put((stream_name, v))
                    num_lines_read_in_current_window = 0
                    output_list_for_current_window = []
                    time.sleep(time_interval)
                    num_steps_taken += 1
                if num_steps is not None and num_steps_taken >= num_steps:
                    break
        return
 
    #------------------------------------------------------------------------
    # End of def thread_target(...)
    #------------------------------------------------------------------------

    return (
        threading.Thread(
            target=thread_target,
            args=(func, stream_name, filename, time_interval, num_steps,
                  window_size, state, args, kwargs)))


def source_list_to_stream(
        in_list, out_stream, time_interval=0, num_steps=None, window_size=1,
        name='source_list_to_stream'):
    """
    Puts elements of the list on to the scheduler's input queue. The scheduler
    reads the queue and appends the elements to out_stream.

    """
    if num_steps is None:
        num_steps = len(in_list)
    def read_list_func(state, in_list):
        return in_list[state], state+1
    return source_func_to_stream(
        read_list_func, out_stream, time_interval, num_steps,
        window_size, state=0, name=name, in_list=in_list)


class source_file(object):
    """
    For an instance, obj, of source_file: obj.source_func()
    returns an agent that puts data from a file called
    self.filename into a stream.
    Each line of the file is parsed by parse_line() and its
    results are put on a stream. parse_line() must return a
    single object which is placed on the stream. 

    An object, obj, of this class is always called as
    obj.source_func() inside the list connect_sources within
    make_process().
    
    Parameters
    ----------
    filename: str
      name of a file. The source reads this file line by line.
    parse_line: func
      The function which converts each line of the file into an
      object (int, float) or list of objects.
    time_interval: int or float, optional
      The time elapsed between successive lines from the file
      placed on the output stream.
    num_steps: int, optional
      The number of elements from the file placed on the output
      stream. If this is omitted or is 0 then the entire file
      is placed on the output stream.
    window_size: int, optional
      The number of lines read from the file in a block
      operation. Large window_sizes can improve performance
      by reducing the number of times a file is read. Generally
      window_size = 1 is adequate.
    state: object, optional
      state of the function, parse_line.
      See source_file_to_stream()
    name: str, optional
      Name of the thread in which this source runs.

    """
    def __init__(
            self, filename, parse_line,
            time_interval=0.0, num_steps=0,
            window_size=1, state=None,
            name='source_file.source.func'):  
        self.filename = filename
        self.parse_line = parse_line
        self.time_interval = time_interval
        self.num_steps=num_steps
        self.window_size=window_size
        self.state = state
        self.name = name
    def source_func(self, out_stream):
        return source_file_to_stream(
            self.parse_line, out_stream,
            self.filename, self.time_interval,
            self.num_steps, self.window_size, self.state,
            self.name)

class source_float_file(source_file):
    """
    Same as source_file except that it requires exactly one
    float per line.

    """
    def __init__(
            self, filename,
            time_interval=0.0, num_steps=0):
        self.filename = filename
        self.time_interval = time_interval
        self.num_steps=num_steps
        self.name = 'source_float_file'
        source_file.__init__(
            self, filename, lambda v: float(v),
            time_interval, num_steps)


class source_int_file(source_file):
    """
    Same as source_file except that it requires exactly one
    int per line.

    """
    def __init__(
            self, filename,
            time_interval=0.0, num_steps=0):
        self.filename = filename
        self.time_interval = time_interval
        self.num_steps=num_steps
        self.name = 'source_float_file'
        source_file.__init__(
            self, filename, lambda v: int(v),
            time_interval, num_steps)



class source_list(object):
    """
    For an instance, obj, of source_list: obj.source_func()
    returns an agent that puts data from a list into a stream.

    An object, obj, of this class is always called as
    obj.source_func() inside the list connect_sources within
    make_process().

    Parameters
    ----------
    in_list: list
      Elements of this list are placed on a stream
    time_interval: int or float, optional
      The time elapsed between successive lines from the file
      placed on the output stream.
    num_steps: int, optional
      The number of elements from the file placed on the output
      stream. If this is omitted or is 0 then the entire file
      is placed on the output stream.
    window_size: int, optional
      The number of lines read from the file in a block
      operation. Large window_sizes can improve performance
      by reducing the number of times a file is read. Generally
      window_size = 1 is adequate.
    state: object, optional
      state of the function, parse_line.
      See source_file_to_stream()
    name: str, optional
      Name of the thread in which this source runs.

    """
    def __init__(
            self, in_list, time_interval=0.0, num_steps=0,
            window_size=1, name='source_file.source.func'):  
        self.in_list = in_list
        self.time_interval = time_interval
        self.num_steps=num_steps
        self.window_size=window_size
        self.name = name
    def source_func(self, out_stream):
        return source_list_to_stream(
            self.in_list, out_stream, self.time_interval,
            self.num_steps, self.window_size, self.name)


class source_function(object):
    """
    For an instance, obj, of source_function: obj.source_func()
    returns an agent that puts data generated by obj.func on an
    output stream.

    An object, obj, of this class is always called as
    obj.source_func() inside the list connect_sources within
    make_process().
    
    Parameters
    ----------
    func: function
      The function that generates values that are put on the stream.
    time_interval: int or float, optional
      The time elapsed between successive lines from the file
      placed on the output stream.
    num_steps: int, optional
      The number of elements from the file placed on the output
      stream. If this is omitted or is 0 then the entire file
      is placed on the output stream.
    window_size: int, optional
      The number of lines read from the file in a block
      operation. Large window_sizes can improve performance
      by reducing the number of times a file is read. Generally
      window_size = 1 is adequate.
    state: object, optional
      state of the function, func.
      See source_func_to_stream()
    name: str, optional
      Name of the thread in which this source runs.

    """
    def __init__(
            self, func, time_interval=0.0, num_steps=0,
            window_size=1, state=None,
            name='source_file.source.func'):  
        self.func = func
        self.time_interval = time_interval
        self.num_steps=num_steps
        self.window_size=window_size
        self.state = state
        self.name = name
    def source_func(self, out_stream):
        return source_func_to_stream(
            self.func, out_stream, self.time_interval,
            self.num_steps, self.window_size, self.state,
            self.name)
