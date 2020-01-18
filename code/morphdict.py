import re
import pymorphy2
from enum import Enum
from prefixes import prefs
from suffixes import *
import logging
import json

suffs = [set(i) for i in (suff_advb, suff_adj, suff_noun, suff_name, suff_verb, morph_wordcreate, morph_wordchange)]
a = set()
for i in suffs:
    a = a | i
suffs = a

roots = {'чин', 'мен', 'нит', 'ым', 'ус', 'ух', 'ос', 'ост', 'бес', 'де', 'воз', 'уч',
         'г', 'шн', 'мя', 'ки', 'яр', 'й', 'ман', 'и', 'ур', 'он', 'ши', 'тур', 'ну', 'лин', 'ем',
         'меж', 'ше', 'ал', 'ах', 'ил', 'ох', 'ор', 'очн', 'сн', 'тор', 'ул', 'уш', 'вор', 'ком', 'лиц', 'у',
         'ком'}
roots_as_pref = {'во', 'вне', 'ба', 'бес', 'де', 'вы', 'вс', 'до', 'ин', 'за', 'микро', 'кило', 'макро', 'контр',
                 'между', 'мимо', 'против', 'низ', 'пан'}
roots_as_suff = {'ка', 'вш', 'ть', 'ку', 'им', 'ук', 'ловк', 'ч', 'к', 'об', 'па', 'чь', 'куда', 'ник'}

roots2 = {'под', 'кто', 'по', 'пост', 'пре', 'д', 'ш', 'раз', 'рас', 'роз', 'рос', 'со'}

bad_words = {('антидот', 'дот')}

signs = {'ъ', 'ь'}

class Check(Enum):
    ALL = suffs
    NOUN = suff_noun
    ADVB = suff_advb
    ADJ = suff_adj
    ADJF = suff_adj
    ADJS = suff_adj
    COMP = suff_adj
    VERB = suff_verb
    INFN = suff_verb
    PRTF = suff_prt
    PRTS = suff_prt
    GRND = suff_grnd
    NUMR = suff_numr
    NPRO = suff_name
    PRED = ""
    PREP = ""
    CONJ = ""
    PRCL = ""
    INTJ = ""


def parse(filename):
    with open(filename, 'r') as file:
        start = False
        complex_part = []
        morph_dict = {}
        roots_dict = {}
        for line in file.readlines():
            if start:
                complex_flag = False
                line = line.rstrip('\n')
                line = line.replace("'", '')
                line = line.replace(',', ' ')
                line = line.replace('/-', '/')
                line = line.replace('ё', 'е')
                arr = line.split(' | ')
                if arr[0][-1] in '.':
                    cur = arr[0].find('.')
                    complex_part.append(arr[0][:cur])
                    continue
                try:
                    arr[1] = re.match(r"([\S]+)", arr[1]).group(0)
                    arr[1] = re.sub(r'[\d]+', '', arr[1])
                    if arr[1].endswith('ь'):
                        arr[1] = arr[1] + '/'
                    arr[1] = re.split(r'[?:/|-]', arr[1])
                except:
                    logging.exception(f're-----------{arr}')
                    break
                parsed = morph.parse(arr[0])[0]
                pos = parsed.tag.POS
                if pos is None: pos = "ALL"
                try:
                    check = getattr(getattr(Check, pos),"value")
                except:
                    logging.exception(f'getattr----------{pos}')

                if arr[1][0] in prefs:
                    arr[1][0] = arr[1][0] + "_P"

                if arr[1][0] in complex_part:
                    for k in range(0, (len(arr[1]) + 1 ) // 2):
                        if arr[1][k] in prefs:
                            arr[1][k] = arr[1][k] + "_CP"

                for k in range(0, len(arr[1])):
                    if '_' not in arr[1][k] and arr[1][k] in {'ть', 'ся'}:
                        arr[1][k] = arr[1][k] + "_RS"

                if '-' not in arr[1][-1] and len(arr[1]) > 1:
                    arr[1][-1] = arr[1][-1] + "_E"

                for k in range(1, len(arr[1])):
                    if '_' not in arr[1][k] and arr[1][k] in check:
                        arr[1][k] = arr[1][k] + "_S"

                for k in range(1, len(arr[1])):
                    if '_' not in arr[1][k] and arr[1][k] in morph_interfixes:
                        arr[1][k] = arr[1][k] + "_I"
                        complex_flag = True

                for k in range(1, len(arr[1])):
                    if '_' not in arr[1][k] and arr[1][k] in morph_wordcreate:
                        arr[1][k] = arr[1][k] + "_WC"

                for k in range(1, len(arr[1])-1):
                    if '_' not in arr[1][k] and arr[1][k] in suffs:
                        arr[1][k] = arr[1][k] + "_SF"

                for k in range(1, len(arr[1])-1):
                    if '_' not in arr[1][k] and arr[1][k] in signs:
                        arr[1][k] = arr[1][k] + "_SIGN"

                while True:
                    if '' in arr[1]:
                        arr[1].remove('')
                    else:
                        break

                count = 0
                for w in arr[1]:
                    if '_' not in w:
                        count += 1

                if count > 1:
                    for k in range(1, len(arr[1])):
                        if '_' not in arr[1][k] and arr[1][k] in prefs:
                            arr[1][k] = arr[1][k] + "_CP"
                            count -= 1

                if count == 0:
                    check_root(arr, count)

                if complex_flag and count < 2:
                    check_root(arr, count)

                arr.append(count)
                prt_list = [i for i in arr[1] if '_' not in i]
                morph_dict[arr[0]] = (arr[1], prt_list)

                for root in prt_list:
                    if roots_dict.get(root):
                        roots_dict[root].append((pos, count, arr[0], arr[1]))
                    else:
                        roots_dict[root] = [(pos, count, arr[0], arr[1])]

            elif line == "START\n":
                start = True

            # i -= 1
            # if i == 0:
            #     print(morph_dict)
            #     print(roots_dict)
            #     print(complex_part)
            #     break
        write_json("../dict/morph_dict.json", morph_dict, ensure_ascii=False, indent=2)
        write_json("../dict/roots_dict.json", roots_dict, ensure_ascii=False, indent=2)
        write_json("../dict/complex_part.json", complex_part, ensure_ascii=False, indent=2)


def check_root(arr, count):
    for k in range(0, len(arr[1])):
        root_check = arr[1][k][:arr[1][k].rfind('_')]
        if root_check in roots:
            arr[1][k] = root_check
            count += 1
            break
    for k in range(0, len(arr[1])):
        root_check = arr[1][k][:arr[1][k].rfind('_')]
        if root_check in roots_as_pref:
            arr[1][k] = root_check
            count += 1
            break
    for k in range(0, len(arr[1])):
        root_check = arr[1][k][:arr[1][k].rfind('_')]
        if root_check in roots_as_suff:
            arr[1][k] = root_check
            count += 1
            break
    for k in range(0, len(arr[1])):
        root_check = arr[1][k][:arr[1][k].rfind('_')]
        if root_check in roots2:
            arr[1][k] = root_check
            count += 1
            break

def read_json(path: str, **kwargs):
    """Чтение из json файла в словарь
    :param path:        путь до файла для чтения"""

    with open(path, "r") as scheme:
        data = json.load(scheme, **kwargs)
    return data

def write_json(path: str, json_text, **kwargs):
    """Запись json_text в файл по пути path
    :param path:        путь к файлу
    :param json_text:   записываемый словарь"""

    with open(path, "w+") as file:
        json.dump(json_text, file, **kwargs)

morph = pymorphy2.MorphAnalyzer()
parse("../dict/MorphDictTikhonov.txt")