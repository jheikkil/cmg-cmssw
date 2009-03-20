#include "GeneratorInterface/ExhumeInterface/interface/ExhumeHadronizer.h"

#include "FWCore/ParameterSet/interface/ParameterSet.h"

#include "HepMC/GenEvent.h"
#include "HepMC/PdfInfo.h"
#include "HepMC/HEPEVT_Wrapper.h"
#include "HepMC/IO_HEPEVT.h"

#include "FWCore/ServiceRegistry/interface/Service.h"
#include "FWCore/MessageLogger/interface/MessageLogger.h"
#include "FWCore/Utilities/interface/RandomNumberGenerator.h"

#include "GeneratorInterface/Core/interface/FortranCallback.h"

#include "GeneratorInterface/LHEInterface/interface/LHERunInfo.h"

#include "SimDataFormats/GeneratorProducts/interface/LHEEventProduct.h"

#include "GeneratorInterface/Core/interface/RNDMEngineAccess.h"

#include "GeneratorInterface/ExhumeInterface/interface/PYR.h"

HepMC::IO_HEPEVT conv;

#include "HepPID/ParticleIDTranslations.hh"

//ExHuME headers
#include "GeneratorInterface/ExhumeInterface/interface/Event.h"
#include "GeneratorInterface/ExhumeInterface/interface/QQ.h"
#include "GeneratorInterface/ExhumeInterface/interface/GG.h"
#include "GeneratorInterface/ExhumeInterface/interface/Higgs.h"

//#include "GeneratorInterface/Pythia6Interface/plugins/Pythia6Hadronizer.h"//not very nice

#include <string>
#include <sstream>

