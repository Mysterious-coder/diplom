#   '',
verb_suffixes = {
    'from_verb':  [("ир", "ова"), "и", ("нич", "а"), "ова", ("ств", "ов", "а"), "а", "я",  "е", "ова",
                   "о", "ну", "ен", ("из", "ир", "ова"), "ка", "ева",
                   "ся", "сь",  ("и", "ть",  "ся"),  ("а",  "ть",  "ся"),  ("ыва",  "ть",  "ся"),
                   ("я",  "ть",  "ся"), ("ова",  "ть",  "ся"), 'ыва'
                   # 'ествова', 'ирова', 'изирова', 'ича', 'нича',
                   # 'ствова', 'ыва',
                   # 'ать', 'еть', 'евать', 'ить', 'ировать', 'изировать', 'ичать', 'кать', 'нуть', 'ничать', 'овать',
                   # 'оть', 'ствовать', 'ывать', 'ять'
                   ],
    'from_noun':  [
                   'и', 'нича', 'ова', 'ствова', 'е', 'а',
                   # 'ить', 'ничать', 'овать', 'ствовать', 'еть', 'ать'
                   ],
    'from_adj':   []
}

suff_noun = {'адь', 'ак', 'алей', 'ан', 'ян', 'ин', 'ар', 'арь', 'ач', 'ени', 'ани',
             'еств', 'ств', 'есть', 'ость', 'ец', 'к', 'янк', 'изм', 'изн', 'ик',
             'ник', 'ат', 'ист', 'иц', 'ниц', 'их', 'л', 'лк', 'ль', 'н', 'щ',
             'щиц', 'ог', 'г', 'от', 'ет', 'р', 'тель', 'итель', 'ун', 'чиц', 'чик',
             'щик', 'ыш', 'ис', 'а', 'ни', 'ем', 'яж', 'яг', 'ек', 'ёнк', 'й'}

suff_adj = {'ал', 'ел', 'ан', 'ян', 'аст', 'ат', 'ев', 'ов', 'еват', 'оват', 'ен', 'енн',
            'онн', 'енск', 'инск', 'ив', 'лив', 'чив', 'ин', 'ист', 'ит', 'овит', 'к', 'л', 'н', 'шн',
            'тельн', 'уч', 'юч', 'яч', 'чат', 'ск', 'ир', 'я', 'ем', 'яц', 'ящ', 'й'}

suff_verb = {'а', 'я', 'ка', 'к', 'е', 'ев', 'ов', 'и', 'нич', 'ну', 'ств', 'ся',
             'ать', 'ять', 'кать', 'еть', 'евать', 'овать', 'ить', 'ничать', 'нуть',
             'ствовать', 'ян'}

suff_advb = {'а', 'е', 'и', 'жды', 'либо', 'нибудь', 'о', 'то', 'учи', 'ючи', 'ом',
             'ком', 'ем', 'ём', 'я', 'у', 'ю', 'его', 'к', 'й'}

suff_name = {'либо', 'нибудь', 'то'}  # , 'кто', 'его'}

suff_prt = {'ущ', 'ющ', 'ащ', 'ящ', 'вш', 'ш', 'ем', 'ом',
            'им', 'нн', 'енн', 'т', 'н', 'ен', 'енн',
            'ён', 'ённ', 'т', 'ыва'}

suff_grnd = {'а', 'я', 'в', 'вш', 'вши', 'ши', 'учи'}

suff_numr = {'дцать', 'дцат', 'на', 'о', 'ер'}

morph_wordchange = ['а', 'в', 'е', 'ее', 'ей', 'ше', 'учи', 'ши', 'вши', 'л', 'им', 'ом', 'нн',
                    'енн', 'ённ', 'т', 'ш', 'вш', 'ащ', 'ущ']

morph_interfixes = ['а', 'ехъ', 'и', 'о', 'у', 'ух', 'ех']

