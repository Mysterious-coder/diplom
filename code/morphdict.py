import re
import pymorphy2
from enum import Enum
from prefixes import prefs
from suffixes import *
import logging

suffs = [set(i) for i in (suff_advb, suff_adj, suff_noun, suff_name, suff_verb, morph_wordcreate, morph_wordchange)]
a = set()
for i in suffs:
    a = a | i
suffs = a

class Check(Enum):
    ALL = suffs
    NOUN = suff_noun
    ADVB = suff_advb
    ADJ  = suff_adj
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
        i = 10000
        start = False
        complex_part = []
        morph_dict = {}
        for line in file.readlines():
            if start:
                line = line.rstrip('\n')
                line = line.replace("'", '')
                line = line.replace(',', ' ')
                arr = line.split(' | ')
                if arr[0][-1] in '.':
                    cur = arr[0].find('.')
                    complex_part.append(arr[0][:cur])
                    continue
                try:
                    arr[1] = re.match(r"([\S]+)", arr[1]).group(0).split('/')
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

                    # if arr[1][k] in complex_part:
                    #     arr[1][k] = arr[1][k] + "_CX"
                    #     if arr[1][k+1] in morph_interfixes:
                    #         arr[1][k+1] = arr[1][k+1] + "_I"
                    #         arr[1][k+2] = arr[1][k+2] + "_CX2"
                    #     else:
                    #         arr[1][k+1] = arr[1][k+1] + "_CX2"

                for k in range(0, len(arr[1])):
                    if arr[1][k] in {'ть', 'ся'}:
                        arr[1][k] = arr[1][k] + "_RS"

                if not arr[1][-1].count('-'):
                    arr[1][-1] = arr[1][-1] + "_E"

                for k in range(1, len(arr[1])):
                    if arr[1][k] in check:
                        arr[1][k] = arr[1][k] + "_S"

                for k in range(1, len(arr[1])):
                    if arr[1][k] in morph_interfixes:
                        arr[1][k] = arr[1][k] + "_I"

                for k in range(1, len(arr[1])):
                    if arr[1][k] in morph_wordcreate:
                        arr[1][k] = arr[1][k] + "_WC"


                print(arr)
                morph_dict[arr[0]] = arr[1]

            elif line == "START\n":
                start = True

            i -= 1
            if i == 0:
                # print(morph_dict)
                print(complex_part)
                break



morph = pymorphy2.MorphAnalyzer()
parse("../dict/MorphDictTikhonov.txt")