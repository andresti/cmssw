import imp
import math
import copy
import time
import re

#from CMGTools.H2TauTau.proto.HistogramSet import histogramSet
from CMGTools.H2TauTau.proto.plotter.H2TauTauDataMC import H2TauTauDataMC
from CMGTools.H2TauTau.proto.plotter.prepareComponents import prepareComponents #, readPickles
from CMGTools.H2TauTau.proto.plotter.rootutils import buildCanvas, draw, drawOfficial, buildCanvasOfficial
from CMGTools.H2TauTau.proto.plotter.binning import binning_svfitMass, binning_svfitMass_finer
from CMGTools.H2TauTau.proto.plotter.titles import xtitles
from CMGTools.H2TauTau.proto.plotter.blind import blind
from CMGTools.H2TauTau.proto.plotter.plotmod import *
from CMGTools.H2TauTau.proto.plotter.datacards import datacards
from CMGTools.H2TauTau.proto.plotter.plotinfo import *
from CMGTools.RootTools.statistics.Counter import Counters
from CMGTools.RootTools.Style import *
from CMGTools.H2TauTau.proto.plotter.categories_common import replaceCategories
from CMGTools.H2TauTau.proto.plotter.categories_TauEle import categories
from ROOT import kGray, kPink, TH1, TPaveText, TPad, TCanvas

cp = copy.deepcopy
EWK = 'WJets'

    
NBINS = 100
XMIN  = 0
XMAX  = 200



def replaceShapeInclusive(plot, var, anaDir,
                          comp, weights, 
                          cut, weight,
                          embed, shift):
    '''Replace WJets with the shape obtained using a relaxed tau iso'''
    cut = cut.replace('l1_looseMvaIso>0.5', 'l1_rawMvaIso>-0.5')
    print '[INCLUSIVE] estimate',comp.name,'with cut',cut
    plotWithNewShape = cp( plot )
    wjyield = plot.Hist(comp.name).Integral()
    nbins = plot.bins
    xmin = plot.xmin
    xmax = plot.xmax
    wjshape = shape(var, anaDir,
                    comp, weights, nbins, xmin, xmax,
                    cut, weight,
                    embed, shift, treeName = 'H2TauTauTreeProducerTauEle')
    # import pdb; pdb.set_trace()
    wjshape.Scale( wjyield )
    # import pdb; pdb.set_trace()
    plotWithNewShape.Replace(comp.name, wjshape) 
    # plotWithNewShape.Hist(comp.name).on = False 
    return plotWithNewShape

    
# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----


