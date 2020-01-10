import pymorphy2
# from enum import Enum

import re
import meanings
import prefixes

vowels = 'ауоыиэяюёе'
vowels_1 = 'еёюя'
prefixes_1 = ('вз', 'дез', 'контр', 'пан', 'пост', 'суб', 'супер', 'транс')


def hard_sign(pref, letter):
    return letter in vowels_1 and pref[-1] not in vowels


def change_letter(pref, letter):
    return letter == 'и' and pref not in prefixes_1 and pref[-1] not in vowels


def check_in_dict(word):
    return morph.word_is_known(word)
        # a = morph.iter_known_word_parses(word[:-3])
        # for i in a:
        #     print(i)


def transform_word(word, type, grammems=None):
    parsed = morph.parse(word)[0]
    result_word = None

    if type == "verb":
        result_word = parsed.inflect({"perf"}).word
    elif type == "noun":
        pass
    elif type == "adj":
        pass
    elif type == "prt":
        pass
    elif type == "grnd":
        pass
    elif type == "advb":
        pass
    elif type == "numr":
        pass
    elif type == "npro":
        pass
    elif type == "intj":
        pass

    print(result_word)
    return result_word

class Word:
    # word = None
    # tags = None
    # new_words = []

    def __init__(self, variation):
        self.word = variation.normal_form
        self.tags = variation.tag
        self.new_words = []
        self.create_new()
    
    def create_new(self):
        if self.tags.POS == 'NOUN':  # сущ
            Noun(self)
        elif self.tags.POS in ('VERB', 'INFN'):  # глагол, инфинитив
            Verb(self)
        elif self.tags.POS in ('ADJF', 'ADJS', 'COMP'):  # полное/краткое/сравнительное прил
            Adj(self)
        elif self.tags.POS in ('PRTF', 'PRTS'):  # полное/краткое причастие
            Prt(self)
        elif self.tags.POS == 'GRND':  # деепричастие
            Grnd(self)
        elif self.tags.POS == 'NUMR':  # числительное
            Numr(self)
        elif self.tags.POS == 'ADVB':  # наречие
            Advb(self)
        elif self.tags.POS == 'NPRO':  # местоимение
            Npro(self)
        elif self.tags.POS == 'INTJ':  # междометие
            Intj(self)


class Verb(Word):

    def __init__(self, word: Word):
        print('in Verb')

        self.word = word.word
        self.tags = word.tags
        self.new_words = dict.fromkeys(meanings.verb_pref.keys(), [])
        new_pref = self.pref_relation()
        print(new_pref)

        for check_word in new_pref.values():
            # print(check_word)
            if not check_in_dict(check_word):
                transform_word(check_word, "verb")

    def pref_relation(self):

        tmp = dict.fromkeys(prefixes.verb_prefixes.get("from_verb"), '')
        letter = self.word[0]
        remove_keys = []

        for key in tmp.keys():
            if re.match(f'{key}', self.word):  # повторение приставки в начале слова
                remove_keys.append(key)
            elif hard_sign(key, letter):
                tmp[key] = key + 'ъ' + self.word
            elif change_letter(key, letter):
                tmp[key] = key + 'ы' + self.word[1:]
            else:
                tmp[key] = key + self.word

        for key in remove_keys:
            tmp.pop(key)

        return tmp

    def suf_relation(self):
        pass
        
        
class Noun(Word):
    def __init__(self, word: Word):
        print('in Noun')
        print(word.word, word.tags)
        self.new_words = []
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
    global morph
    morph = pymorphy2.MorphAnalyzer()
    word = input('Word: ')
#     print("Input word: ", word)
    parsed = morph.parse(word)

    test = morph.parse("сворую")[0]
    print('--', test.tag)
    # print(test.inflect({'INFN','tran','perf'}).word)


    for variation in parsed:
        if variation.is_known:
            instance = Word(variation)
            # print(variation)
        else:
            print("Incorrect word!")
            break

if __name__ == "__main__":
    main()

