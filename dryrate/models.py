from django.db import models
from dryrate.utils import format_minutes
import copy

# Create your models here.

class PowerSetting(models.Model):
	altitude = models.IntegerField()
	percent = models.IntegerField()
	rpm = models.IntegerField()
	mp = models.DecimalField(decimal_places=1, max_digits=3)
	economy_gph = models.DecimalField(decimal_places=1, max_digits=3, blank=True, null=True)
	power_gph = models.DecimalField(decimal_places=1, max_digits=3, blank=True, null=True)
	tas = models.IntegerField()

	def __unicode__(self):
		return str(self.percent) + "% - " + str(self.altitude) + "' " + str(self.rpm) + " @ " + str(self.mp) + "\""

	class Meta:
		ordering = ['percent', 'altitude', 'rpm'] 



class ClimbRate(models.Model):
	altitude = models.IntegerField()
	weight = models.IntegerField()
	fpm = models.IntegerField()

	def __unicode__(self):
		return str(self.weight) + "kg - " + str(self.altitude) + "' = " + str(self.fpm) + "fpm"

	class Meta:
		ordering = ['weight', 'altitude']


"""
Data used to calculate this formula:

	altitude, gph
	0		19
	1000	18.5
	2000	18
	5000	16
	8000	13.7
	12000	11.6
	15000	10
	16000	8.5

GPH is loosely based on test results where we tried to consistenly use best power during the climb.
Not sure how well it worked. Also added a smidge to gph for a buffer.
"""
def get_climb_gph(altitude):
	return (-1.30088041 * (10**-8) * (altitude**2)) - (3.865139004 * 10**-4 * altitude) + 18.95720628


"""
Get GPH during decent

No research was done here and they are mostly just a guess to get this project done.
We should probably go up and do some research to get specific descent rates to get:
- fpm
- power power settings 
- gph 

0	8
2	7
5	6
10	5
13	4.5
14	4.3
15	4.1
16	4

9.98889x10^-9 x^2-0.000397176 x+7.86863 

Generated from Wolfram Alpha
LinearModelFit[{{0, 8}, {2000, 7}, {5000, 6}, {10000, 5}, {13000, 4.5}, {14000, 4.3}, {15000, 4.1}, {16000, 4}}, {x, x^2}, x]
"""
def get_descent_gph(altitude):
	return ((9.98889 * (10**-9)) * (altitude**2)) - (0.000397176 * altitude) + 7.86863 

"""
Get descent speed 
More research needed here, let's just use something near Vno in the DA40 for now
"""
def get_descent_airspeed():
	return 125

def get_descent_fpm():
	return 300



"""
Cruise Climb Speeds
kts
"""
def get_climb_speed(weight):
	weight = int(weight)

	if weight <= 850:
		return 60
	if weight <= 1000:
		return 68
	if weight <= 1150:
		return 73
	# 1200kgs
	return 76


def get_true_airspeed(altitude, ias):
	return ias + ((altitude / 1000) * (ias * .02))


class StaircaseStep:
	#start_altitude
	#end_altitude
	#fpm
	#time
	#gas
	#distance
	pass


class ClimbProfile:
	def __init__(self, weight, start_altitude, end_altitude):
		self.time = 0.0
		self.gas = 0.0
		self.distance = 0.0
		self.staircase = []

		self.start_altitude = start_altitude
		self.end_altitude = end_altitude

		current_altitude = self.start_altitude
		current_thousand = current_altitude / 1000
		first_one = True
		for altitude in range(current_thousand, self.end_altitude, 1000):
			if not first_one:
				current_thousand = altitude / 1000		
				current_altitude = altitude
			else:
				first_one = False

			if current_altitude % 1000 != 0:
				feet_to_climb = ((current_altitude / 1000) * 1000) + 1000 - current_altitude
			else:
				feet_to_climb = 1000

			climb = ClimbRate.objects.filter(altitude=altitude).filter(weight=weight).all()
			climb = climb[0]

			current_time = round(feet_to_climb / (climb.fpm + 0.0), 2)
			current_gas = round(get_climb_gph(altitude) * (current_time / 60), 2)
			current_distance = round(get_true_airspeed(altitude, get_climb_speed(weight)) * (current_time / 60), 2)

			self.time = self.time + current_time
			self.gas = self.gas + current_gas
			self.distance = self.distance + current_distance

			step = StaircaseStep()
			step.start_altitude = current_altitude
			step.end_altitude = current_altitude + feet_to_climb
			step.fpm = climb.fpm
			step.time = current_time
			step.time_readable = format_minutes(step.time)
			step.time_total = self.time
			step.time_total_readable = format_minutes(step.time_total)
			step.gas = current_gas
			step.gas_total = self.gas
			step.distance = current_distance
			step.distance_total = self.distance
			step.ias = int(get_climb_speed(weight))
			step.tas = int(get_true_airspeed(altitude, get_climb_speed(weight)))
			self.staircase.append(step)

	def shell_display(self):
		for step in self.staircase:
			print "CLIMB\t" + str(step.start_altitude) + "'\t" + str(step.end_altitude) + "'\t" + format_minutes(step.time_total) + " \t" + str(step.gas_total) + " gal \t" + \
								str(step.distance_total) + " nm " + " \t" + format_minutes(step.time) + " \t" + str(step.gas) + " gal \t" + str(step.distance) + " nm  \t"  + \
								str(step.fpm) + " fpm\t\t" + str(step.ias) + " kts\t\t" + str(step.tas) + " kts\t"


