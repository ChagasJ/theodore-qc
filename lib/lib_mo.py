"""
Handling and manipulation of MO-coefficients.
"""

import error_handler, lib_file, units
import numpy

class MO_set:
    """
    Main class that contains orbital information.
    """
    def __init__(self, file):
        self.file = file

        self.header = '' # header info for print-out
        self.num_at = 0
        self.basis_fcts = [] # info about basis functions
        self.bf_labels = [] # list of basis function labels
        self.at_dicts = [] # info about atoms: {'Z':, 'x':, 'y':, 'z':}

        self.S = None
        self.mo_mat = None
        self.inv_mo_mat = None
        self.lowdin_mat = None

    def read(self, *args, **kwargs):
        """
        Read MOs from external file.
        """
        raise error_handler.PureVirtualError()

    def compute_inverse(self, lvprt=1):
        """
        Compute the inverse of the MO matrix.
        If the matrix is not square, the pseudoinverse is computed.
        """

        # Preferably, the overlap matrix should be used to avoid explicit inversion
        if type(self.S) is numpy.ndarray:
            if lvprt >= 1:
                print " ... inverse computed as: C^T.S"
            self.inv_mo_mat = numpy.dot(self.mo_mat.transpose(), self.S)
        elif len(self.mo_mat) == len(self.mo_mat[0]):
            if lvprt >= 1:
                print " ... inverting C"
            try:
                self.inv_mo_mat = numpy.linalg.inv(self.mo_mat)
            except:
                if lvprt >= 1:
                    print " WARNING: inversion failed."
                    print '  Using the Moore-Penrose pseudo inverse instead.'
                self.inv_mo_mat = numpy.linalg.pinv(self.mo_mat)
        else:
            if lvprt >= 1:
                print 'MO-matrix not square: %i x %i'%(len(self.mo_mat),len(self.mo_mat[0]))
                print '  Using the Moore-Penrose pseudo inverse.'
            self.inv_mo_mat = numpy.linalg.pinv(self.mo_mat)

    def compute_lowdin_mat(self, lvprt=1):
        print "Performing Lowdin orthogonalization"

        (U, sqrlam, Vt) = numpy.linalg.svd(self.mo_mat)

        if Vt.shape[0] == U.shape[1]:
            self.lowdin_mat = numpy.dot(U, Vt)
        elif Vt.shape[0] < U.shape[1]:
            print '  MO-matrix not square: %i x %i'%(len(self.mo_mat),len(self.mo_mat[0]))
            self.lowdin_mat = numpy.dot(U[:,:Vt.shape[0]], Vt)
        else:
            raise error_handler.ElseError('>', 'Lowdin ortho')

    def ret_mo_mat(self, trnsp=False, inv=False):
        """
        Return the MO matrix, possibly transposed and/or inverted.
        """
        if not trnsp and not inv:
            return self.mo_mat
        elif trnsp and not inv:
            return self.mo_mat.transpose()
        elif not trnsp and inv:
            return self.inv_mo_mat
        elif trnsp and inv:
            return self.inv_mo_mat.transpose()

    def ret_mo_pop(self, imo, dosum=0):
        """
        Return a vector for Mulliken population analysis of the MO.
        dosum: 0 - return the vector directly
               1 - sum over atoms
               2 - sum over basis function types
        """
        MOi    = self.mo_mat[:,imo]
        invMOi = self.inv_mo_mat[imo,:]

        CCinv = MOi * invMOi

        if dosum==0:
            return CCinv

        elif dosum==1:
            mp = numpy.zeros(self.num_at)
            for ibas in range(self.ret_num_bas()):
                iat = self.basis_fcts[ibas].at_ind - 1
                mp[iat] += CCinv[ibas]
            return mp

        elif dosum==2:
            mp = numpy.zeros(len(self.bf_labels))
            for ibas in range(self.ret_num_bas()):
                ilab = self.bf_labels.index(self.basis_fcts[ibas].label())
                mp[ilab] += CCinv[ibas]
            return mp

    def ret_ihomo(self):
        """
        Return the HOMO index (starting with 0).
        This only works if no fractional occupation numbers are present!
        """
        return self.occs.index(0.) - 1

    def ret_num_mo(self):
        return len(self.mo_mat[0])

    def ret_num_bas(self):
        return len(self.mo_mat)

    def ret_eo(self, imo):
        return self.ens[imo], self.occs[imo]

    def ret_sym(self, imo):
        try:
            return self.syms[imo]
        except:
            print "\nNo entry for imo=%i"%imo
            raise

    def set_ens_occs(self):
        """
        In the case of Q-Chem the occupations are actually written into the energy field.
        This subroutine can be used to switch this.
        """
        self.occs = self.ens

    def MdotC(self, M, trnsp=True, inv=False):
        """
        Right-multiplication of matrix M with the MO-coefficients.
        """
        try:
            return numpy.dot(M, self.ret_mo_mat(trnsp, inv))
        except:
            print "M: %i x %i"%(len(M), len(M[0]))
            print "C: %i x %i"%(len(self.ret_mo_mat(trnsp, inv)), len(self.ret_mo_mat(trnsp, inv)[0]))
            raise

    def CdotD(self, D, trnsp=False, inv=False):
        """
        Left-multiplication of matrix D with the MO-coefficients.
        Optionally, D can be a rectangular matrix of dimension occ x (occ + virt).
        """
        if self.ret_num_mo() == len(D):
            return numpy.dot(self.ret_mo_mat(trnsp, inv), D)

        # Handling of special cases
        elif self.ret_num_mo() > len(D):
            if not trnsp and not inv:
                # take only the occ. subblock
                Csub = self.mo_mat.transpose()[:len(D)]
                return numpy.dot(Csub.transpose(), D)
            elif trnsp and inv:
                # take only the occ. subblock
                Csub = self.inv_mo_mat[:len(D)]
                return numpy.dot(Csub.transpose(), D)
            else:
                raise error_handler.ElseError('"transpose xor inverse"', 'CdotD')

        elif self.ret_num_mo() < len(D):
                print "\n WARNING: C/D mismatch"
                print " C: %i x %i"%(self.ret_num_mo(), self.ret_num_bas())
                print " D: %i x %i"%(len(D), len(D[0]))
