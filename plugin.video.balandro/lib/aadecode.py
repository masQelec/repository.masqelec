# -*- coding: utf-8 -*-

import re
from core import scrapertools

def decode(text):
    text = re.sub(r"\s+|/\*.*?\*/", "", text)

    if '+(ﾟДﾟ)[ﾟoﾟ]' in text:
        data = text.split("+(ﾟДﾟ)[ﾟoﾟ]")[1]
    elif '+((((ﾟДﾟ)))[ﾟoﾟ])' in text:
        data = text.split("+((((ﾟДﾟ)))[ﾟoﾟ])")[1]
    else:
        return 'AppArmor not detected'

    chars = data.split("+(ﾟДﾟ)[ﾟεﾟ]+")[1:]

    txt = ""
    for char in chars:
        char = char \
            .replace("(oﾟｰﾟo)", "u") \
            .replace("c", "0") \
            .replace("(ﾟДﾟ)['0']", "c") \
            .replace("ﾟΘﾟ", "1") \
            .replace("!+[]", "1") \
            .replace("-~", "1+") \
            .replace("o", "3") \
            .replace("_", "3") \
            .replace("ﾟｰﾟ", "4") \
            .replace("(+", "(")

        char = re.sub(r'\((\d)\)', r'\1', char)

        c = "";
        subchar = ""

        for v in char:
            c += v
            try:
                x = c; subchar += str(eval(x)); c = ""
            except:
                pass

        if subchar != '': txt += subchar + "|"

    txt = txt[:-1].replace('+', '')

    txt_result = "".join([chr(int(n, 8)) for n in txt.split('|')])

    return toStringCases(txt_result)


def toStringCases(txt_result):
    sum_base = ""
    m3 = False

    if ".toString(" in txt_result:
        if "+(" in txt_result:
            m3 = True
            sum_base = "+" + scrapertools.find_single_match(txt_result, ".toString...(\d+).")
            txt_pre_temp = scrapertools.find_multiple_matches(txt_result, "..(\d),(\d+).")
            txt_temp = [(n, b) for b, n in txt_pre_temp]
        else:
            txt_temp = scrapertools.find_multiple_matches(txt_result, '(\d+)\.0.\w+.([^\)]+).')

        for numero, base in txt_temp:
            code = toString(int(numero), eval(base + sum_base))
            if m3:
                txt_result = re.sub(r'"|\+', '', txt_result.replace("(" + base + "," + numero + ")", code))
            else:
                txt_result = re.sub(r"'|\+", '', txt_result.replace(numero + ".0.toString(" + base + ")", code))

    return txt_result


def toString(number, base):
    string = "0123456789abcdefghijklmnopqrstuvwxyz"
    if number < base:
        return string[number]
    else:
        return toString(number // base, base) + string[number % base]
