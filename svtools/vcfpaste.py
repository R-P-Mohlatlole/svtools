import argparse, sys
import gzip

MAX_SPLIT = 9

class Vcfpaste(object):
    def __init__(self, vcf_list, master=None, sum_quals=None):
        self.vcf_list = vcf_list
        self.master = master
        self.sum_quals = sum_quals

    def execute(self):
        try:
            self.read_filenames()
            self.open_files()
            self.write_header()
            self.write_variants()
        finally:
            self.close_files()

    def read_filenames(self):
        self.vcf_file_names = []
        with open(self.vcf_list, 'r') as vcf_list_file:
            for line in vcf_list_file:
                path = line.rstrip()
                self.vcf_file_names.append(path)
        if self.master == None:
            self.master = self.vcf_file_names[0]
        self.vcf_file_names.insert(0, self.master)

    def open_files(self):
        self.vcf_files = []
        # parse the vcf files to paste
        for path in self.vcf_file_names:
            if path.endswith('.gz'):
                self.vcf_files.append(gzip.open(path, 'rb'))
            else:
                self.vcf_files.append(open(path, 'r'))
    
    def write_header(self):
        master = self.vcf_files[0]
        while 1:
            master_line = master.readline()
            if not master_line:
                break
            if master_line[:2] != '##':
                break
            print master_line.rstrip()
        out_v = master_line.rstrip().split('\t', MAX_SPLIT)[:MAX_SPLIT]

        for vcf in self.vcf_files[1:]:
            while 1:
                l = vcf.readline()
                if not l:
                    break
                if l[:2] == '##':
                    continue
                if l[0] == '#':
                    out_v = out_v + l.rstrip().split('\t', MAX_SPLIT)[MAX_SPLIT:]
                    break
        sys.stdout.write('\t'.join(map(str, out_v)) + '\n')

    def write_variants(self):
        while 1:
            master_line = self.vcf_files[0].readline()
            if not master_line:
                break
            master_v = master_line.rstrip().split('\t', MAX_SPLIT)
            out_v = master_v[:8] # output array of fields
            qual = float(out_v[5])
            format = None # column 9, VCF format field.

            for vcf in self.vcf_files[1:]:
                line = vcf.readline()
                if not line:
                    # XXX This should probably be an exception
                    sys.stderr.write('\nERROR: VCF files differ in length\n')
                    exit(1)
                line_v = line.rstrip().split('\t', MAX_SPLIT)

                # set FORMAT field as format in first VCF.
                # cannot extract this from master, since it may have
                # been altered in the processing of the VCFs.
                if format is None:
                    format = line_v[8]
                    out_v.append(format)

                qual += float(line_v[5])
                out_v = out_v + line_v[9:]
            if self.sum_quals:
                out_v[5] = qual
            sys.stdout.write( '\t'.join(map(str, out_v)) + '\n')

    def close_files(self):
        for f in self.vcf_files:
            f.close()

def description():
    return 'Paste VCFs from multiple samples'

def add_arguments_to_parser(parser):
    parser.add_argument('-m', '--master', type=argparse.FileType('r'), default=None, help='VCF file to set first 8 columns of variant info [first file in vcf_list]')
    parser.add_argument('-q', '--sum-quals', required=False, action='store_true', help='Sum QUAL scores of input VCFs as output QUAL score')
    parser.add_argument('-f', '--vcf-list', required=True, help='Line-delimited list of VCF files to paste')
    parser.set_defaults(entry_point=run_from_args)

def command_parser():
    parser = argparse.ArgumentParser(description=description())
    add_arguments_to_parser(parser)
    return parser

def run_from_args(args):
    paster = Vcfpaste(args.vcf_list, master=args.master, sum_quals=args.sum_quals)
    paster.execute()


# initialize the script
if __name__ == '__main__':
    parser = command_parser()
    args = parser.parse_args()
    sys.exit(args.entry_point(args))
