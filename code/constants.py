vowels = 'ауоыиэяюёе'
vowels_1 = 'еёюя'
prefixes_1 = ('дез', 'контр', 'пан', 'пост', 'суб', 'супер', 'транс', 'ак', 'сверх', 'меж', 'интер', 'экс')
voiced_consonant = 'бвгджзлмнр'
dumb_consonant = 'пкстфхцчшщ'
type_dict = {
    's': r'(?:S|WC)',
    'p': r'P',
    'ps': r'(?:S|WC|P)'
}
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


signs = {'ъ', 'ь'}
alphabet = ('а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 'о', 'п',
            'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ы', 'э', 'ю', 'я')

consonants = 'бвгджзйклмнпрстфхцчшщ'
type_dict_ml = {
    's': r'(?:S|WC)',
    'p': r'P',
    'i': r'I',
    'r': r'ROOT',
    'e': r'E'}