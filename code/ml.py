import numpy as np
import pymorphy2
import time
import re
import logging
from morphdict import read_json, write_json
from copy import copy
from functools import wraps
import progressbar
from catboost import CatBoostClassifier, Pool
from constants import type_dict_ml as type_dict, aliases

def timeit(my_func):
    @wraps(my_func)
    def timed(*args, **kw):
        tstart = time.time()
        output = my_func(*args, **kw)
        tend = time.time()

        print('"{}" took {:.3f} ms to execute'.format(my_func.__name__, (tend - tstart) * 1000))
        return output

    return timed


def create_ngrams(src: str):
    """Создание всевозможных N-грамм до N=len(word)"""
    ngrams = []

    for k in range(len(src)):
        gram = []
        for i in range(len(src) - k):
            gram.append(src[i:i + 1 + k])
        ngrams.extend(gram)

    return ngrams


def create_x_y(word, ngrams_src: list, trg_src: list, token_index, morph, size_of_y=1):
    """Создание датасета"""
    morph_vect = get_morphs(word, morph)
    ngrams = copy(ngrams_src)
    trg = copy(trg_src)
    y = np.zeros((len(ngrams)))
    vect = vect_with_letter_count(ngrams, token_index)

    for trg_morph in trg:
        for morph in filter(lambda x: len(x) == len(trg_morph) and morph != '_E', ngrams):
            if morph != "-" and trg != '_E' and morph == trg_morph:
                y[ngrams.index(morph)] = 1
                break

    c = np.zeros((vect.shape[0], morph_vect.shape[0]))

    for i, row in enumerate(c):
        c[i] = morph_vect

    vect = np.concatenate((vect, c), axis=1)

    return vect, y


def map_create(map_letters, other_chars=None, add_en=False):
    """Создание словаря для кодирования"""
    ru_low = {chr(i): (i - ord('а') + 1) for i in range(ord('а'), ord('я') + 1)}
    map_letters.update(ru_low)
    if other_chars is not None:
        for char in other_chars:
            map_letters[char] = 0

    if add_en:
        l = len(map_letters)
        en_low = {chr(i): (i - ord('a') + l) for i in range(ord('a'), ord('z') + 1)}
        map_letters.update(en_low)


def word_tokenize(token_index: dict, samples):
    """Создание словаря токенов - слово: индекс"""
    for sample in samples:
        for word in sample.split():
            if word not in token_index:
                token_index[word] = len(token_index) + 1


def one_hot_encode(samples, token_index, word_encode=False, get_print=False):
    """Прямое кодирование символов/слов"""
    max_length = max(len(i) for i in samples.keys())
    results = np.zeros(shape=(len(samples), max_length, max(token_index.values()) + 1))

    for i, sample in enumerate(samples):
        for j, character in enumerate(sample[:max_length].lower()) if not word_encode else list(
                enumerate(sample.split()))[:max_length]:
            index = token_index.get(character)
            if get_print:
                print(i, j, character, index)
            results[i, j, index] = 1.
    if get_print:
        print(results)
    return results


def vect_with_letter_count(words, map_letters, fixed_length=False):
    """Кодирование по количеству вхождений символа в слово"""
    vect = np.zeros(shape=(len(words), fixed_length or len(map_letters) + 1))
    for i, word in enumerate(words):
        for letter in word:
            if letter in map_letters:
                vect[i, map_letters.get(letter)] += 1
    return vect


def get_morphs(word, morph):
    """Получение вектора морфологического разбора слова"""
    grammems = ["NOUN", "ADJF", "ADJS", "COMP", "VERB", "INFN", "PRTF", "PRTS", "GRND", "NUMR", "ADVB", "NPRO", "PRED",
                "PREP",
                "CONJ", "PRCL", "INTJ", "ANIM", "INAN", "MASC", "FEMN", "NEUT", "MS-F", "SING", "PLUR", "PERF", "IMPF",
                "TRAN", "INTR", "PRES",
                "PAST", "FUTR"]
    d = dict(zip(grammems, range(1, len(grammems) + 1)))
    a = np.zeros(len(d) + 1)
    p = morph.parse(word)[0]

    if p is not None:
        x = str(p.tag).split(',')
        k = []
        for i in x:
            k.append(i) if ' ' not in i else k.extend(i.split())
        for i in range(len(k)):
            if k[i].upper() in d:
                a[d.get(k[i].upper())] = 1
    return a


