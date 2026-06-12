"""
Analysis file I/O (extracted from model methods).
"""

from analysis.auxil import fileio


def read_analysis_data(analysis):
    return fileio.read2dict(analysis.datafile.path)
