#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Downloads CODATA fundamental physical constants from NIST website
and generates a language-specific (fortran, C/C++) file. For Fortran, 
module CODATA_constants.f90 and also a test.f90 file are generated.
The latter can be used to validate the process.
For C/C++ a header file CODATA_constants.h is generated
Original code by Vincent MAGNIN, 2021-03-11
MIT license
https://github.com/vmagnin/fundamental_constants
Last modifications: 2022-07-02
'''

import argparse
import os
import datetime
from urllib.request import urlopen

def get_number_parts(xstring):
    '''
    Receives a floating point passed as a string, and returns
    a tuple with the digits at the left and right of the
    decimal point, and the value of the exponent.
    '''
    # Is there an exponent?
    exponent_pos = xstring.find("e")
    if exponent_pos != -1:
        expo = int(xstring[exponent_pos+1:])
        # We remove the exponent
        # (right bound excluded in Python):
        xstring = xstring[0:exponent_pos]
    else:
        expo = 0

    # Number of digits at the left of the decimal point:
    point_pos = xstring.find(".")
    if point_pos == -1:
        left = len(xstring)
    else:
        left = point_pos
    # Must be corrected if a sign is present:
    if xstring[0] in ('-', '+'):
        left = left - 1

    # We keep only the decimals and count them:
    if point_pos != -1:
        xstring = xstring[point_pos+1:]
        right = len(xstring)
    else:
        right = 0

    return [left, right, expo]


#**************
# Main program
#**************

# Command line arguments:
PARSARG = argparse.ArgumentParser(description="""Downloads CODATA recommended 
                                  values of physical constants from NIST 
                                  website and generates a Fortran module.""",
                                  epilog="Sources : <https://github.com/vmagnin/fundamental_constants>")
PARSARG.add_argument("-y", action="store", nargs=1, type=int,
                     choices=[2010, 2014, 2018], default=[2018],
                     help="CODATA values: 2010, 2014 or 2018")
PARSARG.add_argument("-d", action="store_true",
                     help="Delete calculated values (...)")
PARSARG.add_argument("-v", action="version",
                     version="%(prog)s v1.1 MIT license", help="Version")
PARSARG.add_argument("-l", nargs=1, type=str, 
                    choices=['fortran', 'Fortran','c','cpp'], default=['fortran'],help="Output language name: fortran, c, cpp")
ARGS = PARSARG.parse_args()

# Those previous values are not available as an ASCII file:
# 2006, 2002, 1998, 1986, 1973, 1969.
# Next version should be released in 2022.
match ARGS.y[0]:
    case 2018:
        url = "https://physics.nist.gov/cuu/Constants/Table/allascii.txt"
    case 2014:
        url = "https://physics.nist.gov/cuu/Constants/Table/allascii_2014.txt"
    case 2010:
        url = "https://physics.nist.gov/cuu/Constants/allascii_2010.txt"

# Downloading the file from NIST website:
with urlopen(url) as nist_file:
    file_content = nist_file.read().decode('utf-8')
    lines_list = file_content.splitlines(True)

MODULE_NAME = "CODATA_constants"
TABS = "  "

match ARGS.l[0].lower():
    case 'fortran':
        fortran=True
        folder_out = 'fortran/'
        extention = ".f90"
        line_comment = '!'
        const_prefix = "  real(wp), parameter :: "
        const_suffix = "_wp "
        final_line = "end module "+MODULE_NAME+"\n"
    case 'c' | 'cpp':
        folder_out = 'c'
        extention = '.h'
        line_comment = '\\'
        pass
    case _: raise Exception("This language is not recognized or has not been implemented yet.")

# Creating the constant-containing file:
out_file_name = MODULE_NAME + extention
out_file = open(folder_out+out_file_name, "w")
print("Generating the "+ folder_out +out_file_name+" file using the recommended "
      + str(ARGS.y[0]) + " values:")
print(url)

# Writing informations in comments:
out_file.write(line_comment + 79*"-" + "\n")
out_file.write(line_comment + " " + out_file_name + "\n")
FILE_HEADER = line_comment + " Automatically generated from " + str(ARGS.y[0]) \
              + " CODATA NIST file:\n" \
              + line_comment + " " + url + "\n" \
              + line_comment + " downloaded on " + datetime.date.today().isoformat() + ".\n"
out_file.write(FILE_HEADER)
out_file.write(line_comment + 79*"-" + "\n")

if fortran:
    # Beginning the Fortran module:
    out_file.write("\nmodule " + MODULE_NAME + "\n" + TABS +
                "use, intrinsic :: iso_fortran_env, only: wp=>real64\n" +
                TABS + "implicit none\n\n")

    # Creating a test file that will generate a txt file from the Fortran constants:
    test_file = open(folder_out + "test/test.f90", "w")
    TEST_MODULE_NAME = "test"
    test_file.write("\nmodule " + TEST_MODULE_NAME + "\n" + TABS +
                "use CODATA_constants\n" + TABS +
                "use functions, only: write_CODATA\n" + TABS +
                "use, intrinsic :: iso_fortran_env, only: wp=>real64\n" +
                TABS + "implicit none\n\ncontains\n" +
                "subroutine tests\ncharacter(125) :: s\n" +
                "open(unit = 1, file = 'fortran_generated_"+str(ARGS.y[0])+".txt')\n")

#-------------------------------------------------------------------------------
# Format description of the NIST allascii.txt file:
#
# Header:   11 lines in the 2018 version, 10 lines in the 2010 & 2014 versions,
#           last line being composed of 125 "-"
# Column 1: Quantity = constant name (60 characters)
# Column 2: Value (25 characters)
# Column 3: Uncertainty (25 characters)
# Column 4: Unit (<=15 characters)
#-------------------------------------------------------------------------------

header = True # changes to False later when the header is over
nb_constants = 0

for line in lines_list:
    if ARGS.y[0] == 2010:
        line2 = line.replace("\r\n", "")
    else:
        line2 = line.replace("\n", "")

    if header:
        if fortran:
            # The Fortran test file will print the same header:
            test_file.write("s='"+line2.rstrip()+"'\n")
            test_file.write("write(1,'(a)') trim(s)\n")
        # Looking for the end of the header:
        if line2 == 125*'-':
            header = False
    else: # Header is over
        # Extracting the four columns (with Python the right bound is excluded):
        quantity = line2[0:60].rstrip()
        value = line2[60:85].rstrip()
        uncertainty = line2[85:110].rstrip()
        unit = line2[110:]

        # A special 2014 case:  "{220} lattice spacing of silicon"
        # => a variable name must begin by a letter
        quantity = quantity.replace("{220}", "twotwozero")
        # Variable names must contain only letters, underscores and numerals.
        # => all other characters will be replaced by underscores.
        quantity = quantity.replace(" ", "_").replace("-", "_").replace("/", "_")
        quantity = quantity.replace(".", "_").replace(",", "_").replace("(", "")
        quantity = quantity.replace(")", "").replace("{", "").replace("}", "")
        value = value.replace(" ", "")

        # Deleting the calculated constants?
        if value.find("...") != -1:
            if ARGS.d:
                continue
            else:
                value = value.replace("...", "")

        if fortran:
            # Some constants are mathematically integers, others have a decimal point:
            if value.find(".") == -1 and value.find("e") == -1:
                value = value + "e0"

            # Test: print the value in a txt file, trying to mimick the CODATA format:
            result = get_number_parts(value)
            #print(value, result)
            left = result[0]
            right = result[1]
            expo = result[2]
            test_file.write("call write_CODATA('"+line2[0:60]+"', &\n" + 
                            TABS +"& " +quantity+", "+str(left)+
                            ", "+str(right)+", "+str(expo)+")\n")

        # Declaration in the CODATA_constants file:
        out_file.write(const_prefix + quantity + " = " + value + const_suffix + line_comment + " " + uncertainty + "  " + unit + "\n")

        nb_constants = nb_constants + 1

# Finalizing the output file:
out_file.write(final_line)
out_file.close()

print(str(nb_constants)+" constants written")
print('{}{}'.format(os.stat(folder_out+out_file_name).st_size, " bytes"))

if fortran:
    # Finalizing the test file:
    test_file.write("close(1)\n" +
                    "end subroutine tests\nend module "+TEST_MODULE_NAME+"\n")
    test_file.close()
