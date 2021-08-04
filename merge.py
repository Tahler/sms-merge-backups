#!/usr/bin/env python3

import glob
import re
import sys


paths = list(glob.glob('data/*.xml'))


def _search(pattern, line):
  match = pattern.search(line)
  return match.group(1) if match else None


DATE_PATTERN = re.compile(r'date="(\d+)"')
def _date(line):
  raw = _search(DATE_PATTERN, line)
  return int(raw) if raw else None


DOUBLE_QUOTE_BODY_PATTERN = re.compile(r'body="(.*?)"')
SINGLE_QUOTE_BODY_PATTERN = re.compile(r"body='(.*?)'")
def _body(line):
  if "body='" in line:
    return _search(SINGLE_QUOTE_BODY_PATTERN, line)
  return _search(DOUBLE_QUOTE_BODY_PATTERN, line)


HTML_SYMBOL_PATTERN = re.compile(r'&.*?;')
def _strip_html_symbols(line):
  return HTML_SYMBOL_PATTERN.sub('', line)


def _key(line):
  date = _date(line)
  body = _body(line)
  stripped = _strip_html_symbols(body)
  return (date, stripped)


def smses():
  by_key = {}
  for path in paths:
    with open(path) as f:
      for line in f:
        stripped = line.strip()
        if not stripped.startswith('<sms '):
          continue

        key = _key(stripped)

        longest = line
        if key in by_key:
          prev = by_key[key]
          if len(_body(prev)) > len(_body(line)):
            longest = prev

        by_key[key] = longest

  lines = sorted(by_key.values(), key=_date)
  with open('smses.xml', 'w') as f:
    f.writelines(lines)


M_ID_PATTERN = re.compile(r'm_id="(.*?)"')
def _mms_key(line):
  date = _date(line)
  m_id = _search(M_ID_PATTERN, line)
  if date is None or m_id is None:
    print('AHH whyyyy')
    print(line)
    sys.exit(1)
  return (date, m_id)


def mmses():
  by_key = {}

  for path in paths:
    with open(path) as f:
      key = None
      lines = []
      for line in f:
        stripped = line.strip()

        in_mms_tag = key is not None
        if in_mms_tag:
          lines.append(line)

          if stripped == '</mms>':
            print('INSERTING KEY', key)
            by_key[key] = ''.join(lines)

            lines = []
            key = None

          continue

        if not stripped.startswith('<mms '):
          continue

        new_key = _mms_key(stripped)
        if new_key in by_key:
          continue
        key = new_key
        lines.append(line)

  lines = sorted(by_key.values(), key=_date)
  with open('mmses.xml', 'w') as f:
    f.writelines(lines)


def _copy_all_lines(input, output):
  output.writelines(input)


def finalize():
  with open('merged.xml', 'w') as w:
    w.write('''<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>''')
    w.write('<smses>')
    with open('smses.xml') as r:
      _copy_all_lines(r, w)
    with open('mmses.xml') as r:
      _copy_all_lines(r, w)
    w.write('</smses>')



def main():
  smses()
  mmses()
  finalize()


if __name__ == '__main__':
  main()