class CruiseProfile:
	def __init__(self, power_setting, flavor, distance):
		if flavor == "economy":
			self.gph = power_setting.economy_gph
			self.lean_description = "Economy"
			self.tas = int(power_setting.tas * 0.95)
		else:
			self.gph = power_setting.power_gph
			self.lean_description = "Best Power"
			self.tas = power_setting.tas

		self.description = str(power_setting) + " - " + str(self.gph) + "gph (" + self.lean_description + ")"
		self.altitude = power_setting.altitude
		self.mp = power_setting.mp
		self.rpm = power_setting.rpm
		self.lean = flavor
		self.time = round((distance / get_true_airspeed(power_setting.altitude, self.tas) * 60), 2)
		self.time_readable = format_minutes(self.time)
		self.time_total = 0
		self.time_total_readable = ""
		self.gas = round((self.time / 60) * float(self.gph), 2)
		self.distance = round(distance, 2)

	def shell_display(self, gas_burned, time_so_far, distance_overall):
		print "CRUISE\t" + str(self.altitude) + "'\t----\t" + format_minutes(self.time + time_so_far) + " \t" + str(self.gas + gas_burned) + " gal \t" + str(self.distance + distance_overall) + " nm " + "\t" + \
						format_minutes(self.time) + " \t" + str(self.gas) + " gal \t" + str(self.distance) + " nm \t"  + \
						"0     \t\t ---- \t\t" + str(self.tas) + " kts\t"





class DescentProfile:
	def __init__(self, start_altitude, end_altitude):
		self.start_altitude = start_altitude
		self.end_altitude = end_altitude
		self.fpm = get_descent_fpm()
		self.ias = get_descent_airspeed()
		self.time = 0.0
		self.distance = 0.0
		self.gas = 0.0
		self.staircase = []

		if self.end_altitude % 1000 == 0:
			last_thousand = self.end_altitude
		else:
			last_thousand = (self.end_altitude / 1000) * 1000

		for altitude in range(self.start_altitude, last_thousand, -1000):

			feet_to_descend = 1000
			if altitude - feet_to_descend < self.end_altitude:
				feet_to_descend = ((altitude / 1000) * 1000) - self.end_altitude

			current_time = round(feet_to_descend / (self.fpm + 0.0), 2)
			current_gas = round(get_descent_gph(altitude) * (current_time / 60), 2)
			current_distance = round(get_true_airspeed(altitude, get_descent_airspeed()) * (current_time / 60), 2)

			self.time = self.time + current_time
			self.gas = self.gas + current_gas
			self.distance = self.distance + current_distance

			step = StaircaseStep()
			step.start_altitude = altitude
			step.end_altitude = altitude - feet_to_descend
			step.fpm = self.fpm * -1
			step.time = current_time
			step.time_readable = format_minutes(step.time)
			step.time_total = self.time
			step.time_total_readable = format_minutes(step.time_total)
			step.gas = current_gas
			step.gas_total = self.gas
			step.distance = current_distance
			step.distance_total = self.distance
			step.ias = get_descent_airspeed()
			step.tas = int(get_true_airspeed(altitude, get_descent_airspeed()))
			self.staircase.append(step)

	def shell_display(self, gas_burned, time_so_far, distance_overall):
		for step in self.staircase:
			print "DESCEND\t" + str(step.start_altitude) + "'\t" + str(step.end_altitude) + "'\t" + format_minutes(step.time_total + time_so_far) + " \t" + str(step.gas_total + gas_burned) + " gal \t" + \
								str(step.distance_total + distance_overall) + " nm " + "\t" + format_minutes(step.time) + " \t" + str(step.gas) + " gal \t" + str(step.distance) + " nm  \t" + \
								str(step.fpm) + " fpm\t" + str(step.ias) + " kts\t\t" + str(step.tas) + " kts\t"

class FlightProfile:
	def __init__(self, climb, cruise, descent):
		self.climb = climb
		self.cruise = cruise
		self.descent = descent
		self.dry_cost = 0.0
		self.wet_cost = 0.0

		self.gas = climb.gas + cruise.gas + descent.gas
		self.time = climb.time + cruise.time + descent.time
		self.time_readable = format_minutes(self.time)
		self.description = cruise.description		

	def calculate_cost(self, fuel_price, dry_rate, wet_rate):
		self.dry_cost = round(dry_rate * (self.time / 60) + fuel_price * self.gas, 2)
		self.wet_cost = round(wet_rate * (self.time / 60), 2)


