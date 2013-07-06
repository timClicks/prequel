import tempfile

import prequel

str_data = """
[
 {
   "make": "Lexus",
   "model": "IS250",
   "url": "http://www.trademe.co.nz/motors/used-cars/lexus/is250/auction-611235722.htm"
 },
 {
   "make": "Jeep",
   "model": "Compass",
   "url": "http://www.trademe.co.nz/Browse/Listing.aspx?id=572499358"
 }
]
"""

int_data = """
[
 {
   "make": "Lexus",
   "model": "IS250",
   "url": "http://www.trademe.co.nz/motors/used-cars/lexus/is250/auction-611235722.htm",
   "year": 2006
 },
 {
   "make": "Jeep",
   "model": "Compass",
   "url": "http://www.trademe.co.nz/Browse/Listing.aspx?id=572499358",
   "year": 2013
 }
]
"""

float_data = """
[
 {
   "make": "Lexus",
   "model": "IS250",
   "url": "http://www.trademe.co.nz/motors/used-cars/lexus/is250/auction-611235722.htm",
   "year": 2006,
   "fuel_economy": 7.6
 },
 {
   "make": "Jeep",
   "model": "Compass",
   "url": "http://www.trademe.co.nz/Browse/Listing.aspx?id=572499358",
   "year": 2013,
   "fuel_economy": 9.1
 }
]
"""

list_data = """
[
 {
   "make": "Lexus",
   "model": "IS250",
   "url": "http://www.trademe.co.nz/motors/used-cars/lexus/is250/auction-611235722.htm",
   "year": 2006,
   "fuel_economy": 7.6,
   "features": [
     "ABS brakes",
     "Air conditioning",
     "Alarm",
     "Alloy wheels",
     "Central locking",
     "Driver airbag",
     "Passenger airbag",
     "Power steering"
   ]
 },
 {
   "make": "Jeep",
   "model": "Compass",
   "url": "http://www.trademe.co.nz/Browse/Listing.aspx?id=572499358",
   "year": 2013,
   "fuel_economy": 9.1,
   "features": [
     "Air conditioning",
     "Central locking",
     "Cruise control",
     "EFI",
     "Electric mirrors",
     "Electric windows",
     "Power steering",
     "Roof racks",
     "Spoiler",
     "Remote Locking"
   ]
 }
]
"""

missing_keys_data = """
[
 {
   "make": "Lexus",
   "model": "IS250",
   "registration_expiry": "Jan 2014",
   "warrant_of_fitness_expiry": "Aug 2013"
 },
 {
   "make": "Jeep",
   "model": "Compass"
 }
]
"""

null_data = """
[
 {
   "make": "Lexus",
   "model": "IS250",
   "registration_expiry": "Jan 2014",
   "warrant_of_fitness_expiry": "Aug 2013"
 },
 {
   "make": "Jeep",
   "model": "Compass",
   "registration_expiry": null,
   "warrant_of_fitness_expiry": null
 }
]
"""



def test_plumbing():
  import json
  for fixture in (globals()[f] for f in globals() if f.endswith("data")):
      assert bool(json.loads(fixture))

def test_read_from_csv():
  basic_csv = [
             "make,model,year,fuel_economy",
             "Lexus,IS250,2006,7.6",
             "Jeep,Compass,2013,9.1"
  ]
  tmpf = tempfile.NamedTemporaryFile(delete=False, prefix="prequel")
  tmpf.file.writelines('%s\n' % line for line in basic_csv)
  tmpf.close()

  prequel.Dataset(tmpf.name)
  tmpf.unlink(tmpf.name)

  assert os.path.isfile(tmpf.name+".db")





