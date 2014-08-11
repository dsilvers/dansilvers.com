from django.core.management.base import BaseCommand, CommandError
import csv
from dryrate.models import ClimbRate


weights = [1200,1150,1100,1050,1000,950]


class Command(BaseCommand):
    args = "<path to csv file>"
    help = "Import Power Settings"

    def handle(self, *args, **options):
        count = 1
        for file in args:
          with open(file, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in reader:
              if count > 1:
                altitude = row[0]

                for fpm_row in range(1, len(weights) + 1):
                    fpm = row[fpm_row]
                    weight = weights[fpm_row - 1]
                    
                    c = ClimbRate()
                    c.fpm = fpm
                    c.altitude = altitude
                    c.weight = weight
                    c.save()

                    self.stdout.write( str(weight) + "kg, " + str(altitude) + "\" " + str(fpm) + " fpm")
              count = count + 1
	                






"""

Climb Rates from POH

Anything above 10000 is a guess
Other values are interpolated

Standard temperature only (15 C)
Did not apply standard lapse rate

,1200,1150,1100,1050,1000,950
0,780,820,900,980,1060,1140
1000,710,760,830,900,960,1040
2000,640,700,760,820,860,940
3000,580,630,690,740,780,860
4000,520,560,620,660,700,780
5000,460,510,560,600,640,700
6000,400,460,500,540,580,620
7000,330,390,420,450,480,520
8000,260,320,340,360,380,420
9000,220,250,270,290,310,330
10000,180,180,200,220,240,240
11000,170,170,185,200,220,220
12000,160,160,170,180,200,200
13000,145,145,155,165,188,188
14000,130,130,140,150,175,175
15000,115,115,120,150,163,163
16000,100,100,100,150,150,150

"""







