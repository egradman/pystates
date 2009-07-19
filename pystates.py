# Copyright (c) 2009 Eric Gradman (Monkeys & Robots)
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
pystates - A simple and powerful python state machine framework using coroutines

Sometimes, a state machine is just what you need.  State machines are
conceptually simple, but make for ugly code.  The pystates module provides a
simple framework that uses coroutines to implement resumable states.  And its
easy on the eyes.

To make a state machine, you will subclass the StateMachine class.  You can
customize your subclass as needed; minimally you must implement your states as
nested State subclasses.  Each State subclass must provide an eval() method
(which must follow a particular structure) and optionally a leave() method.

Look in mymachine.py for a documented example.

The eval method must have the same basic structure as the example.  It should
perform any setup operations, then enter a while loop.  The first statement in
the while loop should read "ev = yield".  This incantataion establishes the
method as a "generator."  Whenever any function containing a yield statement is
called, the function does not run immediately.  Instead, a generator object is
immediately returned to the caller.  This generator object acts as a
"coroutine," that is, a method whose execution can be paused and resumed while
the rest of the program continues.

What this means for you is that for the period of time during which your state
machine is in a given state S, the eval() method of S will never return!
Instead, it will hang out in "while" loop you've written.  Whenever that while
loop reaches the "ev = yield" line, control will return to whoever called the
machine's handle() method.  When the machines handle() method is next called
with an event ev, the current state's eval method will resume, with ev now set
equal to handle()'s ev argument.  You are then free to act on the contents of
ev however you please, possibly by transition()'ing to a new state.

A single State, therefore, doesn't generally need to use non-locally scoped
variables as "memory."  However, when your machine transitions to a new state,
the machine can use machine member variables (the machine is always accessible
as self.m from inside a state) OR it can pass arguments to the target state.
All args and kwargs after the state name argument to transition() are passed to
the eval() method of the newly transitioned-to state.

Whenever a transition to a new state occurs, the State's leave() method is
called (if it exists).  This allows you to include State cleanup code that's
always run regardless of which state you're transitioning to.

Sometimes its useful to make a transition when a given state has been running
for a certain amount of time (such as in timeout scenarios).  For this reason,
any state's eval() method can determine the length of time the state has been
active by calling its duration() method.
"""

import time 
import logging

class StateMachine(object):
  """StateMachine
  Do not instantiate this class directly.  Instead, make a subclass.  Your
  subclass should contain nested subclasses of State that implement the states
  your machine can achieve.
  """

  def __init__(self, name=None, time=time.time, log=None):
    """
    Keyword arguments:
      name: The name by which your state machine is known. It defaults to the name of
            the class
      time: An alternative function used to tell time.  For example, sometimes with
            pygame its useful to use pygame.ticks for consistency.  It defaults to
            time.time()
      log:  If you supply a python logging object, your state machine will use it to
            log transitions.
    """
    self.name = name and name or str(self.__class__.__name__)
    self.time = time
    self.log = log and log.debug or (lambda *args: None)

  def handle(self, ev):
    """
    When you call this method, this machine's current state will resume with
    the supplied ev object.
    """
    try:
      self.state_gen.send(ev)
    except StopIteration, exc:
      self.state_gen = exc.args[0]

  def start(self, state_name, *state_args, **state_kwargs):
    """
    If this machine has a state named by the state_name argument, then the machine
    will activate the named state.  This is essentially a transition from a NULL
    state to the named state.

    Any args and kwargs are passed to the eval method of the named state.
    """
    self.state_gen = self.activate_state(state_name, state_args, state_kwargs)

  def transition(self, state_name, *state_args, **state_kwargs):
    """
    If this machine has a state named by the state_name argument, then the machine
    will transition to the named state.  The current state's leave() method will be
    called, if it exists.

    Any args and kwargs are passed to the eval method of the named state.
    """
    state_gen = self.activate_state(state_name, state_args, state_kwargs)
    raise StopIteration(state_gen)

  def activate_state(self, state_name, state_args, state_kwargs):
    self.log("%s activating state %s", str(self), state_name)

    state_cls = getattr(self, state_name)
    state = state_cls(m=self)
    state.start_time = self.time()
    state_gen = state.eval(*state_args, **state_kwargs)
    state_gen.next()
    return state_gen

  def __str__(self):
    return "<StateMachine:%s>" % self.name

class State(object):
  """State
  Do not instantiate this class directly.  Instead, make a subclass.  Your
  subclass should contain an eval() method and optionally a leave() method.
  """

  def __init__(self, m):
    """Do not override __init__ unless you know what you're doing"""
    self.m = m
    self.name = self.__class__.__name__

  def eval(self, *args, **kwargs):
    """
    Useful states override the eval method.  This method *must* have the structure:
      while True:
        ev = yield
        ... do something based on the value of ev ...
        ... including possibly self.transition("NEW_STATE") ...
    """
    self.m.log("State %s is not implemented", self.name)
    while True:
      ev = yield

  def leave(self):
    """If implemented, this method is called as the machine transitions away"""
    pass

  def transition(self, state_name, *state_args, **state_kwargs):
    self.leave()
    self.m.transition(state_name, state_args, state_kwargs)

  def duration(self):
    return self.m.time() - self.start_time


