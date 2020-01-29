import re
def parse(filename: str) -> None:
    with open(filename, 'r') as file:
        start = False
        arr_lines = []
        for line in file.readlines():
            if start and 'нареч.' in line:
                line = line.rstrip('\n')
                line = line.replace("'", '')
                line = line.replace(',', ' ')
                line = line.replace('/-', '~/')
                line = line.replace('-', '~/')
                line = line.replace('ё', 'е')
                arr = line.split(' | ')
                arr[0] = re.sub(r'[\d]+', '', arr[0])
                arr[1] = re.match(r"([\S]+)", arr[1]).group(0)
                arr[1] = re.sub(r'[\d]+', '', arr[1])
                if arr[1].endswith('ь'):
                    arr[1] = arr[1] + '/'
                arr[1] = re.split(r'/', arr[1])
                arr_lines.append(arr)

            elif line == "START\n":
                start = True
    for i in arr_lines:
        print(i[0], i[1])
parse("../dict/MorphDictTikhonov.txt")