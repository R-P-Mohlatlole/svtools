#!/usr/bin/env python

import argparse, sys, re
import math, time
from argparse import RawTextHelpFormatter

__author__ = "Colby Chiang / Abhijit Badve"
__version__ = "$Revision: 0.0.2 $"
__date__ = "$Date: 2015-09-02 15:00 $"
__revision__ = "added support if in case cipos and ciend are absent"

# --------------------------------------
# define functions

def get_args():
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter, description="\
bedpeToVcf\n\
author: " + __author__ + "\n\
version: " + __version__ + "\n\
description: Convert a bedpe file to VCF")
    parser.add_argument('-b', '--bedpe', type=argparse.FileType('r'), default=None, help='BEDPE input (default: stdin)')
    parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout, help='Output VCF to write (default: stdout)')

    # parse the arguments
    args = parser.parse_args()

    # if no input, check if part of pipe and if so, read stdin.
    if args.bedpe == None:
        if sys.stdin.isatty():
            parser.print_help()
            exit(1)
        else:
            args.bedpe = sys.stdin

    # send back the user input
    return args

class Bedpe(object):
        def __init__(self, bedList):
            self.c1 = bedList[0]
            self.s1 = int(bedList[1])
            self.e1 = int(bedList[2])
            self.c2 = bedList[3]
            self.s2 = int(bedList[4])
            self.e2 = int(bedList[5])
            self.name = bedList[6]
            if bedList[7].isdigit():
                self.score = float(bedList[7])
            else:
                self.score = bedList[7]
            self.o1 = bedList[8]
            self.o2 = bedList[9]
            self.filter = bedList[11]
            self.malformedFlag = 0
            self.misc = bedList[12:]
            if self.misc[0] == 'MISSING':
                  self.malformedFlag = 1
                  self.misc[0] = self.misc[1]
            if self.misc[1] == 'MISSING':
                self.malformedFlag = 2      
            del self.misc[1]
            
            self.svtype = re.split("=",''.join(filter(lambda x: 'SVTYPE=' in x, self.misc[0].split(";"))))[1]
            if self.svtype != bedList[10]:
                sys.stderr.write("SVTYPE at Column 11("+ str(bedList[10]) + ") and SVTYPE in INFO Column(" + str(self.svtype) +  ") don't match at variant ID " + str(self.name) + '\n')
            if 'CIPOS=' in self.misc[0]:
                self.cipos = re.split("=|,",''.join(filter(lambda x: 'CIPOS=' in x, self.misc[0].split(";"))))
                if self.o1 == '-' and self.svtype == 'BND':
                    self.b1 = self.s1 - int(self.cipos[1]) + 1 
                else:
                    self.b1 = self.s1 - int(self.cipos[1])
            else:
                if self.o1 == '-' and self.svtype == 'BND':
                    self.b1 = self.s1 + 1 
                else:
                    self.b1 = self.s1
            if 'CIEND=' in self.misc[0]:     
                self.ciend = re.split("=|,",''.join(filter(lambda x: 'CIEND=' in x, self.misc[0].split(";"))))
                if self.o2 == '-' and self.svtype == 'BND':
                    self.b2 = self.s2 - int(self.ciend[1]) + 1
                else:
                    self.b2 = self.s2 - int(self.ciend[1])
                
            else: 
                self.ciend = None
                if self.o2 == '-' and self.svtype == 'BND':
                    self.b2 = self.s2 + 1
                else:
                    self.b2 = self.s2
  
