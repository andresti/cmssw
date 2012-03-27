## import skeleton process
from PhysicsTools.PatAlgos.patTemplate_cfg import *

### MASTER FLAGS  ######################################################################

# turn this on if you want to pick a relval in input (see below)
## pickRelVal = False

# turn on when running on MC
runOnMC = False

runCMG = True

# choose which kind of scale correction/MC smearing should be applied for electrons. Options are:
if runOnMC :
    gsfEleCorrDataset = "Fall11"
#    gsfEleCorrDataset = "Summer11"
else :
    gsfEleCorrDataset = "Jan16ReReco" 
#    gsfEleCorrDataset = "ReReco" 
#    gsfEleCorrDataset = "Prompt" 

# AK5 sequence with pileup substraction is the default
# the other sequences can be turned off with the following flags.
runAK5NoPUSub = True 

hpsTaus = True
doEmbedPFCandidatesInTaus = True
doJetPileUpCorrection = True


#add the L2L3Residual corrections only for data
if runOnMC:#MC
    jetCorrections=['L1FastJet','L2Relative','L3Absolute']
else:#Data
    jetCorrections=['L1FastJet','L2Relative','L3Absolute','L2L3Residual']

# process.load("CommonTools.ParticleFlow.Sources.source_ZtoMus_DBS_cfi")
process.options   = cms.untracked.PSet( wantSummary = cms.untracked.bool(True))

process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(2000) )
process.MessageLogger.cerr.FwkReport.reportEvery = 10

from CMGTools.Common.Tools.getGlobalTag import getGlobalTag
process.GlobalTag.globaltag = cms.string(getGlobalTag(runOnMC))

sep_line = "-" * 50
print sep_line
print 'running the following PF2PAT+PAT sequences:'
print '\tAK5'
if runAK5NoPUSub: print '\tAK5NoPUSub'
print 'embedding in taus: ', doEmbedPFCandidatesInTaus
print 'HPS taus         : ', hpsTaus
print 'produce CMG tuple: ', runCMG
print 'run on MC        : ', runOnMC
print sep_line
print 'Global tag       : ', process.GlobalTag.globaltag
print sep_line

### SOURCE DEFINITION  ################################################################

# print 'generate source'

from CMGTools.Production.datasetToSource import *
process.source = datasetToSource(
    # to test MC:
    # 'cmgtools',
    # '/TauPlusX/Run2011A-May10ReReco-v1/AOD/V3',
    # 'cmgtools_group',
    # '/DYJetsToLL_TuneZ2_M-50_7TeV-madgraph-tauola/Fall11-PU_S6_START42_V14B-v1/AODSIM/V3',
    # to test Data:
    'cmgtools_group',
    #'/DoubleMu/Run2011A-05Aug2011-v1/AOD/V3',
    '/DYJetsToLL_TuneZ2_M-50_7TeV-madgraph-tauola/Fall11-PU_S6_START42_V14B-v1/AODSIM/V4'
    # '.*root'
    )

## for testing in 5X
## process.source.fileNames = cms.untracked.vstring(
##     '/store/relval/CMSSW_5_1_2/RelValQCD_FlatPt_15_3000/GEN-SIM-RECO/START50_V15A-v1/0240/B830CB12-1861-E111-B1BD-001A92811728.root'
##    # '/store/relval/CMSSW_5_1_2/DoubleMu/RECO/GR_R_50_V12_RelVal_zMu2011B-v1/0237/182F7808-BD60-E111-943C-001A92810AEA.root'
##     )

# ProductionTasks.py will override this change
process.source.fileNames = process.source.fileNames[:10]

print 'PF2PAT+PAT+CMG for files:'
print process.source.fileNames

# sys.exit(1)

### DEFINITION OF THE PF2PAT+PAT SEQUENCES #############################################



# load the PAT config
process.load("PhysicsTools.PatAlgos.patSequences_cff")
process.out.fileName = cms.untracked.string('patTuple_PF2PAT.root')

# Configure PAT to use PF2PAT instead of AOD sources
# this function will modify the PAT sequences. It is currently 
# not possible to run PF2PAT+PAT and standart PAT at the same time
from PhysicsTools.PatAlgos.tools.pfTools import *

# ---------------- rho calculation for JEC ----------------------

from RecoJets.JetProducers.kt4PFJets_cfi import kt4PFJets
process.kt6PFJets = kt4PFJets.clone(
    rParams = cms.double(0.6),
    doAreaFastjet = cms.bool(True),
    doRhoFastjet = cms.bool(True),
)

