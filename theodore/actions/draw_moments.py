#!/usr/bin/env python3
"""
Plot arrows for dipole and quadrupole moments.
"""

from __future__ import print_function, division
import sys
import numpy
from .. import theo_header, units, lib_file, input_options, error_handler
from .actions import Action
from colt import Colt

class DipOptions(Colt):
    _questions = """
    # Scale factor for dipole moments
    dip_scale = 2.0 :: float
    # Radius for dipole moments
    dip_rad = 0.2 :: float
    """
    def from_config(cls, config): return config

class QuadOptions(Colt):
    _questions = """
    # Scale factor for quadrupole moments
    quad_scale = 1.0 :: float
    # Radius for quadrupole moments
    quad_rad = 0.2 :: float
    """
    def from_config(cls, config): return config

class TDipOptions(Colt):
    _questions = """
    # Scale factor for transition dipole moments
    tdip_scale = 6.0 :: float
    # Radius for transition dipole moments
    tdip_rad = 0.2 :: float
    """
    def from_config(cls, config): return config

class TPAOptions(Colt):
    _questions = """
    # Scale factor for 2P moments
    2P_scale = 1.0 :: float
    # Radius for 2P moments
    2P_rad = 0.1 :: float
    """
    def from_config(cls, config): return config

class mom_options():



    def __init__(self, ana_file, dip, quad, tdip, tpa):
        self.data = {}
        self.data['ana_file'] = ana_file
        self.data['do_dip']   = dip
        self.data['do_quad']  = quad
        self.data['do_tdip']  = tdip
        self.data['do_2P']    = tpa

        if self.data['do_dip']:
            data = DipOptions.from_questions()
            for key in data:
                self.data[key] = data[key]

        if self.data['do_quad']:
            data = QuadOptions.from_questions()
            for key in data:
                self.data[key] = data[key]

        if self.data['do_tdip']:
            data = TDipOptions.from_questions()
            for key in data:
                self.data[key] = data[key]

        if self.data['do_2P']:
            data = TPAOptions.from_questions()
            for key in data:
                self.data[key] = data[key]

    # def input(self):
    #     if self.data['do_dip']:
    #         self.read_float('Scale factor for dipole moments', 'dip_scale', 2.0)
    #         self.read_float('Radius for dipole moments', 'dip_rad', 0.2)
    #     if self.data['do_quad']:
    #         self.read_float('Scale factor for quadrupole moments', 'quad_scale', 1.0)
    #         self.read_float('Radius for quadrupole moments', 'quad_rad', 0.1)
    # 
    #     if self.data['do_tdip']:
    #         self.read_float('Scale factor for transition dipole moments', 'tdip_scale', 6.0)
    #         self.read_float('Radius for transition dipole moments', 'tdip_rad', 0.2)
    #     if self.data['do_2P']:
    #         self.read_float('Scale factor for 2P moments', '2P_scale', 1.0)
    #         self.read_float('Radius for 2P moments', '2P_rad', 0.1)

    def write_afile(self, filen='arrows.vmd'):
        """
        File for write arrows for the different states.
        """
        af = open(filen, 'w')
        self.af = af
        af.write(\
"""axes location Off
display projection Orthographic
display depthcue off
color Display Background white
menu graphics on
mol modstyle 0 0 Licorice 0.100000 30.000000 30.000000
""")

        sfile = lib_file.summ_file(self.data['ana_file'])
        ddict = sfile.ret_ddict()
        for state in sfile.ret_state_labels():
            sdict = ddict[state]

            # Dipole and quadrupole moments
            af.write('draw delete all\n')
            if self.data['do_dip']:
                # Conversion from e*Bohr to e*Ang
                dfac = self.data['dip_scale']  * units.length['A']
                if not 'mux' in sdict:
                    print(" *** No dipole info found for state %s"%state)
                else:
                    af.write('draw color green\n')
                    af.write('draw cylinder ')
                    self.vmd_coors(-.5 * dfac, .4 * dfac, sdict['mux'], sdict['muy'], sdict['muz'])
                    af.write('radius % .3f\n'%self.data['dip_rad'])

                    af.write('draw cone ')
                    self.vmd_coors( .4 * dfac, .6 * dfac, sdict['mux'], sdict['muy'], sdict['muz'])
                    af.write('radius % .3f\n'%(2*self.data['dip_rad']))
            if self.data['do_quad']:
                self.plot_quad(sdict)

            af.write('render TachyonInternal state_%s.tga\n\n'%state)

            # Transition dipole and 2P moments
            af.write('draw delete all\n')
            if self.data['do_tdip']:
                # Conversion from e*Bohr to e*Ang
                tdfac = self.data['tdip_scale']  * units.length['A']
                if not 'Tmux' in sdict:
                    print(" *** No transition dipole info found for state %s"%state)
                else:
                    af.write('draw color green\n')
                    af.write('draw cylinder ')
                    self.vmd_coors(-.5 * tdfac, .4 * tdfac, sdict['Tmux'], sdict['Tmuy'], sdict['Tmuz'])
                    af.write('radius % .3f\n'%self.data['tdip_rad'])

                    af.write('draw cone ')
                    self.vmd_coors( .4 * tdfac, .6 * tdfac, sdict['Tmux'], sdict['Tmuy'], sdict['Tmuz'])
                    af.write('radius % .3f\n'%(2*self.data['tdip_rad']))
            if self.data['do_2P']:
                self.plot_2P(sdict)

            af.write('render TachyonInternal trans_%s.tga\n\n'%state)

        af.close()
        print("File %s written."%af.name)

    def plot_quad(self, sdict):
        if not 'Qxx' in sdict:
            return

        tQxx = 2 * sdict['Qxx'] - sdict['Qyy'] - sdict['Qzz']
        tQyy = 2 * sdict['Qyy'] - sdict['Qxx'] - sdict['Qzz']
        tQzz = 2 * sdict['Qzz'] - sdict['Qyy'] - sdict['Qxx']

        af = self.af
        if self.vmd_color(tQxx):
            fac = self.data['quad_scale'] * units.length['A'] * abs(tQxx)**.5
            self.plot_quad_comp(fac, 1., 0., 0., self.data['quad_rad'])
        if self.vmd_color(tQyy):
            fac = self.data['quad_scale'] * units.length['A'] * abs(tQyy)**.5
            self.plot_quad_comp(fac, 0., 1., 0., self.data['quad_rad'])
        if self.vmd_color(tQzz):
            fac = self.data['quad_scale'] * units.length['A'] * abs(tQzz)**.5
            self.plot_quad_comp(fac, 0., 0., 1., self.data['quad_rad'])

    def plot_2P(self, sdict):
        if not '2Pxx' in sdict:
            return

        TPmat = numpy.zeros([3,3], float)
        TPmat[0,:] = sdict['2Pxx'], sdict['2Pxy'], sdict['2Pxz']
        TPmat[1,:] = sdict['2Pyx'], sdict['2Pyy'], sdict['2Pyz']
        TPmat[2,:] = sdict['2Pzx'], sdict['2Pzy'], sdict['2Pzz']

        TPstrength = numpy.trace(TPmat)**2 + numpy.sum(TPmat*TPmat) + numpy.sum(TPmat*TPmat.T)
        print('30*TPA strength [M a.u.]: % .5f'%(TPstrength*0.000002))

        (Sdiag, coor) = numpy.linalg.eigh(TPmat)
        print(Sdiag)
        for mu in range(3):
            if self.vmd_color(Sdiag[mu], eps=1.):
                fac = self.data['2P_scale'] * units.length['A'] * abs(Sdiag[mu])**.5
                self.plot_quad_comp(fac, coor[0, mu], coor[1, mu], coor[2, mu], self.data['2P_rad'])

        #self.af.write('draw color black\ndraw sphere {0 0 0} radius % .3f\n'%self['2P_rad'])

    def plot_quad_comp(self, fac, x, y, z, rad):
        ifac = 0.5 * fac
        self.af.write('draw cylinder ')
        self.vmd_coors(-ifac, ifac, x, y, z)
        self.af.write('radius % .3f\n'%rad)

        self.af.write('draw sphere ')
        self.af.write('{% .3f % .3f % .3f} '%(ifac * x, ifac * y, ifac * z))
        self.af.write('radius % .3f\n'%(3*rad))

        self.af.write('draw sphere ')
        self.af.write('{% .3f % .3f % .3f} '%(-ifac * x, -ifac * y, -ifac * z))
        self.af.write('radius % .3f\n'%(3*rad))

    def vmd_coors(self, fac1, fac2, x, y, z):
        self.af.write('{% .3f % .3f % .3f} '%(fac1 * x, fac1 * y, fac1 * z))
        self.af.write('{% .3f % .3f % .3f} '%(fac2 * x, fac2 * y, fac2 * z))

    def vmd_color(self, val, eps=1.e-3):
        if abs(val) < eps:
            return False
        elif val > 0.0:
            self.af.write('draw color blue\n')
            return True
        else:
            self.af.write('draw color red\n')
            return True

class DrawMoments(Action):
    name = 'draw_moments'

    _colt_description = 'Plotting of dipole and quadrupole moments'

    _questions = """
    # File produced by analyze_tden
    ana_file = :: existing_file
    # Plot dipole moments?
    dip = false :: bool, alias=d
    # Plot (diagonal) quadrupole moments?
    quad = false :: bool, alias=q
    # Plot transition dipole moments?
    tdip = false :: bool, alias=t
    # Plot 2-photon moments?
    tpa = false :: bool, alias=2
    """
    def run(ana_file, dip, quad, tdip, tpa):
        theo_header.print_header(title=__class__._colt_description)
        opt = mom_options(ana_file, dip, quad, tdip, tpa)
        opt.write_afile()