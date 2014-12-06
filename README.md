# dcmpandas - a library for loading dicom directories into pandas

* Author: Dov Grobgeld <dov.grobgeld@gmail.com>
* Created: 2014-12-06 Sat
* Keywords: Dicom, Python, Pandas
* URL: <http://github.com/dov/dcmpandas>
* Version: 0.1

# Description

dcmpandas is a scraper and query system for interacting with a 
directory of dicom images. It builds a database of the tags
of all images in the database, and then allows querying 
these tags through the flexible pandas syntax.

# Example 

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

    In [5]: df.groupby(['SeriesDescription','SeriesNumber']).size()
    Out[5]: 
    SeriesDescription             SeriesNumber
    Ax 3D GRE T1                  4               60
    Ax Diff ep2d_mddw_30          5               31
    Ax Diff ep2d_mddw_30_a/p rpt  8               31
    Ax t2_tse                     2               60
    Ax t2_tse_spair               3               60
    dtype: int64

    In [6]: s2 = df[df.SeriesNumber==2]
    In [7]: s2[['Filename','SliceLocation']]
         Filename  SliceLocation
    1    48863538     -86.537117
    4    48863524     -83.537117
    7    48863510     -80.537117
    10   48863496     -77.537117
    :
    166  48862768      78.462883
    168  48862754      81.462883
    172  48862740      84.462883
    175  48862726      87.462883
    178  48862712      90.462883
    In [8]: dp.view(s2.Filename)
    >>> Opens up an external viewer and shows image in slice location 
    In [9]: tags.SeriesDescription
    
# Image viewing

dcmpandas uses the image viewer giv from http://github.com/dov/giv 
for viewing dicom images through the dcmpandas.view command.

# TODO

* Improve windows friendliness of the dcmpandas.view command.

