# Laser-Induced-DRAM-Bank-Reconstructor
This is a knowledge assissted tool to help uncover bank level mapping as well as internal bank organization

DESCRIPTION:

There are 2 python scripts for determining bank level mapping(full_line_analysis) and physical locations(grid_analysis) of banks in a chip. The result for each analysis will be saved in the same directory as where the user is running the command.



SYNTAX:

full_line_analysis: python3 full_line_analysis.py ./src_directory

grid_analysis: python3 grid_analysis.py ./src_directory chip_offset device_width (NOTE: chip_offset is a number range from 1 to 4 from flip position in error report)


	
TODO:

1: The namings for src files are different for full line analysis and grid analysis: 
	In full line analysis, X -- horizontal & Y -- vertical; value is the horizontal staring point of the laser;
	In grid analysis, X-- vertical & Y -- horizontal; value is the starting position associated with its coordinate; P -- power
	
2: Visually plot the precise bank location and automate the whole process; Currently user has to use knowledge to make educated guess for specific bank location where errors are less;

3: For bank level mapping, if the amount of errors are too little, there will be lots of constant piars that user has to guess the most frequent pairs among all lines and use knowledge to figure out BA0, BA1, BG0, BG1;

3: Deciding the boundary where die exists; Currently have to make attempts from chip bounday towards the center;

4: Haven't tested on different DDR4 machine and DDR3 devices;
