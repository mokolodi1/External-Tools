#!/usr/bin/env python
"""
medbookAdapterPATHMARK.py
    by Robert Baertsch
"""
import logging, math, os, random, re, shutil, sys, types, zipfile
from copy import deepcopy

from optparse import OptionParser

## logger
logging.basicConfig(filename = "medbook-pathmark.log", level = logging.INFO)

## executables
print "startup" 
bin_dir = os.path.dirname(os.path.abspath(__file__))
print "bindir ", bin_dir
signature_exec = os.path.join(bin_dir, "signature.py")
pathmark_exec = os.path.join(bin_dir, "PATHMARK.py")
print "signature.py and pathmark.py ok"

## functions
def zipDirectory(directory, zip):
    for root, dirs, files in os.walk(directory):
        for file in files:
            zip.write(os.path.join(root, file))

def main():
    jobtree_dir = bin_dir + ".."
    sys.path.append(jobtree_dir)
    ## check for fresh run
    if os.path.exists(".jobTree") or os.path.exists("jobTree"):
        logging.warning("WARNING: '.jobTree' directory found, remove it first to start a fresh run\n")
    
    ## parse arguments
    parser = OptionParser(usage = "%prog [options] data_matrix phenotype_matrix pathway_file")
    parser.add_option("-b", "--bootstrap", dest = "bootstrap_size", default = 0,
                      help = "number of bootstrap samples to estimate subnetwork robustness")
    parser.add_option("-n", "--null", dest = "null_size", default = 0,
                      help = "number of null samples to estimate subnetwork signifiance")
    parser.add_option("-p", "--permute", dest = "null_permute", default = "paradigm",
                      help = "permutation method for generation of null samples")
    parser.add_option("-m", "--method", dest = "signature_method", default = "sam",
                      help = "differential method for computing signatures")
    parser.add_option("-f", "--filter", dest = "filter_parameters", default = "0.0;0.0",
                      help = "filter threshold coefficients")
    parser.add_option("-t", "--heat", dest = "heat_diffusion", default = "0.0",
                      help = "diffusion time for heat diffusion of signature scores across the network")
    parser.add_option("-u", "--hub", dest = "hub_filter", action = "store_true", default = False,
                      help = "apply hub filter that includes hubs with high representation of its children")
    parser.add_option("-z", "--seed", dest = "seed", default = None,
                      help = "random seed used for bootstrap and null generation")
    parser.add_option("--bs", "--batchSystem", dest = "batch_system", default = None,
                      help = "override default batch system used by jobTree")
    parser.add_option("--oz", "--output-zip", dest = "output_zip", default = None,
                      help = "output files into a zipfile")
    parser.add_option("--os", "--output-signature", dest = "output_signature", default = None,
                      help = "output signature file")
    options, args = parser.parse_args()
    logging.info("options: %s" % (str(options)))
    
    work_dir = os.path.abspath("./")
    
    if len(args) != 3:
        logging.error("ERROR: incorrect number of arguments\n")
        sys.exit(1)
    data_file = os.path.abspath(args[0])
    phenotype_file = os.path.abspath(args[1])
    pathway_file = os.path.abspath(args[2])
    
    ## run signature.py
    cmd = "%s %s" % (sys.executable, signature_exec)
    print "cmd", cmd
    if options.batch_system is not None:
        cmd += " --batchSystem %s" % (options.batch_system)
    cmd += " -b %s" % (options.bootstrap_size)
    cmd += " -n %s" % (options.null_size)
    cmd += " -p %s" % (options.null_permute)
    cmd += " -m %s" % (options.signature_method)
    if options.seed is not None:
        cmd += " -z %s" % (options.seed)
    cmd += " %s %s" % (data_file, phenotype_file)
    os.system(cmd)
    if os.path.exists(".jobTree_previous"):
        shutil.move(".jobTree_previous", ".jobTree_signature")
    elif os.path.exists("jobTree_previous"):
        shutil.move("jobTree_previous", "jobTree_signature")
    logging.info("system: %s" % (cmd))
    
    ## run PATHMARK.py
    cmd = "%s %s" % (sys.executable, pathmark_exec)
    if options.batch_system is not None:
        cmd += " --batchSystem %s" % (options.batch_system)
    if os.path.exists("null_signature.tab"):
        cmd += " -n %s" % ("null_signature.tab")
    if os.path.exists("bootstrap_signature.tab"):
        cmd += " -b %s" % ("bootstrap_signature.tab")
    cmd += " -f \"%s\"" % (options.filter_parameters)
    cmd += " -t %s" % (options.heat_diffusion)
    if options.hub_filter:
        cmd += " -u"
    cmd += " signature.tab %s" % (pathway_file)
    os.system(cmd)
    if os.path.exists(".jobTree_previous"):
        shutil.move(".jobTree_previous", ".jobTree_pathmark")
    elif os.path.exists("jobTree_previous"):
        shutil.move("jobTree_previous", "jobTree_pathmark")
    logging.info("system: %s" % (cmd))
    
    ## prepare outputs
    report_dir = "report"
    if options.output_zip is not None:
        zip_file = zipfile.ZipFile("report.zip", "w")
        zipDirectory(report_dir, zip_file)
        zip_file.close()
        shutil.copy(os.path.join(work_dir, "report.zip"), options.output_zip)
    if options.output_signature is not None:
        shutil.copy(os.path.join(work_dir, "signature.tab"), options.output_signature)
    print "work_dir", work_dir
    print "output signature", options.output_signature
    from os import listdir
    from os.path import isfile, join
    onlyfiles = [ f for f in listdir(report_dir) if isfile(join(report_dir,f)) ]
    outlist = open('report.list', 'w')
    for f in onlyfiles:
        file = os.path.join(work_dir, "report", f)
        outlist.write(file)
        outlist.write('\n')
    outlist.close()
        
    print "reports", onlyfiles



if __name__ == "__main__":
    main()
