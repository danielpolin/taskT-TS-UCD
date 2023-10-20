#!/usr/bin/env ccs-script
import sys,time
import SphereConfig
#from argparse import ArgumentParser

## Creates a Sphere object and initializes socket connections
sphere = SphereConfig.Sphere()

## Check current before
current = sphere.read_photodiode()
print "Initial current: {0:.3E}".format(current)

#you can turn on the light. 
sphere.turn_light_on()
print "Light turned on."

#you can change the light intensity between 0% and 100% intensity by changin the shutter position. >99 and <1 are all the way open and closed. We have not recently tested how accurate this is.
sphere.set_light_intensity(30)
print "Light intensity set to 30"

#you can read the photodiode output
current = sphere.read_photodiode()
print "New current: {0:.3E}".format(current)