#                raise error_handler.ElseError('C < D', 'MO matrix')

                Dsub = D[:self.ret_num_mo()]
                return numpy.dot(self.ret_mo_mat(trnsp, inv), Dsub)

    def lowdin_trans(self, D):
        """
        MO-AO transformation and Lowdin orthogonalization by using
           S^0.5 C = U V^T
        """
        DUTT = numpy.dot(D, self.lowdin_mat.T)
        if self.lowdin_mat.shape[1] == DUTT.shape[0]:
            return numpy.dot(self.lowdin_mat, DUTT)
        elif self.lowdin_mat.shape[1] > DUTT.shape[0]:
            return numpy.dot(self.lowdin_mat[:,:DUTT.shape[0]], DUTT)
        else:
            raise error_handler.ElseError('<', 'Lowdin trans')

    def export_MO(self, ens, occs, U, *args, **kwargs):
        """
        Exports NO, NDO etc. coefficients given in the MO basis.
        """
        mo_mat = self.CdotD(U, trnsp=False, inv=False)

        self.export_AO(ens, occs, mo_mat.transpose(), *args, **kwargs)

    def export_NTO(self, lam, U, Vt, *args, **kwargs):
        """
        Exports NTO coefficients given in the MO basis.
        """
        U_mat_t = self.CdotD(U,  trnsp=False, inv=False).transpose()
        V_mat_t = self.MdotC(Vt, trnsp=True,  inv=False)

        UV_t = [iU for iU in reversed(U_mat_t)] + [iV for iV in V_mat_t]

        lam2 = [-vlam for vlam in reversed(lam)] + [vlam for vlam in lam] + [0.] * (len(Vt) - len(lam))

        self.export_AO(lam2, lam2, UV_t, *args, **kwargs)

    def export_AO(self, *args, **kwargs):
        raise error_handler.PureVirtualError()

    def bf_blocks(self):
        """
        Return a list with the start and end indices for basis functions on the different atoms.
        [(iat, ist, ien), ...]
        """
        bf_blocks = []
        iat_old = 0
        ist = 0
        for ibas in range(self.ret_num_bas()):
            iat = self.basis_fcts[ibas].at_ind - 1
            if iat != iat_old:
                bf_blocks.append((iat_old, ist, ibas))
                iat_old = iat
                ist = ibas
        bf_blocks.append((iat, ist, self.ret_num_bas()))

        return bf_blocks

    def symsort(self, irrep_labels, sepov=True):
        """
        Sort MOs by symmetry (in case they are sorted by energy).
        This is more of a hack than a clean and stable routine...
        """
        print "Sorting MOs by symmetry"

        occorbs = {}
        virtorbs = {}
        for il in irrep_labels:
            occorbs[il]  = []
            virtorbs[il] = []

        for imo, sym in enumerate(self.syms):
            for il in irrep_labels:
                if il in sym:
                    if self.occs[imo] == 0.:
                        virtorbs[il].append((sym, imo))
                    else:
                        occorbs[il].append((sym, imo))

        T = numpy.zeros([self.ret_num_mo(), self.ret_num_mo()], int)

        orblist = []
        if sepov:
            for il in irrep_labels:
                orblist += occorbs[il]
            for il in irrep_labels:
                orblist += virtorbs[il]
        else:
            raise error_handler.ElseError('False', 'sepov')

        self.syms = []
        for jmo, orb in enumerate(orblist):
            T[jmo, orb[1]] = 1
            self.syms.append(orb[0])

        assert(jmo==self.ret_num_mo()-1)

        self.mo_mat = numpy.dot(self.mo_mat, T.transpose())
        self.compute_inverse()

