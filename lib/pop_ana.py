"""
Module for population analysis.
Currently only Mulliken style analysis is supported.
"""

import numpy

class pop_ana:
    """
    Base class for population analysis.
    """
    def ret_pop(self, dens, mos):
        """
        -> Overload this function.
        """
        return None

class mullpop_ana(pop_ana):
    """
    Mulliken population analysis.
    """
    def ret_pop(self, dens, mos):
        """
        Compute and return the Mulliken population.
        """
        temp = mos.CdotD(dens, trnsp=False, inv=False)  # C.DAO
        DS   = mos.MdotC(temp, trnsp=False, inv=True) # DAO.S = C.D.C^(-1)
        
        mp = numpy.zeros(mos.num_at)
        
        for ibas in xrange(mos.ret_num_bas()):
            iat = mos.basis_fcts[ibas].at_ind - 1
            mp[iat] += DS[ibas, ibas]
            
        return mp    

class pop_printer:
    """
    Printer for population analysis data.
    """
    def __init__(self):
        self.pop_types = []
        self.pops = []
        
    ## \brief Add population data    
    # \param pop_type name to be printed
    # \param pop numpy.array with data
    def add_pop(self, pop_type, pop):
        """
        Add population data to be stored in the printer class.
        """
        if pop==None: return
        
        self.pop_types.append(pop_type)
        self.pops.append(pop)
        
    def ret_table(self):
        """
        Return a table containing all the populations of interest.
        """
        retstr = ''
        
        hstr = '%5s'%'Atom'
        for pop_type in self.pop_types:
            hstr += '%10s'%pop_type
            
        retstr += len(hstr) * '-' + "\n"
        retstr += hstr            
        retstr += "\n" + len(hstr) * '-' + "\n"
        
        for iat in xrange(len(self.pops[0])):
            retstr += '%5i'%(iat + 1)
            for pop in self.pops:
                retstr += '% 10.5f'%pop[iat]
            retstr += '\n'

        retstr += len(hstr) * '-' + "\n"
        
        retstr += '%5s'%''
        for pop in self.pops:
            retstr += '% 10.5f'%pop.sum()
        
        retstr += "\n" + len(hstr) * '-' + "\n"
        
        return retstr
    