class Vcf(object):
    def __init__(self):
            self.sample_list = []
            self.header=[]
    def add_sample_list(self, sample_list):
        self.sample_list.extend(sample_list)
        
    def add_header(self,line):
        if line.split('=')[0] == '##fileformat':
            line = '##fileformat=' + "VCFv4.2" + '\n'
        if line.split('=')[0] == '##fileDate':
            line = '##fileDate=' + time.strftime('%Y%m%d') + '\n'
        self.header.append(line)
     # return the VCF header
    def get_header(self):
        if len(self.header)!= 0:
            if len(self.sample_list)!= 0:
                    return  ''.join(self.header + \
                               ['\t'.join([
                                   '#CHROM',
                                   'POS',
                                   'ID',
                                   'REF',
                                   'ALT',
                                   'QUAL',
                                   'FILTER',
                                   'INFO',
                                   'FORMAT'] + \
                                          self.sample_list
                                      )])
   
            else:
                return     ''.join(self.header + \
                               ['\t'.join([
                                   '#CHROM',
                                   'POS',
                                   'ID',
                                   'REF',
                                   'ALT',
                                   'QUAL',
                                   'FILTER',
                                   'INFO',
                                   'FORMAT'] )])                 
        else:
             if len(self.sample_list)!= 0:
                     return  ''.join(
                                ['\t'.join([
                                    '#CHROM',
                                    'POS',
                                    'ID',
                                    'REF',
                                    'ALT',
                                    'QUAL',
                                    'FILTER',
                                    'INFO',
                                    'FORMAT'] + \
                                           self.sample_list
                                       )])
   
             else:
                 return     ''.join(
                                ['\t'.join([
                                    '#CHROM',
                                    'POS',
                                    'ID',
                                    'REF',
                                    'ALT',
                                    'QUAL',
                                    'FILTER',
                                    'INFO',
                                    'FORMAT'] )])

class Variant(object):
    def __init__(self):
        self.chrom = ''
        self.pos = ''
        self.id = ''
        self.ref = 'N'
        self.alt = ''
        self.qual = ''
        self.filter = ''
        self.misc = list()
    def add_info(self,chromNo,position,name,altStr,qualScore,filterVal,info):
        self.chrom = chromNo
        self.pos = position
        self.id = name
        self.alt = altStr
        self.qual = qualScore
        self.filter = filterVal
        self.misc = list(info)
    def get_var_string(self):
            return '\t'.join([self.chrom,str(self.pos),str(self.id),self.ref,self.alt,str(self.qual),self.filter,'\t'.join(self.misc)])  + '\n'
            
 