class MO_set_molden(MO_set):
    def export_AO(self, ens, occs, Ct, fname='out.mld', cfmt='% 10E', occmin=-1, alphabeta=False):
        """
        Export coefficients given already in the AO basis to molden file.

        Ct can either be a list or numpy array with the coefficients.
        """
        mld = open(fname, 'w')
        mld.write(self.header)
        mld.write('[MO]\n')

        for imo in range(len(Ct)):
            if abs(occs[imo]) < occmin: continue

            mld.write(' Sym= X\n')
            mld.write(' Ene= %f\n'%ens[imo])
            if alphabeta:
                if occs[imo] < 0:
                    mld.write(' Spin= Alpha\n')
                    mld.write(' Occup= %f\n'%-occs[imo])
                else:
                    mld.write(' Spin= Beta\n')
                    mld.write(' Occup= %f\n'%occs[imo])
            else:
                mld.write(' Spin= Alpha\n')
                mld.write(' Occup= %f\n'%occs[imo])
            for ibf, coeff in enumerate(Ct[imo]):
                fmtstr = '%10i   '+cfmt+'\n'
                mld.write(fmtstr%(ibf+1, coeff))

        mld.close()

    def ret_coeffs(self, occmin=-1., occmax=100., eneocc=False, sym='X'):
        outstr = ''

        for imo in range(self.ret_num_mo()):
            if eneocc:
                occ = self.ens[imo]
            else:
                occ = self.occs[imo]
            if abs(occ) < occmin: continue
            if abs(occ) > occmax: continue

            outstr += ' Sym= %s\n'%sym
            outstr += ' Ene= %f\n'%self.ens[imo]
            outstr += ' Spin= Alpha\n'
            outstr += ' Occup= %f\n'%occ
            print self.mo_mat.shape
            for ibf, coeff in enumerate(self.mo_mat[:,imo]):
                outstr += '%10i  % 10E\n'%(ibf+1, coeff)

        return outstr

    def read(self, lvprt=1):
        """
        Read in MO coefficients from a molden File.
        """
        MO = False
        GTO = False
        ATOMS = False
        mo_vecs = []
        mo_ind = 0
        self.syms = [] # list with the orbital descriptions. they are entered after Sym in the molden file.
        self.occs = [] # occupations
        self.ens  = [] # orbital energies (or whatever is written in that field)

        num_bas={'s':1,'p':3,'sp':4,'d':6,'f':10,'g':15}

        orient={'s':['1'],
                'p':['x','y','z'],
               'sp':['1','x','y','z'],
                'd':['x2','y2','z2','xy','xz','yz'],
                'f':['xxx', 'yyy', 'zzz', 'xyy', 'xxy', 'xxz', 'xzz', 'yzz', 'yyz', 'xyz'],
                'g':15*['?']}

        num_orb=0
        curr_at=-1

        self.header = ''

        fileh = open(self.file, 'r')

        fstr = fileh.read()
        if ('[D5' in fstr) or ('[5D' in fstr):
            num_bas['d']=5
            orient['d']=['D0', 'D+1', 'D-1', 'D+2', 'D-2']
        if ('F7]' in fstr) or ('7F]' in fstr):
            num_bas['f']=7
            orient['f']=['F0', 'F+1', 'F-1', 'F+2', 'F-2', 'F+3', 'F-3']
        if ('9G]' in fstr) or ('9G]' in fstr):
            num_bas['g']=9
            orient['g']=9*['?']

        fileh.seek(0) # rewind the file

        for line in fileh:
            words = line.replace('=',' ').split()

            if 'molden format' in line.lower():
                if not '[Molden Format]' in line:
                    print " WARNING: the header may not be understood by Jmol:"
                    print line,
                    print " This has to be changed to:"
                    print " [Molden Format]"

                    line = '[Molden Format]'

            # what section are we in
            if '[' in line:
                MO = False
                GTO = False
                ATOMS = False

            if '[MO]' in line:
                if lvprt >= 2: print "Found [MO] tag"
                MO = True
                GTO = False
            # extract the information in that section
            elif MO:
                if not '=' in line:
                    try:
                        mo_vecs[-1].append(float(words[1]))
                    except:
                        if words==[]: break # stop parsing the file if an empty line is found

                        print " ERROR in lib_mo, parsing the following line:"
                        print line
                        raise
                elif 'ene' in line.lower():
                    mo_ind += 1
                    mo_vecs.append([])
                    self.ens.append(float(words[-1]))
                elif 'sym' in line.lower():
                    self.syms.append(words[-1])
                elif 'occ' in line.lower():
                    self.occs.append(float(words[-1]))

            elif ('[GTO]' in line):
                GTO = True
                # extract the information in that section
            elif GTO:
                if len(words)==0: # empty line: atom is finished
                    curr_at = -1
                elif curr_at==-1:
                    curr_at = int(words[0])
                    self.num_at = max(curr_at, self.num_at)
                elif (len(words) >= 2) and (words[0].lower() in num_bas):
                  orbsymb = words[0].lower()

                  for i in xrange(num_bas[orbsymb]):
                    self.basis_fcts.append(basis_fct(curr_at, orbsymb, orient[orbsymb][i]))
                    label = self.basis_fcts[-1].label()
                    if not label in self.bf_labels:
                        self.bf_labels.append(label)

                    num_orb+=1

            elif '[atoms]' in line.lower():
                ATOMS = True
            elif ATOMS:
                words = line.split()
                self.at_dicts.append({'Z':int(words[2]), 'x':float(words[3]), 'y':float(words[4]), 'z':float(words[5])})

            if not MO:
                self.header += line

        fileh.close()

