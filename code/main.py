import pymorphy2
import logging
import warnings
import re
import itertools
import json
import os
from enum import Enum
from meanings import *
from morphdict import parse
from constants import vowels, vowels_1, type_dict, aliases, all_poses, only_suf_poses
from code.ml import get_morph_segmentation_of_word

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

CONSIDER_POS = True

class Morphems(Enum):
    ALL = ""
    NOUN = (noun_pref, noun_suf, noun_pref_suf)  # сущ
    ADVB = (advb_pref, advb_suf, advb_pref_suf)  # наречие
    ADJF = (adj_pref, adj_suf, adj_pref_suf)  # полное/краткое/сравнительное прил
    ADJS = (adj_pref, adj_suf, adj_pref_suf)
    COMP = (adj_pref, adj_suf, adj_pref_suf)
    VERB = (verb_pref, verb_suf, verb_pref_suf)  # глагол, инфинитив
    INFN = (verb_pref, verb_suf, verb_pref_suf)
    PRTF = (prt_pref, prt_suf, prt_pref_suf)  # причастие
    PRTS = (prt_pref, prt_suf, prt_pref_suf)
    GRND = (grnd_pref, grnd_suf, grnd_pref_suf)  # деепричастие
    NUMR = ("", numr_suf)  # числительное
    NPRO = (npro_pref, npro_suf, npro_pref_suf)  # местоимение
    INTJ = ("", intj_suf)  # междометие
    PRED = ""
    PREP = ""
    CONJ = ""
    PRCL = ""


def read_json(path: str, **kwargs):
    """Чтение из json файла в словарь
    :param path:        путь до файла для чтения"""

    with open(path, "r") as scheme:
        data = json.load(scheme, **kwargs)
    return data


def hard_sign(pref, letter):
    """Предикат - первая буква слова <еёюя> и последняя буква приставки - согласная"""
    return letter in vowels_1 and pref[-1] not in vowels


def check_in_dict(word):
    """Проверка слова в словаре"""
    return morph.word_is_known(word)


# a = morph.iter_known_word_parses(word[:-3])
# for i in a:
#     print(i)


# Глагол:  Время(past, pres, futr), Лицо(1per, 2 per, 3 per), Вид (perf, impf)
#          Число(sing, plur ...), Переход (tran, intr)
def flection(grammems, parsed):
    """Склонение слова"""
    result = None
    grammems = str(grammems)
    # print(grammems)
    grammems = re.sub('[AGQSPMa-z-]+? ', '', grammems)
    grammems = re.sub('(impf|perf|tran|intr|pres|indc|futr)', "", grammems)
    grammems = re.sub(r',{2,}', ",", grammems)
    # print(grammems)
    grammems = grammems.rstrip(',')
    grammems = set(grammems.split(','))

    try:
        result = parsed.inflect(grammems).word
    except:
        logging.info(f"Cannot to create word from {parsed.word} with {grammems}grammems")
    return result


def transform_word(word, stat, pos, grammems=None, get_print=None):
    """Склонение проверочного слова и проверка результата в словаре"""
    parsed = morph.parse(word)[0]
    if get_print:
        print("source word_transform: ", word, f"--{parsed.tag.POS, pos}", end=' | ')
    # result_word = flection(grammems, parsed)          if tags.POS in pos:
    result_word = word
    good_word = False

    if result_word is None:
        stat["bad"] += 1
        if get_print:
            print(' None')
    elif parsed.tag.POS not in pos:
        if get_print:
            print("another POS: ", result_word)
        stat["bad"] += 1
    elif not check_in_dict(result_word):
        if get_print:
            print("not in corpora: ", result_word)
        stat["bad"] += 1
        # stat["good"] += 1
        good_word = True
    else:
        good_word = True
        if get_print:
            print("good result: ", result_word)
        stat["good"] += 1

    return good_word, result_word


