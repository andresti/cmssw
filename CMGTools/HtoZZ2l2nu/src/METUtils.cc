/*
 *  See header file for a description of this class.
 *
 *  $Date: 2011/11/02 15:32:04 $
 *  $Revision: 1.14 $
 *  \author G. Cerminara & D. Trocino
 */

#include "CMGTools/HtoZZ2l2nu/interface/METUtils.h"
#include "DataFormats/Math/interface/deltaR.h"
#include "TVector2.h"
#include "TMath.h"

using namespace std;

namespace METUtils{


std::pair<TVector2, TVector2> defineThrust(const LorentzVector& l1, double sigmaPt1, const LorentzVector& l2, double sigmaPt2, int& event_categ){
  //define the leading and sub-leading lepton
  const LorentzVector &lepton1( l1.pt() > l2.pt() ? l1 : l2);
  const LorentzVector &lepton2( l1.pt() > l2.pt() ? l2 : l1);
  double dphill=fabs(deltaPhi(lepton1.phi(),lepton2.phi()));
  TVector2 lead(lepton1.px(),lepton1.py());
  TVector2 trailer(lepton2.px(),lepton2.py());
  TVector2 reference(lead);

  //define the thrust and dilepton
  TVector2 dil = lead+trailer;
  TVector2 thr = lead-trailer;

  //define the longitudinal and perpendicular axis
  TVector2 longi,perp;
  if(dphill>=TMath::Pi()/2){
      event_categ=OPENANGLE;
      longi = thr.Unit();
      perp = longi.Rotate(TMath::Pi()/2);
      if(perp*reference<0) perp *= -1;
  }else{
      event_categ=COLLIMATED;
      perp=dil.Unit();
      longi = perp.Rotate(TMath::Pi()/2);
      if(longi*reference<0) longi *= -1;
  }
  return std::pair<TVector2, TVector2>(longi,perp);
}

LorentzVector redMET(RedMetType Type, const LorentzVector& theLepton1, double sigmaPt1, const LorentzVector& theLepton2, double sigmaPt2, const LorentzVectorCollection& theJets, const LorentzVector& theMET, bool isZcandidate, stRedMET* out, double kRecoil_l, double kRecoil_t, double kSigmaPt_l, double kSigmaPt_t, double kPerp){
  LorentzVector clusteredMetP4 = -1*(theLepton1+theLepton2);  for(unsigned int i=0;i<theJets.size();i++){clusteredMetP4 -= theJets[i];}
  return redMET(Type, theLepton1, sigmaPt1, theLepton2, sigmaPt2, clusteredMetP4, theMET, theMET, isZcandidate, out, kRecoil_l, kRecoil_t, kSigmaPt_l, kSigmaPt_t, kPerp);
}

LorentzVector redMET(RedMetType Type, const LorentzVector& theLepton1, double sigmaPt1, const LorentzVector& theLepton2, double sigmaPt2, const LorentzVector& theMET1, const LorentzVector& theMET2, bool isZcandidate, stRedMET* out, double kRecoil_l, double kRecoil_t, double kSigmaPt_l, double kSigmaPt_t, double kPerp){
  return redMET(Type, theLepton1, sigmaPt1, theLepton2, sigmaPt2, theMET1, theMET2, theMET2, isZcandidate, out, kRecoil_l, kRecoil_t, kSigmaPt_l, kSigmaPt_t, kPerp);
}


LorentzVector redMET(RedMetType Type, const LorentzVector& theLepton1, double sigmaPt1, const LorentzVector& theLepton2, double sigmaPt2, const LorentzVector& theMET1, const LorentzVector& theMET2, const LorentzVector& theMET3, bool isZcandidate, stRedMET* out, double kRecoil_l, double kRecoil_t, double kSigmaPt_l, double kSigmaPt_t, double kPerp){
  TVector2 a_l,a_t;
  TVector2 redMETxy;
  double redMET_l,redMET_t;
  double redMET;
  int prefRecminRmet;
  int prefRec_l, prefRec_t;
  double recoilProj_l,recoilProj_t;
  double dileptonProj_l,dileptonProj_t;
  double deltaDileptonProj_l, deltaDileptonProj_t;

  //the dilepton candidate
  TVector2 dil(theLepton1.px()+theLepton2.px(),theLepton1.py()+theLepton2.py());

  //define the thrust
   int event_categ;
  if(!isZcandidate){
       std::pair<TVector2, TVector2> thrust=defineThrust(theLepton1,sigmaPt1,theLepton2,sigmaPt2, event_categ);
       a_l=thrust.first;  
       a_t=thrust.second;
  }else {
       dil = TVector2(theLepton1.px(),theLepton1.py());
       a_t = dil.Unit();
       a_l = a_t.Rotate(TMath::Pi()/2);
  }

  //project the dilepton
  dileptonProj_l = dil*a_l;
  dileptonProj_t = dil*a_t;

  //project the met
  TVector2 pfMET1(theMET1.Px(),theMET1.py());
  TVector2 uncl1=pfMET1+dil;
  double uncl1Proj_l = uncl1*a_l;
  double uncl1Proj_t = uncl1*a_t;
  TVector2 pfMET2(theMET2.Px(),theMET2.py());
  TVector2 uncl2=pfMET2+dil;
  double uncl2Proj_l = uncl2*a_l;
  double uncl2Proj_t = uncl2*a_t;
  TVector2 pfMET3(theMET3.Px(),theMET3.py());
  TVector2 uncl3=pfMET3+dil;
  double uncl3Proj_l = uncl3*a_l;
  double uncl3Proj_t = uncl3*a_t;

  //take the minimum recoil possible depending on the event category type
  recoilProj_l = min(-1.0*uncl1Proj_l, min(-1.0*uncl2Proj_l,-1.0*uncl3Proj_l));
  recoilProj_l=min(recoilProj_l,0.);
  recoilProj_t = min(-1.0*uncl1Proj_t, min(-1.0*uncl2Proj_t,-1.0*uncl3Proj_t));
  recoilProj_t=min(recoilProj_t,0.);   

  //propagate the lepton uncertainty (if larger than unity assume 100% rel. uncertainty)                                                                                                                                                                                                                                    
  if(!isZcandidate){
      double relErrPt1 = min(sigmaPt1/theLepton1.pt(), 1.);
      double relErrPt2 = min(sigmaPt2/theLepton2.pt(), 1.);
      LorentzVector loweredLepton1 = theLepton1*(1.0-relErrPt1);
      LorentzVector loweredLepton2 = theLepton2*(1.0-relErrPt2);
      std::pair<TVector2, TVector2> loweredThrust=defineThrust(loweredLepton1,sigmaPt1,loweredLepton2,sigmaPt2, event_categ);
      float loweredDileptonProj_t = dil*loweredThrust.second;
      deltaDileptonProj_t = loweredDileptonProj_t - dileptonProj_t;
      deltaDileptonProj_l = ( -relErrPt1*TVector2(theLepton1.px(),theLepton1.py()) + relErrPt2*TVector2(theLepton2.px(),theLepton2.py()) )*a_l;
  }else{
      deltaDileptonProj_t=0;
      deltaDileptonProj_l=0;
  }

  double uncl1RedMet_l = dileptonProj_l - kRecoil_l*uncl1Proj_l + kSigmaPt_l*deltaDileptonProj_l;
  double uncl1RedMet_t = dileptonProj_t - kRecoil_t*uncl1Proj_t + kSigmaPt_t*deltaDileptonProj_t;
  double uncl1RedMet   = sqrt(pow(uncl1RedMet_l,2)+pow(uncl1RedMet_t,2));

  double uncl2RedMet_l = dileptonProj_l - kRecoil_l*uncl2Proj_l + kSigmaPt_l*deltaDileptonProj_l;
  double uncl2RedMet_t = dileptonProj_t - kRecoil_t*uncl2Proj_t + kSigmaPt_t*deltaDileptonProj_t;
  double uncl2RedMet   = sqrt(pow(uncl2RedMet_l,2)+pow(uncl2RedMet_t,2));

  double uncl3RedMet_l = dileptonProj_l - kRecoil_l*uncl3Proj_l + kSigmaPt_l*deltaDileptonProj_l;
  double uncl3RedMet_t = dileptonProj_t - kRecoil_t*uncl3Proj_t + kSigmaPt_t*deltaDileptonProj_t;
  double uncl3RedMet   = sqrt(pow(uncl3RedMet_l,2)+pow(uncl3RedMet_t,2));

  if(Type==D0){
     //
     // D0 ORIGINAL VERSION
     //
     //recoil is minimized independently
     recoilProj_l = min(-1.0*uncl1Proj_l, min(-1.0*uncl2Proj_l,-1.0*uncl3Proj_l));
     recoilProj_l = min(recoilProj_l,0.);
     prefRec_l    = ( (-1.0*uncl1Proj_l)< min(-1.*uncl2Proj_l,-1.*uncl3Proj_l) ? CLUSTERED : UNCLUSTERED);

     recoilProj_t = min(-1.0*uncl1Proj_t, min(-1.0*uncl2Proj_t,-1.0*uncl3Proj_t));
     recoilProj_t = min(recoilProj_t,0.);
     prefRec_t    = ( (-1.0*uncl1Proj_t)<min(-1.*(uncl2Proj_t),-1.*(uncl3Proj_t)) ? CLUSTERED : UNCLUSTERED);
  
     //compute the reduced met components
     redMET_l = max( (dileptonProj_l + kRecoil_l*recoilProj_l + kSigmaPt_l*deltaDileptonProj_l), 0.);
     redMET_t = max( (dileptonProj_t + kRecoil_t*recoilProj_t + kSigmaPt_t*deltaDileptonProj_t), 0.);
     redMET   = sqrt( pow(redMET_l,2) + pow(redMET_t,2) );
     redMETxy =redMET_l*a_l+redMET_t*a_t;

  }else if(Type==MINIMIZED){
     //
     // CMS MINIMIZED VERSION
     //   
     if(uncl1RedMet<uncl2RedMet && uncl1RedMet<uncl3RedMet){
        prefRecminRmet         = UNCLUSTERED;
        redMET_l = uncl1RedMet_l;
        redMET_t = uncl1RedMet_t;
     }else if(uncl2RedMet<uncl1RedMet && uncl2RedMet<uncl3RedMet){
        prefRecminRmet         = CLUSTERED;
        redMET_l = uncl2RedMet_l;
        redMET_t = uncl2RedMet_t;
     }else{
        prefRecminRmet         = CLUSTERED;
        redMET_l = uncl3RedMet_l;
        redMET_t = uncl3RedMet_t;
     }
     redMET   = sqrt(pow(redMET_l,2)+pow(redMET_t,2));
     redMETxy =redMET_l*a_l+redMET_t*a_t;

  }else if(INDEPENDENTLYMINIMIZED){
     //
     // CMS INDEPEDENT MINIMIZATION VERSION
     //
     prefRec_l     = (fabs(uncl1RedMet_l) < fabs(uncl2RedMet_l) ? UNCLUSTERED : CLUSTERED );
     prefRec_t     = (fabs(uncl1RedMet_t) < fabs(uncl2RedMet_t) ? UNCLUSTERED : CLUSTERED );

     if(fabs(uncl1RedMet_l)<fabs(uncl2RedMet_l) && fabs(uncl1RedMet_l)<fabs(uncl3RedMet_l)){
        prefRec_l  = UNCLUSTERED;
        redMET_l   = uncl1RedMet_l;
     }else if(fabs(uncl2RedMet_l)<fabs(uncl1RedMet_l) && fabs(uncl2RedMet_l)<fabs(uncl3RedMet_l)){
        prefRec_l  = CLUSTERED;
        redMET_l   = uncl2RedMet_l;
     }else{
        prefRec_l  = CLUSTERED;
        redMET_l   = uncl3RedMet_l;
     }

     if(fabs(uncl1RedMet_t)<fabs(uncl2RedMet_t) && fabs(uncl1RedMet_t)<fabs(uncl3RedMet_t)){
        prefRec_t  = UNCLUSTERED;
        redMET_t   = uncl1RedMet_t;
     }else if(fabs(uncl2RedMet_t)<fabs(uncl1RedMet_t) && fabs(uncl2RedMet_t)<fabs(uncl3RedMet_t)){
        prefRec_t  = CLUSTERED;
        redMET_t   = uncl2RedMet_t;
     }else{
        prefRec_t  = CLUSTERED;
        redMET_t   = uncl3RedMet_t;
     }
     redMET = sqrt(pow(redMET_l,2)+pow(redMET_t,2));
     redMETxy=redMET_l*a_l+redMET_t*a_t;
  }


  if(out){
     out->a_l = a_l;
     out->a_t = a_t;
     out->redMETxy = redMETxy;
     out->redMET_l = redMET_l;
     out->redMET_t = redMET_t;
  }
  return LorentzVector( redMETxy.X(),redMETxy.Y(),0,redMET);  
}




  double getRedMETCut(int eventCategory, int workingpoint){
    double cut = 0;
    switch(eventCategory){
      case EventCategory::EQ0JETS :
	if(workingpoint==MEDIUMWP) cut=30.5;
	if(workingpoint==TIGHTWP)  cut=39.0;
	break;
      case EventCategory::EQ1JETS :
	if(workingpoint==MEDIUMWP) cut=38.8;
	if(workingpoint==TIGHTWP)  cut=52.4;
	break;
      case EventCategory::GEQ2JETS :
	if(workingpoint==MEDIUMWP) cut=50.8;
	if(workingpoint==TIGHTWP)  cut=78.7;
	break;
      case EventCategory::VBF :
	if(workingpoint==MEDIUMWP) cut=57.36;  //the tuned point 56.3
	if(workingpoint==TIGHTWP)  cut=60.20;
	break;
      }
    return cut;
  }


}