### file parsing finished ###

        if lvprt >= 1 or len(mo_vecs[0])!=num_orb:
            print '\nMO file %s parsed.'%self.file
            print 'Number of atoms: %i'%self.num_at
            print 'Number of MOs read in: %i'%len(mo_vecs)
            print 'Dimension: %i,%i,...,%i'%(len(mo_vecs[0]),len(mo_vecs[1]),len(mo_vecs[-1]))
            print 'Number of basis functions parsed: ', num_orb

        if len(mo_vecs[0])!=num_orb:
            raise error_handler.MsgError('Inconsistent number of basis functions!')

        if len(mo_vecs[-1]) == 0:
            lv = [len(mo_vec) for mo_vec in mo_vecs]
            imax = lv.index(0)
            print '*** WARNING: MO file contains MO vectors of zero length!'
            print 'Using only the first %i entries'%imax
            mo_vecs = mo_vecs[:imax]

        try:
           self.mo_mat = numpy.array(mo_vecs).transpose()
        except ValueError:
           print "\n *** Unable to construct MO matrix! ***"
           print "Is there a mismatch between spherical/cartesian functions?\n ---"
           raise

class MO_set_adf(MO_set):
    """
    MO_set class for ADF.
    Note that ADF uses STOs!
    """
    def read(self, lvprt=1):
        """
        Extract the MOs from the TAPE21 file.
        Initial code written by S. Mai.
        """
        import kf

        f=kf.kffile(self.file)
        try:
            self.num_at = int(f.read('Geometry','nr of atoms'))
        except:
            print("\n  ERROR: reading TAPE21 file (%s)!\n"%self.file)
            raise

        natomtype=int(f.read('Geometry','nr of atomtypes'))
        atomorder=f.read('Geometry','atom order index')
        atomindex=f.read('Geometry','fragment and atomtype index')
        atcharge=f.read('Geometry', 'atomtype total charge')
        nbptr=f.read('Basis','nbptr')
        naos2=int(f.read('Basis','naos'))

        # get number of basis functions per atomtype
        nbasis={}
        for iaty in range(natomtype):
            nbasis[iaty]=nbptr[iaty+1]-nbptr[iaty]

        if lvprt >= 2:
            print 'Number of basis functions per atomtype:'
            print(nbasis)

        # get which atom is of which atomtype
        atom_type={}
        for iatom in range(self.num_at):
            index=atomorder[iatom]-1
            atom_type[iatom]=atomindex[index+self.num_at]-1

        if lvprt >= 2:
            print 'Mapping of atoms on atomtypes:'
            print(atom_type)

        # get number of basis functions
        naos=0
        for i in atom_type:
            naos+=nbasis[atom_type[i]]
        if lvprt >= 2:
            print 'Total number of basis functions:', naos
        assert naos==naos2, "wrong number of orbitals"

        # map basis functions to atoms
        for iatom in range(self.num_at):
          index=atomorder[self.num_at+iatom]-1
          nb=nbasis[atom_type[index]]
          for iao in range(nb):
            self.basis_fcts.append(basis_fct(index+1))

        if lvprt >= 3:
            print 'Basis functions:'
            for bf in self.basis_fcts:
                print bf

        # get MO coefficients
        NAO=int(f.read('Basis','naos'))
        npart=f.read('A','npart')
        NMO_A=int(f.read('A','nmo_A'))
        mocoef_A=f.read('A','Eigen-Bas_A')

        for i in range(len(npart)):
          npart[i]-=1
        self.mo_mat = numpy.zeros([NAO, NMO_A])
        iao=0
        imo=0
        for i,el in enumerate(mocoef_A):
          iao1=npart[iao]
          self.mo_mat[iao1][imo]=el
          iao+=1
          if iao>=NAO:
            iao=0
            imo+=1

        nelec = int(f.read('General','electrons'))
        assert nelec%2==0, "Odd number of electrons not supported"
        nocc = nelec / 2
        nvirt = NMO_A - nocc
        self.occs = nocc * [2.] + nvirt * [0.]

        # read coordinates and elements
        atom_Z=[int(atcharge[atom_type[i]]) for i in range(self.num_at)]
        xyz = f.read('Geometry', 'xyz').reshape(self.num_at, 3) * units.length['A']

        for iat in range(self.num_at):
            self.at_dicts.append({'Z':atom_Z[iat], 'x':xyz[atomorder[iat]-1, 0], 'y':xyz[atomorder[iat]-1, 1], 'z':xyz[atomorder[iat]-1, 2]})

