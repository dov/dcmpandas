#!/usr/bin/env python
'''dcmpandas is a scraper and query system for interacting with a 
directory of dicom images. It builds a database of the tags
of all images in the database, and then allows querying 
these tags through the flexible pandas syntax.

The following example imports dcmpandas and builds a database of all
dicom images in the current directory. (Obviously the building of the
database only needs to be performed once.) It then loads the database
into memory, and performs a few queries and views the images of one
series.

    In [1]: import dcmpandas as dp
    
    In [2]: dp.scrape('.')
    Processing 48862992
    Processing 48857684
    Processing 48858202
    Processing 48862824
    :
    In [3]: tags,df = dp.load()
    In [4]: df.SeriesDescription.drop_duplicates()
    Out[4]: 
    0                   Ax t2_tse_spair
    1                         Ax t2_tse
    2                      Ax 3D GRE T1
    180            Ax Diff ep2d_mddw_30
    181    Ax Diff ep2d_mddw_30_a/p rpt
    Name: SeriesDescription, dtype: object
'''


#
# a utility library for reading dicom files and place their
# information in a pandas database.
#
# Copyright (c) 2014 Dov Grobgeld <dov.grobgeld@gmail.com>
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 2.1 of the License, or (at your
# option) any later version.
# 
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
# An xnm module in python with an interface similar to json
#
# Utility functions for using pandas with a directory of dicom
# images.

from __future__ import print_function
import os
import sys
import glob
import pydicom
import pandas as pd
import pickle
import fnmatch
import numpy as np
import pdb

# Default viewer is giv. See github.com/dov/giv .
viewer = 'giv'

    
def view(filenames):
    """View the filenames with an external viewer"""
    os.system(viewer + ' ' + ' '.join(filenames) + '&')

def scrape(directory = '.',
           database_file='dicom.pickle',
           glob_pattern = '*',
           verbose=1,
           guess_convert = True,
           sort_slice_location = True,
           recursive = True):
    """Scrape a directory of data
    Flags:
      guess_convert -- Translate some common fields into floats and ints.
    """
    
    # Create A db of the entire dataset
    db = []
    s = []
    tags = {}
    for root, dirnames, filenames in os.walk(directory):
        if verbose:
            print('Visiting ' + root)
        if root != directory and not recursive:
            continue
        for fn in fnmatch.filter(filenames, glob_pattern):
            f = os.path.join(root, fn)
            if not pydicom.misc.is_dicom(f):
                if verbose:
                    print('Skipping non-dicom file: '+f)

                continue
            
            if verbose:
                print('Processing', f)
            try:
                ds = pydicom.dcmread(f,stop_before_pixels=True)

                # Merge the ds tags and the ds file_meta tags
                merge_ds = (
                    { k : ds[k] for k in ds.keys() }
                    | { k : ds.file_meta[k] for k in ds.file_meta.keys() })

                h = {}
                h['Filename'] = f
                for k in merge_ds.keys():
                    v = merge_ds[k]
                    key = (v.name
                           .replace(' ','')
                           .replace('\'','')
                           .replace('/','')
                           .replace('[','')
                           .replace(']','')
                           .replace('(','')
                           .replace(')','')
                           .replace('-','')
                           )

                    value = v.value  # Do I need to encode to bytes?
                    # Carry out some common conversion.
                    if guess_convert:
                        if (k.group,k.elem) in [(0x20,0x1041), # Slice location
                                                (0x18,0x50)    # Slice thickness
                                                ]:
                            value = float(value)
                        elif (k.group,k.elem) in [(0x28,0x30), # Pixel spacing
                                                ]:
                            value = tuple(float(f) for f in v.value)

                        elif not ('\\' in str(value) or '[' in str(value)):
                            if v.VR in ['IS','SL','US']:
                                value = int(value)
                            elif isinstance(value, pydicom.valuerep.DSfloat):
                                value = float(value)
                            elif isinstance(value, bytes):
                                value = value.decode('utf-8')
                            else:
                                value = str(value)
                            
                    # Hack to get around pickle limitation
                    if not type(value) in [str,list,dict,tuple,int,float]:
                        value = str(value)
                    # Turn lists to tuples to make immutable
                    if type(value)==list:
                        value = tuple(value) 
                    h[key] = value
                    h['X%04x_%04x'%(k.group,k.elem)]=h[key] # Use both name and group,element syntax
                    tags[key] = (k.group,
                                 k.element,
                                 '(%04x_%04x)'%(k.group,k.elem),
                                 v.VR)
                db += [h]
                if verbose: 
                    print(' Successful', h['Filename'])

            except RuntimeError as e:
                failed_placeholder = {'AccessionNumber': ds.AccessionNumber,  'Filename': h['Filename'], 'ReadError': e} # collect 
                db.append(failed_placeholder)
                if verbose:
                    print(' Failed    ', h['Filename'], e)

    # Create a dataset of everything
    if sort_slice_location:
        db = sorted(db, key=lambda x: 0 if not 'SliceLocation' in x else x['SliceLocation'])
    
    df = pd.DataFrame(db)
    if 'ReadError' not in df.columns: # if this is true, then there were no failures
        df['ReadError'] = np.nan

    tags =  pd.DataFrame(tags,index=['Group','Element','Tag','VR'])
    
    # Save to disk
    if database_file is not None:
        pickle.dump([tags, df],open(database_file,'wb'))
    else:
        return tags,df

    if verbose:
        print('Scanning done. Load result by `tags,df = dp.load()`')

def load(database_file='dicom.pickle'):
    '''Load a database file from the disk'''
    return pd.read_pickle(database_file)

def load_image(filename):
    '''Load an image into a series'''
    tags,df = scrape(database_file = None,
                     glob_pattern = filename,
                     verbose=0)
    return df.iloc[0]

if __name__=='__main__':
    pass
