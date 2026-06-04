"""
Dataset file I/O (extracted from model methods).
"""

from analysis.auxil import fileio


def read_dataset_data(dataset):
    return fileio.read2dict(dataset.datafile.path)