# Часть_Речи, Кол-во_Корней, Слово, [морфемы]
def create_final_dict(tmp_dict, vocab, count, pos, exp, stat, tags, pref=None, suff=None):
    """Создание словаря МОРФЕМА: НОВОЕ СЛОВО
    :param tmp_dict: заполняемый словарь
    :param vocab: слова с совпадающими корнями
    :param count: кол-во корней
    :param pos: часть речи выходного слова
    :param exp: p - режим префиксный, передача суффиксов слова
                s - режим суффиксный, передача префиксов слова
                ps - префиксно-суффиксный
    :param stat: статистика bad/good
    :param tags: теги слова, поданного на вход
    :param pref: префиксы слова
    :param suff: суффиксы слова"""

    def app_morphem(morphems, exp=exp):
        inapp_morphem = False
        if exp == 'p':  # режим префиксный - значит суффиксы должны сохраняться
            eq_morphem = [morphem[:morphem.find('_')] for morphem in morphems if
                          re.search(type_dict.get('s'), morphem)]  # суффиксы проверяемого в словаре слова
            for i in eq_morphem:
                if i not in suff:
                    inapp_morphem = True
        elif exp == 's':  # режим суффиксный - значит префиксы должны сохраняться
            eq_morphem = [morphem[:morphem.find('_')] for morphem in morphems if
                          re.search(type_dict.get('p'), morphem)]  # префиксы проверяемого в словаре слова
            for i in eq_morphem:
                if i not in pref:
                    inapp_morphem = True
        return inapp_morphem

    re_expr = type_dict.get(exp)

    if exp != 'ps':
        for key in tmp_dict.keys():
            set_of_words = set()
            if not isinstance(key, tuple):
                for rec in vocab:
                    if rec[1] == count and rec[0] in pos and not app_morphem(rec[3]):
                        check = [morphem[:morphem.find('_')] for morphem in rec[3] if re.search(re_expr, morphem)]
                        if key in check:
                            transformed_word = transform_word(rec[2], stat, pos, tags)
                            if transformed_word[0]:
                                set_of_words.add((transformed_word[1], rec[0]))

            else:
                for rec in vocab:
                    if rec[1] == count and rec[0] in pos and not app_morphem(rec[3]):
                        check = [morphem[:morphem.find('_')] for morphem in rec[3] if re.search(re_expr, morphem)]
                        flag = True
                        for subkey in key:
                            if subkey not in check:
                                flag = False
                                break
                        if flag:  # and len(check) == len(key):
                            transformed_word = transform_word(rec[2], stat, pos, tags)
                            if transformed_word[0]:
                                set_of_words.add((transformed_word[1], rec[0]))

            if set_of_words:
                tmp_dict[key] = set_of_words
    else:
        for key in tmp_dict.keys():
            set_of_words = set()
            combinations = itertools.product(key[0], key[1])

            for comb in combinations:
                if isinstance(comb[0], str) and isinstance(comb[1], str):
                    for rec in vocab:
                        if rec[1] == count and rec[0] in pos:
                            check_prefs = [morphem[:morphem.find('_')] for morphem in rec[3] if
                                           re.search(type_dict.get('p'), morphem)]
                            check_suffs = [morphem[:morphem.find('_')] for morphem in rec[3] if
                                           re.search(type_dict.get('s'), morphem)]
                            if comb[0] in check_prefs and comb[1] in check_suffs:
                                transformed_word = transform_word(rec[2], stat, pos, tags)
                                if transformed_word[0]:
                                    set_of_words.add((transformed_word[1], rec[0]))

                elif isinstance(comb[0], str):
                    for rec in vocab:
                        if rec[1] == count and rec[0] in pos:
                            check_prefs = [morphem[:morphem.find('_')] for morphem in rec[3] if
                                           re.search(type_dict.get('p'), morphem)]
                            check_suffs = [morphem[:morphem.find('_')] for morphem in rec[3] if
                                           re.search(type_dict.get('s'), morphem)]

                            flag_s = all(subkey in check_suffs for subkey in comb[1])

                            if flag_s and comb[0] in check_prefs:
                                transformed_word = transform_word(rec[2], stat, pos, tags)
                                if transformed_word[0]:
                                    set_of_words.add((transformed_word[1], rec[0]))

                elif isinstance(comb[1], str):
                    for rec in vocab:
                        if rec[1] == count and rec[0] in pos:
                            check_prefs = [morphem[:morphem.find('_')] for morphem in rec[3] if
                                           re.search(type_dict.get('p'), morphem)]
                            check_suffs = [morphem[:morphem.find('_')] for morphem in rec[3] if
                                           re.search(type_dict.get('s'), morphem)]

                            flag_p = all(subkey in check_prefs for subkey in comb[0])

                            if flag_p and comb[1] in check_suffs:
                                transformed_word = transform_word(rec[2], stat, pos, tags)
                                if transformed_word[0]:
                                    set_of_words.add((transformed_word[1], rec[0]))
                else:
                    for rec in vocab:
                        if rec[1] == count and rec[0] in pos:
                            check_prefs = [morphem[:morphem.find('_')] for morphem in rec[3] if
                                           re.search(type_dict.get('p'), morphem)]
                            check_suffs = [morphem[:morphem.find('_')] for morphem in rec[3] if
                                           re.search(type_dict.get('s'), morphem)]

                            flag_p = all(subkey in check_prefs for subkey in comb[0])
                            flag_s = all(subkey in check_suffs for subkey in comb[1])

                            if flag_s and flag_p:
                                transformed_word = transform_word(rec[2], stat, pos, tags)
                                if transformed_word[0]:
                                    set_of_words.add((transformed_word[1], rec[0]))
                if set_of_words:
                    tmp_dict[key] = set_of_words


