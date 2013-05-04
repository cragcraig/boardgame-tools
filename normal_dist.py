#!/usr/bin/python

import argparse
import math


def normal_dist(std, mean, integral, lower_bound=0):
  def f(x):
    return ((integral / (float(std) * math.sqrt(2 * math.pi))) *
            math.exp(-((float(x) - mean)**2) / (2 * std * std)))
  return {x: f(x) for x in xrange(max(mean - 3 * std, lower_bound),
                                  mean + 3 * std + 1)}

def main():
  parser = argparse.ArgumentParser(description='Compute a normal distribution.')
  parser.add_argument('std', metavar='STD', type=int,
                      help='The desired standard deviation.')
  parser.add_argument('mean', metavar='MEAN', type=int,
                      help='The desired mean.')
  parser.add_argument('integral', metavar='INTEGRAL', type=int,
                      help='The desired sum of the values.')
  parser.add_argument('-i', '--integers', default=False, action='store_true',
                      help='Round final values to integers.')
  parser.add_argument('-s', '--mark', default=False, action='store_true',
                      help='Mark the center of the distribution.')
  parser.add_argument('-m', '--min', default=0, type=int,
                      help='Lower bound of the distribution.')
  args = parser.parse_args()
  dist = normal_dist(args.std, args.mean, args.integral, args.min)
  if args.integers:
    dist = {x: round(v) for x, v in dist.iteritems()}
  print '  n: value'
  print '---:--------'
  for x, v in dist.iteritems():
    print ('%s: %0.2f' % (str(x).rjust(3), v) +
           (' <--' if x == args.mean and args.mark else ''))
  print 'Actual discrete integral: %0.2f' % sum(dist.itervalues())

if __name__ == '__main__':
  main()
