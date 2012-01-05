#ifndef HEMIBALANCEALGOS_H_
#define HEMIBALANCEALGOS_H_

#include "DataFormats/Candidate/interface/Candidate.h"
#include "DataFormats/Math/interface/LorentzVector.h"

#include <cmath>
#include <vector>

namespace cmg{
 
    class Balance{
        public:
            enum Algorithms {PtBalance=0,MassBalance=1};
            typedef std::vector<edm::Ptr<reco::Candidate> > Candidates;
            virtual double balance(const Candidates& a, const Candidates& b) const = 0;
    };

    class PtBalance : public Balance{
        public:
            virtual double balance(const Candidates& a, const Candidates& b) const{
                /** Implements the alpha_T algorithm*/
                double partSum = 0;
                for(Candidates::const_iterator it = a.begin(); it != a.end(); it++){
                       partSum += (*it)->et();
                }
                double fullSum = partSum;
                for(Candidates::const_iterator it = b.begin(); it != b.end(); it++){
                       fullSum += (*it)->et();
                }
                return abs(fullSum - (2*partSum));
            }
    };
    
    class MassBalance : public Balance{
        public:
            virtual double balance(const Candidates& a, const Candidates& b) const{
                /** Implements the Razor algorithm*/
                reco::Candidate::LorentzVector aSum(0., 0., 0., 0.);
                for(Candidates::const_iterator it = a.begin(); it != a.end(); it++){
                    aSum += (*it)->p4();
                }
                reco::Candidate::LorentzVector bSum(0., 0., 0., 0.);                
                for(Candidates::const_iterator it = b.begin(); it != b.end(); it++){
                    bSum += (*it)->p4();
                }
                return aSum.M2() + bSum.M2();
            }
    };
    
}


#endif /*HEMIBALANCEALGOS_H_*/
