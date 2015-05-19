#!/usr/bin/python
from bibliopixel.animation import BaseStripAnim
import math
import time
import threading
import json
import urllib
import cStringIO
from bibliopixel import *
from bibliopixel.drivers.LPD8806 import *
import pycurl
import bibliopixel.colors as colors
f = open('creds.txt','r')
user = f.readline().split('\n')[0]
password = f.readline().split('\n')[0]
count = 50
driver = DriverLPD8806(48, c_order = ChannelOrder.BRG)
leds = LEDStrip(driver)
data = cStringIO.StringIO()
rainbowcolors = [colors.Red, colors.Orange, colors.Yellow, colors.Green, colors.Blue, colors.Violet]
diskcount = 0
offlinecount = 0
p831count = 0
eventcount = 0
quit = 0
timerun = 29
dataerror = 0
class ledControl(threading.Thread):
	def run(self):
		while quit == 0:
			global count
			"""MAX 383, Blue 250"""
			lightvalue = 1075-20*count
			if lightvalue > 250:
				lightvalue=250
			if lightvalue < 0:
				lightvalue=0
			anim = ColorChase(leds, color=colors.wheel_color(lightvalue))
			anim.run(fps=30,max_steps=288)
class ColorChase(BaseStripAnim):
	"""Chase one pixel down the strip."""
	global diskcount
	global offlinecount
	global p831count
	global eventcount
	global timerun
	global dataerror
	def __init__(self, led, color, width=1, start=0, end=-1):
		super(ColorChase, self).__init__(led, start, end)
		self._color = color
		self._width = width
	def setlights(self,substart, count):
		if (count > 8):
			count = 8
		if (count > 0):
			for j in range(count): #8 LEDS per indicator
				self._led.set(substart + j, colors.Red)
			if ((self._step/6)%2): #flash at 5fps
				for k in range(count, 8):
					self._led.set(substart + k, colors.color_scale((255,100,25),255))
			else: #all off
				for k in range(count, 8):
					self._led.set(substart + k, colors.color_scale((255,100,0),0))
		else: #no problems
					self._led.set(substart + (self._step/6)%8, colors.Green)
	def progressbar(self): #Max 288 steps
		numlit = (((30-timerun)*10)/30)
		if (dataerror != 0): #flash red
			if ((self._step/6)%2): #flash at 5fps
				for n in range(10):
					self._led.set(47-n,colors.Red)
			else:
				for n in range(10):
					self._led.set(47-n,colors.color_scale((255,100,0),0))
		else:
			if (timerun < 29): 
				self._led.set(37,colors.Green) #Start indicator
				for m in range(numlit,10):
					self._led.set(47-m,colors.color_scale((255,100,0),0))
				for l in range(numlit):
					self._led.set(47-l,colors.color_scale((255-(255*timerun/30),255-(255*timerun/30),255),255))
			else:
				if ((self._step/6)%2): #flash at 5fps
					for n in range(10):
						self._led.set(47-n,colors.White)
				else:
					for n in range(10):
						self._led.set(47-n,colors.color_scale((255,100,0),0))
	def step(self, amt = 1):
		self._led.all_off() #because I am lazy
		self.setlights(0,diskcount)
		self.setlights(8,offlinecount)
		self.setlights(16,eventcount)
		self.setlights(24,p831count)
		self.progressbar()
		self._step += amt
		overflow = (self._start + self._step) - 288
		if overflow >= 0:
			self._step = overflow
class ColorWipe(BaseStripAnim):
	"""Fill the dots progressively along the strip."""

	def __init__(self, led, color, start=0, end=-1):
		super(ColorWipe, self).__init__(led, start, end)
		self._color = color

	def step(self, amt = 1):
		if self._step == 0:
			self._led.all_off()
		for i in range(amt):
			self._led.set(self._start + self._step - i, self._color)
		self._step += amt
		overflow = (self._start + self._step) - self._end
		if overflow >= 0:
			self._step = overflow
def authenticate():
	postdata = urllib.urlencode([("pro_user[email]", user), ("pro_user[password]",password)])
	c = pycurl.Curl()
	c.setopt(c.URL, "http://vcuhststorit.vcuhs.mcvh-vcu.edu/pro_users/login")
	c.setopt(pycurl.USERAGENT,"Mozilla/5.0 (Windows NT 6.3; WOW64; rv:37.0) Gecko/20100101 Firefox/37.0")
	c.setopt(pycurl.TIMEOUT, 10)
	c.setopt(pycurl.POST, 1)
	c.setopt(pycurl.FOLLOWLOCATION, 0)
	c.setopt(pycurl.POSTFIELDS, postdata)
	c.setopt(pycurl.COOKIEFILE, 'cookie.txt')
	c.setopt(pycurl.COOKIEJAR, 'cookie.txt')
	c.setopt(pycurl.WRITEFUNCTION, lambda x: None) #be silent
	c.perform()
def getData():
	c = pycurl.Curl()
	fetchurl = "http://vcuhststorit.vcuhs.mcvh-vcu.edu/api/alerts.json?filter=recent&date=" + time.strftime("%Y-%m-%d") #only today
	#fetchurl = "http://vcuhststorit.vcuhs.mcvh-vcu.edu/api/alerts.json?filter=recent" #this week
	c.setopt(pycurl.COOKIEFILE, 'cookie.txt')
	c.setopt(pycurl.URL, fetchurl)
	c.setopt(pycurl.HTTPHEADER, ['Accept: application/json'])
	c.setopt(pycurl.VERBOSE, 0)
	c.setopt(pycurl.WRITEFUNCTION, data.write)
	c.perform()

ledControl().start()
while True:
	try:
		print "Getting Data..."
		try:
			getData()
			rdata = json.loads(data.getvalue())
			data = cStringIO.StringIO()
			dataerror = 0
		except:
			print "Cookie expired, refreshing"
			print data.getvalue()
			data = cStringIO.StringIO()
			authenticate()
			getData()
			try:
				rdata = json.loads(data.getvalue())
				dataerror = 0
			except:
				rdata = rdata
				print "Error loading data!"
				dataerror = 1
				raise
		count = 0
		diskcount = 0
		offlinecount = 0
		p831count = 0
		eventcount = 0
		for x in range(len(rdata)):
			if rdata[x]["active"] == 1:
				count = count + 1
				if rdata[x]["lookup_key"] == "disk_free_percent":
					diskcount = diskcount + 1
				if rdata[x]["lookup_key"] == "device_offline":
					offlinecount = offlinecount + 1
				if rdata[x]["lookup_key"] == "event_created":
					eventcount = eventcount + 1
				if "DMService_P831 has been stopped" in rdata[x]["title"]:
					p831count = p831count + 1
		print "Got " + str(count) + " active alert(s):"
		print "      Disk: " + str(diskcount)
		print "   Offline: " + str(offlinecount)
		print "  DMS_P831: " + str(p831count)
		print "     Event: " + str(eventcount)
		for t in range(30):		
			time.sleep(1)
			timerun = t
	except:
		print "Quitting..."
		quit = 1
		raise