# primary function
def bedpeToVcf(bedpe_file, vcf_out):
    myvcf = Vcf()
    in_header = True
    sample_list = []
    # parse the bedpe data
    for line in bedpe_file:
        if in_header:
            if line[0:2] == '##':
                myvcf.add_header(line) 
                continue
            elif line[0] == '#' and line[1] != '#':    
                sample_list = line.rstrip().split('\t')[15:]
                continue
            else:
                in_header = False
                myvcf.add_sample_list(sample_list)
                vcf_out.write(myvcf.get_header() + '\n')
        # 
        bedpe = Bedpe(line.rstrip().split('\t'))
        if bedpe.svtype == 'BND':
            var1=Variant()
            var1.add_info(bedpe.c1,  #chrom1
                 bedpe.b1,
                 bedpe.name + '_1', #ID
                 '<' + str(bedpe.svtype) + '>', #ALT
                 bedpe.score,
                 bedpe.filter,
                 bedpe.misc #Info
                 )
            if bedpe.o1 == '+':
                if bedpe.o2 == '-':
                    var1.alt = '%s[%s:%s[' % (var1.ref, bedpe.c2, bedpe.b2)
                elif bedpe.o2 == '+':
                    var1.alt = '%s]%s:%s]' % (var1.ref, bedpe.c2, bedpe.b2)
            elif bedpe.o1 == '-':
                if bedpe.o2 == '+':
                    var1.alt = ']%s:%s]%s' % (bedpe.c2, bedpe.b2, var1.ref)
                elif bedpe.o2 == '-':
                    var1.alt = '[%s:%s[%s' % (bedpe.c2, bedpe.b2, var1.ref)
            var2 = Variant()        
            var2.add_info(bedpe.c2,  #chrom1
                bedpe.b2,
                bedpe.name + '_2', #ID
                '<' + str(bedpe.svtype) + '>', #ALT
                bedpe.score,
                bedpe.filter,
                bedpe.misc #Info
            )
            # add the strands field. For variant 2 must switch the order
            strands = re.split('=|:',''.join(filter(lambda x: 'STRANDS=' in x, bedpe.misc[0].split(";"))))
            strands_str = str(strands[0]) + '=' + str(strands[1][::-1]) + ':' + str(strands[2])
            var2.misc[0]=var2.misc[0].replace(''.join(filter(lambda x: 'STRANDS=' in x, bedpe.misc[0].split(";"))), strands_str)
            #add the cipos ciend,cipos95 and ciend95 variables
            var2.misc[0]=var2.misc[0].replace(''.join(filter(lambda x: 'CIPOS=' in x, bedpe.misc[0].split(";"))),'CIPOS='+ re.split('=',''.join(filter(lambda x: 'CIEND=' in x, bedpe.misc[0].split(";"))))[1])            
            var2.misc[0]=var2.misc[0].replace(''.join(filter(lambda x: 'CIEND='  in x, bedpe.misc[0].split(";"))),'CIEND='+ re.split('=',''.join(filter(lambda x: 'CIPOS=' in x, bedpe.misc[0].split(";"))))[1])
            var2.misc[0]=var2.misc[0].replace(''.join(filter(lambda x: 'CIPOS95=' in x, bedpe.misc[0].split(";"))),'CIPOS95='+ re.split('=',''.join(filter(lambda x: 'CIEND95=' in x, bedpe.misc[0].split(";"))))[1])
            var2.misc[0]=var2.misc[0].replace(''.join(filter(lambda x: 'CIEND95=' in x, bedpe.misc[0].split(";"))),'CIEND95='+ re.split('=',''.join(filter(lambda x: 'CIPOS95=' in x, bedpe.misc[0].split(";"))))[1])
            #Change MATEID
            var2.misc[0]= var2.misc[0].replace(''.join(filter(lambda x: 'MATEID=' in x, bedpe.misc[0].split(";"))),'MATEID=' + bedpe.name + '_2')
            #ADD IDENTIFIER FOR SECONDARY BREAKEND MATE
            var2.misc[0]=var2.misc[0].replace(''.join(filter(lambda x: 'EVENT=' in x, bedpe.misc[0].split(";"))),''.join(filter(lambda x: 'EVENT=' in x, bedpe.misc[0].split(";"))) + ';SECONDARY;')
            if bedpe.o2 == '+':
                if bedpe.o1 == '-':
                    var2.alt = '%s[%s:%s[' % (var2.ref, bedpe.c1, bedpe.b1)
                elif bedpe.o1 == '+':
                    var2.alt = '%s]%s:%s]' % (var2.ref, bedpe.c1, bedpe.b1)
            elif bedpe.o2 == '-':
                if bedpe.o1 == '+':
                    var2.alt = ']%s:%s]%s' % (bedpe.c1, bedpe.b1, var2.ref)
                elif bedpe.o1 == '-':
                    var2.alt = '[%s:%s[%s' % (bedpe.c1, bedpe.b1, var2.ref)
            if bedpe.malformedFlag == 0:
                vcf_out.write(var1.get_var_string())
                vcf_out.write(var2.get_var_string())
            elif bedpe.malformedFlag == 1:
                vcf_out.write(var2.get_var_string())
            elif bedpe.malformedFlag == 2:
                vcf_out.write(var1.get_var_string())    
        else:
            # set VCF info elements for simple events
            refbase = 'N'
            var=Variant()
            #self,chromNo,position,name,alt,qualScore,filterVal,info
            var.add_info(bedpe.c1,  #chrom1
                 bedpe.b1,
                 bedpe.name, #ID
                 '<' + str(bedpe.svtype) + '>', #ALT
                 bedpe.score,
                 bedpe.filter,
                 bedpe.misc #Info
                 )
            

            # write the record to the VCF output file
            vcf_out.write(var.get_var_string())

    # close the VCF output file
    vcf_out.close()
    
    return

# --------------------------------------
# main function

def main():
    # parse the command line args
    args = get_args()
   # call primary function
    bedpeToVcf(args.bedpe, args.output)
    # close the files
    args.bedpe.close()
# initialize the script
if __name__ == '__main__':
    try:
        sys.exit(main())
    except IOError, e:
        if e.errno != 32: # ignore SIGPIPE
            raise 
