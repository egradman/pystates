import logging
import time

from pystates import StateMachine, State

class TestMachine(StateMachine):
  class STATE0(State):
    def eval(self, x=0):
      self.m.log("x is " + str(x))

      while True:
        ev = yield
        if ev['i'] % 5 == 0:
          self.transition("STATE1", x+1)
        if x > 10:
          self.transition("END")

    def leave(self):
      self.m.log("leaving state %s", self.name)

  class STATE1(State):
    def eval(self, x):
      self.m.log("x is " + str(x))
      while True:
        ev = yield
        if ev['i'] % 5 == 0:
          self.transition("STATE0", x+1)

  class END(State):
    def eval(self):
      self.m.log("waiting 5 seconds to start over")
      while True:
        ev = yield
        if self.duration() > 5:
          self.m.log("timeout!")
          self.transition("STATE0", 0)
    def leave(self):
      self.m.log("starting over with x=0")

def main():
  logging.basicConfig(level=logging.DEBUG)

  m = TestMachine(log=logging)
  m.start("STATE0")

  i = 0
  while True:
    time.sleep(0.1)
    ev = dict(i=i)
    m.handle(ev)
    i += 1

if __name__=='__main__':
  main()
