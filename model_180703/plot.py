#!/usr/bin/env python
# encoding: utf-8

import matplotlib.pyplot as plt
import numpy as np


if __name__ == '__main__':
    plt.figure()
    x = [x for x in range(200)]
    apt_flex_1 = np.loadtxt('acceptedratio_flexible.txt', usecols=(0, 1))
    apt_flex_1 = np.delete(apt_flex_1, -1, axis=1)
    apt_flex_1 = apt_flex_1[0:200, :]
    # c, r = apt_flex_1.shape
    # print(c, r)
    apt_flex_2 = np.loadtxt('acceptedratio_flexible.txt', usecols=(4,))
    apt_flex_2 = apt_flex_2[0:200]
    apt_flex_2 = apt_flex_2.reshape(-1, 1)
    # c1= apt_flex_2.shape
    # print(c1)
    apt_fixed = np.loadtxt('acceptedratio_fixed.txt', usecols=(4,))
    apt_fixed = apt_fixed[0:200]
    apt_fixed = apt_fixed.reshape(-1, 1)

    accpet_ratio = np.hstack((apt_flex_1, apt_flex_2))
    accpet_ratio = np.hstack((accpet_ratio, apt_fixed))
    # print(accpet_ratio.shape)\

    # colors = ['r', 'g', 'b']
    # legends = {'flexible_src': '*', 'fixed_srcflexible_src': '--'}
    # legends = {'star': '*', 'x_mark': 'x'}

    x = [x for x in range(200)]

    # x.astype(np.int32)
    # y = accpet_ratio[:, 1:3]
    y1 = np.log10(accpet_ratio[:, 1])
    y2 = np.log10(accpet_ratio[:, 2])
    # print(y)

    # for index, t in enumerate(legends.values()):
    plt.plot(x, y1, '-*', color='r')
    plt.plot(x, y2, '-*', color='g')

    plt.legend(['flexible_src', 'fixed_src'], loc=2)
    plt.show()
