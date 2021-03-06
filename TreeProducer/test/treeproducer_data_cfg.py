import FWCore.ParameterSet.Config as cms


### CMSSW command line parameter parser
from FWCore.ParameterSet.VarParsing import VarParsing
options = VarParsing('python')

## data or MC options
options.register(
	'isData',True,VarParsing.multiplicity.singleton,VarParsing.varType.bool,
	'flag to indicate data or MC')

options.register(
	'maxEvts',-1,VarParsing.multiplicity.singleton,VarParsing.varType.int,
	'flag to indicate max events to process')


process = cms.Process("SEXAQ")

process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = cms.untracked.int32(100)
process.options = cms.untracked.PSet(wantSummary = cms.untracked.bool(True))

process.load('Configuration.StandardSequences.GeometryRecoDB_cff')
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")

process.load('Configuration/StandardSequences/MagneticField_38T_cff')
process.load('Configuration/StandardSequences/Reconstruction_cff')
process.load('Configuration/EventContent/EventContent_cff')

from Configuration.AlCa.GlobalTag import GlobalTag

if(options.isData==True):
    process.GlobalTag = GlobalTag(process.GlobalTag, '80X_dataRun2_2016SeptRepro_v7', '')
else:
    process.GlobalTag = GlobalTag(process.GlobalTag, '80X_mcRun2_asymptotic_2016_miniAODv2_v1', '')


process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(options.maxEvts))

process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring(
#     'file:///user/lowette/SexaQ/RunIISummer16DR80_MinBias_TuneCUETP8M1_13TeV-pythia8_GEN-SIM-RECO_NoPU_RECO_80X_mcRun2_asymptotic_v14-v1_100000_00150044-D075-E611-AAE8-001E67505A2D.root',
     'file:///user/lowette/SexaQ/Run2016H_SingleMuon_AOD_07Aug17-v1_10000_F068EC7F-FB96-E711-96FF-7845C4FC3BFF.root'
    )
)


process.nEvTotal        = cms.EDProducer("EventCountProducer")
process.nEvLambdaKshort = cms.EDProducer("EventCountProducer")
process.nEvLambdaKshortVertex = cms.EDProducer("EventCountProducer")
process.nEvSMass        = cms.EDProducer("EventCountProducer")

process.genParticlePlusGEANT = cms.EDProducer("GenPlusSimParticleProducer",
  src           = cms.InputTag("g4SimHits"),
  setStatus     = cms.int32(8),                # set status = 8 for GEANT GPs
  particleTypes = cms.vstring("Xi-","Xibar+","Lambda0","Lambdabar0","K_S0","K0"),      # also picks pi- (optional)
  filter        = cms.vstring("pt >= 0.0"),     # just for testing
  genParticles  = cms.InputTag("genParticles") # original genParticle list
)

process.load("SexaQAnalysis.Skimming.LambdaKshortFilter_cfi")
process.lambdaKshortFilter.genCollection = cms.InputTag("genParticlePlusGEANT")
process.lambdaKshortFilter.isData = options.isData
process.lambdaKshortFilter.minPtLambda = 1.5 # gives pT(proton,pion)>0.5GeV
process.lambdaKshortFilter.minPtKshort = 0.9 # gives pT(pion,pion)>0.5GeV
process.lambdaKshortFilter.checkLambdaDaughters = True
process.lambdaKshortFilter.prescaleFalse = 0

process.load("SexaQAnalysis.Skimming.LambdaKshortVertexFilter_cfi")
process.lambdaKshortVertexFilter.lambdaCollection = cms.InputTag("lambdaKshortFilter","lambda")
process.lambdaKshortVertexFilter.kshortCollection = cms.InputTag("lambdaKshortFilter","kshort")
process.lambdaKshortVertexFilter.maxchi2ndofVertexFit = 10.

from SexaQAnalysis.Skimming.MassFilter_cfi import massFilter
massFilter.lambdakshortCollection = cms.InputTag("lambdaKshortVertexFilter","sParticles")
massFilter.minMass = -10000 # effectively no filter
massFilter.maxMass = 10000  # effectively no filter
process.rMassFilter = massFilter.clone()
process.rMassFilter.targetMass = 0
process.sMassFilter = massFilter.clone()
process.sMassFilter.targetMass = 0.939565


process.load("SexaQAnalysis.TreeProducer.Treeproducer_AOD_cfi")
process.tree.genCollection = cms.InputTag("genParticlePlusGEANT")
process.tree.sCollection = cms.InputTag("lambdaKshortVertexFilter","sParticles")
process.tree.sTrackCollection = cms.InputTag("lambdaKshortVertexFilter","sParticlesTracks")
process.tree.isData = cms.untracked.bool(options.isData)

process.p = cms.Path(
#  process.genParticlePlusGEANT *
  process.nEvTotal *
  process.lambdaKshortFilter *
  process.nEvLambdaKshort *
  process.lambdaKshortVertexFilter *
  process.nEvLambdaKshortVertex *
  process.rMassFilter *
  process.sMassFilter *
  process.nEvSMass *
  process.tree 
)

# Output
process.TFileService = cms.Service('TFileService',
    fileName = cms.string('tree.root')
)

#Keep edm output file only during debugging
process.out = cms.OutputModule("PoolOutputModule",
  outputCommands = cms.untracked.vstring(
    'drop *',
    'keep recoVertexCompositeCandidates_generalV0Candidates_*_*',
    'keep recoVertexs_offlinePrimaryVertices_*_*',
    'keep *_offlineBeamSpot_*_*',
    'keep *_*_*_SEXAQ',
  ),
  fileName = cms.untracked.string("events_skimmed.root"),
  SelectEvents = cms.untracked.PSet(
    SelectEvents = cms.vstring('p')
  )
)

process.output_step = cms.EndPath(process.out)
