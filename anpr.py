#!/usr/bin/python
import beanstalkc
import json
from pprint import pprint
import sqlite3
import RPi.GPIO as GPIO
import requests
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(18,GPIO.OUT)

ifttt_webhook_key = "__YOUR_IFTTT_KEY__"

# Specify the Beanstalk Queue that the ALPR Daemon uses to store its results
beanstalk = beanstalkc.Connection(host='localhost', port=11300)

# Watch the "alprd" tube, this is where the plate data is.
beanstalk.watch('alprd')

# Define function to wipe out queue - used when first run, and before each sleep
def empty_queue(beanstalk):
	# Clean out the tube to make sure we're starting afresh
	while True:
		jobWipe = beanstalk.reserve(timeout=0)
	
		if jobWipe is None:
			break
		else:
			jobWipe.delete()

# Clean out the tube to make sure we're starting afresh
empty_queue(beanstalk)
			
# Connect to SQLite database - this contains current car location state, number plate to watch for, etc.
conn = sqlite3.connect("/home/pi/anpr.db")
conn.row_factory = sqlite3.Row

cur = conn.cursor()
cur.execute("SELECT car, isHome FROM anpr_cars WHERE id = 1")
 
row = cur.fetchone()
plate_required = row['car']
car_is_home = row['isHome']
conn.close()

# Set LED status based on last-known status
if car_is_home == 1:
	GPIO.output(18,GPIO.HIGH)
else:
	GPIO.output(18,GPIO.LOW)
 
print "Looking for car with %s number plate." % plate_required
print "Car Is Home Boolean status: %s" % car_is_home

print "Sleeping for 5 seconds to give the system a chance to assess if the car is here or not right now."
time.sleep(5)

# Loop forever
while True:

	# Wait for a second to get a job.  If there's a job, process it and delete it from the queue.  
	# If not, go back to sleep
	job = beanstalk.reserve(timeout=1.0)
	

	if job is None:
		# No jobs - which means no car plates can be seen - so the car is "gone".
		# Set car's status to away, if it's not already
		if car_is_home == 1:
			print "Detected car has left."
			
			# Set local variable
			car_is_home = 0
			
			# Turn LED off
			GPIO.output(18,GPIO.LOW)
			
			# Update field in SQLite database
			conn = sqlite3.connect("/home/pi/anpr.db")
			cur = conn.cursor()
			cur.execute("UPDATE anpr_cars SET isHome = %s WHERE id = 1" % car_is_home)
			conn.commit()
			conn.close()
			
			# Activate IFTTT Applet for car gone (uncomment printing url/http code for debugging)
			webhook_url = 'https://maker.ifttt.com/trigger/car_gone/with/key/%s' % ifttt_webhook_key
			response = requests.post(webhook_url)
			#print webhook_url
			#print response.status_code
	
	else:
		
		plates_info = json.loads(job.body)

		#pprint(plates_info)
		plate_spotted = plates_info['results'][0]['plate']
		plates_info = None
		
		if plate_spotted == plate_required and car_is_home == 0:
			print "Car ARRIVED! - %s" % plate_spotted
			
			# Set local variable
			car_is_home = 1
			
			# Turn LED off
			GPIO.output(18,GPIO.HIGH)
			
			# Update field in SQLite database
			conn = sqlite3.connect("/home/pi/anpr.db")
			cur = conn.cursor()
			cur.execute("UPDATE anpr_cars SET isHome = %s WHERE id = 1" % car_is_home)
			conn.commit()
			conn.close()
			
			# Activate IFTTT Applet for car arrived (uncomment printing url/http code for debugging)
			webhook_url = 'https://maker.ifttt.com/trigger/car_arrived/with/key/%s' % ifttt_webhook_key
			response = requests.post(webhook_url)
			#print webhook_url
			#print response.status_code
			
			#exit()
			
			# Pause 10 seconds before re-assessing tube, to give a chance for "car's still here"
			print "Now sleeping for 10 seconds..."
			job.delete()
			empty_queue(beanstalk)
			time.sleep(10)
			
		elif plate_spotted == plate_required and car_is_home == 1:
			print "Car is still here... - %s" % plate_spotted
			print "(Sleeping again for 10 seconds...)"
			job.delete()
			empty_queue(beanstalk)
			time.sleep(10)
		
		else:
			print "Another plate spotted: %s" % plate_spotted

			# Delete the job from the queue now that we have processed it
			job.delete()