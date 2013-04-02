import abc
import logging
import Sea
import numpy as np
import itertools
from baseclass import BaseClass


class Connection(BaseClass):
    """
    Abstract base class for all :mod:`Sea.adapter.connections` classes.
    """
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, obj, system, components):
        
        model = Sea.model.connection.Connection
        
        BaseClass.__init__(self, obj, model)
        system.Connections = system.Connections + [obj]
        
        obj.makeCoupling = self.makeCoupling
        
        obj.addProperty("App::PropertyLinkList", "Couplings", "Connection", "List of all couplings.")
        obj.addProperty("App::PropertyLinkList", "Components", "Connection", "Components that are connected via this connection.")
        obj.Frequency = system.Frequency
        
        #obj.addProperty("App::PropertyLink", "CouplingsGroup", "Groups", "Couplings that are part of System.")
        #obj.CouplingsGroup = group.newObject("App::DocumentObjectGroup", "GroupCouplings")
        #obj.CouplingsGroup.Label = "Couplings"
        
        #obj.addProperty("Part::PropertyPartShape", "Shape", "Connection", "Shape of the connection.")
        
        #obj.addProperty("App::PropertyBool", "UpdateCouplings", "Connection", "Update couplings when the connection changes.").UpdateCouplings = True
       
        #obj.addProperty("App::PropertyString", "Sort", "Connection", "Is the connection described by a point, line or area.")
        
        obj.addProperty("App::PropertyFloatList", "ImpedanceJunction", "Connection", "Total impedance at the junction.")

        obj.Components = components
        
        #obj.Shape = component_a.Shape.common(component_b.Shape)
        
        
    def onChanged(self, obj, prop):
        BaseClass.onChanged(self, obj, prop)
        
        
        if prop == 'Components':
            self.updateComponents(obj)
            
        #elif prop == 'Shape':
            #self.updateCouplings(obj)    
        
        if prop == 'Frequency':
            for coupling in obj.Couplings:
                coupling.Frequency = obj.Frequency
            
        
    def execute(self, obj):
        BaseClass.execute(self, obj)
        
    @abc.abstractmethod
    def updateComponents(self, obj):
        pass
        
    
    #@staticmethod
    #def updateShape(obj):
        #"""
        #Update the common shape between the components.
        #"""
        #connection = Sea.adapter.connection.ShapeConnection([item.Shape for item in self.Components])
        #shape = connection.shape()
        
        #obj.Shape = shape
    
    def updateCouplings(self, obj):
        """
        The shape has changed, which means couplings might have to change, be added or removed.
        To be sure all couplings in this connection are deleted and then build up from scratch.
        """
        
        """Remove all old couplings."""
        for coupling in obj.Couplings:
            obj.Document.removeObject(coupling.Name)
            
        """Add couplings for every shape."""
        self.addCouplings(obj)
            
    @staticmethod
    def addCouplings(connection):
        """
        Add couplings to the :attr:`connection`.
        
        :param connection: an instance of :class:`Sea.adapter.baseclasses.Connection`
        """ 
        
        for comp_from, comp_to in itertools.permutations(connection.Components, 2):
            coupling_sort = Connection.determineCouplingType(connection.ClassName, comp_from, comp_to)
            
            if not coupling_sort:
                App.Console.PrintWarning("Cannot add coupling.\n")
                return

            for sub_from, sub_to in itertools.product(comp_from.AvailableSubsystems, comp_to.AvailableSubsystems):
                #print connection
                #print 'From: ' + comp_from.ClassName + sub_from
                #print 'To: ' + comp_to.ClassName + sub_to
                connection.makeCoupling(comp_from, getattr(comp_from, 'Subsystem' + sub_from), comp_to, getattr(comp_to, 'Subsystem' + sub_to), coupling_sort)
    
    coupling_options = {        
            ('ConnectionPoint', 'Component1DBeam', 'Component1DBeam') : 'Coupling1DStructural',
            ('ConnectionLine', 'Component1DBeam', 'Component1DBeam') : 'Coupling1DStructural',
            ('ConnectionSurface', 'Component1DBeam', 'Component1DBeam') : 'Coupling1DStructural',
            ('ConnectionPoint', 'Component2DPlate', 'Component2DPlate') : 'Coupling1DStructural',
            ('ConnectionLine', 'Component2DPlate', 'Component2DPlate') : 'Coupling2DStructural',
            ('ConnectionSurface', 'Component2DPlate', 'Component2DPlate') : 'Coupling2DStructural',
            
            ('ConnectionSurface', 'Component2DPlate', 'Component3DCavity') : 'Coupling3DPlateCavity',
            ('ConnectionSurface', 'Component3DCavity', 'Component2DPlate') : 'Coupling3DCavityPlate',
        }
            
            
    @staticmethod
    def determineCouplingType(connection_type, component_from, component_to):
        """
        Determine the type of coupling. Detects what type of connection the components have.
        Based on the type of connection and on the types of components a coupling is returned.
        
        :param component_from: an instance of a child of :class:`Sea.adapter.baseclasses.Component`
        :param component_to: an instance of a child of :class:`Sea.adapter.baseclasses.Component`
        """
        
        if connection_type:
            item = (connection_type, component_from.ClassName, component_to.ClassName)   
            try:
                return Connection.coupling_options[item]
            except KeyError:
                txt = 'Could not determine the type of coupling for ' + component_from.ClassName + ' to ' + component_to.ClassName + ' with ' + connection_type +  '.\n'
                App.Console.PrintWarning(txt)
                return None
        
    
    @staticmethod
    def makeCoupling(connection, component_from, subsystem_from, component_to, subsystem_to, sort):
        """
        Add a coupling to system.
        
        :param connection: an instance of :class:`Sea.adapter.baseclasses.Connection`
        :param component_from: an instance of a child of :class:`Sea.adapter.baseclasses.Component`
        :param subsystem_from: string representing the type of subsystem
        :param component_to: an instance of a child of :class:`Sea.adapter.baseclasses.Component`
        :param subsystem_to: string representing the type of subsystem
        :param sort: sort of coupling as specified in :class:`Sea.adapter.couplings.couplings_map`
        
        """
        #if connection.System == component_from.System == component_to.System:
        from Sea.adapter.object_maps import couplings_map
        
        obj = connection.newObject("App::FeaturePython", 'Coupling')
        couplings_map[sort](obj, connection, component_from, subsystem_from, component_to, subsystem_to)
        logging.info("Sea: Created %s.", obj.Name)
        obj.Document.recompute()
        return obj
    