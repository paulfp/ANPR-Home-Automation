# ANPR Home Automation
This repo contains a Python script which can be used as the brains of an ANPR Home Automation system which, in this example, turns on the light in your hallway when the system spots your car arriving in the driveway. When you drive away again, the lights are turned off.

A text tutorial using this code is due to feature in an upcoming issue of [HackSpace Magazine](https://hackspace.raspberrypi.org/issues) and an in-depth video is coming soon on the [Switched On Network](https://www.youtube.com/SwitchedOnNetwork?sub_confirmation=1) YouTube channel.

The main image processing and searching for & identifying number plates is carried out by using the On-Premesis [OpenALPR](http://doc.openalpr.com/on_premises.html) software installed on a Raspberry Pi 3, set to monitor the RTSP feed from an inexpensive home Network IP Camera. On detection of the correct number plate, an IFTTT webhook event is triggered, which instructs a TP-Link Smart WiFi LED to switch on, via the Kasa web service. (You could use a relay switch connected to the GPIO ports instead).

## ANPR vs. ALPR
ANPR = Automatic Number Plate Recognition, which is the common term here in the UK.
ALPR = Automatic License Plate Recognition, which is the term used in some other countries such as those in North America.

### Thanks
Thanks to Matthew Hill for his [example script](https://gist.github.com/matthill/2daa79804a17c5d101d0195caa78bd5b) showing how to process the Beanstalk queue.