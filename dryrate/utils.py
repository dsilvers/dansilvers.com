from datetime import datetime, timedelta

def format_minutes(minutes):
		sec = timedelta(seconds=int(minutes * 60))
		d = datetime(1,1,1) + sec
		return "%d:%02d:%02d" % (d.hour, d.minute, d.second)

