 
import os
import h5py
 
 
def read2dict(filename):
   """
   Read the filestructure of a hdf5 file to a dictionary.
   
   automatically convert attributes of type bytes to a string using utf-8 encoding
   
   @param filename: the name of the hdf5 file to read
   @type filename: str
   @return: dictionary with read filestructure
   @rtype: dict
   """
   
   if not os.path.isfile(filename):
      raise IOError
   
   def read_rec(hdf):
      """ recusively read the hdf5 file """
      res = {}
      for name,grp in hdf.items():
            #-- read the subgroups and datasets
            if hasattr(grp, 'items'):
               # in case of a group, read the group into a new dictionary key
               res[name] = read_rec(grp)
            else:
               # in case of dataset, read the value
               if type(grp.value) == bytes:
                  res[name] = str(grp.value.decode("utf-8"))
               else:
                  res[name] = grp.value
               
      #-- read all the attributes
      for name, atr in hdf.attrs.items():
         if type(atr) == bytes:
            atr = str(atr.decode("utf-8"))
         res[name] = atr
               
      return res
   
   hdf = h5py.File(filename, 'r')
   result = read_rec(hdf)
   hdf.close()
   
   return result