def create_relations(final_dict, mean_dict, tagpos, ps=None, get_print=None):
    """Создание словаря ТИП_СВЯЗИ: СЛОВА"""

    new_relations = dict.fromkeys(mean_dict.keys(), [])
    remove_keys = []
    for key in new_relations.keys():
        arr = set()
        # if isinstance(mean_dict[key][1], str):
        if ps is None:
            for morphem in mean_dict[key][1]:
                val = final_dict.get(morphem)
                if val:
                    arr.update(val)
        else:
            val = final_dict.get(tuple(mean_dict[key][1:]))
            if val:
                arr.update(val)
        if any(arr):
            new_relations[key] = arr
        else:
            remove_keys.append(key)

    for key in remove_keys:
        new_relations.pop(key)

    if not CONSIDER_POS:
        for key in new_relations.keys():
            new_relations[key] = [mean_dict.get(key)[0], new_relations[key]]
    else:
        remove_keys = []
        if isinstance(tagpos, str):
            tagpos = [tagpos]

        for key in new_relations.keys():
            brackets = re.match(r'\[([?:\w|+]*)\]', mean_dict.get(key)[0]).group(1)
            if brackets == '':
                new_relations[key] = [mean_dict.get(key)[0], new_relations[key]]
            else:
                flag = any(it in brackets for it in tagpos)
                flag_common = any(it in brackets for it in all_poses + only_suf_poses)

                if flag and '+' in brackets:
                    brackets = brackets.split('+')
                    a = {k for k in new_relations[key] if any(str(it) in k for it in tagpos)}
                    new_relations[key] = [mean_dict.get(key)[0], a]
                elif flag:
                    a = {k for k in new_relations[key] if brackets in tagpos}
                    new_relations[key] = [mean_dict.get(key)[0], a]
                elif not flag_common:
                    new_relations[key] = [mean_dict.get(key)[0], new_relations[key]]
                else:
                    if get_print:
                        print(f"LOOK {mean_dict.get(key)[0], new_relations[key]}")
                    remove_keys.append(key)
        for key in remove_keys:
            new_relations.pop(key)

    return new_relations


