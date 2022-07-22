#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 10 09:37:14 2018

@author: pavan
"""

class Color:
    
    @staticmethod
    def isColor(value):
        return type(value) is type((0,0,0)) and len(value) == 3 \
            or type(value) is int
    
    @staticmethod
    def fromBitValue(bitValue):
        for i in range(0, 12):
            if ((bitValue >> i) & 1) == 1:
                return Color.fromIndex(i)
        return (0, 0, 0)
    
    @staticmethod
    def fromIndexNormalized(index):
        color = Color.hexFromIndex(index % 16)
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        return (float(r) / 255, float(g) / 255, float(b) / 255)
    
    @staticmethod
    def fromIndex(index):
        color = Color.hexFromIndex(index % 16)
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        return (r, g, b)
        
    @staticmethod
    def hexFromIndex(index):
        # see also: http://www.farb-tabelle.de/en/table-of-color.htm
        if index == 0:
            # mediumslateblue
            return 0x7b68ee
        elif index == 1:
            # yellowgreen
            return 0x9ACD32
        elif index == 2:
            # deeppink
            return 0xFF1493
        elif index == 3:   
            # darkgoldenrod1
            return 0xFFB90F
        elif index == 4:
            # dodgerblue
            return 0x1E90FF
        elif index == 5:   
            # lawngreen
            return 0x7CFC00
        elif index == 6:
            # orangered
            return 0xFF4500
        elif index == 7:
            # gold
            return 0xFFD700
        elif index == 8:
            # aquamarine
            return 0x7FFFD4
        elif index == 9:
            # seagreen
            return 0x2E8B57
        elif index == 10:
            # tomato
            return 0xff6347
        elif index == 11:
            # navojawhite2
            return 0xEECFA1
        elif index == 12:
            # skyblue
            return 0x87CEEB
        elif index == 13:
            # olivedrab
            return 0x6B8E23
        elif index == 14:
            # orange
            return 0xff6347
        elif index == 15:
            # yellow
            return 0xFFFF00
        else:
            return 0
        