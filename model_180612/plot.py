#!/usr/bin/env python
# encoding: utf-8

import matplotlib as mpl
import matplotlib.pyplot as plt

if __name__ == '__main__':
    mpl.rcParams['font.family'] = 'sans-serif'
    mpl.rcParams['font.sans-serif'] = 'NSimSun,Times New Roman'

    font1 = {'family': 'Times New Roman',
             'weight': 'normal',
             'size': 9,
             }

    font2 = {'family': 'Times New Roman',
             'weight': 'normal',
             'size': 14,
             }

    x1 = []
    y1 = []
    y3 = []

    x2 = []
    y2 = []
    y4 = []

    # x1 = [float(l.split()[4]) for l in open("request_2.txt")]
    # y1 = [float(l.split()[int(l.split()[4])+5]) for l in open("request_2.txt")]
    # y3 = [float(l.split()[int(l.split()[4])+5]) for l in open("request.txt")]

    x2 = [float(k.split()[2]) for k in open("request_deadline_2.txt")]
    y2 = [float(k.split()[9]) for k in open("request_deadline_2.txt")]
    y4 = [float(k.split()[9]) for k in open("request_deadline.txt")]

    # plt.plot(x1, y1, color='black')
    # plt.plot(x1, y1, 'o', color='red', label='$Flexible$')
    # y3 = range(0, len(y1))
    # plt.plot(x1, y3, color='black')
    # plt.plot(x1, y3, 'o', color='blue', label='$Fixed$')

    plt.plot(x2, y2, color='black')
    plt.plot(x2, y2, 'o', color='red')
    y4 = range(0, len(y2))
    plt.plot(x2, y4, color='black')
    plt.plot(x2, y4, 'o', color='blue')


    #
    # # plt.plot(x2, y2, color='black')
    # # plt.plot(x2, y2, 'o', color='blue')
    #
    # plt.xlabel('destination')
    plt.xlabel('deadline')
    plt.ylabel('RUNTIME')

    # plt.legend()
    plt.show()