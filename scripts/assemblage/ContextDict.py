#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import os
import re
import abc

class ContextDict(dict):

    RE_FUNC = re.compile(r'{([^:}]+):([^:}]+)}')
    RE_REPLACE = re.compile(r'{([^}]+)}')

    def __init__(self, context_dict=None):
        super(ContextDict, self).__init__()
        if context_dict is None:
            context_dict = {}
        if not isinstance(context_dict, dict):
            raise TypeError('require dictionary but it is ' + str(type(context_dict)))
        # for key, value in context_dict.items():
        #     context_dict[unicode(key)] = unicode(value)
        noext_lambda = lambda path: os.path.basename(path).split(os.path.extsep)[0]
        ext_lambda = lambda path: os.path.basename(path).split(os.path.extsep)[1]
        self._context_dict = {}
        for k, v in context_dict.items():
            if isinstance(v, dict):
                self._context_dict[k.lower()] = ContextDict(v)
            else:
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
        if isinstance(item, str) or isinstance(item, unicode):
            return self.format(item)
        else:
            return item

    def to_dict(self):
        d = {}
        for key in self._context_dict.keys():
            d[key] = self[key]
        return d
        
    def __cmp__(self, other):
        if isinstance(other, ContextDict):
            return self._context_dict.__cmp__(other._context_dict)
        return self._context_dict.__cmp__(other)
        
    def __contains__(self, key):
        return self._context_dict.__contains__(key)
        
    def __delattr__(self, name):
        return self._context_dict.__delattr__(name)

    def __setitem__(self, name, value):
        self.set(name, value)
        
    def __getitem__(self, name):
        return self.get(name)

    def __delitem__(self, name):
        self._context_dict.__delitem__(name)
        
    def __eq__(self, other):
        if isinstance(other, ContextDict):
            return self._context_dict.__eq__(other._context_dict)
        return self._context_dict.__eq__(other)

    def __hash__(self):
        return self._context_dict.__hash__()
        
    def __iter__(self):
        return iter(self.to_dict())

    def __len__(self):
        return self._context_dict.__len__()

    def clear(self):
        self._context_dict.clear()

    def has_key(self, key):
        return self._context_dict.has_key(key)

    def keys(self):
        return self._context_dict.keys()

    def pop(self, *args, **kvargs):
        item = self._context_dict.pop(*args, **kvargs)
        if isinstance(item, type(lambda: None)):
            item = item()
        if isinstance(item, str) or isinstance(item, unicode):
            return self.format(item)
        else:
            return item

    def fromkeys(self, *args, **kvargs):
        return ContextDict(self._context_dict.fromkeys(*args, **kvargs))

    def items(self):
        items = []
        for key in self._context_dict.keys():
            items.append((key, self.get(key), ))
        return items

    def iteritems(self, *args, **kvargs):
        for key in self._context_dict.keys():
            yield key, self.get(key)

    def iterkeys(self, *args, **kvargs):
        for key in self._context_dict.keys():
            yield key

    def popitem(self):
        (key, item) = self._context_dict.popitem()
        if isinstance(item, type(lambda: None)):
            item = item()
        if isinstance(item, str) or isinstance(item, unicode):
            return key, self.format(item)
        else:
            return key, item

    def setdefault(self, *args, **kvargs):
        item = self._context_dict.setdefault(*args, **kvargs)
        if isinstance(item, type(lambda: None)):
            item = item()
        if isinstance(item, str) or isinstance(item, unicode):
            return self.format(item)
        else:
            return item

    def update(self, d):
        for key, value in d.items():
            key = key.lower()
            self._context_dict[key] = value

    def values(self):
        items = self._context_dict.values()
        ret_items = []
        for item in items:
            if isinstance(item, type(lambda: None)):
                ret_items.append(item())
            else:
                if isinstance(item, str) or isinstance(item, unicode):
                    ret_items.append(self.format(item))
                else:
                    ret_items.append(item)
        return ret_items

    def viewitems(self, *args, **kvargs):
        return set(self.items())

    def viewkeys(self, *args, **kvargs):
        return set(self.keys())

    def viewvalues(self, *args, **kvargs):
        return set(self.values())

    def register_func(self, name, func):
        name = name.lower()
        if not isinstance(func, type(lambda _: None)):
            raise TypeError('require function or lambda but it is ' + str(type(func)))
        self._context_func_dict[name] = func

    def get(self, name, default=None):
        name = name.lower()
        if default is None:
            item = self._context_dict.get(name)
        else:
            item = self._context_dict.get(name, default)
        if isinstance(item, str) or isinstance(item, unicode):
            return self.format(item)
        else:
            return item
    
    def getOrDefault(self, name, default=None):
        name = name.lower()
        if default is None:
            item = self._context_dict.get(name)
        else:
            item = self._context_dict.get(name, default)
            self.set(name, default)
        if isinstance(item, str) or isinstance(item, unicode):
            return self.format(item)
        else:
            return item

    def set(self, name, value):
        name = name.lower()
        if isinstance(value, dict):
            self._context_dict[name] = ContextDict(value)
        elif isinstance(value, type(lambda _: None)):
            self.register_func(name, value)
        else:
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

    def copy(self):
        return self.clone()

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
    print isinstance(ctx, dict)
    ctx['test'] = 'test'
    ctx['test1'] = '{PATH}|{TEST}'
    ctx['test2'] = '{home}|{Test}'
    ctx['test3'] = '{dirname:ZSH}|{test}'
    ctx['test4'] = '{basename:ZSH}|{test}'
    print ctx['test1']
    print ctx['test2']
    print ctx['test3']
    print ctx['test4']
    print dict(ctx)

if __name__ == '__main__':
    main()