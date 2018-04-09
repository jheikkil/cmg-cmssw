####from CMGTools.SVfitStandalone import loadlibs
print "moiku"

from TauAnalysis.ClassicSVfit import loadlibs

print "heipu"
####from ROOT import SVfitStandaloneAlgorithm
from ROOT import ClassicSVfit

# importing the python binding to the C++ class from ROOT 

class SVfitAlgo( ClassicSVfit ):
    '''Just an additional wrapper, not really needed :-)
    We just want to illustrate the fact that you could
    use such a wrapper to add functions, attributes, etc,
    in an improved interface to the original C++ class. 
    '''
    def __init__ (self, *args) :
        print "jaanuska"
        super(SVfitAlgo, self).__init__(*args) 