class FlightProfileGroup:

	# associated profiles:
	#   climb = ClimbProfile
	#   cruise_profiles = [CruiseProfile, CruiseProfile ... ]
	#   descent = DescentProfile
	#
	#   flight_profiles = [ FlightProfile, ... ]

	# data:
	#   start_altitude
	#   cruise_altitude
	#   end_altitude
	#   weight

	def __init__(self, weight, distance, start_altitude, cruise_altitude, end_altitude):
		self.start_altitude = start_altitude
		self.cruise_altitude = cruise_altitude
		self.end_altitude = end_altitude
		self.weight = weight

		# Get climb profile
		self.climb = ClimbProfile(weight, start_altitude, cruise_altitude)

		# Get descent profile
		self.descent = DescentProfile(cruise_altitude, end_altitude)

		# Get cruise power settings
		# Calculate the distance we will be in cruise between climb and descent
		self.cruise_profiles= []
		cruise_distance = distance - self.climb.distance - self.descent.distance

		# Flight is impossible at this altitude, cannot climb or descent quickly enough
		if cruise_distance < 0:
			return

		available_power_settings = PowerSetting.objects.filter(altitude=cruise_altitude)

		for power_setting in available_power_settings:
			if power_setting.economy_gph > 0:
				self.cruise_profiles.append(CruiseProfile(power_setting, "economy", cruise_distance))
			if power_setting.power_gph > 0:
				self.cruise_profiles.append(CruiseProfile(power_setting, "power", cruise_distance))

		# Built FlightProfiles
		self.flight_profiles = []
		for cruise in self.cruise_profiles:
			
			rolling_counter = self.climb.staircase[-1].time_total + cruise.time
			rolling_distance = self.climb.staircase[-1].distance_total + cruise.distance
			rolling_gas = self.climb.staircase[-1].gas_total + cruise.gas

			cruise.time_total = rolling_counter
			cruise.time_total_readable = format_minutes(cruise.time_total)
			cruise.distance_total = rolling_distance
			cruise.gas_total = rolling_gas

			descent = self.descent
			for step in descent.staircase:

				rolling_counter = step.time + rolling_counter
				rolling_distance = step.distance + rolling_distance
				rolling_gas = step.gas + rolling_gas

				step.time_total = rolling_counter
				step.time_total_readable = format_minutes(step.time_total)
				step.distance_total = rolling_distance
				step.gas_total = rolling_gas

			self.flight_profiles.append(FlightProfile(self.climb, cruise, descent))



def analyze(weight, distance, departure_elevation, altitudes_to_consider, destination_elevation, fuel_price, dry_rate, wet_rate):
	# Calculate some numbers
	profiles = {}
	for altitude in altitudes_to_consider:
		group = FlightProfileGroup(weight, distance, departure_elevation, altitude, destination_elevation)
		profiles[altitude] = group.flight_profiles

	cheapest_dry = False
	fastest = False

	for altitude, altitude_profiles in profiles.items():
		for profile in altitude_profiles:

			profile.calculate_cost(fuel_price, dry_rate, wet_rate)

			print ""
			print profile.description
			print ""
			print "Dry: $" + str(profile.dry_cost)
			print "Wet: $" + str(profile.wet_cost)
			print "Time: " + format_minutes(profile.time)
			print "Fuel: " + str(round(profile.gas, 2)) + " gal"
			print ""

			print "\t\t\t   [-------- ROLLING TOTALS ---------]\t\t   [--------- LEG TOTALS --------- ]"
			print "\t\t\tTime\t\tFuel\t\tDistance\tLeg Time\tLeg Fuel\tDistance\tFPM Change\tIAS\t\tTAS"
			profile.climb.shell_display()
			profile.cruise.shell_display(profile.climb.gas, profile.climb.time, profile.climb.distance)
			profile.descent.shell_display(profile.climb.gas + profile.cruise.gas, profile.climb.time + profile.cruise.time, profile.climb.distance + profile.cruise.distance)

			print ""
			print "---------------------------------------------------------"

			if not cheapest_dry or profile.dry_cost < cheapest_dry.dry_cost:
				cheapest_dry = profile
			if not fastest or profile.time < fastest.time:
				fastest = profile



	print ""
	print ""
	if cheapest_dry:
		print "CHEAPEST DRY: " + cheapest_dry.description + " (" + format_minutes(cheapest_dry.time) + ") - ($" + str(cheapest_dry.dry_cost) + " dry, otherwise wet would be $" + str(cheapest_dry.wet_cost) + ")"
	if fastest:
		print "FASTEST: " + fastest.description + " (" + format_minutes(fastest.time) + ") - ($" + str(fastest.dry_cost) + " dry,  $" + str(fastest.wet_cost) + " wet)"