## get AO overlap matrix
## NOTE: Smat is only read from TAPE15 !
## hence, if necessary, say "SAVE TAPE21 TAPE15" in input
#if f2:
#  NAO = f2.read('Basis','naos')
#  Smat = f2.read('Matrices','Smat')
#
#  ao_ovl=[ [ 0. for i in range(NAO) ] for j in range(NAO) ]
#  x=0
#  y=0
#  for el in Smat:
#    ao_ovl[x][y]=el
#    ao_ovl[y][x]=el
#    x+=1
#    if x>y:
#      x=0
#      y+=1

class basis_fct:
    """
    Container for basisfunction information.
    """
    def __init__(self, at_ind=-1, l='?', ml='?'):
        self.set(at_ind, l, ml)

    def set(self, at_ind=-1, l='?', ml='?'):
        self.at_ind = at_ind # atom where the function is located, starting at 1
        self.l = l   # s, p, d, f
        self.ml = ml # x, y, z

    def __str__(self):
        return "Basis function (%s, %s) at atom %i"%(self.l, self.ml, self.at_ind)

    def label(self):
        return "%s-%s"%(self.l, self.ml)

class jmol_MOs:
    """
    Class for producing input for the Jmol program that can be used to plot MOs.
    """
    def __init__(self, name, width=400):
        self.name = name
        self.imo = -1
        self.width = width

    def pre(self, ofile=None):
        self.jmfile = open("%s_jmol.spt"%self.name,'w')
        if not ofile==None:
            self.jmfile.write('load %s FILTER "nosort"\n'%ofile)
        self.jmfile.write ('mo titleformat ""\n\n')
        self.jmfile.write('background white\nmo fill\nmo cutoff 0.04\n')

        self.htmlfile = lib_file.htmlfile("%s.html"%self.name)
        self.htmlfile.pre(self.name)

    def add_mo(self, jmolstr, name, val):
        imfile = "%s_%.2f.png"%(name,abs(val))

        self.jmfile.write(jmolstr)
        self.jmfile.write('write image png "%s"\n'%imfile)

        if self.imo%2==0: self.htmlfile.write("<tr>\n")
        self.htmlfile.write("<td>")
        self.htmlfile.write("<img src=\"%s\" "%(imfile))
        self.htmlfile.write("border=\"1\" width=\"%i\">"%self.width)
        self.htmlfile.write("<br> %.3f"%val)
        self.htmlfile.write("</td>\n")
        if self.imo%2==1: self.htmlfile.write("</tr>\n")

        self.imo += 1

    def next_set(self,header):
        if self.imo%2==1: self.htmlfile.write("</tr>\n")
        if not self.imo==-1: self.htmlfile.write("</table>\n")

        self.imo = 0

        self.jmfile.write("\n")

        self.htmlfile.write("\n<h2>%s</h2>\n"%header)
        self.htmlfile.write("<table>\n")

    def post(self):
        self.jmfile.close()

        if self.imo%2==1: self.htmlfile.write("</tr>\n")

        self.htmlfile.write("</table>\n")
        self.htmlfile.post()

        print "\nJmol input file %s.jmol and %s.html written"%(self.name, self.name)

