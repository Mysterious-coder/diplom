import pymorphy2
import logging
import warnings
import re
import meanings
import prefixes
from morphdict import read_json

vowels = 'ауоыиэяюёе'
vowels_1 = 'еёюя'
prefixes_1 = ('вз', 'дез', 'контр', 'пан', 'пост', 'суб', 'супер', 'транс')
voiced_consonant = 'бвгджзлмнр'
dumb_consonant = 'пкстфхцчшщ'


def hard_sign(pref, letter):
    """Предикат - первая буква слова <еёюя> и последняя буква приставки - согласная"""
    return letter in vowels_1 and pref[-1] not in vowels


def change_letter(pref, letter, functionality):
    """Предикат 1 - для смены <и> на <ы>
                2 - для смены <и> на <й>"""
    predicat = None

    if functionality == 1:  # и на ы
        predicat = (letter == 'и' and pref not in prefixes_1 and pref[-1] not in vowels)
    elif functionality == 2:  # и на й
        predicat = (letter == 'и' and pref[-1] in 'иоуыае')
    elif functionality == 3:  # з на с
        predicat = (pref[-1] == 'з' and letter in dumb_consonant)

    return predicat


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
    elif not check_in_dict(result_word):
        print("bad result: ", result_word)
        stat["bad"] += 1
    else:
        good_word = True
        print("good result: ", result_word)
        stat["good"] += 1

    return good_word, result_word


def create_final_dict(tmp_dict, stat, tags):
    """Создание словаря МОРФЕМА: НОВОЕ СЛОВО"""
    for key, check_words in tmp_dict.items():
        if isinstance(check_words, list):
            arr = []
            for check_word in check_words:
                transformed_word = transform_word(check_word, stat, tags)
                if transformed_word[0]:
                    arr.append(transformed_word[1])
            if len(arr) == 1: arr = arr[0]
            tmp_dict[key] = arr if arr else None
        else:
            transformed_word = transform_word(check_words, stat, tags)
            tmp_dict[key] = transformed_word[1] if transformed_word[0] else None

    return tmp_dict


def create_relations(final_dict, mean_dict):
    new_pref = dict.fromkeys(mean_dict.keys(), [])
    for key in new_pref.keys():
        arr = []
        for pref in mean_dict[key][1]:
            val = final_dict.get(pref)
            if val is not None:
                arr.append(val)
        new_pref[key] = arr
    return new_pref


class Word:
    # word = None
    # tags = None
    # new_words = []

    def __init__(self, variation):
        self.word = variation.word
        self.normal = variation.normal_form
        self.tags = variation.tag
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
        self.tags = word.tags
        self.new_pref_words = []

        new_pref = self.pref_relation()

    def pref_relation(self):
        """Создание префиксальной связи"""
        tmp = dict.fromkeys(prefixes.verb_prefixes.get("from_verb"), [])
        letter = self.word[0]
        remove_keys = []

        for key in tmp.keys():
            if re.match(f'{key}', self.word):  # повторение приставки в начале слова
                remove_keys.append(key)
            elif hard_sign(key, letter):
                tmp[key] = [key + 'ъ' + self.word]
            elif change_letter(key, letter, 1):
                arr = [key + self.word]
                arr.append(key + 'ы' + self.word[1:])
                arr.append(key + 'ой' + self.word[2:])
                arr.append(key + 'ой' + self.word[1:])
                tmp[key] = arr
            elif change_letter(key, letter, 2):
                arr = [key + self.word]
                arr.append(key + 'й' + self.word[2:])
                arr.append(key + 'й' + self.word[1:])
                tmp[key] = arr
            elif change_letter(key, letter, 3):
                arr = [key + self.word, key[:-1] + 'с' + self.word]
                tmp[key] = arr
            else:
                tmp[key] = [key + self.word]

        for key in remove_keys:
            tmp.pop(key)

        tmp = create_final_dict(tmp, self.stat, self. tags)
        print(f"PREF_from_verb : {tmp}")

        return create_relations(tmp, meanings.verb_pref)

    def suf_relation(self):
        pass


class Noun(Word):
    def __init__(self, word: Word):
        print('in Noun')
        self.stat = {"good": 0,
                     "bad": 0}
        self.word = word.word
        self.tags = word.tags
        self.new_pref_words = dict.fromkeys(meanings.verb_pref.keys(), [])
        new_pref = self.pref_relation()
        print(f"NEW_PREF : {new_pref}")
        print(self.stat)
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
    morph_dict = read_json(f"../dict/morph_dict.json")
    roots_dict = read_json(f"../dict/roots_dict.json")

    global morph
    morph = pymorphy2.MorphAnalyzer()
    word = input('Word: ')
    parsed = morph.parse(word)

    for variation in parsed:
        if variation.is_known:
            instance = Word(variation)
            print(instance.inst.stat)
            print(variation)
        else:
            print("Incorrect word!")
            break


if __name__ == "__main__":

    logging.basicConfig(format="►►► %(funcName)s() [LINE:%(lineno)d]} %(message)s ◄◄◄", level=logging.INFO)
    logging.captureWarnings(False)
    warnings.simplefilter("ignore")
    main()
