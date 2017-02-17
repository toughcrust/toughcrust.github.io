#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import json
import os
import re

HTML_FILE = os.path.join(os.path.dirname(__file__), 'test_index.html')
LOL_DATABASE = os.path.join(os.path.dirname(__file__), 'lol_database.md')

output = {
    'titles': [],
    'haikus': [],
}

with open(LOL_DATABASE, 'r') as in_file:
    lines = in_file.readlines()

sections_titles = [
    "### TITLES",
    "### HAIKUS",
]

current_section = None
next_section = sections_titles[0]


class HaikuBuffer(object):
    haikus = []
    data_stream = {'type': 'paragraph', 'data': []}
    output = None
    current = None

    def __init__(self, output):
        self.output = output

    def init_haiku(self, title):
        self.current = {
            'index': len(self.haikus),
            'title': title,
            'tags': [],
            'content': [],
        }

    def digest_haiku(self):
        self.digest_stream()
        if self.current:
            self.haikus.append(copy.deepcopy(self.current))

    def set_tags(self, tags):
        self.current['tags'] = tags      

    def digest_stream(self, next_type='paragraph'):
        if len(self.data_stream['data']) > 0:
            self.current['content'].append(copy.deepcopy(self.data_stream))
        self.data_stream = {'type': next_type, 'data': []}

    def set_stream(self, type):
        if type != self.data_stream['type']:
            self.digest_stream(next_type=type)

    def toggle_stream(self, type, default='paragraph'):
        if type != self.data_stream['type']:
            self.set_stream(type)
        else:
            self.set_stream(default) 

    def stream_content(self, content):
        self.data_stream['data'].append(content)


buffer = HaikuBuffer(output)
haiku_title_regex = re.compile('^##\s(.*)')
haiku_tags_regex = re.compile('^tags:\s(.*)')
list_regex = re.compile('^-\s(.*)')
quote_regex = re.compile('^""$')


for line in lines:
    text = line.strip('\n')

    if next_section in text:
        if current_section is None:
            current_section = 0
        else:
            current_section += 1
        if current_section < len(sections_titles) - 1:
            next_section = sections_titles[current_section + 1]
        continue

    is_blank_line = True if not text else False

    if current_section == 0 and not is_blank_line:
        output['titles'].append(text)
    elif current_section == 1:
        if haiku_title_regex.match(text):
            title = haiku_title_regex.match(text).group(1)
            buffer.digest_haiku()
            buffer.init_haiku(title)
        elif haiku_tags_regex.match(text):
            tags = [tag.strip().lstrip() for tag in haiku_tags_regex.match(text).group(1).split(',')]
            buffer.set_tags(tags)
        else:
            if is_blank_line:
                buffer.digest_stream()
            else:
                content = text
                if list_regex.match(text):
                    content = list_regex.match(text).group(1)
                    buffer.set_stream('list')
                elif quote_regex.match(text):
                    buffer.toggle_stream('quote')
                    continue
                buffer.stream_content(content)

buffer.digest_haiku()

output['haikus'] = buffer.haikus
output['tags'] = list(set([tag for haiku in output['haikus'] for tag in haiku['tags']]))

# Substitution de la variable dans le script JS par un dump JSON python
# bien bien dégueu cette DB :ok_hand:
haiku_placeholder_regex = re.compile(r'\s*const\srawHaikus\s=\s(.*)')
new_haiku_content = json.dumps(output['haikus'], ensure_ascii=False)

titles_placeholder_regex = re.compile(r'^\s*const\srawTitles\s=\s(.*)')
new_titles = json.dumps(output['titles'], ensure_ascii=False)

tags_placeholder_regex = re.compile(r'^\s*const\srawTags\s=\s(.*)')
new_tags = json.dumps(output['tags'], ensure_ascii=False)

with open(HTML_FILE, 'r') as in_file:
    lines = in_file.readlines()

for index, line in enumerate(lines):
    if haiku_placeholder_regex.match(line):
        to_replace = haiku_placeholder_regex.match(line).group(1)
        lines[index] = line.replace(to_replace, new_haiku_content)
    if titles_placeholder_regex.match(line):
        to_replace = titles_placeholder_regex.match(line).group(1)
        lines[index] = line.replace(to_replace, new_titles)
    if tags_placeholder_regex.match(line):
        to_replace = tags_placeholder_regex.match(line).group(1)
        lines[index] = line.replace(to_replace, new_tags)

with open(HTML_FILE, 'w') as out_file:
    for line in lines:
        out_file.write(line)
