import pymorphy2
import logging
import warnings
import re
import prefixes
import suffixes
import itertools
import json
import os
from enum import Enum
from meanings import *

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

vowels = 'ауоыиэяюёе'
vowels_1 = 'еёюя'
prefixes_1 = ('дез', 'контр', 'пан', 'пост', 'суб', 'супер', 'транс', 'ак', 'сверх', 'меж', 'интер', 'экс')
voiced_consonant = 'бвгджзлмнр'
dumb_consonant = 'пкстфхцчшщ'
type_dict = {
    # 's': r'(?:RS|WC|SF|S|SI)',
    # 'p': r'(?:P|CP)',
    # 'ps': r'(?:RS|WC|SF|S|SI|P|CP)'
    's': r'(?:S|WC)',
    'p': r'P',
    'ps': r'(?:S|WC|P)'
}


class Morphems(Enum):
    ALL = ""
    NOUN = (noun_pref, noun_suf, noun_pref_suf) # сущ
    ADVB = (advb_pref, advb_suf, advb_pref_suf) # наречие
    ADJF = (adj_pref, adj_suf, adj_pref_suf)    # полное/краткое/сравнительное прил
    ADJS = (adj_pref, adj_suf, adj_pref_suf)
    COMP = (adj_pref, adj_suf, adj_pref_suf)
    VERB = (verb_pref, verb_suf, verb_pref_suf) # глагол, инфинитив
    INFN = (verb_pref, verb_suf, verb_pref_suf)
    PRTF = (prt_pref, prt_suf, prt_pref_suf)    # причастие
    PRTS = (prt_pref, prt_suf, prt_pref_suf)
    GRND = (grnd_pref, grnd_suf, grnd_pref_suf) # деепричастие
    NUMR = ("", numr_suf)                           # числительное
    NPRO = (npro_pref, npro_suf, npro_pref_suf) # местоимение
    INTJ = ("", intj_suf)                           # междометие
    PRED = ""
    PREP = ""
    CONJ = ""
    PRCL = ""

aliases = {
    'VERB': ('VERB', 'INFN'),
    'INFN': ('VERB', 'INFN'),
    'ADJF': ('ADJF', 'ADJS', 'COMP'),
    'ADJS': ('ADJF', 'ADJS', 'COMP'),
    'COMP': ('ADJF', 'ADJS', 'COMP'),
    'PRTF': ('PRTF', 'PRTS'),
    'PRTS': ('PRTF', 'PRTS')
}
all_poses = ['NOUN', 'ADVB', 'ADJF', 'VERB', 'PRTF', 'GRND', 'NPRO']
only_suf_poses = ['NUMR', 'INTJ']

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


def transform_word(word, stat, grammems=None):
    """Склонение проверочного слова и проверка результата в словаре"""
    parsed = morph.parse(word)[0]
    print("source word_transform: ", word, end=' | ')
    result_word = flection(grammems, parsed)
    good_word = False

    if result_word is None:
        stat["bad"] += 1
        print(' None')
    elif not check_in_dict(result_word):
        print("bad result: ", result_word)
        stat["bad"] += 1
    else:
        good_word = True
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
                                    if tags.POS in pos: # если ЧР совпадают - пытаемся просклонять
                                        transformed_word = transform_word(rec[2], stat, tags)
                                        if transformed_word[0]:
                                            set_of_words.add(transformed_word[1])
                                    else:               # иначе просто добавляем слово
                                        set_of_words.add(rec[2])
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
                            if tags.POS in pos:  # если ЧР исходного слова и необходимого совпадают - пытаемся просклонять
                                transformed_word = transform_word(rec[2], stat, tags)
                                if transformed_word[0]:
                                    set_of_words.add(transformed_word[1])
                            else:  # иначе просто добавляем слово
                                set_of_words.add(rec[2])
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
                                if tags.POS in pos:  # если ЧР исходного слова и необходимого совпадают - пытаемся просклонять
                                    transformed_word = transform_word(rec[2], stat, tags)
                                    if transformed_word[0]:
                                        set_of_words.add(transformed_word[1])
                                else:  # иначе просто добавляем слово
                                    set_of_words.add(rec[2])
                elif isinstance(comb[0], str):
                    for rec in vocab:
                        if rec[1] == count and rec[0] in pos:
                            check_prefs = [morphem[:morphem.find('_')] for morphem in rec[3] if
                                           re.search(type_dict.get('p'), morphem)]
                            check_suffs = [morphem[:morphem.find('_')] for morphem in rec[3] if
                                           re.search(type_dict.get('s'), morphem)]
                            flag = True
                            for subkey in comb[1]:
                                if subkey not in check_suffs:
                                    flag = False
                                    break

                            if flag and comb[0] in check_prefs:
                                if tags.POS in pos:  # если ЧР исходного слова и необходимого совпадают - пытаемся просклонять
                                    transformed_word = transform_word(rec[2], stat, tags)
                                    if transformed_word[0]:
                                        set_of_words.add(transformed_word[1])
                                else:  # иначе просто добавляем слово
                                    set_of_words.add(rec[2])
                elif isinstance(comb[1], str):
                    for rec in vocab:
                        if rec[1] == count and rec[0] in pos:
                            check_prefs = [morphem[:morphem.find('_')] for morphem in rec[3] if
                                           re.search(type_dict.get('p'), morphem)]
                            check_suffs = [morphem[:morphem.find('_')] for morphem in rec[3] if
                                           re.search(type_dict.get('s'), morphem)]
                            flag = True
                            for subkey in comb[0]:
                                if subkey not in check_prefs:
                                    flag = False
                                    break

                            if flag and comb[1] in check_suffs:
                                if tags.POS in pos:  # если ЧР исходного слова и необходимого совпадают - пытаемся просклонять
                                    transformed_word = transform_word(rec[2], stat, tags)
                                    if transformed_word[0]:
                                        set_of_words.add(transformed_word[1])
                                else:  # иначе просто добавляем слово
                                    set_of_words.add(rec[2])
                else:
                    for rec in vocab:
                        if rec[1] == count and rec[0] in pos:
                            check_prefs = [morphem[:morphem.find('_')] for morphem in rec[3] if
                                           re.search(type_dict.get('p'), morphem)]
                            check_suffs = [morphem[:morphem.find('_')] for morphem in rec[3] if
                                           re.search(type_dict.get('s'), morphem)]
                            flag_p = True
                            for subkey in comb[0]:
                                if subkey not in check_prefs:
                                    flag_p = False
                                    break
                            flag_s = True
                            for subkey in comb[1]:
                                if subkey not in check_suffs:
                                    flag_s = False
                                    break

                            if flag_s and flag_p:
                                if tags.POS in pos:  # если ЧР исходного слова и необходимого совпадают - пытаемся просклонять
                                    transformed_word = transform_word(rec[2], stat, tags)
                                    if transformed_word[0]:
                                        set_of_words.add(transformed_word[1])
                                else:  # иначе просто добавляем слово
                                    set_of_words.add(rec[2])
                if set_of_words:
                    tmp_dict[key] = set_of_words

