#!/usr/bin/python

import sys
import os
import bitarray
import argparse
from bisect import *
import utils

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--pwm_cycle", help="PWM cycle in samples, default 1024: 1MHz, 1ms cycle", type=int, default=1024)
parser.add_argument("-f", "--filter", help="filter spikes of size, default 1", type=int, default=1)
parser.add_argument("-s", "--pwm_simple", help="simple PWM value calculation (faster), default off", action="store_true")
parser.add_argument("-o", "--output", help='output filename, default "out.png"', default='')
parser.add_argument('filename', help='filename, default "out.bin"',nargs='?', default="out.bin")
args = parser.parse_args()


#read binary file
b = bitarray.bitarray()
with open(args.filename, 'rb') as fh:
    b.fromfile(fh)

#extract signal from bytestream (edit if necessary)
_,_,_,out,Y_step,Y_dir,X_step,X_dir = [ b[i::8] for i in range(8)]
#_,_,_,out,Y_dir,Y_step,X_step,X_dir = [ b[i::8] for i in range(8)]


#filter signals (remove spikes of size 2)
print 'filter signals:'
for s in [out, Y_step,Y_dir,X_step,X_dir]:
    utils.filter_signal(s, args.filter)

xp = utils.find_pulses(X_step, 'x')
yp = utils.find_pulses(Y_step, 'y')
p = xp + yp

if args.pwm_simple:
    p += utils.find_pulses(out, 's')
else:
    print 'calculate PWM output integral'
    out_integral = utils.signal_integral(out)
    print 'integral calculation done'

p = sorted(p)

def draw(points, x_off=0,y_off=0, scycle=1, img = None):
    x,y,s,si,xmin,xmax,ymin,ymax,smax=x_off,y_off,0,0,100000,0,100000,0,0
    for i,tag,d,_ in points:
        if tag == 'x':
            if not X_dir[i]: x+=1
            else: x-=1
        if tag == 'y':
            if Y_dir[i]: y+=1
            else: y-=1
        if tag == 's':
            s = d
            si = i
        if i-si > scycle:
            si += scycle
            s -= scycle
        if s < 0: s = 0

        if img is not None:
            if not args.pwm_simple and i+scycle < len(out_integral): v = out_integral[i+scycle] - out_integral[i]
            else: v = s
            if v > scycle: v = scycle
            v = v*255/scycle
            b = 0
            if X_dir[i]: b = 30
            img[x,y] = (v,v,b)

        xmin,xmax = min(xmin, x), max(xmax, x)
        ymin,ymax = min(ymin, y), max(ymax, y)
        smax = max(s, smax)
    return xmin,xmax,ymin,ymax,smax

xmin,xmax,ymin,ymax,smax = draw(p)
print 'xm:',xmin,xmax
print 'ym:',ymin,ymax
print 'sm:',smax


###### display 
from PIL import Image

img = Image.new( 'RGB', (xmax-xmin+1,ymax-ymin+1), (10,10,0)) # create a new black image
pixels = img.load() # create the pixel map
draw(p, -xmin,-ymin, args.pwm_cycle, pixels)

output = args.output
if len(output) == 0:
    output = os.path.splitext(args.filename)[0] + '.png'
print 'saving to file:', output
img.save(output)
img.show()
