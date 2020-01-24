import typing
import json
roots = {'чин', 'мен', 'нит', 'ым', 'ус', 'ух', 'ос', 'ост', 'бес', 'де', 'воз', 'уч',
		 'г', 'шн', 'мя', 'ки', 'яр', 'й', 'ман', 'и', 'ур', 'он', 'ши', 'тур', 'ну', 'лин', 'ем',
		 'меж', 'ше', 'ал', 'ах', 'ил', 'ох', 'ор', 'очн', 'сн', 'тор', 'ул', 'уш', 'вор', 'ком', 'лиц', 'у',
		 'ком'}
roots_as_pref = {'во', 'вне', 'ба', 'бес', 'де', 'вы', 'вс', 'до', 'ин', 'за', 'микро', 'кило', 'макро', 'контр',
				 'между', 'мимо', 'против', 'низ', 'пан'}
roots_as_suff = {'ка', 'вш', 'ть', 'ку', 'им', 'ук', 'ловк', 'ч', 'к', 'об', 'па', 'чь', 'куда', 'ник'}

roots2 = {'под', 'кто', 'по', 'пост', 'пре', 'д', 'ш', 'раз', 'рас', 'роз', 'рос', 'со'}


def create_root_dict(change_roots):
	tmp = {}
	for key, val in change_roots.items():
		if isinstance(val, str) and not change_roots.get(val):
			tmp.update({val: key})
		elif isinstance(val, list):
			for i in val:
				if not change_roots.get(i):
					a = val.copy()
					a.remove(i)
					a.append(key)
					tmp.update({i: a})
	change_roots.update(tmp)


change_roots = {
	"воз": "вез",
	"нос": ["нес", "нош", "наш"],
	"по": "пе",
	"брос": ["брас", "брош"],
	"кон": "кан",
	"во": "вы",
	"ши": "ше",
	"бер": ["бир", "бор"],
	"сох": ["сых", "сух"],
	"рот": "рт",
	"день": "дн",
	"рук": "руч",
	"друг": ["друж", "друз"],
	"вод": ["вож", "вожд", "вод"],
	"свет": ["свеч", "свещ"],
	"пестр": "испещ",
	"вед": "вес",
	"бреш": "брех",
	"мет": "мес",
	"люб": "любл",
	"куп": "купл",
	"лов": "ловл",
	"граф": "графл",
	"корм": "кормл",
	"жа": ["жим", "жин"],
	# "жа": "жм",
	# "жим": "жм",
	# "жа": "жн",
	# "жин": "жн",
	"слеп": "слепл",
	"воздух": "воздуш",
	"громозд": "громожд",
	"драж": "дроз",
	"гар": "гор",
	"клан": "клон",
	"твар": "твор",
	"зар": "зор",
	"плав": "плов",
	"раст": ["рощ", "рос", "ращ"],
	"скак": "скоч",
	"лаг": "лож",
	"кас": "кос",
	"мак": ["мок", "моч"],  # мач
	"мог": ["мож", "моч"],
	"жег": ["жиг", "жеч"],
	"стел": "стил",
	"блист": "блест",
	"мир": "мер",
	"тир": "тер",
	"дир": "дер",
	"пир": "пер",
	"чит": ["чет", "чес"],
	"мин": "мя",
	"поним": "поня",
	"ним": "ня",
	"помин": "память",
	"чин": "ча",
	"кля": "клин",
	"работ": "рабат",
	"тро": "траг",
	"сво": "сва",
	"дво": "два",
	"досто": "доста",
	"булк": "булоч",
}


def display2(display_dict: typing.Dict[str, typing.Any]) -> None:
	txt = json.dumps(display_dict, ensure_ascii=False, indent=2)
	print(txt)


letter_change = [
	['г', 'ж', 'з'],
	['д', 'ж', 'жд'],
	['к', 'ч', 'ц'],
	['щ', 'ск'],
	['з', 'ж'],
	['г', 'ж'],
	['с', 'ш'],
	['х', 'ш'],
	['ц', 'ч'],
	['н', 'ш'],
	['ст', 'щ'],
	['жд', 'ж'],
	['жд', 'д'],
	['ск', 'щ'],
	['бл', 'б'],
	['пл', 'п'],
	['мл', 'м'],
	['вл', 'в'],
	['фл', 'ф'],
	['ок', 'ец'],
	['ак', 'ат'],
	['иц', 'ит'],
	['ыч', 'ыт'],
	['ач', 'ат'],
	['ет', 'ещ'],
	['ет', 'еч'],
	['ещ', 'еч'],
	['аз', 'аж'],
	['оз', 'ож'],
]
create_root_dict(change_roots)
# display2(change_roots)


def work_letter_change(letter_change, letter):
	arr = []
	for i in letter_change:
		if letter in i:
			pair = set(i).difference({letter})
			arr.append(pair)
	return arr