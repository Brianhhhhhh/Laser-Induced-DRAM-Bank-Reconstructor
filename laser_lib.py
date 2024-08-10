from bs4 import BeautifulSoup
import json
import sys
import re
import os
import matplotlib.pyplot as plt
import numpy as np
import openpyxl
import numpy as np
import matplotlib.pyplot as plt
    
class line_cls:
	def __init__(self):
		self.coor = 'X'
		self.value = 0
		self.name= ""
		self.power = 'N/A'
		self.addr = []
		self.bank_row_dict= {}
		self.error_bit_offset = 8

	def enter_error(self, address, expected_value, actual_value):
		[bank,row, col] = calc_mappings(int(address, 16))
		flip_mask = actual_value ^ expected_value
		actual_value  = flip_mask
		actual_value = actual_value >> self.error_bit_offset
		
		bits = []
		bit =0
		for bit in range(0,16):
			if actual_value & 0x1:
				bits.append(bit)
			bit = bit +1
			actual_value   = actual_value>>1
			

		if bank not in self.bank_row_dict:
			self.bank_row_dict[bank] = {}
		if row not in self.bank_row_dict[bank]:
			self.bank_row_dict[bank][row] = {}
		if col not in self.bank_row_dict[bank][row]:
			self.bank_row_dict[bank][row][col] ={}
		for bit in bits:
			if bit not in self.bank_row_dict[bank][row][col]:
				self.bank_row_dict[bank][row][col][bit] = [0,0]  #0th index for 0->1, 1st index for 1->0

			if expected_value == 0:
				self.bank_row_dict[bank][row][col][bit][0] += 1
			else:
				self.bank_row_dict[bank][row][col][bit][1] += 1
			

	def get_line_name(self):
		line_name = self.coor+"_"+ str(self.value) + "_" + str(self.power)
		return line_name 
	


	def print_attr (self):
		print("==============================================================================================")
		print("==============================================================================================")
		print(self.get_line_name())
		print("************************************************************")
		for bank in self.bank_row_dict:
			print(bank, len(self.bank_row_dict[bank].keys()))


def get_bit(val, bit):
    return ((val & 1<<bit)>>bit)



def calc_mappings(addr):
    #DIMM8,15,16
    bank = (get_bit(addr, 6)^get_bit(addr,13)) | ((get_bit(addr, 14)^get_bit(addr,17))<<1) | ((get_bit(addr, 15)^get_bit(addr,18))<<2) |  ((get_bit(addr, 16)^get_bit(addr,19))<<3)   
    #DIMM12
   # bank = (get_bit(addr, 6)^get_bit(addr,13)) | ((get_bit(addr, 14)^get_bit(addr,18))<<1) | ((get_bit(addr, 15)^get_bit(addr,19))<<2) | ((get_bit(addr, 16)^get_bit(addr,20))<<3) | ((get_bit(addr, 17)^get_bit(addr,21))<<4)
    #DIMM17
    #bank = (get_bit(addr, 6)^get_bit(addr,13)) | ((get_bit(addr, 14)^get_bit(addr,16))<<1) | ((get_bit(addr, 15)^get_bit(addr,17))<<2) 
    row = (addr&0x1fffe0000)>>17
    col = (addr&0x1fff)>>3
    return [bank, row, col]

def parse_file(file_name):
	print(file_name)
	f = open(file_name, encoding="UTF-16LE")
	soup = BeautifulSoup(f, "html.parser")
	tables = soup.findChildren('table')
	
	table = None
	selected_table = None
	


	for table in tables:
		if re.match(".*Last 5000 Errors.*", table.findChild('tr').findChild('td').text):
			selected_table = table
			break
	return selected_table




def list_files(directory):
    file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths




def parse_run_directory(directory, chip_offset):
	file_paths = list_files(directory)
	print(file_paths)
	
	lines = []
	addr_dict_x = {}
	addr_dict_y = {}
	for pathl in file_paths:
		filename  = pathl.split("/")[-1]
		filename_wo_ext = filename[:-5]
		arr = filename_wo_ext.split("_")
		coor = arr[0]
		val = arr[1]
		line = line_cls()
		if len(arr) > 2:
			line.power = arr[3]
		line.coor = coor
		line.value = int(float(val)*10)
		line.name =  line.coor+"="+str(line.value)
		device_width = (64 / int(sys.argv[3]))
		line.error_bit_offset = (int(chip_offset)-1) * int(device_width)
		
		table  = parse_file(pathl)
		if table is not None:
			for x in table.findAll('td')[1:]:	#MK splits on the basis of whitespace, create a list of words from the lines.
				str_lst = str(x).split()
				address = str_lst[-5][:-1]
				line.addr.append(address)
				
				expected_value = int(str_lst[-3][:-1].lower(), 16)
				actual_value = int(str_lst[-1][:-5].lower(), 16)	
		
				addr_str = address #+  "_" + hex(expected_value) + "_" + hex(actual_value)
				if line.coor == "X":
					if addr_str not in addr_dict_x:
						# Dont let common addresses enter the database.
						line.enter_error(address, expected_value, actual_value)
						addr_dict_x[addr_str] =[1,[]]
						addr_dict_x[addr_str][1].append(line.coor + "_" + str(line.value))
					else:
						addr_dict_x[addr_str][0] +=1
						addr_dict_x[addr_str][1].append(line.coor + "_" + str(line.value))
	
				if line.coor == "Y":
					if addr_str not in addr_dict_y:
						# Dont let common addresses enter the database.
						line.enter_error(address, expected_value, actual_value)
						addr_dict_y[addr_str] =[1,[]]
						addr_dict_y[addr_str][1].append(line.coor + "_" + str(line.value))
					else:
						addr_dict_y[addr_str][0] +=1
						addr_dict_y[addr_str][1].append(line.coor + "_" + str(line.value))
	
	
		lines.append(line)
	return lines