def prepare_data(path: str):
    """Создание numpy-массивов датасета и их сохранение в файлы .npy"""
    morphdict = read_json(path)
    morph = pymorphy2.MorphAnalyzer()
    token_index = {}
    map_create(token_index)
    x_vect = []
    y_vect = []

    for word, parsed in morphdict.items():
        word = word.replace('-', '')
        ngrams = create_ngrams(word)
        x, y = create_x_y(word, ngrams, parsed[0], token_index, morph)
        x_vect.append(x)
        y_vect.append(y)

    np.save("../data/x.npy", x_vect, allow_pickle=True)
    np.save("../data/y.npy", y_vect, allow_pickle=True)

    return x_vect, y_vect


def read_data(path: str):
    """Извлечение датасета"""
    x_vect = np.load(path + "x.npy", allow_pickle=True)
    y_vect = np.load(path + "y.npy", allow_pickle=True)
    # print(y_vect[1], x_vect[1])
    return x_vect, y_vect


def one_hot_encode_character(character, token_index, get_print=False):
    """Прямое кодирование символов"""
    results = np.zeros(shape=(max(token_index.values()) + 1))

    index = token_index.get(character.lower())
    results[index] = 1.
    if get_print:
        print(results)
    return results


def create_window(word, char_index, size=3):
    """Создание окна из символов слова"""
    window = [None] * size * 2
    length = len(word)
    help_index = char_index
    for i in range(size-1, -1, -1):
        help_index -= 1
        if help_index > -1:
            window[i] = word[help_index]
    help_index = char_index
    for i in range(size, size*2):
        help_index += 1
        if help_index < length:
            window[i] = word[help_index]

    return window


def frequence(morphdict, freq_dict):
    amount_of_chars = 0
    for word, parsed in morphdict.items():
        amount_of_chars += len(word)
        try:
            for char in word:
                freq_dict[char] += 1
        except Exception as e:
            print("Bad word - ", word)
    for key, value in freq_dict.items():
        freq_dict[key] = round(value * 10 / amount_of_chars, 2)


