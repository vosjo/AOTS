from django.test import TestCase

from stars.models import Star, Identifier, Project

class IdentifierBookkeeping(TestCase):
   
   def setUp(self):
       
      p = Project.objects.create(
          name='TestCase', 
          description='TestCase_description',
          )
      s = Star.objects.create(
          name='Vega', 
          project=p, 
          ra=279.23473479, 
          dec=38.78368896,
          )
      
   
   def test_create_identifier_on_create_star(self):
      
      s = Star.objects.get(name__exact='Vega')
      
      i = s.identifier_set.all()
      
      self.assertEqual(len(i), 1, 
                       "Identifier not created when star is created")
      self.assertEqual(i[0].name, s.name, 
                       "Name of identifier is not equal to star name on creation")
      
      
   def test_modify_identifier_on_modify_star_name(self):
      
      s = Star.objects.get(name__exact='Vega')
      
      s.name = 'alf Lyr'
      s.save()
      
      #i = s.identifier_set.filter(name__exact='Vega')
      #self.assertEqual(len(i), 0, 
                       #"Old star name not removed from identifiers on star name change")
      
      i = s.identifier_set.filter(name__exact='alf Lyr')
      self.assertEqual(len(i), 1, 
                       "New star name not added to identifiers on star name change")
      
