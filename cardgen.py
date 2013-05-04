#!/usr/bin/python

"""Produces SVG files for a set of cards specified in a CSV file.

The CSV file should contain one card per line.

Run this script with the --help option for help.
"""

import argparse
import copy
import math
import re
import sys
import xml.etree.ElementTree as ET

TEMPLATE_REGEX = '\[\[(\d+)\]\]'


def parse_csv(fname):
  """CSV file describing the cards. First column is the card count."""
  result = []
  with open(fname, 'r') as f:
    for line in f:
      tmp = line.strip('\n').split(',')
      result.extend([tmp[1:]] * int(tmp[0]))
  return result


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('csv', metavar='CARDS_CSV', type=str,
                      help='a csv file with one card type defined per line in '
                           'this order: \nname, combat value, card count, '
                           'additional effects')
  parser.add_argument('template', metavar='TEMPLATE_SVG', type=str,
                      help='a template SVG file, text matching [[N]] will be '
                           'replaced by the Nth csv column.')
  parser.add_argument('out', metavar='OUT', type=str, default='out',
                      nargs='?',
                      help='optional output filename base, defaults to out')
  parser.add_argument('--width', type=int, default=4,
                      help='card per page horizontally')
  parser.add_argument('--height', type=int, default=2,
                      help='card per page vertically')
  args = parser.parse_args()

  # Template regex.
  template_regex = re.compile(TEMPLATE_REGEX)

  # Parse cards from input CSV file.
  csv = parse_csv(args.csv)
  digits = int(math.log10(len(csv)))  # Used to pad output filename.

  # Template file.
  dom = ET.ElementTree(file=args.template)
  template_width = int(dom.getroot().attrib['width'])
  template_height = int(dom.getroot().attrib['height'])

  # Construct all pages.
  index = 0
  filenum = 0
  while index < len(csv):
    # New SVG DOM.
    root = ET.Element('svg', {'xmlns':'http://www.w3.org/2000/svg'})
    dom_out = ET.ElementTree(element=root)
    root.attrib['width'] = str(template_width * int(args.width))
    root.attrib['height'] = str(template_height * int(args.height))

    # Construct page.
    for x in xrange(args.width):
      for y in xrange(args.height):
        if index == len(csv):
          break
        doc_copy = copy.deepcopy(dom.getroot())
        # Set offset.
        doc_copy.attrib['x'] = str(template_width * x)
        doc_copy.attrib['y'] = str(template_height * y)
        # Substitute templated text.
        for node in doc_copy.iter():
          if node.text:
            match = template_regex.match(node.text)
            if match:
              node.text = csv[index][int(match.group(1))].replace('\\n', '\n')
        root.append(doc_copy)
        index +=1

    # Write output SVG file for the page.
    fname = '%s_%s.svg' % (args.out, str(filenum).zfill(digits))
    with open(fname, 'w') as out:
      dom_out.write(out)
    filenum += 1



if __name__ == '__main__':
  main()
