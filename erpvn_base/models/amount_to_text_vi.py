# -*- encoding: utf-8 -*-
to_19_vi = (u'không', u'một', u'hai', u'ba', u'bốn', u'năm', u'sáu',
          u'bảy', u'tám', u'chín', u'mười', u'mười một', u'mười hai', u'mười ba',
          u'mười bốn', u'mười lăm', u'mười sáu', u'mười bảy', u'mười tám', u'mười chín')
tens_vi = (u'hai mươi', u'ba mươi', u'bốn mươi', u'năm mươi', u'sáu mươi', u'bảy mươi', u'tám mươi', u'chín mươi')
denom_vi = (u'',
          u'nghìn', u'triệu', u'tỉ', u'nghìn tỉ', u'triệu tỉ',
          u'tỉ tỉ', u'nghìn tỉ tỉ', u'triệu tỉ tỉ', u'tỉ tỉ tỉ', u'Nonillion',
          u'Décillion', u'Undecillion', u'Duodecillion', u'Tredecillion', u'Quattuordecillion',
          u'Sexdecillion', u'Septendecillion', u'Octodecillion', u'Icosillion', u'Vigintillion')

# convert a value < 100 to Vietnamese.
def _convert_nn_vi(val):
    if val < 20:
        return to_19_vi[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens_vi)):
        if dval + 10 > val:
            if (val % 10) == 1:
                return dcap + u' mốt'
            elif (val % 10) == 5:
                return dcap + u' lăm'
            elif val % 10:
                return dcap + u' ' + to_19_vi[val % 10]
            return dcap

# convert a value < 1000 to Vietnamese, special cased because it is the level that kicks 
# off the < 100 special case.  The rest are more general.  This also allows you to
# get strings in the form of 'forty-five hundred' if called directly.
def _convert_nnn_vi(val):
    word = ''
    (mod, rem) = (val % 100, val // 100)
    if rem > 0:
        word = to_19_vi[rem] + u' trăm'
        if mod > 0:
            word = word + u' '
    if mod > 0:
        if mod < 10:
            word = word + u'lẻ '
        word = word + _convert_nn_vi(mod)
    return word

def vi_number(val):
    if val < 100:
        return _convert_nn_vi(val)
    if val < 1000:
         return _convert_nnn_vi(val)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom_vi))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            if l < 10:
                ret = _convert_nn_vi(l) + u' ' + denom_vi[didx]
            else:
                ret = _convert_nnn_vi(l) + u' ' + denom_vi[didx]
            if r > 0:
                ret = ret + u' ' + vi_number(r)
            return ret

def amount_to_text_vi(number, currency='VND'):
    if currency == 'VND':
        currency = u'đồng'
    number = '%.2f' % number
    units_name = currency
    list = str(number).split('.')
    start_word = vi_number(abs(int(list[0])))
    cents_number = int(list[1])
    end_word = u''
    if cents_number > 0:
        end_word = u' ' + vi_number(int(list[1]))

    cents_name = (cents_number > 1) and u' xu' or u''
    final_result = start_word + u' ' + units_name + end_word + cents_name
    return final_result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