#compute rho correction for lepton isolation
process.kt6PFJetsForIso = process.kt6PFJets.clone( Rho_EtaMax = cms.double(2.5), Ghost_EtaMax = cms.double(2.5) )

# ---------------- Sequence AK5 ----------------------


process.eIdSequence = cms.Sequence()

# PF2PAT+PAT sequence 1:
# no lepton cleaning, AK5PFJets

postfixAK5 = "AK5"
jetAlgoAK5="AK5"

#COLIN : we will need to add the L2L3Residual when they become available! also check the other calls to the usePF2PAT function. 
usePF2PAT(process,runPF2PAT=True, jetAlgo=jetAlgoAK5, runOnMC=runOnMC, postfix=postfixAK5,
          jetCorrections=('AK5PFchs', jetCorrections))

# removing stupid useless stuff from our muons:
getattr(process,"patMuons"+postfixAK5).embedCaloMETMuonCorrs = False 
getattr(process,"patMuons"+postfixAK5).embedTcMETMuonCorrs = False
#but embed the tracker track for cutting on 
getattr(process,"patMuons"+postfixAK5).embedTrack = True

# removing default cuts on muons 
getattr(process,"pfMuonsFromVertexAK5").dzCut = 99
getattr(process,"pfMuonsFromVertexAK5").d0Cut = 99
getattr(process,"pfSelectedMuonsAK5").cut="pt()>3"

# removing default cuts on electrons 
getattr(process,"pfElectronsFromVertexAK5").dzCut = 99
getattr(process,"pfElectronsFromVertexAK5").d0Cut = 99
getattr(process,"pfSelectedElectronsAK5").cut="pt()>5"


if doJetPileUpCorrection:
    from CommonTools.ParticleFlow.Tools.enablePileUpCorrection import enablePileUpCorrection
    enablePileUpCorrection( process, postfix=postfixAK5)

#configure the taus
from CMGTools.Common.PAT.tauTools import *
if doEmbedPFCandidatesInTaus:
    embedPFCandidatesInTaus( process, postfix=postfixAK5, enable=True )
if hpsTaus:
    #Lucie : HPS is the default in 52X & V08-08-11-03, see PhysicsTools/PatAlgos/python/Tools/pfTools.py. Following line not needed (crash) in 5X.
    import os
    if os.environ['CMSSW_VERSION'] < "CMSSW_5_0":
        adaptPFTaus(process,"hpsPFTau",postfix=postfixAK5) 
    #  note that the following disables the tau cleaning in patJets
    adaptSelectedPFJetForHPSTau(process,jetSelection="pt()>15.0",postfix=postfixAK5)
    # currently (Sept 27,2011) there are three sets of tau isolation discriminators better to choose in CMG tuples.
    removeHPSTauIsolation(process,postfix=postfixAK5)

   
# curing a weird bug in PAT..
from CMGTools.Common.PAT.removePhotonMatching import removePhotonMatching
removePhotonMatching( process, postfixAK5 )

# use non pileup substracted rho as in the Jan2012 JEC set
getattr(process,"patJetCorrFactors"+postfixAK5).rho = cms.InputTag("kt6PFJets","rho")

getattr(process,"pfNoMuon"+postfixAK5).enable = False 
getattr(process,"pfNoElectron"+postfixAK5).enable = False 
getattr(process,"pfNoTau"+postfixAK5).enable = False 
getattr(process,"pfNoJet"+postfixAK5).enable = True
getattr(process,"pfIsolatedMuons"+postfixAK5).isolationCut = 999999
getattr(process,"pfIsolatedElectrons"+postfixAK5).isolationCut = 999999

# insert the PFMET sifnificance calculation
from CMGTools.Common.PAT.addMETSignificance_cff import addMETSig
addMETSig( process, postfixAK5 )


# adding "standard muons and electons"
# (made from all reco muons, and all gsf electrons, respectively)
from CMGTools.Common.PAT.addStdLeptons import addStdMuons
from CMGTools.Common.PAT.addStdLeptons import addStdElectrons
stdMuonSeq = addStdMuons( process, postfixAK5, 'StdLep', 'pt()>3', runOnMC )
stdElectronSeq = addStdElectrons( process, postfixAK5, 'StdLep', 'pt()>5', runOnMC )

