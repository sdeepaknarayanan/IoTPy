import sys
import os
sys.path.append(os.path.abspath("../helper_functions"))
sys.path.append(os.path.abspath("../core"))
sys.path.append(os.path.abspath("../agent_types"))

from agent import Agent
from stream import Stream, StreamArray
from stream import _no_value, _multivalue
from check_agent_parameter_types import *
from recent_values import recent_values
from op import *
from sink import sink

def sort(lst):
    """
    Parameters
    ----------
    lst: list

    """
    def flip(I):
        """
        Flips elements of list, lst, if they are out of order.
        
        Parameters
        ----------
        I : array of length 1 consisting of index of an element of the
            list. The index is put into an array because Python passes
            parameters that are integer by value and arrays by
            reference. This is merely a trick to pass a parameter by
            reference.
        
        """
        # Extract index from the array.
        i = I[0]
        # Flip elements if out of order and return any value (1 in
        # this case) to indicate a change to lst.
        # Return no value if the elements are in order.
        if lst[i] > lst[i+1]:
            lst[i], lst[i+1] = lst[i+1], lst[i]
            return (1)
        else:
            return (_no_value)

    x = Stream('x')

    # Create an agent for each of the elements 0, 1, ..., len(lst)-1,
    # The agent executes its action when it reads a new value on
    # stream x. The agent sends a signal (the value 1 in our example)
    # on stream x when, and only when, the agent changes the list.
    for i in range(len(lst) - 1):
        signal_element(func=flip, in_stream=x, out_stream=x, name=i, I=[i])
    scheduler = Stream.scheduler
    # Start the computation by putting any value (1 in this case) in
    # stream x.
    x.append(1)
    # Start the scheduler.
    scheduler.step()

def shortest_path(D):
    """
    Parameters
    ----------
    D: matrix where D[j,k] is the length of the edge from vertex j to
    vertex k.

    Returns
    -------
    D: matrix where D[j,k] is the length of the shortest path from
    vertex j to  vertex k.
    
    """
    def triangle_inequality(triple):
        """
        Apply the triangle inequality. If this changes D then
        return any value (1 in our example). If D is unchanged
        then return no value.

        Parameters
        ----------
        triple: 3-element array or list

        """
        i, j, k = triple
        if D[i][j] + D[j][k] < D[i][k]:
            D[i][k] = D[i][j] + D[j][k]
            return(1)
        else:
            return (_no_value)

    x = Stream('x')
    # Create an agent for each triple i,j,k. The agent executes its
    # action when it reads a new element of stream x. If it changes D
    # it then puts a new element on x.
    indices = range(len(D))
    for i in indices:
        for j in indices:
            for k in indices:
                signal_element(func=triangle_inequality,
                               in_stream=x, out_stream=x,
                               name=str(i)+"_"+str(j)+"_"+str(k),
                               triple=[i, j, k])

    scheduler = Stream.scheduler
    # Start the computation by putting a value on x.
    x.append(1)
    scheduler.step()
    
    return D

def test_stop():
    """
    Stops a sequence of numbers.
    Shows how shared variables can be used to stop streams.

    """
    def generate_numbers(v, state, stop):
        """
        This function generates the sequence 0, 1, 2, ... starting
        with the specified initial state. The function stops execution
        when stop becomes True.

        Parameters
        ----------
        v: The element in the sequence, 0,1,2,.. read from the input
           stream.
        state: The last element of the sequence
        stop: array of length 1. This is a shared variable of the agent.

        """
        if not stop[0]:
            return state, state+1
        else:
            return _no_value, state

    def call_halt(v, N, stop):
        if v > N:
            stop[0] = True

    # stop is a variable shared by both agents that are created
    # below. It is initially False and set to True and then remains
    # True. 
    stop = [False]
    numbers = Stream('numbers')
    # Create an agent that reads and writes the same stream: numbers.
    # The agent executes its action when a new value appears on
    # numbers. The action puts the next value on numbers if stop is
    # False. The action has no effect (it is a skip operation) if stop
    # is True.
    map_element(
        func=generate_numbers, in_stream=numbers,
        out_stream=numbers, state=1, stop=stop)
    # Create an agent that sets stop to True after it reads more than
    # N values.
    N = 3
    sink(func=call_halt, in_stream=numbers, N=N, stop=stop)

    scheduler = Stream.scheduler
    # Start the computation by putting a value into the numbers stream.
    numbers.append(0)
    scheduler.step()
    # The stream numbers will be 0, 1, ... up to N-1 and possibly may
    # contain additional values. For example, if N = 3 then numbers
    # could be 0, 1, 2 or 0, 1, 2, 3, 4, 5.
    assert range(N) == recent_values(numbers)[:N]

def test_shared_variables():
    lst = [10, 6, 8, 3, 20, 2, 23, 35]
    sort(lst)
    assert lst == [2, 3, 6, 8, 10, 20, 23, 35]

    D = [[0, 20, 40, 60], [20, 0, 10, 1], [40, 10, 0, 100],
         [60, 1, 100, 0]]
    shortest_path(D)
    assert D == [[0, 20, 30, 21], [20, 0, 10, 1],
                 [30, 10, 0, 11], [21, 1, 11, 0]]
    print 'TEST OF SHARED VARIABLES IS SUCCESSFUL!'

if __name__ == '__main__':
    test_shared_variables()
    test_stop()

    
            