namespace gen
{
extern "C" {
extern struct {
   int mstu[200];
   double paru[200];
   int mstj[200];
   double parj[200];
} pydat1_;
#define pydat1 pydat1_

extern struct {
   int mstp[200];
   double parp[200];
   int msti[200];
   double pari[200];
} pypars_;
#define pypars pypars_

extern struct {
   int mint[400];
   double vint[400];
} pyint1_;
#define pyint1 pyint1_
}

extern "C" {
   void pylist_(int*);
   int  pycomp_(int&);
   void pygive_(const char*, int);
}
#define pylist pylist_
#define pycomp pycomp_
#define pygive pygive_

inline void call_pylist( int mode ){ pylist( &mode ); } 
inline bool call_pygive(const std::string &line)
{
   int numWarn = pydat1.mstu[26];    // # warnings
   int numErr = pydat1.mstu[22];     // # errors

   pygive(line.c_str(), line.length());

   return (pydat1.mstu[26] == numWarn)&&(pydat1.mstu[22] == numErr);
} 
 
ExhumeHadronizer::ExhumeHadronizer(edm::ParameterSet const& pset) 
   : comEnergy_(pset.getParameter<double>("comEnergy")),
     //processPSet_(pset.getParameter<edm::ParameterSet>("ExhumeProcess")),
     //paramsPSet_(pset.getParameter<edm::ParameterSet>("ExhumeParameters")),
     myPSet_(pset),
     hepMCVerbosity_(pset.getUntrackedParameter<bool>("pythiaHepMCVerbosity",false)),
     maxEventsToPrint_(pset.getUntrackedParameter<int>("maxEventsToPrint", 0)),
     pythiaListVerbosity_(pset.getUntrackedParameter<int>("pythiaPylistVerbosity", 0))
{ 

   convertToPDG_ = false;
   if ( pset.exists( "doPDGConvert" ) )
   {
      convertToPDG_ = pset.getParameter<bool>("doPDGConvert");
   }
   
   runInfo().setFilterEfficiency(
      pset.getUntrackedParameter<double>("filterEfficiency", -1.) );

   runInfo().setExternalXSecLO(
      pset.getUntrackedParameter<double>("crossSection", -1.0));

   // Initialize the random engine unconditionally
   //
   randomEngine = &getEngineReference();
  
   //pythia6Hadronizer_ = new Pythia6Hadronizer(pset);  
}

ExhumeHadronizer::~ExhumeHadronizer(){
   //delete pythia6Hadronizer_;
   delete exhumeEvent_;
   delete exhumeProcess_;
}

void ExhumeHadronizer::finalizeEvent()
{
   //pythia6Hadronizer_->finalizeEvent();

   bool lhe = lheEvent() != 0;

   HepMC::PdfInfo pdf;

   // if we are in hadronizer mode, we can pass on information from
   // the LHE input
   if (lhe)
   {
      lheEvent()->fillEventInfo( event().get() );
      lheEvent()->fillPdfInfo( &pdf );
   }

   if (!lhe || event()->signal_process_id() < 0) event()->set_signal_process_id( pypars.msti[0] );
   if (!lhe || event()->event_scale() < 0)       event()->set_event_scale( pypars.pari[16] );
   
   // get pdf info directly from Pythia6 and set it up into HepMC::GenEvent
   // S. Mrenna: Prefer vint block
   //
   if (!lhe || pdf.id1() < 0)      pdf.set_id1( pyint1.mint[14] == 21 ? 0 : pyint1.mint[14] );
   if (!lhe || pdf.id2() < 0)      pdf.set_id2( pyint1.mint[15] == 21 ? 0 : pyint1.mint[15] );
   if (!lhe || pdf.x1() < 0)       pdf.set_x1( pyint1.vint[40] );
   if (!lhe || pdf.x2() < 0)       pdf.set_x2( pyint1.vint[41] );
   if (!lhe || pdf.pdf1() < 0)     pdf.set_pdf1( pyint1.vint[38] / pyint1.vint[40] );
   if (!lhe || pdf.pdf2() < 0)     pdf.set_pdf2( pyint1.vint[39] / pyint1.vint[41] );
   if (!lhe || pdf.scalePDF() < 0) pdf.set_scalePDF( pyint1.vint[50] );

   event()->set_pdf_info( pdf ) ;

   event()->weights().push_back( pyint1.vint[96] );

   // service printouts, if requested
   //
   if (maxEventsToPrint_ > 0) 
   {
      --maxEventsToPrint_;
      if (pythiaListVerbosity_) call_pylist(pythiaListVerbosity_);
      if (hepMCVerbosity_) 
      {
         std::cout << "Event process = " << pypars.msti[0] << std::endl 
	      << "----------------------" << std::endl;
         event()->print();
      }
   }

   return;
}

bool ExhumeHadronizer::generatePartonsAndHadronize()
{

   FortranCallback::getInstance()->resetIterationsPerEvent();
   
   // generate event
   
   exhumeEvent_->Generate();
   exhumeProcess_->Hadronise();

   event().reset( conv.read_next_event() );
   
   return true;
}

bool ExhumeHadronizer::hadronize()
{
   return false;
}

bool ExhumeHadronizer::decay()
{
   return true;
}

bool ExhumeHadronizer::residualDecay()
{
   return true;
}

bool ExhumeHadronizer::initializeForExternalPartons()
{
   return false;
}

bool ExhumeHadronizer::initializeForInternalPartons()
{
   //Exhume Initialization
   //std::string processType = processPSet_.getParameter<std::string>("ProcessType");
   edm::ParameterSet processPSet = myPSet_.getParameter<edm::ParameterSet>("ExhumeProcess");
   std::string processType = processPSet.getParameter<std::string>("ProcessType");
   int sigID = -1;
   if(processType == "Higgs"){
      exhumeProcess_ = new Exhume::Higgs(myPSet_);
      int higgsDecay = processPSet.getParameter<int>("HiggsDecay");
      ((Exhume::Higgs*)exhumeProcess_)->SetHiggsDecay(higgsDecay);
      sigID = 100 + higgsDecay;
   } else if(processType == "QQ"){	
      exhumeProcess_ = new Exhume::QQ(myPSet_);
      int quarkType = processPSet.getParameter<int>("QuarkType");
      double thetaMin = processPSet.getParameter<double>("ThetaMin");
      ((Exhume::QQ*)exhumeProcess_)->SetQuarkType(quarkType);
      ((Exhume::QQ*)exhumeProcess_)->SetThetaMin(thetaMin);
      sigID = 200 + quarkType;
   } else if(processType == "GG"){
      exhumeProcess_ = new Exhume::GG(myPSet_);
      double thetaMin = processPSet.getParameter<double>("ThetaMin");
      ((Exhume::GG*)exhumeProcess_)->SetThetaMin(thetaMin);
      sigID = 300;
   } else{
      sigID = -1;
      throw edm::Exception(edm::errors::Configuration,"ExhumeError") <<" No valid Exhume Process";
   }
    
   pypars.msti[0] = sigID;
   exhumeEvent_ = new Exhume::Event(*exhumeProcess_,randomEngine->getSeed());

   double massRangeLow = processPSet.getParameter<double>("MassRangeLow");
   double massRangeHigh = processPSet.getParameter<double>("MassRangeHigh");
   exhumeEvent_->SetMassRange(massRangeLow,massRangeHigh);
   exhumeEvent_->SetParameterSpace();

   return true;
}

bool ExhumeHadronizer::declareStableParticles( std::vector<int> pdg )
{
   //return pythia6Hadronizer_->declareStableParticles(pdg);

   for ( size_t i=0; i < pdg.size(); i++ )
   {
      int pyCode = pycomp( pdg[i] );
      std::ostringstream pyCard ;
      pyCard << "MDCY(" << pyCode << ",1)=0";
      std::cout << pyCard.str() << std::endl;
      call_pygive( pyCard.str() );
   }
   
   return true;

}

void ExhumeHadronizer::statistics()
{
  std::ostringstream footer_str;

  double cs = exhumeEvent_->CrossSectionCalculation();
  double eff = exhumeEvent_->GetEfficiency();
  std::string name = exhumeProcess_->GetName();

  footer_str << "\n" <<"   You have just been ExHuMEd." << "\n" << "\n";
  footer_str << "   The cross section for process " << name
             << " is " << cs << " fb" << "\n" << "\n";
  footer_str << "   The efficiency of event generation was " << eff << "%" << "\n" << "\n";

  edm::LogInfo("") << footer_str.str();

  if ( !runInfo().internalXSec() )
  {
     runInfo().setInternalXSec( cs );
  }

  return;
}

const char* ExhumeHadronizer::classname() const
{
   return "gen::ExhumeHadronizer";
}

} // namespace gen
