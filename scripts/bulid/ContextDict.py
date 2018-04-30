#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import os
import re

class ContextDict(dict):
    RE_FUNC = re.compile(r'{([^:}]+):([^:}]+)}')
    RE_REPLACE = re.compile(r'{([^}]+)}')

    def __init__(self, context_dict=None):
        super(ContextDict, self).__init__()
        if context_dict is None:
            context_dict = {}
        if not isinstance(context_dict, type({})):
            raise TypeError('require dictionary but it is ' + str(type(context_dict)))
        # for key, value in context_dict.items():
        #     context_dict[unicode(key)] = unicode(value)
        noext_lambda = lambda path: os.path.basename(path).split(os.path.extsep)[0]
        ext_lambda = lambda path: os.path.basename(path).split(os.path.extsep)[1]
        self._context_dict = {}
        for k, v in context_dict.items():
            self._context_dict[k.lower()] = v
        self._context_func_dict = {
            "basename": os.path.basename,
            "dirname": os.path.dirname,
            "noext": noext_lambda,
            "ext": ext_lambda,
        }

    def has(self, name):
        return name.lower() in self._context_dict

    def __getattr__(self, name):
        name = name.lower()
        item = self._context_dict[name]
        if isinstance(item, type(lambda: None)):
            return item()
        return item
        
    def __setitem__(self, name, value):
        name = name.lower()
        self._context_dict[name] = value
        
    def __getitem__(self, name):
        name = name.lower()
        item = self._context_dict[name]
        if isinstance(item, type(lambda: None)):
            return item()
        return self.format(item)

    def register_func(self, name, func):
        name = name.lower()
        if not isinstance(func, type(lambda _: None)):
            raise TypeError('require function or lambda but it is ' + str(type(func)))
        self._context_func_dict[name] = func

    def get(self, name):
        name = name.lower()
        return self._context_dict[name]

    def set(self, name, value):
        name = name.lower()
        self._context_dict[name] = value

    def format(self, text):
        context_dict = {}
        for key, value in self._context_dict.items():
            key = key.lower()
            if isinstance(value, type(lambda: None)):
                context_dict[key] = value()
            else:
                context_dict[key] = value
        for key, value in os.environ.items():
            key = key.lower()
            context_dict[key] = value

        all_match = []
        for match in self.RE_FUNC.finditer(text):
            all_match.append(match)
        if len(all_match) == 0:
            new_text = text
        else:
            start = 0
            new_text_pieces = []
            for match in all_match:
                new_text_pieces += [text[start:match.start()]]
                replaced_text = text[match.start():match.end()]
                funcname = match.group(1)
                key = match.group(2)
                key = key.lower()
                if funcname in self._context_func_dict and key in context_dict:
                    func = self._context_func_dict[funcname]
                    try:
                        replaced_text = func(context_dict[key])
                    except:
                        replaced_text = context_dict[key]
                new_text_pieces += [replaced_text]
                start = match.end()
            new_text_pieces += [text[all_match[-1].end():]]
            new_text = ''.join(new_text_pieces)
        new_text = self.RE_REPLACE.sub(lambda m: str(m.group(0)).lower(), new_text)
        return new_text.format(**context_dict)

    def merge(self, context_dict):
        for key, value in context_dict.items():
            key = key.lower()
            self._context_dict[key] = value
        return self

    def clone(self):
        return ContextDict(dict(self._context_dict))

    def __str__(self):
        ret = '-' * 20 + '\n'
        for key, value in self._context_dict.items():
            ret += '' + str(key) + ': ' + str(value) + '\n'
        ret += '-' * 20 + '\n'
        return ret

def main():
    ctx = ContextDict()
    ctx['test'] = 'test'
    ctx['test1'] = '{PATH}|{TEST}'
    ctx['test2'] = '{home}|{Test}'
    ctx['test3'] = '{dirname:ZSH}|{test}'
    ctx['test4'] = '{basename:ZSH}|{test}'
    print ctx['test1']
    print ctx['test2']
    print ctx['test3']
    print ctx['test4']

if __name__ == '__main__':
    main()