def create_relations(final_dict, mean_dict, ps=None):
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

    for key in new_relations.keys():
        new_relations[key] = [mean_dict.get(key)[0], new_relations[key]]

    # print(new_relations)
    return new_relations


class Word:
    # word = None
    # tags = None
    # new_words = []

    def __init__(self, variation):
        self.word = variation.word
        self.normal = variation.normal_form
        self.parsed = morph_dict.get(self.normal)
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
        # new_pref = self.pref_relation('VERB', aliases.get('VERB'))
        # new_suf = self.suf_relation('VERB', aliases.get('VERB'))
        # new_pref_suf = self.pref_suf_relation('VERB', aliases.get('VERB'))
        for pos in all_poses:
            self.new_words_pref.extend(self.pref_relation(pos, aliases.get(pos)).values())
            self.new_words_suf.extend(self.suf_relation(pos, aliases.get(pos)).values())
            self.new_words_pref_suf.extend(self.pref_suf_relation(pos, aliases.get(pos)).values())
        for pos in only_suf_poses:
            self.new_words_suf.extend(self.suf_relation(pos, aliases.get(pos)).values())

    def pref_relation(self, pos, aliases=None):
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
        create_final_dict(tmp, self.vocab, self.roots_count, aliases or pos, 'p', self.stat, self.tags,
                          suff=self.word_suff)
        # print(f"P_{pos} : {tmp}")

        return create_relations(tmp, meanings_dict)

    def suf_relation(self, pos, aliases=None):
        suffs = set()
        meanings_dict = getattr(getattr(Morphems, pos), "value")[1]
        for relation_value in meanings_dict.values():
            suffs.update(relation_value[1])

        tmp = dict.fromkeys(suffs, [])
        create_final_dict(tmp, self.vocab, self.roots_count, aliases or pos, 's', self.stat, self.tags,
                          pref=self.word_pref)
        # print(f"S_{pos} : {tmp}")

        return create_relations(tmp, meanings_dict)

    def pref_suf_relation(self, pos, aliases=None):
        prefs_sufs = []
        meanings_dict = getattr(getattr(Morphems, self.tags.POS), "value")[2]
        for relation_value in meanings_dict.values():
            prefs_sufs.append((relation_value[1], relation_value[2]))

        prefs_sufs = set(prefs_sufs)
        for i in prefs_sufs:
            if isinstance(i, str) and hard_sign(i, self.normal[0]):
                prefs_sufs.remove(i)
                prefs_sufs.add(i + 'ъ')

        tmp = dict.fromkeys(prefs_sufs, [])
        create_final_dict(tmp, self.vocab, self.roots_count, aliases or pos, 'ps', self.stat, self.tags,
                          pref=self.word_pref)
        # print(f"PS_{pos} : {tmp}")

        return create_relations(tmp, meanings_dict, True)


# .is_known


def main():
    global morph_dict, roots_dict, morph
    dict_path = ROOT_DIR[:ROOT_DIR.rfind('diplom')] + 'diplom/dict'
    morph_dict = read_json(f"{dict_path}/morph_dict.json")
    roots_dict = read_json(f"{dict_path}/roots_dict.json")

    morph = pymorphy2.MorphAnalyzer()
    word = input('Word: ')
    parsed = morph.parse(word)
    variation = parsed[0]
    # for variation in parsed:
    if variation.is_known:
       # print(variation)
       instance = Word(variation)
       print(instance.stat)
       for w in instance.new_words_pref:
           print(w)
       for w in instance.new_words_suf:
           print(w)
       for w in instance.new_words_pref_suf:
           print(w)
    else:
        print("Incorrect word!")


if __name__ == "__main__":

    logging.basicConfig(format="►►► %(funcName)s() [LINE:%(lineno)d]} %(message)s ◄◄◄", level=logging.INFO)
    logging.captureWarnings(False)
    warnings.simplefilter("ignore")
    main()
