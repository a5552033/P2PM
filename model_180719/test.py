from __future__ import print_function
from __future__ import division
import networkx as nx
import matplotlib.pyplot as plt
import pandas
from node import *
from link import *
import copy
import math
import random
import time
import numpy as np
from kShortestPath import *
from genRequest import *

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
    print(df)
    print(df['a']['b'])