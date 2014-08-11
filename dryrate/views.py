from django.shortcuts import render
from dryrate.forms import CalculatorForm
from dryrate.models import FlightProfileGroup
# Create your views here.

MAXIMUM_ALTITUDE = 16500 # Yes, this is higher than 16400. No, this is more work to make work at a stupid non-500's altitude.


def dry_calculator(request):
	if request.method == 'POST':
		form = CalculatorForm(request.POST)
		if form.is_valid():
			# Process form data
			departure_elevation = form.cleaned_data['departure_elevation']
			destination_elevation = form.cleaned_data['destination_elevation']
			distance = form.cleaned_data['distance']
			flight_rules = form.cleaned_data['flight_rules']
			direction = form.cleaned_data['direction']
			weight = form.cleaned_data['weight']
			dry_rate = form.cleaned_data['dry_rate']
			wet_rate = form.cleaned_data['wet_rate']
			gas_price = form.cleaned_data['gas_price']
			#temperature = standard
			#winds = calm

			# Calculate valid altitudes
			altitudes_to_consider = []
			start_altitude = departure_elevation
			if destination_elevation > departure_elevation:
				start_altitude = destination_elevation

			start_altitude = ((start_altitude / 1000) * 1000) + 2000
			end_altitude = (MAXIMUM_ALTITUDE / 1000) * 1000
			for altitude in range(start_altitude, end_altitude, 1000):
				# Check that we're using a valid altitude for our direction of flight
				if (direction == "WEST" and altitude % 2000 == 0) or (direction == "EAST" and altitude % 2000 == 1000):
					if flight_rules == "VFR":
						altitude = altitude + 500
					# Check that we are not over the maximum altitude
					if altitude > MAXIMUM_ALTITUDE:
						break
					altitudes_to_consider.append(altitude)

			profiles = {}
			for altitude in altitudes_to_consider:
				# analyze(1100, 600, 840, [5000,7000,9000,11000,13000,15000], 840, 5.79, 91, 147)
				group = FlightProfileGroup(weight, distance, departure_elevation, altitude, destination_elevation)
				profiles[altitude] = group.flight_profiles

			cheapest_dry_altitude = False
			cheapest_dry = False
			cheapest_wet = False
			fastest = False
			fastest_altitude = False
			for altitude, altitude_profiles in profiles.items():
				for profile in altitude_profiles:
					profile.calculate_cost(gas_price, dry_rate, wet_rate)

					if not cheapest_dry or profile.dry_cost < cheapest_dry.dry_cost:
						cheapest_dry = profile
						cheapest_dry_altitude = altitude
					if not cheapest_wet or profile.wet_cost < cheapest_wet.wet_cost:
						cheapest_wet = profile						
					if not fastest or profile.time < fastest.time:
						fastest = profile
						fastest_altitude = altitude		

		return render(request, 'dry-calculator.html', { 'form': form, 
														'altitudes': altitudes_to_consider,
														'profiles': profiles,
														'cheapest_dry': cheapest_dry,
														'cheapest_dry_altitude': cheapest_dry_altitude,
														'cheapest_wet': cheapest_wet,
														'fastest': fastest,
														'fastest_altitude': fastest_altitude,
		})

	# Not yet submitted
	else:
		form = CalculatorForm()
		return render(request, 'dry-calculator.html', {'form': form })

	

