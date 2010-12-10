#!/usr/bin/python
'''
A command-line calculator over streams of numbers.
Requires numpy.

  For example:

# create a file with 100 random numbers, 1 per line
$ jot -r 100 > /tmp/random

# the max, min, mean of that random data
$ calc.py max /tmp/random
100.0
$ calc.py min /tmp/random
1.0
$ calc.py mean /tmp/random
48.86

# the median, using pipes instead of the file name
$ cat /tmp/random | calc.py median
51.0

# chaining commands -- exponentiating, then adding the numbers
$ cat /tmp/random | calc.py exp | calc.py sum
8.22200074586e+43

# print a histogram of random data
$ jot -r 100 | calc.py hist
[ 3.00,12.30): ############
[12.30,21.60): ########
[21.60,30.90): #######
[30.90,40.20): #########
[40.20,49.50): ###############
[49.50,58.80): #########
[58.80,68.10): #########
[68.10,77.40): #######
[77.40,86.70): ###############
[86.70,96.00]: #########

# same thing, but logarithmic histogram bins
$ jot -r 100 | calc.py log | calc.py hist
[0.00,0.46): ###
[0.46,0.92): ##
[0.92,1.38):
[1.38,1.84): ###
[1.84,2.30): ###
[2.30,2.76): #####
[2.76,3.22): ############
[3.22,3.68): ###########
[3.68,4.14): #############################
[4.14,4.60]: ################################

'''
from __future__ import division
import numpy as n
import math as m
from itertools import imap

def list_formatter(l):
  return '\n'.join( str(x) for x in l )

def hist_formatter(x, tick_char = '#', max_width = 80):
  '''prints a histogram'''
  (vals, bins) = x
  s_bins = ['%0.2g' % b for b in bins]
  max_bin_len = max(len(x) for x in s_bins)
  s_bins = [x.rjust(max_bin_len) for x in s_bins]
  max_val = max(vals)
  if max_val + 5 + (max_bin_len*2) > max_width:
    max_available_width = max_width - 5 - (max_bin_len*2)
    vals = [ max_available_width * v // max_val for v in vals]

  s = '\n'.join('[%s,%s): %s' % (s_bins[i], s_bins[i+1], tick_char*vals[i]) \
                for i in xrange(len(vals)-1))
  s = s + '\n[%s,%s]: %s' % (s_bins[len(vals)-1], s_bins[len(vals)],
                                tick_char*vals[-1])
  return s

def s_mean_var(data):
  '''calculates the mean & variance with minimal intermediate data structures.
  see http://www.johndcook.com/standard_deviation.html'''
  m_n = 0
  m_oldM, m_newM, m_oldS, m_newS = 0.0, 0.0, 0.0, 0.0
  for x in data:
    m_n += 1
    if m_n == 1:
      m_oldM = m_newM = x
      m_oldS = 0.0
    else:
      m_newM = m_oldM + (x - m_oldM) / m_n
      m_newS = m_oldS + (x - m_oldM)*(x - m_newM)
      m_oldM, m_oldS = m_newM, m_newS
  mean = m_newM if m_n > 0 else 0.0
  var = m_newS / (m_n - 1) if m_n > 1 else 0.0
  return (mean, var)

def s_mean(data): return s_mean_var(data)[0]
def s_var(data): return s_mean_var(data)[1]
def s_std(data): return m.sqrt(s_var(data))

def s_cumsum(data):
  sum = 0
  for x in data:
    sum += x
    yield x

def s_cumprod(data):
  prod = 1.0
  for x in data:
    prod *= x
    yield prod

s_exp = lambda data: imap(m.exp, data)
s_log = lambda data: imap(m.log, data)

def s_prod(data):
  prod = 1.0
  for x in data: prod *= x
  return prod

def l(func):
  '''Simple function wrapper to convert the input into a list.  Used for
  making the numpy functions below behave correctly with a generator input.'''
  return lambda data: func(list(data))

class Command(object):
  '''An individual command, deals with execution & formatting'''

  def __init__(self, function = None, formatter = str, help = None):
    self.formatter = formatter
    self.function = function
    self.help = help

  def __call__(self, data):
    return self.function(data) if self.function else data

  def process(self, data):
    return self.formatter(self(data))

class CommandProcessor(object):
  '''Handles processing commands'''
  def __init__(self):
    self._commands = {}

  def register_command(self, name, command = None, function = None,
                       formatter = str, help = None):
    if command:
      self._commands[name] = command
    else:
      self._commands[name] = Command(function, formatter, help)

  def valid_command(self, command):
    return command in self._commands

  def command_list(self):
    all_commands_help = ['\t%s\t%s' % (name, c.help) for (name, c) in \
                      sorted(self._commands.items())]
    return '\n'.join(all_commands_help)

  def process(self, command, data):
    try:
      c =self._commands[command]
    except KeyError, e:
      raise ValueError('Command not found: %s' % command)
    return c.process(data)

c = CommandProcessor()
c.register_command('sum', function=sum, help='Add a list of numbers')
c.register_command('add', function=sum, help='see sum')
c.register_command('max', function=max, help='Max')
c.register_command('min', function=min, help='Min')
c.register_command('prod', function=s_prod,
                   help='Multiply a list of numbers')
c.register_command('hist', function=lambda x: n.histogram(list(x), new=True),
                   formatter=hist_formatter, help='Produce a histogram')
c.register_command('mean', function=s_mean, help='Mean')
c.register_command('median', function=l(n.median), help='Median')
c.register_command('var', function=s_var, help='Variance')
c.register_command('std', function=s_std, help='Standard Deviation')
c.register_command('cumsum', function=l(n.cumsum), formatter=list_formatter,
                   help='Cumulative sum')
c.register_command('cumprod', function=s_cumprod, formatter=list_formatter,
                   help='Cumulative product')
c.register_command('exp', function=s_exp, formatter=list_formatter,
                   help='Exponentiate every element in the list')
c.register_command('log', function=s_log, formatter=list_formatter,
                   help='Take the log of every element in the list')
c.register_command('print', function=None, formatter=list_formatter,
                   help='Just print the (cleaned) input')
c.register_command('help', function=None, help="Print this message")
c.register_command('rstat', function=s_mean_var,
                   help='Computes mean & variance with lower memory usage')


if __name__ == "__main__":
  import fileinput, sys
  def help_quit(i, e = None):
    help = '''Usage: calc.py [command] [files or -]
Reads a list of numbers from the files or standard input if files are missing
and performs the calculation specified by the command.
Available Commands:
%s''' % c.command_list()
    print >> sys.stderr, help
    if e: print >> sys.stderr, e
    sys.exit(i)

  if len(sys.argv) < 2: help_quit(1)

  command = sys.argv[1]

  if command == 'help': help_quit(0)

  l = (float(x.strip()) for x in fileinput.input(sys.argv[2:]) \
          if len(x.strip()) > 0 and x[0] != '#')
  try:
    print c.process(command, l)
  except ValueError, e:
    help_quit(1, e)


