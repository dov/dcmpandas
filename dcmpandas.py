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

import os
import sys
import glob
import dicom
import pandas as pd
import pickle
import fnmatch

# Default viewer is giv. See github.com/dov/giv .
viewer = 'giv'

def is_dicom(filename):
    try:
        fh = open(filename)
        fh.seek(0x80)
        if fh.read(4) != 'DICM':
            return False
        return True
    except:
        return False
    
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
    success_path = []
    fail_path = []
    read_error = []
    tags = {}
    for root, dirnames, filenames in os.walk(directory):
        if verbose:
            print 'Visiting ' + root
        if root != directory and not recursive:
            continue
        for fn in fnmatch.filter(filenames, glob_pattern):
            f = os.path.join(root, fn)
            if not is_dicom(f):
                continue
            
            if verbose:
                print 'Processing', f
            try:
                ds = dicom.read_file(f,defer_size='10KB')
                h = {}
                h['Filename'] = f
                for k in ds.keys():
                    # Skip images
                    if (k.group,k.elem) == (0x7fe0,0x0010):
                        continue
                    v = ds[k]
                    key = (v.name
                           .replace(' ','')
                           .replace('\'','')
                           .replace('/','')
                           .replace('[','')
                           .replace(']','')
                           .replace('(','')
                           .replace(')','')
                           )
                    # TBD - interpret VR and act accordingly
                    value = str(v.value)

                    # Carry out some common convertion.
                    if guess_convert:
                        if (k.group,k.elem) in [(0x20,0x1041), # Slice location
                                                (0x18,0x50)    # Slice thickness
                                                ]:
                            value = float(value)
                        elif (k.group,k.elem) in [(0x28,0x30), # Pixel spacing
                                                ]:
                            value = [float(f) for f in v.value]

                        elif not ('\\' in value or '[' in value):
                            if v.VR in ['IS','SL','US']:
                                value = int(value)

                    h[key] = value
                    h['X%04x_%04x'%(k.group,k.elem)]=h[key] # Use both name and group,element syntax
                    tags[key] = (k.group,
                                 k.element,
                                 '(%04x_%04x)'%(k.group,k.elem),
                                 v.VR)
                db += [h]
                success_path.append(h['Filename'])
                read_error.append(0)
            except:
                print 'failed:', h['Filename']
                fail_path.append(h['Filename'])
                read_error.append(1)
        
    # Create a dataset of everything
    if sort_slice_location:
        db = sorted(db, key=lambda x: 0 if not 'SliceLocation' in x else x['SliceLocation'])

    df = pd.DataFrame(db)

    tags =  pd.DataFrame(tags,index=['Group','Element','Tag','VR'])
    
    df = pd.merge(df, pd.DataFrame(fail_path,  columns=['Filename']), how="outer")
    df['ReadError'] = read_error

    Save to disk
    if database_file is not None:
        pickle.dump([tags, df],open(database_file,'wb'))
    else:
        return tags,df

    
def load(database_file='dicom.pickle'):
    '''Load a database file from the disk'''
    return pd.read_pickle(database_file)

def load_image(filename):
    '''Load an image into a series'''
    tags,df = scrape(database_file = None,
                     glob_pattern = filename,
                     verbose=0)
    return df.iloc[0]
    
def load(database_file='dicom.pickle'):
    '''Load a database file from the disk'''
    return pandas.read_pickle(database_file)

def load_image(filename):
    '''Load an image into a series'''
    tags,df = scrape(database_file = None,
                     glob_pattern = filename,
                     verbose=0)
    return df.iloc[0]

if __name__=='__main__':
    pass
