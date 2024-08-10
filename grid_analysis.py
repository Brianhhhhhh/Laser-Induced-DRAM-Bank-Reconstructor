import sys
import os
import laser_lib as ll
import pandas as pd
import matplotlib.pyplot as plt


# Function to calculate errors for each bank per line
def calc_bank_errors(bank_row_dict, bank):
    errors = 0
    for row in bank_row_dict[bank]:
        for col in bank_row_dict[bank][row]:
            for bit in bank_row_dict[bank][row][col]:
                errors += bank_row_dict[bank][row][col][bit][0] + bank_row_dict[bank][row][col][bit][1]
    return errors


# Parse the run directory
lines = ll.parse_run_directory(sys.argv[1], sys.argv[2])
lines = sorted(lines, key=lambda line: line.name)

data = []
bank_error_data = {}

# Collect all unique bank numbers
all_banks = set()
for line in lines:
    all_banks.update(line.bank_row_dict.keys())

# Create column names for banks, with a blank column between Total Error and banks
columns = ['Coordinate=Value', 'Total Error', 'Power', ''] + [f"Bank {bank}" for bank in sorted(all_banks)]

for line in lines:
    row_base = [f"{line.coor} = {line.value}"]
    total_error = sum(calc_bank_errors(line.bank_row_dict, bank) for bank in line.bank_row_dict)
    row = row_base + [total_error, line.power, '']  # Adding a blank cell
    
    bank_errors = {f"Bank {bank}": calc_bank_errors(line.bank_row_dict, bank) for bank in line.bank_row_dict}
    
    # Fill in bank error columns
    for bank in sorted(all_banks):
        row.append(bank_errors.get(f"Bank {bank}", 0))
    
    data.append(row)

    for bank in line.bank_row_dict:
        error = calc_bank_errors(line.bank_row_dict, bank)
        if bank not in bank_error_data:
            bank_error_data[bank] = error
        else:
            bank_error_data[bank] += error

# Create output directory if it doesn't exist
output_dir = os.path.join(os.getcwd(), 'grid_output')
os.makedirs(output_dir, exist_ok=True)

# Create DataFrame for line-specific data and save it to the output directory
df = pd.DataFrame(data, columns=columns)
output_line_file = os.path.join(output_dir, 'output_per_line.xlsx')
df.to_excel(output_line_file, index=False)

# Create DataFrame for total error per bank and save it to the output directory
df_bank = pd.DataFrame(list(bank_error_data.items()), columns=['Bank', 'Total Error per Bank'])
output_bank_file = os.path.join(output_dir, 'output_per_bank.xlsx')
df_bank.to_excel(output_bank_file, index=False)

# Print bank set information for lines with coordinate X
for line in lines:
    if line.coor == "X":
        bank_set = set(line.bank_row_dict.keys())
        print(f"Line {line.coor} = {line.value} has banks: {bank_set}")

print("/n")        

# Print bank set information for lines with coordinate Y
for line in lines:
    if line.coor == "Y":
        bank_set = set(line.bank_row_dict.keys())
        print(f"Line {line.coor} = {line.value} has banks: {bank_set}")


# plot bank location on the chip     
banks = {}
for line in lines:
	for bank in line.bank_row_dict:
		if bank not in banks:
			banks[bank] = [[],[]]
		if line.coor == "X":
			banks[bank][0].append(line.value)
		if line.coor == "Y":
			banks[bank][1].append(line.value)
banks2 = {}
for bank in banks:
	banks2[bank] = []
	for X in banks[bank][0]:
		for Y in banks[bank][1]:
			banks2[bank].append([X,Y])

# Full path to save the figure
save_path = os.path.join(output_dir, "spatial_mapping_of_banks.png")

# Plot the banks with shifts to avoid overlap
banks_list = list(banks2.keys())
scatter_plot = []
position_shift = {}

for bank in banks2:
    bank_id = banks_list.index(bank)
    X = []
    Y = []
    for point in banks2[bank]:
        x, y = point[0], point[1]
        
        # Check if this (x, y) position is already used
        if (x, y) in position_shift:
            x_shift, y_shift = position_shift[(x, y)]
            position_shift[(x, y)] = (x_shift + 1.5, y_shift + 1.5)  # Incremental shift for each overlap
        else:
            x_shift, y_shift = (0, 0)
            position_shift[(x, y)] = (x_shift + 1.5, y_shift + 1.5)
        
        # Apply the shift to avoid overlap
        X.append(x + x_shift)
        Y.append(y + y_shift)
    
    scatter_plot.append(plt.scatter(X, Y, color='black', s=0, marker="o"))
    
    # Plot text with shifts applied
    for x, y in zip(X, Y):
        plt.text(x, y, str(bank), color="red", fontsize=6)

plt.title("Spatial Mapping of Banks")
plt.xlim(0, 110)
plt.ylim(0, 110)

# Save the plot to the specified directory
plt.savefig(save_path)

plt.show()
plt.close()
        
        
        

