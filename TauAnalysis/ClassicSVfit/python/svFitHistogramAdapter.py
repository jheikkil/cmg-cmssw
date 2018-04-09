from CMGTools.TauAnalysis.svFitHistogramAdapter import loadlibs

from ROOT import svFitHistogramAdapter

# importing the python binding to the C++ class from ROOT 

class svFitHistogramAdapter( ClassicSVfit.svFitHistogramAdapter ):
    '''Just an additional wrapper, not really needed :-)
    We just want to illustrate the fact that you could
    use such a wrapper to add functions, attributes, etc,
    in an improved interface to the original C++ class. 
    '''
    def __init__ (self, *args) :
        super(svFitHistogramAdapter, self).__init__(*args) 

