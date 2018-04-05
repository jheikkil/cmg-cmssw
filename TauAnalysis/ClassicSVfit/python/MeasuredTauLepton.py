#####from CMGTools.SVfitStandalone import loadlibs
from TauAnalysis.ClassicSVfit import loadlibs

#####from ROOT import svFitStandalone
#from ROOT import TauAnalysis
from ROOT import classic_svFit
# importing the python binding to the C++ class from ROOT 

class MeasuredTauLepton( classic_svFit.MeasuredTauLepton ):
    '''
       decayType : {
                    0:kUndefinedDecayType,
                    1:kTauToHadDecay, 
                    2:kTauToElecDecay,
                    3:kTauToMuDecay,  
                    4:kPrompt
                   }          
    '''
    
    def __init__(self, decayType, pt, eta, phi, mass, decayMode=-1):        
        #print "VOI PEURA"
        super(MeasuredTauLepton, self).__init__(decayType, pt, eta, phi, mass, decayMode) 
