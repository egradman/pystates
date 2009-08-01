import logging
import time

from pystates import StateMachine

class TestMachine(StateMachine):
  def STATE0(self, x=0):
    self.log("x is " + str(x))

    while True:
      ev = yield
      if ev['i'] % 5 == 0:
        self.transition(self.STATE1, x+1)
      if x > 10:
        self.transition(self.END)

  def STATE1(self, x):
    self.log("x is " + str(x))
    while True:
      ev = yield
      if ev['i'] % 5 == 0:
        self.transition(self.STATE0, x+1)

  def END(self):
    self.log("waiting 5 seconds to start over")
    while True:
      ev = yield
      if self.duration() > 5:
        self.log("timeout!")
        self.transition(self.STATE0, 0)

def main():
  logging.basicConfig(level=logging.DEBUG)

  m = TestMachine(log=logging)
  m.start(m.STATE0)

  i = 0
  while True:
    time.sleep(0.1)
    ev = dict(i=i)
    m.handle(ev)
    i += 1

if __name__=='__main__':
  main()
