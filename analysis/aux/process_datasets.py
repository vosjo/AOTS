 
from analysis.models import DataSource, DataSet, DataTable, Method, DerivedParameter
from stars.models import Star

import read_datasets
 
def create_parameters(analmethod, data):
   """
   Adds all parameters from the analfile
   """
   parameters = read_datasets.get_parameters(data)
   for name, value in parameters.items():
      if name == 't0':
         # exception for t0 as this 0 ending might cause problems
         name = 't00'
         
      component = 0
      if name[-1] in ['0', '1', '2']:
         component = int(name[-1])
         name = name[:-1]
         
      analmethod.parameter_set.create(name=name, component=component, value=value[0],
                                      error_u=value[1], error_l=value[2], 
                                      unit=value[3], star=analmethod.star)
   
   return len(parameters.keys())

def create_derived_parameters(analmethod):
   """
   Adds the parameters that can be automatically derived for this method
   """
   
   try:
      ds = DataSource.objects.get(name__exact='AVG')
   except DataSource.DoesNotExist:
      ds = DataSource.objects.create(name='AVG')
   
   params = analmethod.method.derived_parameters
   if params.strip() == '': return 0
   
   params = params.split(',')
   for p in params:
      p = p.strip()
      if '_' in p:
         pname = p.split('_')[-2]
         pcomp = int(p.split('_')[-1])
      elif p[-1] in ['0', '1', '2']:
         pname = p[:-1]
         pcomp = int(p[-1])
      else:
         pname = p
         pcomp = 0
      
      p = DerivedParameter.objects.create(star=analmethod.star, name=pname,
                                                 component=pcomp, average=True, 
                                                 data_source = ds )
      print p
      
   return len(params)
   
def process_analysis_file(file_id):
   
   analfile = DataSet.objects.get(pk=file_id)
   
   try:
      data = analfile.get_data()
   except Exception, e:
      print e
      return False, 'Not added, file has wrong format / file is unreadable'
   
   # read the basic data
   try:
      systemname, ra, dec, name, note, atype = read_datasets.get_basic_info(data)
   except Exception, e:
      print e
      return False, 'Not added, basic info unreadable'
   
   try:
      analfile.method = Method.objects.get(slug__iexact = atype)
   except Exception, e:
      return False, 'Not added, analysis method not known'
      
   analfile.name = name
   analfile.note = note
   
   analfile.save()
   
   #-- try to find corresponding star
   if ra != 0.0 and dec != 0.0:
      star = Star.objects.filter(ra__range = (ra - 0.01, ra + 0.01), 
                                 dec__range = (dec - 0.01, dec + 0.01))
   else:
      star = Star.objects.filter(name__iexact = systemname)
      if not star: # there is no way to add this star, cause no coordinates are known.
         return False, "Not added, no system information present"
   
   
   message = "Validated the analysis file"
   if len(star) > 0:
      # there is an existing star
      star = star[0]
      star.dataset_set.add(analfile)
      message += ", added to existing System {}".format(star)
   else:
      # Need to create a new star
      star = Star(name=systemname, ra=ra, dec=dec, classification='')
      star.save()
      star.dataset_set.add(analfile)
      message += ", created new System {}".format(star)
   
   #-- add parameters
   try:
      npars = create_parameters(analfile, data)
      if npars == 0:
         analfile.valid = False
         analfile.save()
         message += ", (No parameters included, default to invalid dataset)"
      else:
         message += ", ({} parameters)".format(npars)
   except Exception, e:
      return False, 'Not added, error reading parameters'
   
   #-- add derived parameters
   npars = create_derived_parameters(analfile)
   if npars > 0: message += ", ({} derived parameters)".format(npars)
   
   #-- check if star already has this type of dataset, if so, replace
   #   only do so at the end so only valid datasets can replace an old one.
   similar = DataSet.objects.filter(method__exact=analfile.method,
                                    star__exact=star).order_by('added_on')
   if len(similar) > 1:
      similar[0].delete()
      message += ", replaced older analysis method"
   
   return True, message