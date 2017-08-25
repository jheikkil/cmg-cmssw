import ROOT

from PhysicsTools.Heppy.analyzers.core.Analyzer import Analyzer
from PhysicsTools.Heppy.analyzers.core.AutoHandle import AutoHandle
from PhysicsTools.Heppy.analyzers.core.AutoFillTreeProducer  import NTupleVariable
from PhysicsTools.HeppyCore.utils.deltar import matchObjectCollection, matchObjectCollection3
import PhysicsTools.HeppyCore.framework.config as cfg
        
class TriggerMatchAnalyzer( Analyzer ):
    def __init__(self, cfg_ana, cfg_comp, looperName ):
        super(TriggerMatchAnalyzer,self).__init__(cfg_ana,cfg_comp,looperName)
        self.processName = getattr(self.cfg_ana,"processName","PAT")
        self.fallbackName = getattr(self.cfg_ana,"fallbackProcessName","RECO")
        self.unpackPathNames = getattr(self.cfg_ana,"unpackPathNames",True)
        self.label = self.cfg_ana.label
        self.trgObjSelectors = []
        self.trgObjSelectors.extend(getattr(self.cfg_ana,"trgObjSelectors",[]))
        self.collToMatch = getattr(self.cfg_ana,"collToMatch",None)
        self.collMatchSelectors = []
        self.collMatchSelectors.extend(getattr(self.cfg_ana,"collMatchSelectors",[]))
        self.collMatchDRCut = getattr(self.cfg_ana,"collMatchDRCut",0.3)
        self.id = getattr(self.cfg_ana,"id", 11)
        self.pt1 = getattr(self.cfg_ana,"pt1", 20)
        self.pt2 = getattr(self.cfg_ana,"pt2", 11)
        self.applyCuts = getattr(self.cfg_ana,"applyCuts",False)
        if self.collToMatch and not hasattr(self.cfg_ana,"univoqueMatching"): raise RuntimeError("Please specify if the matching to trigger objects should be 1-to-1 or 1-to-many")
        self.match1To1 = getattr(self.cfg_ana,"univoqueMatching",True)

    def declareHandles(self):
        super(TriggerMatchAnalyzer, self).declareHandles()
        self.handles['TriggerBits'] = AutoHandle( ('TriggerResults','','HLT'), 'edm::TriggerResults' )
        fallback = ( 'selectedPatTrigger','', self.fallbackName) if self.fallbackName else None
        self.handles['TriggerObjects'] = AutoHandle( ('selectedPatTrigger','',self.processName), 'std::vector<pat::TriggerObjectStandAlone>', fallbackLabel=fallback )

    def beginLoop(self, setup):
        super(TriggerMatchAnalyzer,self).beginLoop(setup)

    def process(self, event):
        self.readCollections( event.input )
        triggerBits = self.handles['TriggerBits'].product()
        allTriggerObjects = self.handles['TriggerObjects'].product()
        names = event.input.object().triggerNames(triggerBits)
        for ob in allTriggerObjects: ob.unpackPathNames(names)
        #print "all:"
        #for ob in allTriggerObjects: 
        #    print ob.collection()
        #    print ob.pt()
        #    print ob.eta()
        #    print ob.phi()
        triggerObjects = [ob for ob in allTriggerObjects if False not in [sel(ob) for sel in self.trgObjSelectors]]

       # print "final"
       # for obj in triggerObjects:
       #     print obj.collection()
       #     print obj.pt()
       #     print obj.eta()
       #     print obj.phi()
       #     print "filterlabels"
       #     print [ l for l in obj.filterLabels() ]
       #     print "paths"
       #     print [ l for l in obj.pathNames() ] 
       #     print "fired"
       #     print [ l for l in obj.pathNames(True) ]


        setattr(event,'trgObjects_'+self.label,triggerObjects)

        if self.applyCuts:
            leptons = getattr(event,self.collToMatch)
            objects = []
            for lepton in leptons:
               if abs(lepton.pdgId())==11:
                   label = "Els"
               elif abs(lepton.pdgId())==13:
                   label = "Mus"             
               else:
                   label = ""  
               if hasattr(lepton,'matchedTrgObj'+label):
                   ob = getattr(lepton,'matchedTrgObj'+label)
                   if ob:
                       objects += [ob]

            if len(objects)>1:
                return True
            else:
                return False             

        if self.collToMatch:
            #print "OK, LETS DO IT"
            #print "DR CUT AT TRIGGERMATCH"
            #print self.collMatchDRCut
            #print "ONE TO ONE?"
            #print self.match1To1
            tcoll = getattr(event,self.collToMatch)
           # tcoll = [lep for lep in tcoll if abs(lep.pdgId()) == self.id]
           # tcoll.sort(key=lambda x: x.pt(), reverse=True)         
            #if len(tcoll)>1:
              #  if tcoll[0].pt()>self.pt1 and tcoll[1].pt()>self.pt2:
            doubleandselector = lambda lep,ob: False if False in [sel(lep,ob) for sel in self.collMatchSelectors] else True
            pairs = matchObjectCollection3(tcoll,triggerObjects,deltaRMax=self.collMatchDRCut,filter=doubleandselector) if self.match1To1 else matchObjectCollection(tcoll,triggerObjects,self.collMatchDRCut,filter=doubleandselector)
            for ob in getattr(event,'trgObjects_'+self.label):
                types = ", ".join([str(f) for f in ob.filterIds()])
                filters = ", ".join([str(f) for f in ob.filterLabels()])
                #filters = ", ".join([])
                paths = ", ".join([("%s***" if f in set(ob.pathNames(True)) else "%s")%f for f in ob.pathNames()]) # asterisks indicate final paths fired by this object, see pat::TriggerObjectStandAlone class
                #print 'Trigger object: pt=%.2f, eta=%.2f, phi=%.2f, collection=%s, type_ids=%s, filters=%s, paths=%s'%(ob.pt(),ob.eta(),ob.phi(),ob.collection(),types,filters,paths)

            for lep in tcoll: 
                #print pairs[lep]
                if pairs[lep] != None:
                    #print pairs[lep]
                    #print len(pairs[lep])
                    #print "TAMA LEPTONI MATCH"
                    #print lep
                    #print "JEE"
                    setattr(lep,'matchedTrgObj'+self.label,pairs[lep])
                    #ob = getattr(lep,'matchedTrgObj'+self.label)
                    #if ob: mstring = 'trigger obj with pt=%.2f, eta=%.2f, phi=%.2f, collection=%s'%(ob.pt(),ob.eta(),ob.phi(),ob.collection())
                    #print 'Lepton pt=%.2f, eta=%.2f, phi=%.2f matched to %s'%(lep.pt(),lep.eta(),lep.phi(),mstring) 

        if self.verbose:
            print 'Verbose debug for triggerMatchAnalyzer %s'%self.label
            for ob in getattr(event,'trgObjects_'+self.label):
                types = ", ".join([str(f) for f in ob.filterIds()])
                filters = ", ".join([str(f) for f in ob.filterLabels()])
                paths = ", ".join([("%s***" if f in set(ob.pathNames(True)) else "%s")%f for f in ob.pathNames()]) # asterisks indicate final paths fired by this object, see pat::TriggerObjectStandAlone class
                print 'Trigger object: pt=%.2f, eta=%.2f, phi=%.2f, collection=%s, type_ids=%s, filters=%s, paths=%s'%(ob.pt(),ob.eta(),ob.phi(),ob.collection(),types,filters,paths)
            if self.collToMatch:
                for lep in tcoll:
                    mstring = 'None'
                    ob = getattr(lep,'matchedTrgObj'+self.label)
                    if ob: mstring = 'trigger obj with pt=%.2f, eta=%.2f, phi=%.2f, collection=%s'%(ob.pt(),ob.eta(),ob.phi(),ob.collection())
                    print 'Lepton pt=%.2f, eta=%.2f, phi=%.2f matched to %s'%(lep.pt(),lep.eta(),lep.phi(),mstring)

        return True


setattr(TriggerMatchAnalyzer,"defaultConfig",cfg.Analyzer(
    TriggerMatchAnalyzer, name="TriggerMatchAnalyzerDefault",
    label='DefaultTrigObjSelection',
    processName = 'PAT',
    fallbackProcessName = 'RECO',
    unpackPathNames = True,
    trgObjSelectors = [],
    collToMatch = None,
    collMatchSelectors = [],
    collMatchDRCut = 0.3,
    univoqueMatching = True,
    verbose = False
)
)


