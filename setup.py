#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages
from distutils.extension import Extension

import numpy as np
import os

PWD = os.path.abspath(os.path.dirname(__file__))

def ljoin(path):
    global PWD
    return os.path.join(PWD, path)


with open('README') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = []

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]


setup(
    author="Felix Plasser",
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="Theoretical Density, Orbital Relaxation and Exciton analysis",
    entry_points={
        'console_scripts': [
           "analyze_NOs.py=theodore.scripts.analyze_NOs:analyze_nos",
           "analyze_correlations.py=theodore.scripts.analyze_correlations:analyze_correlations",
           "analyze_sden.py=theodore.scripts.analyze_sden:analyze_sden",
           "analyze_tden.py=theodore.scripts.analyze_tden:analyze_tden",
           "analyze_tden_soc.py=theodore.scripts.analyze_tden_soc:analyze_tden_soc",
           "analyze_tden_unr.py=theodore.scripts.analyze_tden_unr:analyze_tden_unr",
           "babel.py=theodore.scripts.babel:babel",
           "cc2molden.py=theodore.scripts.cc2molden:cc2molden",
           "cc_check.py=theodore.scripts.cc_check:cc_check",
           "cc_opt.py=theodore.scripts.cc_opt:cc_opt",
           "convert_table.py=theodore.scripts.convert_table:convert_table",
           "dgrid_prep.py=theodore.scripts.dgrid_prep:dgrid_prep",
           "draw_moments.py=theodore.scripts.draw_moments:draw_moments",
           "extract_molden.py=theodore.scripts.extract_molden:extract_molden",
           "fcd.py=theodore.scripts.fcd:fcd",
           "jmol_MOs.py=theodore.scripts.jmol_MOs:jmol_MOs",
           "jmol_vibs.py=theodore.scripts.jmol_vibs:jmol_vibs",
           "parse_libwfa.py=theodore.scripts.parse_libwfa:parse_libwfa",
           "plot_OmFrag.py=theodore.scripts.plot_OmFrag:plot_OmFrag",
           "plot_Om_bars.py=theodore.scripts.plot_Om_bars:plot_Om_bars",
           "plot_VIST.py=theodore.scripts.plot_VIST:plot_VIST",
           "plot_frag_decomp.py=theodore.scripts.plot_frag_decomp:plot_frag_decomp",
           "plot_graph.py=theodore.scripts.plot_graph:plot_graph",
           "plot_graph_nx.py=theodore.scripts.plot_graph_nx:plot_graph_nx",
           "spectrum.py=theodore.scripts.spectrum:spectrum",
           "tden_OV.py=theodore.scripts.tden_OV:tden_OV",
           "vmd_plots.py=theodore.scripts.vmd_plots:vmd_plots",
           "theoinp=theodore.scripts.theoinp:theoinp",
           ]
        },
    install_requires=requirements,
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='theodore',
    name='theodore',
    packages=find_packages(include=['theodore', 'theodore.*']),
    license="Apache License v2.0",
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/felixplasser/theodore-qc',
    version='2.3.0',
    zip_safe=False,
)
