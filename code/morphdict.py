import re
import logging
import json
import pymorphy2
import typing
from enum import Enum
from prefixes import prefs, complex_pref
from roots import *
from suffixes import *
from main import vowels, prefixes_1

suffs = [set(i) for i in (suff_advb, suff_adj, suff_noun, suff_name, suff_verb, morph_wordcreate, morph_wordchange)]
a = set()
for i in suffs:
    a = a | i
suffs = a

signs = {'ъ', 'ь'}

TEST = True
CREATE_ROOTS = False

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

aplhabet = ('а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 'о', 'п',
            'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ы', 'э', 'ю', 'я')

def parse(filename: str) -> None:
    with open(filename, 'r') as file:
        start = False
        if TEST:
            i = 500
        if CREATE_ROOTS:
            all_roots = dict.fromkeys(aplhabet, set())
        else:
            all_roots_dict = read_json('../dict/all_roots.json')
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
                    arr[0] = re.sub(r'[\d]+', '', arr[0])
                    arr[1] = re.match(r"([\S]+)", arr[1]).group(0)
                    arr[1] = re.sub(r'[\d]+', '', arr[1])
                    if arr[1].endswith('ь'):
                        arr[1] = arr[1] + '/'
                    arr[1] = re.split(r'(?:/|-)', arr[1])
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


                if arr[1][0] in complex_pref.keys() and len(arr[1]) > 2 and arr[1][1] in complex_pref.get(arr[1][0]):
                    arr[1][0] = arr[1][0] + "_P"
                    arr[1][1] = arr[1][1] + "_P"
                elif arr[1][0] in prefs:
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

                for k in range(len(arr[1]) - 1, 0, -1):
                    if '_' not in arr[1][k] and arr[1][k] in morph_interfixes:
                        if re.search(r'(?:S|WC)', arr[1][k + 1]):
                            arr[1][k] = arr[1][k] + "_SI"
                        else:
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
                    check_root(arr[1], count)

                if complex_flag and count < 2:
                    check_root(arr[1], count)

                arr.append(count)
                root_list = [i for i in arr[1] if '_' not in i] # список корней
                copy_root_list = root_list[:] # копия списка корней, куда добавляется корень с чередованием

                # добавление корня с чередованием "ы" на "и"
                for idx in range(1, len(arr[1])):
                    if arr[1][idx] in copy_root_list and 'P' in arr[1][idx - 1]:
                        pref_tmp = re.match(r'([\w]+)_', arr[1][idx - 1]).group(1)
                        if change_letter(pref_tmp, arr[1][idx][0]):
                            copy_root_list.append('и' + arr[1][idx][1:])
                copy_root_list = list(set(copy_root_list))

                changed_roots_1 = []
                for root in copy_root_list:
                    if root in change_roots.keys():
                        tmp = change_roots.get(root)
                        changed_roots_1.append(tmp) if isinstance(tmp, str) else changed_roots_1.extend(tmp)
                # copy_root_list.extend(changed_roots_1)
                # copy_root_list = list(set(copy_root_list))

                changed_roots_2 = []
                for root in copy_root_list:
                    if work_letter_change(letter_change, root[-1]):
                        for group in work_letter_change(letter_change, root[-1]):
                            for letter in group:
                                root_check = root[:-1] + letter
                                if root_check in all_roots_dict.get(root_check[0]):
                                    changed_roots_2.append(root_check)
                    if work_letter_change(letter_change, root[-2:]):
                        for group in work_letter_change(letter_change, root[-2:]):
                            for letter in group:
                                root_check = root[:-2] + letter
                                if root_check in all_roots_dict.get(root_check[0]):
                                    changed_roots_2.append(root_check)

                copy_root_list.extend(changed_roots_1)
                copy_root_list.extend(changed_roots_2)
                copy_root_list = list(set(copy_root_list))
                print(arr[0], copy_root_list)

                if morph_dict.get(arr[0]):
                    morph_dict[arr[0]].append([arr[1], root_list])
                else:
                    morph_dict[arr[0]] = [[arr[1], root_list]]

                for root in root_list:
                    if CREATE_ROOTS:
                        if all_roots.get(root[0]):
                            all_roots[root[0]].add(root)
                        else:
                            all_roots[root[0]] = {root}
                    if roots_dict.get(root):
                        roots_dict[root].append((pos, count, arr[0], arr[1], root_list))
                    else:
                        roots_dict[root] = [(pos, count, arr[0], arr[1], root_list)]

            elif line == "START\n":
                start = True

            if TEST:
                if i == 0:
                    break
                else:
                    i -= 1
        if TEST:
            return
        if CREATE_ROOTS:
            for letter in all_roots.keys():
                all_roots[letter] = list(all_roots.get(letter))
            write_json("../dict/all_roots.json", all_roots, ensure_ascii=False, indent=2)
        write_json("../dict/morph_dict.json", morph_dict, ensure_ascii=False, indent=2)
        write_json("../dict/roots_dict.json", roots_dict, ensure_ascii=False, indent=2)
        write_json("../dict/complex_part.json", complex_part, ensure_ascii=False, indent=2)


def check_root(arr: typing.List[typing.Any], count: int) -> None:
    """Проверка среди помеченных морфем наличие корня
    :param arr: морфемы
    :param count: кол-во определенных корней"""
    for k in range(0, len(arr)):
        root_check = arr[k][:arr[k].rfind('_')]
        if root_check in roots:
            arr[k] = root_check
            count += 1
            return
    for k in range(0, len(arr)):
        root_check = arr[k][:arr[k].rfind('_')]
        if root_check in roots_as_pref:
            arr[k] = root_check
            count += 1
            return
    for k in range(0, len(arr)):
        root_check = arr[k][:arr[k].rfind('_')]
        if root_check in roots_as_suff:
            arr[k] = root_check
            count += 1
            return
    for k in range(0, len(arr)):
        root_check = arr[k][:arr[k].rfind('_')]
        if root_check in roots2:
            arr[k] = root_check
            count += 1
            return


def read_json(path: str, **kwargs) -> str:
    """Чтение из json файла в словарь
    :param path:        путь до файла для чтения"""

    with open(path, "r") as scheme:
        data = json.load(scheme, **kwargs)
    return data


def write_json(path: str, json_text, **kwargs) -> None:
    """Запись json_text в файл по пути path
    :param path:        путь к файлу
    :param json_text:   записываемый словарь"""

    with open(path, "w+") as file:
        json.dump(json_text, file, **kwargs)


def display(display_dict: typing.Dict[str, typing.Any]) -> None:
    txt = json.dumps(display_dict, ensure_ascii=False, indent=2)
    print(txt)


def change_letter(pref: str, letter: str) -> bool:
    """Предикат  - для смены <и> на <ы>"""

    return letter == 'ы' and pref not in prefixes_1 and pref[-1] not in vowels


morph = pymorphy2.MorphAnalyzer()

if TEST:
    parse("../dict/test.txt")
else:
    parse("../dict/MorphDictTikhonov.txt")
