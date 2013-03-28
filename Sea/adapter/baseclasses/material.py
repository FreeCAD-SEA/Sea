
import abc
import logging
import FreeCAD as App

import FreeCAD, FreeCADGui
from pivy import coin

import Sea

import numpy as np


import abc
import logging
import Sea
import numpy as np
from baseclass import BaseClass
        
class Material(BaseClass):
    """
    Abstract base class for all :mod:`Sea.adapter.materials` classes.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, obj, system):
        obj.addProperty("App::PropertyLinkList", "Components", "Material", "Components that make use of this material.")
        BaseClass.__init__(self, obj, 'Material')
        system.Materials = system.Materials + [obj]
        obj.Frequency = system.Frequency
        
        obj.addProperty("App::PropertyFloat", "Density", "Material", "Density of the material.").Density=0.0
        obj.addProperty("App::PropertyFloatList", "LossFactor", "Material", "Loss factor of the material.").LossFactor=0.0
        obj.addProperty("App::PropertyFloat", "Temperature", "Material", "Temperature of the material.").Temperature=0.0
        obj.addProperty("App::PropertyFloat", "Pressure", "Material", "Pressure of the material.").Pressure=0.0
        obj.addProperty("App::PropertyFloat", "Bulk", "Material", "Bulk modulus of the material").Bulk=0.0

        
        
        
    def onChanged(self, obj, prop):
        BaseClass.onChanged(self, obj, prop)
        
        for comp in obj.Components:
            comp.touch()
            for sub in comp.Subsystems:
                sub.touch()
        
        if prop == 'Density':
            self.model.density = obj.Density
        elif prop == 'LossFactor':
            if len(obj.LossFactor) == 1:
                self.model.loss_factor = np.ones(len(obj.Frequency)) * obj.LossFactor
            else:
                self.model.loss_factor = obj.LossFactor
        elif prop == 'Temperature':
            self.model.temperature = obj.Temperature
        elif prop == 'Pressure':
            self.model.pressure = obj.Pressure
        elif prop == 'Bulk':
            self.model.bulk = obj.Bulk
        
    def execute(self, obj):
        obj.Density = self.model.density
        obj.LossFactor = self.toList(self.model.loss_factor)
        obj.Temperature = self.model.temperature
        obj.Pressure = self.model.pressure
        obj.Bulk = self.model.bulk
        