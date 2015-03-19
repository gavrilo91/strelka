#
# Starka
# Copyright (c) 2009-2014 Illumina, Inc.
#
# This software is provided under the terms and conditions of the
# Illumina Open Source Software License 1.
#
# You should have received a copy of the Illumina Open Source
# Software License 1 along with this program. If not, see
# <https://github.com/sequencing/licenses/>
#

"""
Workflow configuration options shared by multiple
configuration scripts.
"""

import os,sys

scriptDir=os.path.abspath(os.path.dirname(__file__))
scriptName=os.path.basename(__file__)

sys.path.append(scriptDir)

from configureOptions import ConfigureWorkflowOptions
from configureUtil import assertOptionExists, joinFile, OptParseException, \
                          validateFixExistingDirArg, validateFixExistingFileArg, \
                          checkTabixListOption
from workflowUtil import parseGenomeRegion


def cleanLocals(locals_dict) :
    """
    When passed a locals() dictionary, clean out all of the hidden keys and return
    """

    return dict((k,v) for (k,v) in locals_dict.items() if not k.startswith("__") and k != "self")



class StarkaWorkflowOptionsBase(ConfigureWorkflowOptions) :

    validAlignerModes = ["bwa","isaac"]

    def addWorkflowGroupOptions(self,group) :
        group.add_option("--referenceFasta",type="string",metavar="FILE",
                         help="samtools-indexed reference fasta file [required]")
        group.add_option("--indelCandidates", type="string", dest="indelCandidatesList", metavar="FILE", action="append",
                         help="Specify a vcf describing indel candidates. Candidates are always evaluated but only output"
                              " if a variant genotype is likely."
                              " File must be tabix indexed."
                              " Option may be specified more than once, multiple inputs will be merged."
                              " (default: None)")
        group.add_option("--forcedGT", type="string", dest="forcedGTList", metavar="FILE", action="append",
                         help="Specify a vcf describing indels which must be genotyped and output even if a variant genotype is unlikely."
                              " File must be tabix indexed."
                              " Option may be specified more than once, multiple inputs will be merged."
                              " (default: None)")
        group.add_option("--exome", dest="isExome", action="store_true",
                         help="Set options for WES input: turn off depth filters")
        group.add_option("--runDir", type="string",metavar="DIR",
                         help="Run script and run output will be written to this directory [required] (default: %default)")

    def addExtendedGroupOptions(self,group) :
        group.add_option("--scanSizeMb", type="int", metavar="INT",
                         help="Maximum sequence region size (in megabases) scanned by each task during "
                         "genome variant calling. (default: %default)")
        group.add_option("--region", type="string",dest="regionStrList",metavar="REGION", action="append",
                         help="Limit the analysis to a region of the genome for debugging purposes. "
                              "If this argument is provided multiple times all specified regions will "
                              "be analyzed together. All regions must be non-overlapping to get a "
                              "meaningful result. Examples: '--region chr20' (whole chromosome), "
                              "'--region chr2:100-2000 --region chr3:2500-3000' (two regions)'")
        # re-rig this to work with SGE/local selection scheme
        #group.add_option("--callMemMb",type="int",metavar="INT",
        #                 help="Set variant calling task memory limit (in megabytes). It is not "
        #                      "recommended to change the default in most cases, but this might be required "
        #                      "for a sample of unusual depth. (default: %default)")

        ConfigureWorkflowOptions.addExtendedGroupOptions(self,group)


    def getOptionDefaults(self) :
        """
        Set option defaults.

        Every local variable in this method becomes part of the default hash
        """

        alignerMode = "isaac"

        libexecDir=os.path.abspath(os.path.join(scriptDir,"@THIS_RELATIVE_LIBEXECDIR@"))
        assert os.path.isdir(libexecDir)

        bgzipBin=joinFile(libexecDir,"bgzip")
        samtoolsBin=joinFile(libexecDir,"samtools")
        tabixBin=joinFile(libexecDir,"tabix")
        bgcatBin=joinFile(libexecDir,"bgzf_cat")

        countFastaBin=joinFile(libexecDir,"countFastaBases")
        starlingBin=joinFile(libexecDir,"starling2")
        strelkaBin=joinFile(libexecDir,"strelka2")
        inovoBin=joinFile(libexecDir,"inovo")

        getChromDepth=joinFile(libexecDir,"getBamAvgChromDepth.py")

        # default memory request per process-type
        #
        # where different values are provided for SGE and local runs note:
        #  1. for SGE the memory limits must be greater than the highest memory use ever
        #      expected in a production run. The consequence of exceeding this limit is a failed
        #      run.
        #   2. for localhost the memory usage should be at least above the highest mean memory
        #       use ever expected in a production run. The consequence of exceeding the mean is
        #       a slow run due to swapping.
        #
        callSGEMemMb=4*1024
        callLocalMemMb=2*1024


        runDir = "variantCallWorkflow"
        scanSizeMb = 12

        isExome = False

        return cleanLocals(locals())



    def validateAndSanitizeExistingOptions(self,options) :

        options.runDir=os.path.abspath(options.runDir)

        # check alignerMode:
        if options.alignerMode is not None :
            options.alignerMode = options.alignerMode.lower()
            if options.alignerMode not in self.validAlignerModes :
                raise OptParseException("Invalid aligner mode: '%s'" % options.alignerMode)

        options.referenceFasta=validateFixExistingFileArg(options.referenceFasta,"reference")

        # check for reference fasta index file:
        if options.referenceFasta is not None :
            faiFile=options.referenceFasta + ".fai"
            if not os.path.isfile(faiFile) :
                raise OptParseException("Can't find expected fasta index file: '%s'" % (faiFile))

        checkTabixListOption(options.indelCandidatesList,"candidate indel vcf")
        checkTabixListOption(options.forcedGTList,"forced genotype vcf")

        if (options.regionStrList is None) or (len(options.regionStrList) == 0) :
            options.genomeRegionList = None
        else :
            options.genomeRegionList = [parseGenomeRegion(r) for r in options.regionStrList]


    def validateOptionExistence(self,options) :

        assertOptionExists(options.runDir,"run directory")

        assertOptionExists(options.alignerMode,"aligner mode")
        assertOptionExists(options.referenceFasta,"reference fasta file")