morph_wordcreate = {'инск', 'овиан', 'очк', 'am', 'инит', 'ур', 'овенн', 'ность', 'ун', 'охоньки', 'оньк',
                    'ышком', 'елин', 'ачей', 'ива', 'альн', 'еств', 'няком', 'ариус', 'уч', 'ох', 'ительн',
                    'ловк', 'в', 'лк', 'ствова', 'ашн', 'д', 'яжн', 'ович', 'овин', 'енек', 'ионн',
                    'бин', 'тв', 'ённ', 'тор', 'нит', 'ышек', 'тян', 'шк', 'ичка', 'енец', 'йск', 'унк',
                    'ишом', 'итет', 'иян', 'очки', 'мейстер', 'б', 'чук', 'овчан', 'иад', 'урк', 'юк', 'up',
                    'ич', 'алей', 'ну', 'орн', 'менн', 'иат', 'ни', 'иничн', 'сн', 'енци', 'отк', 'но',
                    'ебн', 'обн', 'амент', 'ичн', 'ол', 'ан', 'ую', 'яка', 'ёж', 'инец', 'шн', 'ичниц',
                    'няк', 'евск', 'их', 'ениц', 'ежк', 'ядь', 'арн', 'ки', 'лин', 'лищ', 'евт', 'члив',
                    'к', 'льн', 'итель', 'жды', 'анк', 'ал', 'овиц', 'иком', 'етк', 'ку', 'ятн', 'охонько',
                    'л', 'ш', 'овлив', 'истичес', 'ованн', 'ани', 'ышк', 'анин', 'ырь', 'овец', 'лезск',
                    'бищ', 'овск', 'ошеньки', 'овищ', 'ошенько', 'анск', 'льщин', 'ис', 'ени', 'ач', 'аг',
                    'ествова', 'йн', 'ист', 'мент', 'ц', 'стви', 'аж', 'омец', 'иот', 'атник', 'ец',
                    'онер', 'o', 'ейск', 'тельств', 'чив', 'иш', 'чонок', 'ть', 'ачий', 'ель', 'ашк', 'ий',
                    'ейш', 'анс', 'ому', 'лиц', 'ко', 'айк', 'ерк', 'еник', 'овниц', 'имость', 'уш', 'ен',
                    'ляв', 'ажды', 'ах', 'уй', 'еющ', 'ственн', 'ниц', 'евн', 'енн', 'тур', 'езн', 'ез', 'овств',
                    'с', 'е', 'анн', 'атарь', 'еск', 'ишн', 'ческ', 'ав', 'нск', 'он', 'ёшк', 'ощав', 'ые',
                    'идальн', 'инг', 'жан', 'ами', 'e', 'вор', 'ачк', 'онько', 'овн', 'т', 'ом', 'ечк',
                    'евик', 'надцать', 'ова', 'ейн', 'ник', 'ат', 'ушки', 'ютк', 'аш', 'арий', 'ант', 'ства',
                    'енность', 'онн', 'нича', 'озн', 'очниц', 'тельниц', 'ейник', 'ой', 'ош', 'овато', 'ад',
                    'усеньк', 'тельск', 'истик', 'ут', 'дцать', 'льц', 'уном', 'ою', 'ей', 'енько', 'уальн',
                    'ушк', 'евич', 'инк', 'тяй', 'еньку', 'инств', 'ул', 'ин', 'очн', 'смен', 'ай', 'ирова',
                    'овник', 'ак', 'ет', 'ч', 'ированн', 'ынь', 'ук', 'ел', 'им', 'чан', 'эзск', 'овани',
                    'иальн', 'amyp', 'остью', 'льниц', 'льник', 'авк', 'ы', 'ка', 'ым', 'ущ', 'итор', 'ик',
                    'ошь', 'униц', 'ианск', 'овизн', 'ейк', 'аци', 'ационн', 'ар', 'ён', 'ое', 'арник',
                    'ибельн', 'инчан', 'отн', 'овит', 'чак', 'нин', 'очко', 'арь', 'аст', 'знь', 'еньки',
                    'ками', 'льщик', 'оз', 'аль', 'ичан', 'ащ', 'ильн', 'изн', 'ическ', 'ург', 'як', 'ери',
                    'уган', 'ульк', 'лив', 'изаци', 'нюшки', 'атниц', 'ент', 'тельн', 'изм', 'оньку', 'ор',
                    'онк', 'овал', 'ив', 'вск', 'овщин', 'ану', 'ичий', 'овщик', 'щин', 'щик', 'нь',
                    'х', 'ытьб', 'ивн', 'ёжь', 'есс', 'ича', 'ошеньк', 'ок', 'ком', 'овий', 'овк', 'онек',
                    'ень', 'оид', 'ыль', 'иозн', 'оват', 'мен', 'орий', 'от', 'ус', 'елив', 'онок', 'ици',
                    'ци', 'арад', 'ишк', 'ацк', 'итян', 'оныш', 'ык', 'ёл', 'ельн', 'онизм', 'нич', 'н',
                    'атин', 'ев', 'яр', 'об', 'из', 'изирова', 'оль', 'емент', 'чк', 'снь', 'енск', 'ецк',
                    'атай', 'имск', 'лец', 'абельн', 'ушок', 'тель', 'чик', 'ль', 'изова', 'ер', 'чат',
                    'итур', 'уг', 'ыг', 'лан', 'авец', 'оть', 'ти', 'ман', 'тость', 'нн', 'атор', 'a',
                    'чин', 'айш', 'кой', 'иан', 'мя', 'охоньк', 'оту', 'ость', 'ыч', 'анек', 'нность',
                    'нци', 'ов', 'ищ', 'ышн', 'ках', 'иц', 'ств', 'ешниц', 'нец', 'ийск', 'ональн', 'ит',
                    'овь', 'ск', 'унюшки', 'унск', 'ил', 'ир', 'ни', 'ятор', 'ят', 'ющ', 'ва', 'енок',
                    'яци', 'еньк', 'оч', 'ёр', 'уз', 'яч', 'ёнок', 'ярн', 'зн', 'я', 'яц', 'няц', 'яж',
                    'унь', 'юшк', 'иньк', 'ифик', 'ян', 'ёнк', 'ид', 'ань', 'ыр', 'ос', 'ыва', 'еч',
                    'ичк', 'ёз', 'ост', 'ын', 'ерий', 'ём', 'ящ', 'еб', 'й', 'з', 'атр', 'ац', 'ёхоньк',
                    'ехоньк'
                    # 'а', 'о',  'у', 'ух',  'и',
                    }