def makePlot( var, anaDir, selComps, weights, wJetScaleSS, wJetScaleOS,
              nbins=None, xmin=None, xmax=None,
              cut='', weight='weight', embed=False, shift=None, replaceW=False,
              VVgroup = None, antiMuIsoForQCD=False):
    
    print 'making the plot:', var, 'cut', cut

    oscut = cut+' && diTau_charge==0'
    osign = H2TauTauDataMC(var, anaDir,
                           selComps, weights, nbins, xmin, xmax,
                           cut=oscut, weight=weight,
                           embed=embed, shift=shift, treeName = 'H2TauTauTreeProducerTauEle')
    osign.Hist(EWK).Scale( wJetScaleOS )

    import pdb; pdb.set_trace()

    replaceW = False
    if replaceW:
        osign = replaceShapeInclusive(osign, var, anaDir,
                                      selComps['WJets'], weights, 
                                      oscut, weight,
                                      embed, shift)
    if VVgroup != None:
         osign.Group('VV', cfg.VVgroup)
         
    sscut = cut+' && diTau_charge!=0'
    ssign = H2TauTauDataMC(var, anaDir,
                           selComps, weights, nbins, xmin, xmax,
                           cut=sscut, weight=weight,
                           embed=embed, shift=shift, treeName = 'H2TauTauTreeProducerTauEle')
    ssign.Hist(EWK).Scale( wJetScaleSS ) 
    if replaceW:
        ssign = replaceShapeInclusive(ssign, var, anaDir,
                                      selComps['WJets'], weights, 
                                      sscut, weight,
                                      embed, shift)
    if VVgroup != None:
         ssign.Group('VV', cfg.VVgroup)
    # import pdb; pdb.set_trace()

    ssQCD, osQCD = getQCD( ssign, osign, 'Data', 1.06 ) #PG scale value according Jose, 18/10

    #COLIN was buggy. iso was relaxed even in the 0jet low category, and the QCD
    # estimation clearly wrong
    if antiMuIsoForQCD:
        print 'WARNING RELAXING ISO FOR QCD SHAPE'
        # replace QCD with a shape obtained from data in an anti-iso control region
        qcd_yield = osQCD.Hist('QCD').Integral()
        
        sscut_qcdshape = cut.replace('l2_relIso05<0.1', '(l2_relIso05<0.5 && l2_relIso05>0.2)').replace('l1_looseMvaIso>0.5', 'l1_rawMvaIso>0.7') + ' && diTau_charge!=0'
        ssign_qcdshape = H2TauTauDataMC(var, anaDir,
                                        selComps, weights, nbins, xmin, xmax,
                                        cut=sscut_qcdshape, weight=weight,
                                        embed=embed, treeName = 'H2TauTauTreeProducerTauEle')
        qcd_shape = copy.deepcopy( ssign_qcdshape.Hist('Data') )
        # subtract subtracting off templates from ZLL (no real taus) and ttbar with the same selection
        # ignore the others as they're small
        try:
            qcd_shape.Add(ssign_qcdshape.Hist('Ztt_ZL'), -1)
            qcd_shape.Add(ssign_qcdshape.Hist('Ztt_ZJ'), -1)
        except:
            print 'cannot find Ztt_Fakes in W+jets estimate'
            pass    
        qcd_shape.Add(ssign_qcdshape.Hist('TTJets'), -1)

        qcd_shape.Normalize()
        qcd_shape.Scale(qcd_yield)
        osQCD.Replace('QCD', qcd_shape)
        
    osQCD.Group('EWK', ['WJets', 'Ztt_ZJ','VV'])
    osQCD.Group('Higgs 125', ['HiggsVBF125', 'HiggsGGH125', 'HiggsVH125'])

    ssQCD.Group('EWK', ['WJets', 'Ztt_ZJ','VV'])
    ssQCD.Group('Higgs 125', ['HiggsVBF125', 'HiggsGGH125', 'HiggsVH125'])

    return ssign, osign, ssQCD, osQCD


# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----


def drawAll(cut, plots, embed, selComps, weights, fwss, fwos, VVgroup = None):
    '''See plotinfo for more information'''
    for plot in plots.values():
        print 'PLOTTING',plot.var
        thecut = copy.copy (cut)
        if plot.var == 'mt' or plot.var == 'met' or plot.var == 'pfmet':
           thecut = cut.replace('mt<20', '1')
        ss, os, ssQ, osQ = makePlot( plot.var, anaDir,
                                     selComps, weights, fwss, fwos,
                                     plot.nbins, plot.xmin, plot.xmax,
                                     thecut, weight = weight, embed = embed,
                                     VVgroup = VVgroup)

        scaleFactor = 1.
        osQ.legendOn = True
        osQ.Hist ('HiggsVBF125').Scale (scaleFactor)
        osQ.Hist ('HiggsGGH125').Scale (scaleFactor)
        osQ.Hist ('HiggsVH125').Scale  (scaleFactor)

        ssQ.legendOn = True
        ssQ.Hist ('HiggsVBF125').Scale (scaleFactor)
        ssQ.Hist ('HiggsGGH125').Scale (scaleFactor)
        ssQ.Hist ('HiggsVH125').Scale  (scaleFactor)

        print 'drawing ', plot.var
        blindMe = False
        if plot.var == 'svfitMass' and \
           thecut.find('nJets') != -1 : blindMe = True

        draw (osQ, blindMe, 'TauEle', plotprefix = 'CTRL_OS_lin')
        osQ.Hist('Higgs 125').stack = False
        osQ.Hist('Higgs 125').weighted.SetMarkerStyle (1)
        draw (osQ, blindMe, 'TauEle', plotprefix = 'CTRL_OS_log', SetLogy = 1)
        draw (ssQ, False,   'TauEle', plotprefix = 'CTRL_SS_lin')