def predict_pos(pos_check, pos_word):
    """Предикат - совпадение или принадлежность к одному семейству частей речи"""
    flag = False
    if aliases.get(pos_check) is not None:
        flag = pos_word in aliases.get(pos_check)
    return pos_check == pos_word or flag

class Ontology:
    def __init__(self, dict, max_size=None):
        info = {}
        self.size = 0
        self.word_objects = {}
        for word, _ in morph_dict.items():
            parsed = morph.parse(word)
            variation = parsed[0]
            instance = Word(variation, roots_dict)
            info['pref'] = instance.new_words_pref
            info['suff'] = instance.new_words_suf
            info['prefsuff'] = instance.new_words_pref_suf
            wb = WordBase(word, info)
            # print('---------------------word')
            # wb.print_childs()
            self.word_objects[word] = wb
            self.size += 1
            if max_size and self.size >= max_size:
                break
    def get_size(self):
        return self.size

    def get_objects(self):
        return self.word_objects


class WordBase:
    """word - родитель
    childs - слова-потомки
    childs_{pos} - объекты-потомки по частям речи"""

    def __init__(self, word, info):
        self.word = word
        self.childs = []
        self.childs_noun = []
        self.childs_adj = []
        self.childs_verb = []
        self.childs_advb = []
        self.childs_npro = []
        self.childs_num = []
        self.childs_intj = []
        self.childs_prt = []
        self.childs_grnd = []

        for name, pos_class in names.items():
            pos = pos_class(info)
            self.add_child(name.lower(), pos)
            self.childs.extend(pos.words)

    def add_child(self, type_child, child):
        getattr(self, f'childs_{type_child}').append(child)

    def print_childs(self):
        for child in self.childs:
            print(child)

    def get_childs(self, type_child=None):
        return getattr(self, f'childs_{type_child}') if type_child else self.childs


class Pref:
    def __init__(self, info, pos):
        self.pairs = []
        self.words = set()
        info = info.get('pref')
        for i in info:
            for pair in i[1]:
                if predict_pos(pair[-1], pos):
                    self.pairs.append((i[0], pair[0]))
                    self.words.add(pair[0])

    def get_pairs(self):
        return self.pairs

    def get_words(self):
        return  self.words


class Suff:
    def __init__(self, info, pos):
        self.pairs = []
        self.words = set()
        info = info.get('suff')
        for i in info:
            for pair in i[1]:
                if predict_pos(pair[-1], pos):
                    self.pairs.append((i[0], pair[0]))
                    self.words.add(pair[0])


class PrefSuff:
    def __init__(self, info, pos):
        self.pairs = []
        self.words = set()
        info = info.get('prefsuff')
        for i in info:
            for pair in i[1]:
                if predict_pos(pair[-1], pos):
                    self.pairs.append((i[0], pair[0]))
                    self.words.add(pair[0])


class Noun:
    def __init__(self, info):
        self.words = set()
        self.childs_link = []

        for link_class in links:
            link = link_class(info, 'NOUN')
            self.words = self.words.union(link.words)
            self.childs_link.append(link)


class Adjf:
    def __init__(self, info):
        self.words = set()
        self.childs_link = []
        for link_class in links:
            link = link_class(info, 'ADJF')
            self.words = self.words.union(link.words)
            self.childs_link.append(link)


class Verb:
    def __init__(self, info):
        self.words = set()
        self.childs_link = []
        for link_class in links:
            link = link_class(info, 'VERB')
            self.words = self.words.union(link.words)
            self.childs_link.append(link)


class Advb:
    def __init__(self, info):
        self.words = set()
        self.childs_link = []
        for link_class in links:
            link = link_class(info, 'ADVB')
            self.words = self.words.union(link.words)
            self.childs_link.append(link)


class Npro:
    def __init__(self, info):
        self.words = set()
        self.childs_link = []
        for link_class in links:
            link = link_class(info, 'NPRO')
            self.words = self.words.union(link.words)
            self.childs_link.append(link)


