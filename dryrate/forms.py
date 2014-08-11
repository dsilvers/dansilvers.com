from django import forms

FLIGHT_RULE_CHOICES = (
	('IFR', 'IFR'),
	('VFR', 'VFR'),
)

DIRECTION_CHOICES = (
	('EAST', 'East (odd)'),
	('WEST', 'West (even)'),
)

WEIGHT_CHOICES = (
	('1200', '2646lbs'),
	('1150', '2535lbs'),
	('1100', '2430lbs'),
	('1050', '2320lbs'),
	('1000', '2205lbs'),
	('950', '2100lbs'),
)

class CalculatorForm(forms.Form):
	departure_elevation = forms.IntegerField(label="Departure Elevation", initial=840)
	destination_elevation = forms.IntegerField(label="Destination Elevation", initial=840)
	distance = forms.IntegerField(label="Distance (nm)", initial=500)
	flight_rules = forms.ChoiceField(label="Flight Rules", choices=FLIGHT_RULE_CHOICES, initial="IFR")
	direction = forms.ChoiceField(label="Direction", choices=DIRECTION_CHOICES, initial="EAST")
	weight = forms.ChoiceField(label="Weight", choices=WEIGHT_CHOICES, initial=2646)

	dry_rate = forms.IntegerField(label="Dry Rate", initial=91)
	wet_rate = forms.IntegerField(label="Wet Rate", initial=150)
	gas_price = forms.FloatField(label="100LL Price", initial=5.84)
