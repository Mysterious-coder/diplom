import re
import logging
import pymorphy2
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

TEST = False
CREATE_ROOTS = False
MANUAL = True


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
            all_roots = read_json('../dict/all_roots.json')
        complex_part = []
        manual_list = []
        morph_dict = {}
        roots_dict = {}
        for line in file.readlines():
            if start:
                complex_flag = False
                line = line.rstrip('\n')
                line = line.replace("'", '')
                line = line.replace(',', ' ')
                line = line.replace('/-', '~/')
                line = line.replace('ё', 'е')
                arr = line.split(' | ')
                if arr[0][-1] in '.':
                    cur = arr[0].find('.')
                    complex_part.append(arr[0][:cur])
                    continue
                try:
                    arr[1] = arr[1].replace('-', '~/')
                    arr[0] = re.sub(r'[\d]+', '', arr[0])
                    arr[1] = re.match(r"([\S]+)", arr[1]).group(0)
                    arr[1] = re.sub(r'[\d]+', '', arr[1])
                    if arr[1].endswith('ь'):
                        arr[1] = arr[1] + '/'
                    arr[1] = re.split(r'/', arr[1])
                except:
                    logging.exception(f're-----------{arr}')
                    break

                parsed = morph.parse(arr[0])[0]
                pos = parsed.tag.POS
                if pos is None: pos = "ALL"
                try:
                    check = getattr(getattr(Check, pos), "value")
                except:
                    logging.exception(f'getattr----------{pos}')

                # определение морфемы перед '-' (который-нибудь : ый_Е)
                for k, n in enumerate(arr[1]):
                    if n.endswith('~'):
                        arr[1][k] = arr[1][k].replace('~', '')
                        if arr[1][k] in {'ть', 'ся'}:
                            arr[1][k] = arr[1][k] + '_RS'
                        elif arr[1][k] in check:
                            arr[1][k] = arr[1][k] + '_S'
                        elif arr[1][k] in morph_interfixes:
                            arr[1][k] = arr[1][k] + '_I'
                        elif arr[1][k] in morph_wordcreate:
                            arr[1][k] = arr[1][k] + '_WC'
                        elif arr[1][k] in suffs:
                            arr[1][k] = arr[1][k] + '_SF'
                        elif k > 0:
                            arr[1][k] = arr[1][k] + '_E'

                # определение составной приставки _P
                if arr[1][0] in complex_pref.keys() and len(arr[1]) > 2 and arr[1][1] in complex_pref.get(arr[1][0]):
                    arr[1][0] = arr[1][0] + "_P"
                    arr[1][1] = arr[1][1] + "_P"
                elif arr[1][0] in prefs:
                    arr[1][0] = arr[1][0] + "_P"

                # определение приставки в сложных словах с распространенными корнями (авто, био ...) _CP
                if arr[1][0] in complex_part:
                    for k in range(0, (len(arr[1]) + 1 ) // 2):
                        if arr[1][k] in prefs:
                            arr[1][k] = arr[1][k] + "_CP"

                # определение возвратного суффикса _RS
                for k in range(0, len(arr[1])):
                    if '_' not in arr[1][k] and arr[1][k] in {'ть', 'ся'}:
                        arr[1][k] = arr[1][k] + "_RS"

                # определение окончания _E
                if len(arr[1]) > 1:
                    arr[1][-1] = arr[1][-1] + "_E"

                # определение суффикса среди суффиксов конкретной части речи _S
                for k in range(1, len(arr[1])):
                    if '_' not in arr[1][k] and arr[1][k] in check:
                        arr[1][k] = arr[1][k] + "_S"

                # определение морфемы среди словообразующих
                for k in range(1, len(arr[1])):
                    if '_' not in arr[1][k] and arr[1][k] in morph_wordcreate:
                        arr[1][k] = arr[1][k] + "_WC"

                # определение соединительного суффикса сложных слов - _I, а _SI - как I, но все-таки суффикс
                for k in range(len(arr[1]) - 1, 0, -1):
                    if '_' not in arr[1][k] and arr[1][k] in morph_interfixes:
                        if re.search(r'(?:S|WC|E)', arr[1][k + 1]):
                            arr[1][k] = arr[1][k] + "_SI"
                        else:
                            arr[1][k] = arr[1][k] + "_I"
                            complex_flag = True

                # определение суффикса среди всех суффиксов русского языка
                for k in range(1, len(arr[1])-1):
                    if '_' not in arr[1][k] and arr[1][k] in suffs:
                        arr[1][k] = arr[1][k] + "_SF"

                # если каким-то чудом в словаре ь или ъ знаки отделены /
                for k in range(1, len(arr[1])-1):
                    if '_' not in arr[1][k] and arr[1][k] in signs:
                        arr[1][k] = arr[1][k] + "_SIGN"

                while True:
                    if '' in arr[1]:
                        arr[1].remove('')
                    else:
                        break
                count = 0
                # подсчет непомеченных морфем
                for w in arr[1]:
                    if '_' not in w:
                        count += 1

                # определение приставки внутри слова
                if count > 1:
                    for k in range(1, len(arr[1])):
                        if '_' not in arr[1][k] and arr[1][k] in prefs:
                            arr[1][k] = arr[1][k] + "_CP"
                            count -= 1

                # пометили корень, нужно разметить обратно - поиск среди корней, совпадающих с приставками/суффиксами...
                if count == 0:
                    count = check_root(arr[1], count)

                if complex_flag and count < 2:
                    count = check_root(arr[1], count)

                arr.append(count)
                root_list = [i for i in arr[1] if '_' not in i] # список корней
                copy_root_list = set(root_list) # копия списка корней, куда добавляется корень с чередованием

                # добавление корня с чередованием "ы" на "и"
                for idx in range(1, len(arr[1])):
                    if arr[1][idx] in copy_root_list and 'P' in arr[1][idx - 1]:
                        pref_tmp = re.match(r'([\w]+)_', arr[1][idx - 1]).group(1)
                        if change_letter(pref_tmp, arr[1][idx][0]):
                            copy_root_list.add('и' + arr[1][idx][1:])

                # добавление чередующихся корней из соотв. списка
                changed_roots_1 = set()
                for root in copy_root_list:
                    if root in change_roots.keys():
                        tmp = change_roots.get(root)
                        changed_roots_1.add(tmp) if isinstance(tmp, str) else changed_roots_1.union(tmp)

                # добавление чередующихся корней с помощью проверки наиболее частотных чередований последних букв
                changed_roots_2 = set()
                for root in copy_root_list:
                    if root not in not_change_roots:
                        if work_letter_change(letter_change, root[-1]):
                            for group in work_letter_change(letter_change, root[-1]):
                                for letter in group:
                                    root_check = root[:-1] + letter
                                    if root_check in all_roots.get(root_check[0]):
                                        changed_roots_2.add(root_check)
                        if work_letter_change(letter_change, root[-2:]):
                            for group in work_letter_change(letter_change, root[-2:]):
                                for letter in group:
                                    root_check = root[:-2] + letter
                                    if root_check in all_roots.get(root_check[0]):
                                        changed_roots_2.add(root_check)

                copy_root_list = copy_root_list.union(set(changed_roots_1))
                copy_root_list = copy_root_list.union(set(changed_roots_2))
                # список корней с чередованием
                other_roots = list(copy_root_list.difference(root_list))
                # print(arr[0], copy_root_list, root_list)

                # создание морфемного словаря morph_dict
                if morph_dict.get(arr[0]):
                    morph_dict[arr[0]].append([arr[1], root_list, other_roots])
                else:
                    morph_dict[arr[0]] = [arr[1], root_list, other_roots]

                # создание корневых гнезд
                for root in root_list:
                    if CREATE_ROOTS: # создание словаря со всеми корнями all_roots
                        if all_roots.get(root[0]):
                            all_roots[root[0]].add(root)
                        else:
                            all_roots[root[0]] = {root}
                    if roots_dict.get(root):
                        roots_dict[root].append((pos, count, arr[0], arr[1], root_list))
                    else:
                        roots_dict[root] = [[pos, count, arr[0], arr[1], root_list]]

                if MANUAL and other_roots:
                    manual_list.append([arr[0], root_list, other_roots])

            elif line == "START\n":
                start = True

            if TEST:
                if i == 0:
                    break
                else:
                    i -= 1
        if MANUAL:
            with open("../dict/manual.txt", "w+") as file:
                for i in manual_list:
                    file.write(str(i) + '\n')
        if TEST:
            ii = 0
            for key, val in morph_dict.items():
                print(key, val)
                ii += 1
                if ii == 5: break
            print('-' * 50)
            for key, val in roots_dict.items():
                print(key, val)
                ii -= 1
                if ii == 0: break
            return

        if CREATE_ROOTS:
            for letter in all_roots.keys():
                all_roots[letter] = list(all_roots.get(letter))
            write_json("../dict/all_roots.json", all_roots, ensure_ascii=False, indent=2)
        write_json("../dict/morph_dict.json", morph_dict, ensure_ascii=False, indent=2)
        write_json("../dict/roots_dict.json", roots_dict, ensure_ascii=False, indent=2)
        write_json("../dict/complex_part.json", complex_part, ensure_ascii=False, indent=2)


def check_root(arr: typing.List[typing.Any], count: int) -> int:
    """Проверка среди помеченных морфем наличие корня
    :param arr: морфемы
    :param count: кол-во определенных корней"""
    for k in range(0, len(arr)):
        if '_' in arr[k]:
            root_check = arr[k][:arr[k].rfind('_')]
        else:
            root_check = arr[k]
        if root_check in roots:
            arr[k] = root_check
            return count + 1
    for k in range(0, len(arr)):
        if '_' in arr[k]:
            root_check = arr[k][:arr[k].rfind('_')]
        else:
            root_check = arr[k]
        if root_check in roots_as_pref:
            arr[k] = root_check
            return count + 1
    for k in range(0, len(arr)):
        if '_' in arr[k]:
            root_check = arr[k][:arr[k].rfind('_')]
        else:
            root_check = arr[k]
        if root_check in roots_as_suff:
            arr[k] = root_check
            return count + 1
    for k in range(0, len(arr)):
        if '_' in arr[k]:
            root_check = arr[k][:arr[k].rfind('_')]
        else:
            root_check = arr[k]
        if root_check in roots2:
            arr[k] = root_check
            return count + 1


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