class Numr:
    def __init__(self, info):
        self.words = set()
        self.childs_link = []
        for link_class in links:
            link = link_class(info, 'NUMR')
            self.words = self.words.union(link.words)
            self.childs_link.append(link)


class Intj:
    def __init__(self, info):
        self.words = set()
        self.childs_link = []
        for link_class in links:
            link = link_class(info, 'INTJ')
            self.words = self.words.union(link.words)
            self.childs_link.append(link)


class Prt:
  def __init__(self, info):
        self.words = set()
        self.childs_link = []
        for link_class in links:
            link = link_class(info, 'PRT')
            self.words = self.words.union(link.words)
            self.childs_link.append(link)


class Grnd:
    def __init__(self, info):
        self.words = set()
        self.childs_link = []
        for link_class in links:
            link = link_class(info, 'GRND')
            self.words = self.words.union(link.words)
            self.childs_link.append(link)


names = {'Noun':Noun, 'Adj':Adjf,  'Verb':Verb,  'Advb':Advb,  'Npro':Npro,  'Num':Numr,  'Intj':Intj,  'Prt':Prt,  'Grnd': Grnd}
links = [Pref, Suff, PrefSuff]


class Word:
    # word = None
    # tags = None
    # new_words = []

    def __init__(self, variation, roots_dict, one_word=None, ow_morph_dict=None):
        self.word = variation.word if not one_word else one_word
        self.normal = variation.normal_form if not one_word else one_word
        self.parsed = morph_dict.get(self.normal) if not one_word else ow_morph_dict.get(self.normal)
        # print(self.parsed)
        self.roots = self.parsed[1]
        self.other_roots = self.parsed[2]
        self.roots_count = len(self.roots)
        self.vocab = []
        self.tags = variation.tag

        for root in self.roots:
            a = [r for r in roots_dict.get(root) if r[1] == self.roots_count and set(r[4]) == set(self.roots)]
            self.vocab.extend(a)
        for root in self.other_roots:  # возможна некорректная выборка из-за условия
            a = [r for r in roots_dict.get(root) if r[1] == self.roots_count and
                 set(r[4]).issubset(set(self.other_roots).union(set(self.roots)))]
            self.vocab.extend(a)

        self.word_pref = []  # префиксы слова
        self.word_suff = []  # суффиксы слова
        for i in self.parsed[0]:
            if re.search(type_dict.get('p'), i):
                self.word_pref.append(i[:i.find('_')])
            elif re.search(type_dict.get('s'), i):
                self.word_suff.append(i[:i.find('_')])

        self.stat = {"good": 0,
                     "bad": 0}
        self.new_words_pref = []
        self.new_words_suf = []
        self.new_words_pref_suf = []

        # self.new_words_pref.extend(self.pref_relation('ADVB', aliases.get('ADVB')).values())
        # self.new_words_suf.extend(self.suf_relation('ADVB', aliases.get('ADVB')).values())
        # self.new_words_pref_suf.extend(self.pref_suf_relation('ADVB', aliases.get('ADVB')).values())

        for pos in all_poses:
            self.new_words_pref.extend(self.pref_relation(pos, aliases.get(pos)).values())
            self.new_words_suf.extend(self.suf_relation(pos, aliases.get(pos)).values())
            self.new_words_pref_suf.extend(self.pref_suf_relation(pos, aliases.get(pos)).values())
        for pos in only_suf_poses:
            self.new_words_suf.extend(self.suf_relation(pos, aliases.get(pos)).values())

    def pref_relation(self, pos, alias=None):
        """Создание префиксальной связи"""
        prefs = set()
        meanings_dict = getattr(getattr(Morphems, pos), "value")[0]

        for relation_value in meanings_dict.values():
            prefs.update(relation_value[1])

        for i in prefs:
            if isinstance(i, str) and hard_sign(i, self.normal[0]):
                prefs.remove(i)
                prefs.add(i + 'ъ')

        tmp = dict.fromkeys(prefs, [])
        remove_keys = []

        for key in tmp.keys():
            tmp_key = key
            if isinstance(key, tuple):
                tmp_key = ''.join(key)
            if re.match(f'{tmp_key}', self.normal):  # повторение приставки в начале слова
                remove_keys.append(key)
        for key in remove_keys:
            tmp.pop(key)
        # a = json.dumps(self.vocab, ensure_ascii=False, indent=2)
        # print(a)
        # print(self.word_suff, self.word_pref)
        create_final_dict(tmp, self.vocab, self.roots_count, alias or pos, 'p', self.stat, self.tags,
                          suff=self.word_suff)
        # print(f"P_{pos} : {tmp}")

        return create_relations(tmp, meanings_dict, aliases.get(self.tags.POS) or self.tags.POS)

    def suf_relation(self, pos, alias=None):
        suffs = set()
        meanings_dict = getattr(getattr(Morphems, pos), "value")[1]
        for relation_value in meanings_dict.values():
            suffs.update(relation_value[1])

        tmp = dict.fromkeys(suffs, [])
        create_final_dict(tmp, self.vocab, self.roots_count, alias or pos, 's', self.stat, self.tags,
                          pref=self.word_pref)
        # print(f"S_{pos} : {tmp}")

        return create_relations(tmp, meanings_dict, aliases.get(self.tags.POS) or self.tags.POS)

    def pref_suf_relation(self, pos, alias=None):
        prefs_sufs = []
        meanings_dict = getattr(getattr(Morphems, pos), "value")[2]
        for relation_value in meanings_dict.values():
            prefs_sufs.append((relation_value[1], relation_value[2]))

        prefs_sufs = set(prefs_sufs)

        tmp = dict.fromkeys(prefs_sufs, [])
        create_final_dict(tmp, self.vocab, self.roots_count, alias or pos, 'ps', self.stat, self.tags,
                          pref=self.word_pref)
        # print(f"PS_{pos} : {tmp}")

        return create_relations(tmp, meanings_dict, aliases.get(self.tags.POS) or self.tags.POS, True)


