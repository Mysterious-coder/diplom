import pymorphy2
import logging
import warnings
import re
import meanings
import prefixes
import suffixes
import json
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

vowels = 'ауоыиэяюёе'
vowels_1 = 'еёюя'
prefixes_1 = ('дез', 'контр', 'пан', 'пост', 'суб', 'супер', 'транс', 'ак', 'сверх', 'меж', 'интер', 'экс')
voiced_consonant = 'бвгджзлмнр'
dumb_consonant = 'пкстфхцчшщ'
type_dict = {
    's': r'(?:RS|WC|SF|S)',
    'p': r'(?:P|CP)',
    'ps': r'(?:RS|WC|SF|S|P|CP)'
}


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
    for key in tmp_dict.keys():
        arr = []
        if not isinstance(key, tuple):
            for rec in vocab:
                if rec[1] == count and rec[0] in pos and not app_morphem(rec[3]):
                            check = [morphem[:morphem.find('_')] for morphem in rec[3] if re.search(re_expr, morphem)]
                            if key in check:
                                transformed_word = transform_word(rec[2], stat, tags)
                                if transformed_word[0]:
                                    arr.append(transformed_word[1])
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
                        transformed_word = transform_word(rec[2], stat, tags)
                        if transformed_word[0]:
                            arr.append(transformed_word[1])
        tmp_dict[key] = arr


def create_relations(final_dict, mean_dict):
    """Создание словаря ТИП_СВЯЗИ: СЛОВА"""
    new_pref = dict.fromkeys(mean_dict.keys(), [])
    for key in new_pref.keys():
        arr = []
        # if isinstance(mean_dict[key][1], str):
        for morphem in mean_dict[key][1]:
            val = final_dict.get(morphem)
            if val is not None:
                arr.append(val)
        new_pref[key] = arr

    print(new_pref)
    return new_pref


class Word:
    # word = None
    # tags = None
    # new_words = []

    def __init__(self, variation):
        self.word = variation.word
        self.normal = variation.normal_form
        self.parsed = morph_dict.get(self.normal)
        print(self.parsed)
        self.roots = self.parsed[1]
        self.other_roots = self.parsed[2]
        self.roots_count = len(self.roots)
        self.vocab = []
        self.tags = variation.tag
        # self.morph_count = len(self.parsed[0])
        for root in self.roots:
            a = [r for r in roots_dict.get(root) if r[1] == self.roots_count and set(r[4]) == set(self.roots)]
            self.vocab.extend(a)
        for root in self.other_roots:  # возможна некорректная выборка из-за условия
            a = [r for r in roots_dict.get(root) if r[1] == self.roots_count and
                 set(r[4]).issubset(set(self.other_roots).union(set(self.roots)))]
            self.vocab.extend(a)
        self.new_words = []
        self.inst = self.create_new()

    def create_new(self):
        """Вызов подкласса в зависимости от части речи"""
        if self.tags.POS == 'NOUN':  # сущ
            inst = Noun(self)
        elif self.tags.POS in ('VERB', 'INFN'):  # глагол, инфинитив
            inst = Verb(self)
        elif self.tags.POS in ('ADJF', 'ADJS', 'COMP'):  # полное/краткое/сравнительное прил
            inst = Adj(self)
        elif self.tags.POS in ('PRTF', 'PRTS'):  # полное/краткое причастие
            inst = Prt(self)
        elif self.tags.POS == 'GRND':  # деепричастие
            inst = Grnd(self)
        elif self.tags.POS == 'NUMR':  # числительное
            inst = Numr(self)
        elif self.tags.POS == 'ADVB':  # наречие
            inst = Advb(self)
        elif self.tags.POS == 'NPRO':  # местоимение
            inst = Npro(self)
        elif self.tags.POS == 'INTJ':  # междометие
            inst = Intj(self)

        return inst


class Verb(Word):
    def __init__(self, word: Word):
        print('in Verb')
        self.stat = {"good": 0,
                     "bad": 0}
        self.word = word.word
        self.normal = word.normal
        self.roots = word.roots
        self.parsed = word.parsed
        self.roots_count = word.roots_count
        self.vocab = word.vocab
        self.tags = word.tags
        self.new_pref_words = []
        self.word_pref = []  # префиксы слова
        self.word_suff = []  # суффиксы слова
        for i in self.parsed[0]:
            if re.search(type_dict.get('p'), i):
                self.word_pref.append(i[:i.find('_')])
            elif re.search(type_dict.get('s'), i):
                self.word_suff.append(i[:i.find('_')])

        new_pref = self.pref_relation()
        new_suff = self.suf_relation()

    def pref_relation(self):
        """Создание префиксальной связи"""
        prefs = prefixes.verb_prefixes.get("from_verb")

        for i in range(len(prefs)):
            if isinstance(prefs[i], str) and hard_sign(prefs[i], self.normal[0]):
                prefs[i] = prefs[i] + 'ъ'

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
        create_final_dict(tmp, self.vocab, self.roots_count, ('VERB', 'INFN'), 'p', self.stat, self.tags,
                          suff=self.word_suff)
        print(f"PREF_from_verb : {tmp}")

        return create_relations(tmp, meanings.verb_pref)

    def suf_relation(self):
        tmp = dict.fromkeys(suffixes.verb_suffixes.get("from_verb"), [])
        create_final_dict(tmp, self.vocab, self.roots_count, ('VERB', 'INFN'), 's', self.stat, self.tags,
                          pref=self.word_pref)
        print(f"SUFF_from_verb : {tmp}")

        return create_relations(tmp, meanings.verb_pref)


class Noun(Word):
    def __init__(self, word: Word):
        print('in Noun')
        self.stat = {"good": 0,
                     "bad": 0}
        self.word = word.word
        self.tags = word.tags
        self.new_pref_words = dict.fromkeys(meanings.verb_pref.keys(), [])
        # new_pref = self.pref_relation()
        # print(f"NEW_PREF : {new_pref}")
        # print(self.stat)
        pass


class Adj(Word):
    def __init__(self, word: Word):
        print('in Adj')
        pass


class Prt(Word):
    def __init__(self, word: Word):
        print('in Prt')
        pass


class Grnd(Word):
    def __init__(self, word: Word):
        print('in Grnd')
        pass


class Numr(Word):
    def __init__(self, word: Word):
        print('in Numr')
        pass


class Advb(Word):
    def __init__(self, word: Word):
        print('in Advb')
        pass


class Npro(Word):
    def __init__(self, word: Word):
        print('in Npro')
        pass


class Intj(Word):
    def __init__(self, word: Word):
        print('in Intj')
        pass

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
       print(variation)
       instance = Word(variation)
       print(instance.inst.stat)
    else:
        print("Incorrect word!")


if __name__ == "__main__":

    logging.basicConfig(format="►►► %(funcName)s() [LINE:%(lineno)d]} %(message)s ◄◄◄", level=logging.INFO)
    logging.captureWarnings(False)
    warnings.simplefilter("ignore")
    main()
