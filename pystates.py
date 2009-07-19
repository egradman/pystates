import time 
import logging
import random

class StateMachine(object):
  def __init__(self, name=None, time=time.time, log=None):
    self.name = name and name or str(self.__class__.__name__)
    self.time = time
    self.log = log

  def handle(self, ev):
    try:
      self.state_gen.send(ev)
    except StopIteration, exc:
      self.state_gen = exc.args[0]

  def start(self, state_name, *state_args, **state_kwargs):
    self.state_gen = self.activate_state(state_name, state_args, state_kwargs)

  def transition(self, state_name, *state_args, **state_kwargs):
    state_gen = self.activate_state(state_name, state_args, state_kwargs)
    raise StopIteration(state_gen)

  def activate_state(self, state_name, state_args, state_kwargs):
    self.log and self.log.debug("%s activating state %s", str(self), state_name)

    state_cls = getattr(self, state_name)
    state = state_cls(machine=self)
    state.start_time = self.time()
    state_gen = state.eval(*state_args, **state_kwargs)
    state_gen.next()
    return state_gen

  def __str__(self):
    return "<StateMachine:%s>" % self.name

class State(object):
  def __init__(self, machine):
    self.machine = machine

  def leave(self):
    pass

  def transition(self, state_name, *state_args, **state_kwargs):
    self.leave()
    self.machine.transition(state_name, state_args, state_kwargs)

  def duration(self):
    return self.machine.time() - self.start_time

class TestMachine(StateMachine):
  class STATE0(State):
    def eval(self, a, b):
      while True:
        ev = yield
        print "eval s0!"
        if ev['i'] % 5 == 0:
          self.transition("STATE1", random.random(), random.random())

    def leave(self):
      print "leave s0!"

  class STATE1(State):
    def eval(self, a, b):
      while True:
        ev = yield
        print "eval s1!"
        if self.duration() > 7.0:
          print "timeout!"
          self.transition("STATE0", random.random(), random.random())

    def leave(self):
      print "leave s1!"

def main():
  logging.basicConfig(level=logging.DEBUG)

  m = TestMachine(log=logging)
  m.start("STATE0", random.random(), random.random())

  i = 0
  while True:
    time.sleep(0.5)
    ev = dict(i=i)
    m.handle(ev)
    i += 1

if __name__=='__main__':
  l = logging.log
  main()

