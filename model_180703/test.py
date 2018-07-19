import pandas

if __name__ == '__main__':
    a = {}

    a = {'x': {'a': 2.0, 'b': 1.0},
         'c': {'y': 2.0},
         'b': {'c': 0, 'd': 1.0},
         'y': {},
         'd': {'e': 1.0},
         'e': {'y': 1.0},
         'a': {'c': 2.0}}
    df = pandas.DataFrame(a).T.fillna(0)
    print(df['a']['b'])

