def flection(lex_neighb, tags):
    tags = str(tags)
    tags = re.sub(',[AGQSPMa-z-]+? ', ',', tags)
    tags = tags.replace("impf,", "")
    tags = re.sub('([A-Z]) (plur|masc|femn|neut|inan)', '\\1,\\2', tags)
    tags = tags.replace("Impe neut", "")
    tags = tags.split(',')
    print(tags)
    tags_clean = []
    for t in tags:
        if t:
            if ' ' in t:
                t1, t2 = t.split(' ')
                t = t2
            tags_clean.append(t)
    tags = frozenset(tags_clean)
    prep_for_gen = morph.parse(lex_neighb)
    ana_array = []
    for ana in prep_for_gen:
        if ana.normal_form == lex_neighb:
            ana_array.append(ana)
    for ana in ana_array:
        try:
            flect = ana.inflect(tags)
        except:
            print(tags)
            return None
        if flect:
            word_to_replace = flect.word
            return word_to_replace
    return None