def create_ontology(morph_dict):
    ontology = Ontology(morph_dict, 50)


def main():
    MANUAL = False
    global morph_dict, roots_dict, morph
    dict_path = ROOT_DIR[:ROOT_DIR.rfind('diplom')] + 'diplom/dict'
    morph_dict = read_json(f"{dict_path}/morph_dict.json")
    roots_dict = read_json(f"{dict_path}/roots_dict.json")
    info = {}
    morph = pymorphy2.MorphAnalyzer()

    if MANUAL:
        word = input('Word: ')
        parsed = morph.parse(word)
        variation = parsed[0]

        if variation.is_known:
            instance = Word(variation, roots_dict)
            info['pref'] = instance.new_words_pref
            info['suff'] = instance.new_words_suf
            info['prefsuff'] = instance.new_words_pref_suf
            print(info)
        else:
            segmented = get_morph_segmentation_of_word(word)
            with open('unrecognize.txt', 'w+') as file:
                file.write('START\n')
                file.write(segmented)
            morph_dict, roots_dict, complex_part = parse('unrecognize.txt', True)
            instance = Word(variation, roots_dict, one_word=word, ow_morph_dict=morph_dict)
            info['pref'] = instance.new_words_pref
            info['suff'] = instance.new_words_suf
            info['prefsuff'] = instance.new_words_pref_suf
            print(info)
    else:
        create_ontology(morph_dict)

if __name__ == "__main__":
    logging.basicConfig(format="►►► %(funcName)s() [LINE:%(lineno)d]} %(message)s ◄◄◄", level=logging.INFO)
    logging.captureWarnings(False)
    warnings.simplefilter("ignore")
    main()
