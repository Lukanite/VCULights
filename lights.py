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
			anim.run(fps=5,max_steps=48)
class ColorChase(BaseStripAnim):
	"""Chase one pixel down the strip."""
	global diskcount
	global offlinecount
	global p831count
	global eventcount
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
			if (self._step%2): #flash
				for k in range(count, 8):
					self._led.set(substart + k, colors.color_scale((255,100,25),255))
			else: #all off
				for k in range(count, 8):
					self._led.set(substart + k, colors.color_scale((255,100,0),0))
		else: #no problems
					self._led.set(substart + self._step%8, colors.Green)
	def step(self, amt = 1):
		self._led.all_off() #because I am lazy
		for i in range(self._width):
			self._led.set((self._start + self._step + i + 0)%12 + 36, colors.Red)
			self._led.set((self._start + self._step + i + 2)%12 + 36, colors.color_scale((255,100,25),255))
			self._led.set((self._start + self._step + i + 4)%12 + 36, colors.Orange)
			self._led.set((self._start + self._step + i + 6)%12 + 36, colors.Green)
			self._led.set((self._start + self._step + i + 8)%12 + 36, colors.Blue)
			self._led.set((self._start + self._step + i + 10)%12 + 36, colors.Violet)
		self.setlights(0,diskcount)
		self.setlights(8,offlinecount)
		self.setlights(16,eventcount)
		self.setlights(24,p831count)
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
	fetchurl = "http://vcuhststorit.vcuhs.mcvh-vcu.edu/api/alerts.json?filter=recent" #this week
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
		except:
			print "Cookie expired, refreshing"
			print data.getvalue()
			data = cStringIO.StringIO()
			authenticate()
			getData()
		try:
			rdata = json.loads(data.getvalue())
		except:
			rdata = rdata
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
		time.sleep(30)
	except:
		print "Quitting..."
		quit = 1
		raise