# adding vbtf and cic electron IDs to both electron collections
from CMGTools.Common.PAT.addPATElectronID_cff import addPATElectronID
addPATElectronID( process, 'patDefaultSequence', postfixAK5)
addPATElectronID( process, 'stdElectronSequence', postfixAK5+'StdLep')

# adding MIT electron id
from CMGTools.Common.PAT.addMITElectronID import addMITElectronID
addMITElectronID( process, 'selectedPatElectrons', 'patDefaultSequence', postfixAK5)
addMITElectronID( process, 'selectedPatElectrons', 'stdElectronSequence', postfixAK5+'StdLep')


# # adding custom detector based iso deposit ---> !!! this works only on V4 event content !!!
from RecoLocalCalo.EcalRecAlgos.EcalSeverityLevelESProducer_cfi import *
from CMGTools.Common.PAT.addLeptCustomIsoDeposit_cff import addMuonCustomIsoDeposit
from CMGTools.Common.PAT.addLeptCustomIsoDeposit_cff import addElectronCustomIsoDeposit
addMuonCustomIsoDeposit( process, 'patDefaultSequence', postfixAK5)
addMuonCustomIsoDeposit( process, 'stdElectronSequence', postfixAK5+'StdLep')
addElectronCustomIsoDeposit( process, 'patDefaultSequence', postfixAK5)
addElectronCustomIsoDeposit( process, 'stdElectronSequence', postfixAK5+'StdLep')


# ---------------- Sequence AK5NoPUSub, pfNoPileUp switched off ---------------

# PF2PAT+PAT sequence 2:
# pfNoPileUp switched off, AK5PFJets. This sequence is a clone of the AK5 sequence defined previously.

if runAK5NoPUSub:
    print 'Preparing AK5NoPUSub sequence...',

    postfixNoPUSub = 'NoPUSub'
    postfixAK5NoPUSub = postfixAK5+postfixNoPUSub

    from PhysicsTools.PatAlgos.tools.helpers import cloneProcessingSnippet
    cloneProcessingSnippet(process, getattr(process, 'patPF2PATSequence'+postfixAK5), postfixNoPUSub)

    getattr(process,"pfNoPileUp"+postfixAK5NoPUSub).enable = False
    getattr(process,"patJetCorrFactors"+postfixAK5NoPUSub).payload = "AK5PF"
    print 'Done'


# ---------------- Common stuff ---------------

process.load('CMGTools.Common.gen_cff')


process.load("PhysicsTools.PatAlgos.triggerLayer1.triggerProducer_cff")
process.patTrigger.processName = cms.string('*')

### PATH DEFINITION #############################################

# counters that can be used at analysis level to know the processed events
process.prePathCounter = cms.EDProducer("EventCountProducer")
process.postPathCounter = cms.EDProducer("EventCountProducer")

# trigger information (no selection)

process.p = cms.Path( process.prePathCounter + process.patTriggerDefaultSequence )
process.p += process.kt6PFJets
process.p += process.kt6PFJetsForIso

# PF2PAT+PAT ---

process.p += getattr(process,"patPF2PATSequence"+postfixAK5)

process.stdLeptonSequence = cms.Sequence(
    stdMuonSeq +
    stdElectronSeq 
    )
process.p += process.stdLeptonSequence


if runAK5NoPUSub:
    process.p += getattr(process,"patPF2PATSequence"+postfixAK5NoPUSub)


# event cleaning (in tagging mode, no event rejected)

process.load('CMGTools.Common.eventCleaning.eventCleaning_cff')

process.p += process.eventCleaningSequence

# gen ---- 

if runOnMC:
    process.p += process.genSequence 

process.p += getattr(process,"postPathCounter") 
 
# CMG ---

if runCMG:
    
    process.load('CMGTools.Common.analysis_cff')
    # running on PFAOD -> calo objects are not available.
    # we'll need to reactivate caloMET, though
    # process.p += process.analysisSequence

    from CMGTools.Common.Tools.visitorUtils import replacePostfix
    
    from CMGTools.Common.Tools.tuneCMGSequences import * 
    tuneCMGSequences(process, postpostfix='CMG')

    process.p += process.analysisSequence

    from CMGTools.Common.PAT.addStdLeptons import addCmgMuons, addCmgElectrons
    process.cmgStdLeptonSequence = cms.Sequence(
        addCmgMuons( process, 'StdLep', 'selectedPatMuonsAK5StdLep'  ) +
        addCmgElectrons( process, 'StdLep', 'selectedPatElectronsAK5StdLep'  ) 
        )
    process.cmgObjectSequence += process.cmgStdLeptonSequence

    if runAK5NoPUSub:
        cloneProcessingSnippet(process, getattr(process, 'analysisSequence'), 'AK5NoPUSubCMG')
        replacePostfix(getattr(process,"analysisSequenceAK5NoPUSubCMG"),'AK5','AK5NoPUSub') 
        process.p += process.analysisSequenceAK5NoPUSubCMG


