from collections import defaultdict
symbols = list(input())
symbol_dict = {')':'(',
              ']':'[',
              '>':'<',
              '}':'{'}
dict_temp = defaultdict(int)
def is_correct(symbols):
    for symbol in enumerate(symbols):
        if symbol[1] in '([<{':
            dict_temp[symbol[1]] += 1
        elif symbol[1] in ')]>}':
            dict_temp[symbol_dict[symbol[1]]] -= 1
            if dict_temp[symbol_dict[symbol[1]]] < 0:
                return symbol[0] + 1
    return True
print(is_correct(symbols))