def create_vect(morphdict, freq_dict):
    y_vect = []
    x_vect = []

    cc = 2
    done = len(morphdict)
    count = 1

    for word, parsed in morphdict.items():
        bar.update(count * 100//done)
        count += 1
        x = [None] * len(word)
        mp = morph.parse(word)[0]
        length = len(word)
        pos = 0
        print(count)
        # print(word)
        # print(mp.tag)
        try:
            for char in word:
                char = char.lower()
                window = create_window(word, pos)
                begin = word[:pos+1]
                end = word[pos:]
                # result = one_hot_encode_character(char, token_index)
                result = [char]
                # result = np.append(result, 1 if char in vowels else 0)
                result.append('да' if char in vowels else 'нет')
                result.append(freq_dict.get(char))
                result.extend(window)
                result.extend((mp.tag.POS if mp.tag.POS is not None else "ALL", mp.tag.case, mp.tag.gender, mp.tag.number, mp.tag.tense, length))
                # result.extend(harris(begin, end, morphdict))
                result.extend(harris_pos(begin, end, morphdict, mp.tag.POS))
                x[pos] = result
                pos += 1

            y = create_y(word, parsed[1])
            y_vect.append(y)
            x_vect.append(x)
        except Exception as e:
            logging.exception(f"ERROR on  {word}, {parsed}")
        # count += 1
        # cc -= 1
        # if cc == 0:
        #     break

    write_json("../data/x_test.json", x_vect)
    write_json("../data/y_test.json", y_vect)

    return


def create_y(word, parsed):
    def mark_lbl(lbl, length, y, pos):
        if y[pos] is not None:
            pos += 1
        if length > 1:
            count = length - 1
            y[pos] = f'B{lbl}'
            while count:
                pos += 1
                y[pos] = f'{lbl}'
                count -= 1
        elif length == 1:
            y[pos] = f'B{lbl}'
            pos += 1

        return pos

    y = [None] * len(word)
    pos = 0
    while word.find('-', pos) > 0:
        y[word.find('-', pos)] = 'H'
        pos += 1
    pos = 0
    for morphem in parsed:
        morph = morphem[:morphem.find('_')]
        if len(morph):
            if re.search(type_dict.get('r'), morphem):
                pos = mark_lbl('R', len(morph), y, pos)
            elif re.search(type_dict.get('p'), morphem):
                pos = mark_lbl('P', len(morph), y, pos)
            elif re.search(type_dict.get('s'), morphem):
                pos = mark_lbl('S', len(morph), y, pos)
            elif re.search(type_dict.get('i'), morphem):
                pos = mark_lbl('I', len(morph), y, pos)
            elif re.search(type_dict.get('e'), morphem):
                pos = mark_lbl('E', len(morph), y, pos)

    return y


harris_dict_b = {}
harris_dict_e = {}

def harris(begin, end, morphdict):
    """Сбор статистики Харриса: при morph_dependence=True сбор осуществляется по одинаковым частям речи"""
    b_set = set()
    e_set = set()
    # morphdict = {"интересный":1, "красный": 2, "зеленый": 3, "телесный": 4, "лесной": 5, 'направо': 6}
    if harris_dict_b.get(begin) is None and harris_dict_e.get(end) is None:
        for word in morphdict.keys():
            length = len(word)
            pos = 0
            if begin in word:
                while word.find(begin, pos) > -1:
                    pos = word.find(begin, pos)
                    if pos+len(begin) < length:
                        b_set.add(word[pos+len(begin)])
                    pos += 1
            if end in word:
                while word.find(end, pos) > -1:
                    pos = word.find(end, pos)
                    if pos-1 > -1:
                        e_set.add(word[pos - 1])
                    pos += 1
        harris_dict_b[begin] = len(b_set)
        harris_dict_e[end] = len(e_set)
        return len(b_set), len(e_set)

    elif harris_dict_b.get(begin) is None:
        for word in morphdict.keys():
            length = len(word)
            pos = 0
            if begin in word:
                while word.find(begin, pos) > -1:
                    pos = word.find(begin, pos)
                    if pos+len(begin) < length:
                        b_set.add(word[pos+len(begin)])
                    pos += 1
        harris_dict_b[begin] = len(b_set)
        return len(b_set), harris_dict_e.get(end)
    elif harris_dict_e.get(end) is None:
        for word in morphdict.keys():
            pos = 0
            if end in word:
                while word.find(end, pos) > -1:
                    pos = word.find(end, pos)
                    if pos-1 > -1:
                        e_set.add(word[pos - 1])
                    pos += 1
        harris_dict_e[end] = len(e_set)
        return harris_dict_b.get(begin), len(e_set)
    else:
        return harris_dict_b.get(begin), harris_dict_e.get(end)


harris_dict_b_pos = {}
harris_dict_e_pos = {}
v = dict.fromkeys(aliases.get('VERB'), {})
a = dict.fromkeys(aliases.get('ADJF'), {})
p = dict.fromkeys(aliases.get('PRTF'), {})
ve = dict.fromkeys(aliases.get('VERB'), {})
ae = dict.fromkeys(aliases.get('ADJF'), {})
pe = dict.fromkeys(aliases.get('PRTF'), {})

harris_dict_b_pos.update(v)
harris_dict_e_pos.update(ve)
harris_dict_b_pos.update(a)
harris_dict_e_pos.update(ae)
harris_dict_b_pos.update(p)
harris_dict_e_pos.update(pe)


def harris_pos(begin, end, morphdict, pos_check):
    """Сбор статистики Харриса: при morph_dependence=True сбор осуществляется по одинаковым частям речи"""
    b_set = set()
    e_set = set()
    if pos_check not in harris_dict_b_pos:
        harris_dict_b_pos[pos_check] = {}
    if pos_check not in harris_dict_e_pos:
        harris_dict_e_pos[pos_check] = {}

    # morphdict = {"интересный":1, "красный": 2, "зеленый": 3, "телесный": 4, "лесной": 5, 'направо': 6}
    if harris_dict_b_pos.get(pos_check).get(begin) is None and harris_dict_e_pos.get(pos_check).get(end) is None:
        for word, parsed in morphdict.items():
            if predict_pos(pos_check, parsed[2]):
                length = len(word)
                pos = 0
                if begin in word:
                    while word.find(begin, pos) > -1:
                        pos = word.find(begin, pos)
                        if pos+len(begin) < length:
                            b_set.add(word[pos+len(begin)])
                        pos += 1
                if end in word:
                    while word.find(end, pos) > -1:
                        pos = word.find(end, pos)
                        if pos-1 > -1:
                            e_set.add(word[pos - 1])
                        pos += 1
        harris_dict_b_pos[pos_check][begin] = len(b_set)
        harris_dict_e_pos[pos_check][end] = len(e_set)
        return len(b_set), len(e_set)

    elif harris_dict_b_pos.get(pos_check).get(begin) is None:
        for word, parsed in morphdict.items():
            if predict_pos(pos_check, parsed[2]):
                length = len(word)
                pos = 0
                if begin in word:
                    while word.find(begin, pos) > -1:
                        pos = word.find(begin, pos)
                        if pos+len(begin) < length:
                            b_set.add(word[pos+len(begin)])
                        pos += 1
        harris_dict_b_pos[pos_check][begin] = len(b_set)
        return len(b_set), harris_dict_e_pos.get(pos_check).get(end)

    elif harris_dict_e_pos.get(pos_check).get(end) is None:
        for word, parsed in morphdict.items():
            if predict_pos(pos_check, parsed[2]):
                pos = 0
                if end in word:
                    while word.find(end, pos) > -1:
                        pos = word.find(end, pos)
                        if pos-1 > -1:
                            e_set.add(word[pos - 1])
                        pos += 1
        harris_dict_e_pos[pos_check][end] = len(e_set)
        return harris_dict_b_pos.get(pos_check).get(begin), len(e_set)
    else:
        return harris_dict_b_pos.get(pos_check).get(begin), harris_dict_e_pos.get(pos_check).get(end)

def predict_pos(pos_check, pos_word):
    """Предикат - совпадение или принадлежность к одному семейству частей речи"""
    flag = False
    pos_check = str(pos_check)
    if aliases.get(pos_check) is not None:
        flag = pos_word in aliases.get(pos_check)
    return pos_check == pos_word or flag


def prepare_data_new():
    token_index = {}
    map_create(token_index, '-')
    freq_dict = dict.fromkeys(token_index, 0)
    morphdict = read_json("../dict/ml_dict.json")
    frequence(morphdict, freq_dict)
    bar = progressbar.ProgressBar().start()
    create_vect(morphdict, freq_dict)
    bar.finish()


def change_data(data):
    """change_data"""
    for idx, i in enumerate(data):
        for idj, j in enumerate(i):
                if j is None:
                    data[idx][idj] = str(j)


def create_vect_word(input_word, get_pos=False):
    vowels = 'ауоыиэяюёе'
    morph = pymorphy2.MorphAnalyzer()
    token_index = {}
    map_create(token_index, '-')
    freq_dict = dict.fromkeys(token_index, 0)
    morphdict = read_json("../dict/ml_dict.json")
    frequence(morphdict, freq_dict)

    x = [None] * len(input_word)
    mp = morph.parse(input_word)[0]
    length = len(input_word)
    pos = 0
    for char in input_word:
        char = char.lower()
        window = create_window(input_word, pos)
        begin = input_word[:pos + 1]
        end = input_word[pos:]
        result = [char]
        result.append('да' if char in vowels else 'нет')
        result.append(freq_dict.get(char))
        result.extend(window)
        result.extend((mp.tag.POS if mp.tag.POS is not None else "ALL", mp.tag.case, mp.tag.gender, mp.tag.number,
                       mp.tag.tense, length))
        if get_pos:
            result.extend(harris_pos(begin, end, morphdict, mp.tag.POS))
        else:
            result.extend(harris(begin, end, morphdict))
        x[pos] = result
        pos += 1
    change_data(x)

    return x


def create_model(data, labels, iter, learn_rate, name):

    train_data = data[:-200000]
    train_labels = labels[:-200000]
    cat_features = [0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    eval_data = data[-200000:-100]
    eval_labels = labels[-200000:-100]

    train_dataset = Pool(data=train_data, label=train_labels, cat_features=cat_features)
    eval_dataset = Pool(data=eval_data, label=eval_labels, cat_features=cat_features)

    model = CatBoostClassifier(iterations=iter,
                               learning_rate=learn_rate,
                               random_seed=63,
                               eval_metric="Accuracy",
                               save_snapshot=True,
                               snapshot_file='snapshot.bkp',
                               snapshot_interval=10,
                               loss_function='MultiClass',
                               custom_loss=['AUC', 'Accuracy'],
                               train_dir=f"../data/{name}_{iter}_{learn_rate}",
                               early_stopping_rounds=20,
                               )
    model.fit(train_dataset,
              eval_set=eval_dataset,
              verbose=True,
              # plot=True
              )
    model.get_best_iteration()
    model.save_model(f'../data/{name}_{iter}_{learn_rate}_model.json', format='json')

    return model


def get_model_from_file(path):
    from_file = CatBoostClassifier()
    from_file.load_model(path, format='json')

    return from_file


def get_model_score(model):
    preds_model = model.predict(control_dataset_pos if POS else control_dataset)
    score = 0
    for i in range(len(control_labels)):
        print(f"{control_labels[i]} --- {preds_model[i][0]}")
        if control_labels[i] == preds_model[i][0]:
            score += 1
    print(score/len(control_labels))

def get_morph_segmentation_of_word(word):
    model = get_model_from_file("../data/model_pos_150_0.35_model.json")
    x = create_vect_word(word, not POS)
    preds_model = model.predict(x)
    history = preds_model[0][0][-1]
    segmented_word = word[:]

    for idx,char in enumerate(word):
        if preds_model[idx][0][-1] != history:
            segmented_word = segmented_word[:idx] + '/' + segmented_word[idx:]
        history = preds_model[idx][0][-1]

    answ = word + ' | ' + segmented_word

    return answ

# morph = pymorphy2.MorphAnalyzer()
# morphdict = read_json("../dict/ml_dict.json")
# print(harris('п', 'адать', morphdict))
POS = True
MODEL_SCORING = False
cat_features = [0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]


if MODEL_SCORING:
    if POS:
        data_pos = read_json(f"../data/x_pos_new.json")
        labels_pos = read_json("../data/y_pos_new.json")
        control_data_pos = data_pos[-100:]
        control_labels = labels_pos[-100:]
        control_dataset_pos = Pool(data=control_data_pos, cat_features=cat_features)

        model = create_model(data_pos, labels_pos, 150, 0.35, "model_pos")
        print(model.get_best_score())

    else:
        data = read_json("../data/x_new.json")
        labels = read_json("../data/y_new.json")
        control_data = data[-100:]
        control_labels = labels[-100:]
        control_dataset = Pool(data=control_data, cat_features=cat_features)

        model = create_model(data, labels, 200, 0.2, "model")
        print(model.get_best_score())

        model = create_model(data, labels, 200, 0.4, "model")
        print(model.get_best_score())




# seg = get_morph_segmentation_of_word("чиллить")