### OUTPUT DEFINITION #############################################

# PF2PAT+PAT ---

# Add PF2PAT output to the created file
from PhysicsTools.PatAlgos.patEventContent_cff import patEventContentNoCleaning, patTriggerEventContent, patTriggerStandAloneEventContent
process.out.outputCommands = cms.untracked.vstring('drop *',
                                                   *patEventContentNoCleaning
                                                   )
# add trigger information to the pat-tuple
process.out.outputCommands += patTriggerEventContent
process.out.outputCommands += patTriggerStandAloneEventContent

from CMGTools.Common.eventContent.everything_cff import everything 
process.out.outputCommands.extend( everything )

# tuning the PAT event content to our needs
from CMGTools.Common.eventContent.patEventContentCMG_cff import patEventContentCMG
process.out.outputCommands.extend( patEventContentCMG )

# add counters to the pat-tuple
process.out.outputCommands.extend(['keep edmMergeableCounter_*_*_*'])

# CMG ---


process.outcmg = cms.OutputModule(
    "PoolOutputModule",
    fileName = cms.untracked.string('tree_CMG.root'),
    SelectEvents   = cms.untracked.PSet( SelectEvents = cms.vstring('p') ),
    outputCommands = everything,
    dropMetaData = cms.untracked.string('PRIOR')
    )
process.outcmg.outputCommands.extend( [ # 'keep patMuons_selectedPatMuonsAK5*_*_*',
                                        # 'keep patElectrons_selectedPatElectronAK5*_*_*',
                                       'keep edmMergeableCounter_*_*_*'] )

if runCMG:
    process.outpath += process.outcmg


#Patrick: Make the embedded track available for electrons (curing a bug in PAT)
process.patElectronsAK5.embedTrack = True
process.patElectronsAK5StdLep.embedTrack = True

 
# electron energy-scale corrections (from Claude C., Paramatti & al.)
print sep_line
print "Replacing gsfElectrons with calibratedGsfElectrons..."
for modulename in process.p.moduleNames():
    module = getattr(process, modulename)
    ml = dir(module)
    for attr in ml:
        v = getattr(module,attr)
        if (isinstance(v, cms.InputTag) and v == cms.InputTag("gsfElectrons")):
            setattr(module,attr,"calibratedGsfElectrons")
            #print "Setting ",
            #print module,
            #print ".", 
            #print attr,
            #print " = ", 
            #print getattr(module,attr)
process.load("EgammaCalibratedGsfElectrons.CalibratedElectronProducers.calibratedGsfElectrons_cfi")
process.calibratedGsfElectrons.isMC = cms.bool(runOnMC)
process.calibratedGsfElectrons.updateEnergyError = cms.bool(True)

process.RandomNumberGeneratorService = cms.Service("RandomNumberGeneratorService",

    # Include a PSet for each module label that needs a
    # random engine.  The name is the module label.
    # You must supply a seed or seeds.
    # Optionally an engine type can be specified
    #t1 = cms.PSet(
    #    initialSeed = cms.untracked.uint32(81)
    #),
    calibratedGsfElectrons = cms.PSet(
        initialSeed = cms.untracked.uint32(1),
        engineName = cms.untracked.string('TRandom3')
    ),
)

if gsfEleCorrDataset == "NOT_PROVIDED" :
    if isMC:
        process.calibratedGsfElectrons.inputDataset = cms.string("Fall11")
    else:
        process.calibratedGsfElectrons.inputDataset = cms.string("Jan16ReReco")
else :
    process.calibratedGsfElectrons.inputDataset = cms.string(gsfEleCorrDataset)

print "Setting process.calibratedGsfElectrons.inputDataset=",
print process.calibratedGsfElectrons.inputDataset


process.PF2PATAK5.replace(process.goodOfflinePrimaryVertices,
                          process.goodOfflinePrimaryVertices+
                          process.calibratedGsfElectrons
                          )