#        ssQ.Hist('Higgs 125').stack = False
#        ssQ.Hist('Higgs 125').weighted.SetMarkerStyle (1)
#        draw (ssQ, False,   'TauEle', plotprefix = 'CTRL_SS_lin', SetLogy = 1)

        ss = None
        os = None
        ssQ = None
        osQ = None


# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----


def handleW( anaDir, selComps, weights,
             cut, weight, embed, VVgroup, nbins=50, highMTMin=70., highMTMax=1070,
             lowMTMax=20.):
    
    cut = cut.replace('mt<20', '1')
    fwss, fwos, ss, os = plot_W(
        anaDir, selComps, weights,
        nbins, highMTMin, highMTMax, cut,
        weight=weight, embed=embed,
        VVgroup = VVgroup,
        treeName = 'H2TauTauTreeProducerTauEle')

    w_mt_ratio_ss = w_lowHighMTRatio('mt', anaDir, selComps['WJets'], weights, cut, weight, lowMTMax, highMTMin, highMTMax, 'diTau_charge!=0', treeName = 'H2TauTauTreeProducerTauEle')
    w_mt_ratio_os = w_lowHighMTRatio('mt', anaDir, selComps['WJets'], weights, cut, weight, lowMTMax, highMTMin, highMTMax, 'diTau_charge==0', treeName = 'H2TauTauTreeProducerTauEle')
    w_mt_ratio    = w_lowHighMTRatio('mt', anaDir, selComps['WJets'], weights, cut, weight, lowMTMax, highMTMin, highMTMax, '1',               treeName = 'H2TauTauTreeProducerTauEle')

    return fwss, fwos, w_mt_ratio_ss, w_mt_ratio_os, w_mt_ratio


# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----


if __name__ == '__main__':

    import copy
    from optparse import OptionParser
    from CMGTools.RootTools.RootInit import *

    parser = OptionParser()
    parser.usage = '''
    %prog <anaDir> <cfgFile>

    cfgFile: analysis configuration file, see CMGTools.H2TauTau.macros.MultiLoop
    anaDir: analysis directory containing all components, see CMGTools.H2TauTau.macros.MultiLoop.
    hist: histogram you want to plot
    '''
    parser.add_option("-H", "--hist", 
                      dest="hist", 
                      help="histogram list",
                      default=None)
    parser.add_option("-C", "--cut", 
                      dest="cut", 
                      help="cut to apply in TTree::Draw",
                      default='1')
    parser.add_option("-E", "--embed", 
                      dest="embed", 
                      help="Use embedd samples.",
                      action="store_true",
                      default=False)
    parser.add_option("-X", "--exclusiveVV", 
                      dest="useExcusiveVV", 
                      help="Use exclusive VV.",
                      action="store_true",
                      default=False)
    parser.add_option("-B", "--blind", 
                      dest="blind", 
                      help="Blind.",
                      action="store_true",
                      default=False)
    parser.add_option("-W", "--replaceW", 
                      dest="replaceW", 
                      help="replace W shape by relaxing isolation on the hadronic tau",
                      action="store_true",
                      default=False)
    parser.add_option("-n", "--nbins", 
                      dest="nbins", 
                      help="Number of bins",
                      default=None)
    parser.add_option("-m", "--min", 
                      dest="xmin", 
                      help="xmin",
                      default=None)
    parser.add_option("-M", "--max", 
                      dest="xmax", 
                      help="xmax",
                      default=None)
    parser.add_option("-g", "--higgs", 
                      dest="higgs", 
                      help="Higgs mass: 125, 130,... or dummy",
                      default=None)
    parser.add_option("-p", "--plots", 
                      dest="plots", 
                      help="plots: set it to true to make control plots",
                      action="store_true",
                      default=False)

    (options,args) = parser.parse_args()

    if len(args) != 2:
        parser.print_help()
        sys.exit(1)

    if options.nbins is None:
        NBINS = binning_svfitMass_finer
        XMIN = None
        XMAX = None
    else:
        NBINS = int(options.nbins)
        XMIN = float(options.xmin)
        XMAX = float(options.xmax)
        
    cutstring = options.cut
    antiMuIsoForQCD = cutstring.find('l1_pt>40')!=-1 or cutstring.find('Xcat_J1X')!=-1
    options.cut = replaceCategories(options.cut, categories) 

    print 'CUT APPLIED:', options.cut
    
    # TH1.AddDirectory(False)
    dataName = 'Data'
    weight='weight'
    replaceW = options.replaceW
    
    anaDir = args[0].rstrip('/')
    shift = None
    if anaDir.endswith('_Down'):
        shift = 'Down'
    elif anaDir.endswith('_Up'):
        shift = 'Up'
        
    cfgFileName = args[1]
    file = open( cfgFileName, 'r' )
    cfg = imp.load_source( 'cfg', cfgFileName, file)
