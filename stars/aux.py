 
from stars.models import Star

#from astroquery import Simbad

#def get_altnames_from_simbad(star_id):
   #"""
   #Looks up alternative names for the star from Simbad
   #"""
   #star = Star.objects.get(pk = star_id)
   
   #try:
      #altnames = Simbad.query_objectids(star.name)
   #except Exception, e:
      #return
   
   #for altname in altnames:
      #star.altname_set.create(name = altname[0])

def add_star_from_spectrum(header):
   """
   Adds a new star from the headerinfo of a spectrum
   """
   
   ra = header.get('RA', -1)
   dec = header.get('DEC', -1)
   name = header.get('OBJECT', '')
   
   star = Star(name=name, ra=ra, dec=dec, classification='')
   star.save()
   
   return star.id
