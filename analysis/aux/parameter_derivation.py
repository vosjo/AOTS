
import numpy as np

#from analysis.models import Parameter

def find_parameters(dpar, **kwargs):
   """
   Searches for necessary parameters to calculate the derived parameter
   """
   
   fname = 'parameters_for_' + dpar.name
   
   if fname in globals():
      return globals()[fname](dpar, **kwargs)

def calculate(dpar, *args, **kwargs):
   """
   Calculates the parameter
   """
   
   fname = 'calculate_' + dpar.name
   
   if fname in globals():
      return globals()[fname](dpar, **kwargs)
   
# MASS RATIO
#===================================================

def parameters_for_q(dpar, **kwargs):
   """
   Mass ratio is calculated from the two amplitudes K1 and K2 
   """
   return ['K', 'K'],\
          [ 1,   2 ]

def calculate_q(dpar, *args, **kwargs):
   """
   Mass ratio is just K2 / K1
   """
   
   k1 = dpar.source_parameters.get(name__exact='K', component__exact=1, average__exact=True)
   k2 = dpar.source_parameters.get(name__exact='K', component__exact=2, average__exact=True)
   
   q = np.random.normal(k1.value, k1.error, 512) / np.random.normal(k2.value, k2.error, 512)
   dpar.value = np.average(q)
   dpar.error = np.std(q)


# RADIUS
#===================================================

def parameters_for_r(dpar, **kwargs):
   """
   Radius is derived from the mass and the surface gravity
   """
   c = dpar.component
   return ['m', 'logg'],\
          [ c ,  c    ]

def calculate_r(dpar, *args, **kwargs):
   """
   radius is calculate as sqrt(G M / g)
   """
   
   M = self.source_parameters.get(name__exact='m', component__exact=dpar.component)
   g = self.source_parameters.get(name__exact='logg', component__exact=dpar.component)
   
   G = 6.673839999999998e-05
   M = np.random.normal(M.value, M.error, 512)
   g = np.random.normal(g.value, g.error, 512)
   r = np.sqrt(G * M * 1.988547e+30 / 10**g) / 69550800000.0
   
   self.value = np.average(r)
   self.error = np.std(r)
   self.unit = 'Rsol'
   self.average = True
