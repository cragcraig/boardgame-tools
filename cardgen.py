#!/usr/bin/python

"""Produces SVG and/or PDF files for a set of cards specified in a CSV file.

The CSV file should contain one card per line, where the first column is the
number of duplicates of the card to create. Subsequent columns will be used to
generate the cards according to the template file, where any text in the
template file matching the pattern [[N]] will be replaced by the corresponding
Nth column of text from the csv file.

Run this script with the --help option for help. Example usage:
python cardgen.py example_files/cards.csv example_files/template.svg
"""

import argparse
import copy
import math
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

GRID_FRACTION = 0.3
TEMPLATE_REGEX = re.compile('\[\[(\d+)\]\]')


def parse_csv(fname):
  """CSV file describing the cards. First column is the card count."""
  result = []
  with open(fname, 'r') as f:
    for line in f:
      tmp = line.strip('\n').split(',')
      result.extend([tmp[1:]] * int(tmp[0]))
  return result


def add_line(root, stroke, x1, y1, x2, y2):
  elem = ET.Element('line', {
      'style': 'stroke:rgb(150,150,150);stroke-width:%d' % stroke,
      'x1': str(x1),
      'y1': str(y1),
      'x2': str(x2),
      'y2': str(y2), })
  root.append(elem)


def add_hline(root, stroke, x, y, length):
  add_line(root, stroke, x, y, x + length, y)


def add_vline(root, stroke, x, y, length):
  add_line(root, stroke, x, y, x, y + length)


def apply_template(text, csv_row):
  if not text:
    return None
  match = TEMPLATE_REGEX.match(text)
  if match:
    repl_text = csv_row[int(match.group(1))].replace('\\n', '\n')
    return TEMPLATE_REGEX.sub(repl_text, text)
  return None


def main():
  # Parse arguments.
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
  parser.add_argument('--pdf', default=False, action='store_true',
                      help='Output a single PDF, defaults to SVG files')
  parser.add_argument('--no-grid', default=False, action='store_true',
                      help='Do not add a grid in the margins')
  parser.add_argument('--width', type=int, default=4,
                      help='cards per page horizontally')
  parser.add_argument('--height', type=int, default=2,
                      help='cards per page vertically')
  parser.add_argument('--horiz-margin', type=float, default=0.5,
                      help='horizontal margins in inches, defaults to 0.5')
  parser.add_argument('--vert-margin', type=float, default=0.75,
                      help='vertical margins in inches, defaults to 0.75')
  parser.add_argument('--units-per-inch', type=int, default=90,
                      help='number of svg units per inch, defaults to 90')
  args = parser.parse_args()

  # Constants.
  horiz_margin = args.units_per_inch * args.horiz_margin
  vert_margin = args.units_per_inch * args.vert_margin

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
  output_fnames = []
  while index < len(csv):
    # New SVG DOM.
    root = ET.Element('svg', {'xmlns':'http://www.w3.org/2000/svg'})
    dom_out = ET.ElementTree(element=root)
    root.attrib['width'] = str(template_width * int(args.width) +
                               2 * horiz_margin)
    root.attrib['height'] = str(template_height * int(args.height) +
                                2 * vert_margin)

    # Optionally construct grid.
    if not args.no_grid:
      for x in xrange(args.width + 1):
        add_vline(root, args.units_per_inch * 0.025,
                  x * template_width + horiz_margin,
                  vert_margin * (1.0 - GRID_FRACTION),
                  vert_margin * GRID_FRACTION)
        add_vline(root, args.units_per_inch * 0.025,
                  x * template_width + horiz_margin,
                  args.height * template_height + vert_margin,
                  vert_margin * GRID_FRACTION)
      for y in xrange(args.height + 1):
        add_hline(root, args.units_per_inch * 0.025,
                  horiz_margin * (1.0 - GRID_FRACTION),
                  y * template_height + vert_margin,
                  horiz_margin * GRID_FRACTION)
        add_hline(root, args.units_per_inch * 0.025,
                  args.width * template_width + horiz_margin,
                  y * template_height + vert_margin,
                  horiz_margin * GRID_FRACTION)

    # Construct page.
    for x in xrange(args.width):
      for y in xrange(args.height):
        if index == len(csv):
          break
        doc_copy = copy.deepcopy(dom.getroot())
        # Set offset.
        doc_copy.attrib['x'] = str(template_width * x + horiz_margin)
        doc_copy.attrib['y'] = str(template_height * y + vert_margin)
        # Substitute templated text.
        for node in doc_copy.iter():
          repl_text = apply_template(node.text, csv[index])
          if repl_text:
            node.text = repl_text
          for attrib, value in node.attrib.iteritems():
            repl_text = apply_template(value, csv[index])
            if repl_text:
              node.attrib[attrib] = repl_text
        root.append(doc_copy)
        index +=1

    # Write output SVG file for the page.
    if args.pdf:
      with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as out:
        dom_out.write(out)
        output_fnames.append(out.name)
    else:
      fname = '%s_%s.svg' % (args.out, str(filenum).zfill(digits))
      with open(fname, 'w') as out:
        dom_out.write(out)
      output_fnames.append(fname)
    filenum += 1

  # Optionally generate merged PDF.
  pdf_fnames = []
  if args.pdf:
    # Convert each SVG page to PDF.
    for out in output_fnames:
      tfile = tempfile.mkstemp(suffix='.pdf')
      os.close(tfile[0])
      fname = '%s.pdf' % tfile[1]
      pdf_fnames.append(fname)
      try:
        subprocess.check_call(['inkscape', '--file=%s' % out,
                               '--export-pdf=%s' % fname])
      except OSError as e:
        raise OSError('inkscape must be installed and in your path.')
    # Merge PDF pages.
    pdfunite = ['pdfunite']
    pdfunite.extend(pdf_fnames)
    pdfunite.append('%s.pdf' % args.out)
    try:
      subprocess.check_call(pdfunite)
    except OSError as e:
      raise OSError('pdfunite must be installed and in your path.')


if __name__ == '__main__':
  main()
