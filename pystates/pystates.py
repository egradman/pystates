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

Example:

  from pystates import StateMachine, State

  class MyMachine(StateMachine):
    class IDLE(State):
      def eval(self):
        while True:
          ev = yield
          if ev.type == pygame.KEYDOWN:
            self.transition("RUNNING", ev.key)

    class RUNNING(State):
      def eval(self, key):
        print "you pressed the %s key" % key
        while True:
          ev = yield
          if self.duration() > 5.0:
            self.transition("COUNTDOWN")

      def leave(self):
        print "timeout!"

    class COUNTDOWN(State):
      def eval(self):
        i = 10
        while True:
          ev = yield
          print "i = %d" % i
          if i == 0:
            self.transition("IDLE")
          i -= 1

See the README for a details on how to implement your own StateMachines
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
      name: The name by which your StateMachine is known. It defaults to the name of
            the class
      time: An alternative function used to tell time.  For example, sometimes with
            pygame its useful to use pygame.ticks for consistency.  It defaults to
            time.time()
      log:  If you supply a python logging object, your StateMachine will use it to
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

  def start(self, state_name, *state_args):
    """
    If this machine has a state named by the state_name argument, then the machine
    will activate the named state.  This is essentially a transition from a NULL
    state to the named state.

    Any args are passed to the eval method of the named state.
    """
    self.state_gen = self.activate_state(state_name, state_args)

  def transition(self, state_name, state_args):
    """
    If this machine has a state named by the state_name argument, then the machine
    will transition to the named state.  The current state's leave() method will be
    called, if it exists.

    Any args are passed to the eval method of the named state.
    """
    state_gen = self.activate_state(state_name, state_args)
    raise StopIteration(state_gen)

  def activate_state(self, state_name, state_args):
    self.log("%s activating state %s", str(self), state_name)

    state_cls = getattr(self, state_name, None)
    if state_cls is None:
      raise NotImplementedError("state %s is not implemented" % state_name)
    state = state_cls(m=self)
    state.start_time = self.time()
    state_gen = state.eval(*state_args)
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

  def eval(self, *args):
    """
    Useful states override the eval method.  This method *must* have the structure:
      while True:
        ev = yield
        ... do something based on the value of ev ...
        ... including possibly self.transition("NEW_STATE") ...
    """
    raise NotImplementedError("State %s is not implemented" % self.name)

  def leave(self):
    """If implemented, this method is called as the machine transitions away"""
    pass

  def transition(self, state_name, *state_args):
    self.leave()
    self.m.transition(state_name, state_args)

  def duration(self):
    return self.m.time() - self.start_time