#    embed = options.embed

    selComps, weights, zComps = prepareComponents(anaDir, cfg.config, None, 
                                                  options.embed, 'TauEle', options.higgs)


    #PG apply the TT scale factor to the cross-section
    #PG ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----

    TTfactor = None
    if 'Xcat_J0X' in cutstring    : TTfactor = 1.08
    elif 'Xcat_J1X' in cutstring  : TTfactor = 1.01
    elif 'Xcat_IncX' in cutstring : TTfactor = 1.08
    else :
        TTfactor = 1.03
        print 'using 2J scale factor for TTJets'

    #PG when I will use the cut "cat_VBF" in my code, I can change this here above

    #PG WARNING assuming the TTbar will not change name
    selComps['TTJets'].xSection = selComps['TTJets'].xSection * TTfactor


    #PG (STEP 1) evaluate the WJets contribution from high mT sideband
    #PG ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----

    # can, pad, padr = buildCanvas()
    ocan = buildCanvasOfficial()
    
    # Jose calculates this factor within the svfit mass cuts
    fwss, fwos, w_mt_ratio_ss, w_mt_ratio_os, w_mt_ratio = handleW(
        anaDir, selComps, weights,
        options.cut, 
        weight  = weight, 
        embed   = options.embed, 
        VVgroup = cfg.VVgroup
        )

    print 'PIETRO', fwss, fwos

    #PG fwss = W normalization factor for the same sign plots
    #PG fwos = W normalization factor for the opposite sign plots
    #PG ss   = mt plot with the scaled W, according to fwss
    #PG os   = mt plot with the scaled W, according to fwos

    #PG final drawing
    #PG ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----

    if (options.plots == True) :
        print 'CONTOL PLOTS'
#        plots_TauEle_basic = {
#            'l1_pt'      : PlotInfo ('l1_pt',       25,  0,    100), # tau
#            'svfitMass'  : PlotInfo ('svfitMass',   30,  0,    300),
#           }
        drawAll(options.cut, plots_TauEle_basic, options.embed, selComps, weights, fwss, fwos,
                VVgroup = cfg.VVgroup)
    else :
    
        ssign, osign, ssQCD, osQCD = makePlot( options.hist, anaDir, selComps, weights, 
                                               fwss, fwos, NBINS, XMIN, XMAX, 
                                               options.cut, 
                                               weight   = weight, 
                                               embed    = options.embed,
                                               VVgroup  = cfg.VVgroup,
                                               replaceW = replaceW,
                                               antiMuIsoForQCD = antiMuIsoForQCD)
        # ssign = all cuts, same sign, before QCD estimate
        # osign = all cuts, opposite sign, before QCD estimate
        # ssQCD = all cuts, same sign, after QCD estimate, i.e. the QCD is in
        # osQCD = all cuts, opposite sign, after QCD estimate, i.e. the QCD is in
        # draw(ssign, False, 'TauEle', 'QCD_ss')
        # draw(osign, False, 'TauEle', 'QCD_os')

#        osQCD.legendOn = False
        drawOfficial(osQCD, options.blind, 'TauEle')
        datacards(osQCD, cutstring, shift, 'eTau')

