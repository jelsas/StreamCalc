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
import numpy as n

def list_formatter(l):
  return '\n'.join( str(x) for x in l )

def hist_formatter(x, tick_char = '#', max_width = 80):
  '''prints a histogram'''
  (vals, bins) = x
  s_bins = ['%0.2f' % b for b in bins]
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

class Command(object):
  '''An individual command, deals with execution & formatting'''
  formatter = str
  function = sum
  help = ''

  def __init__(self, function = None, formatter = None, help = None):
    if formatter: self.formatter = formatter
    if function: self.function = function
    if help: self.help = help

  def __call__(self, *args):
    return self.function(*args)

  def process(self, *args):
    return self.formatter(self(*args))

class CommandProcessor(object):
  '''Handles processing commands'''
  def __init__(self):
    self._commands = {}

  def register_command(self, name, command = None, function = None,
                       formatter = None, help = None):
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

  def process(self, command, *args):
    try:
      c =self._commands[command]
    except KeyError, e:
      raise ValueError('Command not found: %s' % command)
    return c.process(*args)

c = CommandProcessor()
c.register_command('sum', function=sum, help='Add a list of numbers')
c.register_command('add', function=sum, help='see sum')
c.register_command('max', function=max, help='Max')
c.register_command('min', function=min, help='Min')
c.register_command('prod', function=n.prod, help='Multiply a list of numbers')
c.register_command('hist', function=lambda x: n.histogram(x, new=True),
                   formatter=hist_formatter, help='Produce a histogram')
c.register_command('mean', function=n.mean, help='Mean')
c.register_command('median', function=n.median, help='Median')
c.register_command('var', function=n.var, help='Variance')
c.register_command('std', function=n.std, help='Standard Deviation')
c.register_command('cumsum', function=n.cumsum, formatter=list_formatter,
                   help='Cumulative sum')
c.register_command('cumprod', function=n.cumprod, formatter=list_formatter,
                   help='Cumulative product')
c.register_command('exp', function=n.exp, formatter=list_formatter,
                   help='Exponentiate every element in the list')
c.register_command('log', function=n.log, formatter=list_formatter,
                   help='Take the log of every element in the list')
c.register_command('print', function=lambda x: x, formatter=list_formatter,
                  help='Just print the (cleaned) input')
c.register_command('help', function=None, help="Print this message")


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
  if not c.valid_command(command): help_quit(1)


  l = [float(x.strip()) for x in fileinput.input(sys.argv[2:]) \
          if len(x.strip()) > 0 and x[0] != '#']
  try:
    print c.process(command, l)
  except ValueError, e:
    help_quit(1, e)


