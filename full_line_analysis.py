import os
import sys
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import re
from collections import Counter

class Line:
    def __init__(self, file_name):
        self.file_name = file_name
        self.data = []

    def parse_file(self):
        print(self.file_name)
        with open(self.file_name, encoding="UTF-16LE") as f:
            soup = BeautifulSoup(f, "html.parser")
        
        tables = soup.find_all('table')
        selected_table = None
        
        for table in tables:
            if re.match(".*Last 5000 Errors.*", table.find('tr').find('td').text):
                selected_table = table
                break
        
        if selected_table is not None:
            rows = selected_table.find_all('tr')[1:]  # Skipping the header row
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 1:
                    text = cols[0].text.strip()
                    address_match = re.search(r"(Address:\s*[0-9A-Fa-f]+)", text)
                    expected_match = re.search(r"(Expected:\s*[0-9A-Fa-f]+)", text)
                    actual_match = re.search(r"(Actual:\s*[0-9A-Fa-f]+)", text)
                    
                    if address_match and expected_match and actual_match:
                        address = address_match.group(1).strip()
                        expected_value = expected_match.group(1).strip()
                        actual_value = actual_match.group(1).replace("</td>", "").strip()
                        self.data.append([address, expected_value, actual_value])

    def to_dataframe(self):
        df = pd.DataFrame(self.data, columns=['Address', 'Expected Value', 'Actual Value'])
        return df.astype(str)

def process_html_directory(directory):
    dataframes = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                line = Line(file_path)
                line.parse_file()
                df = line.to_dataframe()
                dataframes[file] = df
    return dataframes

def hex_to_decimal(hex_string):
    try:
        return int(hex_string, 16)
    except ValueError:
        print(f"Invalid hexadecimal number: {hex_string}")
        return None

def process_error_addresses(dataframes):
    data = {}
    for file_name, df in dataframes.items():
        error_addresses = [hex_to_decimal(ele.split('Address:')[1]) for ele in df['Address']]
        data[file_name] = set(error_addresses)

    return data

def decimal_to_32bit_binary(decimal_number):
    return bin(decimal_number)[2:].zfill(32)

def compute_xor_matrix(binary_string):
    xor_matrix = np.zeros((32, 32), dtype=int)
    for i in range(32):
        for j in range(32):
            xor_matrix[i][j] = int(binary_string[i]) ^ int(binary_string[j])
    return xor_matrix

def all_bits_same(bit_list):
    return len(set(bit_list)) == 1

def majority_bits_same(bit_list, threshold):
    _threshold = round(len(bit_list) * (threshold / 100))
    cntr = Counter(bit_list)
    return cntr[1] > _threshold or cntr[0] > _threshold

def list_to_tensor(matrix_list):
    if not matrix_list:
        raise ValueError("The matrix list should not be empty")
    
    shape = matrix_list[0].shape
    for matrix in matrix_list:
        if matrix.shape != shape:
            raise ValueError("All matrices must have the same shape")
    
    return np.stack(matrix_list, axis=0)

def analyze_data(data):
    intersections = {}
    cleaned_data = {}

    # Compute intersections and clean the data
    for file1, set1 in data.items():
        for file2, set2 in data.items():
            if file1 != file2:
                inter_key = f"{file1}_and_{file2}"
                intersections[inter_key] = set1.intersection(set2)

    for file, original_set in data.items():
        clean_set = original_set.copy()
        for inter_key, inter_set in intersections.items():
            if file in inter_key:
                clean_set -= inter_set
        cleaned_data[file] = sorted(clean_set)

    # Analyze cleaned data
    results = {}
    for file, clean_set in cleaned_data.items():
        if not clean_set:
            print(f"Cleaned set is empty for {file}, skipping processing.")
            continue
        list_matrix = []
        for ele in clean_set:
            data_binary = decimal_to_32bit_binary(ele)
            matrix_xor = compute_xor_matrix(data_binary[::-1])
            list_matrix.append(matrix_xor)

        tensor_experiment = list_to_tensor(list_matrix)
        checked_pairs = set()
        file_results = []

        for i in range(3, 28):
            for j in range(3, 28):
                if i != j:
                    sorted_pair = tuple(sorted((i, j)))
                    if sorted_pair not in checked_pairs:
                        checked_pairs.add(sorted_pair)
                        result = all_bits_same(list(tensor_experiment[:, i, j]))
                        result_maj = majority_bits_same(list(tensor_experiment[:, i, j]), 96)
                        if result:
                            file_results.append(f"Pair {i}-{j} is constant")
                        elif result_maj:
                            file_results.append(f"Pair {i}-{j} is almost constant")

        results[file] = file_results

    return results

def save_script(output_dir, results):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path = os.path.join(output_dir, 'analysis_results.txt')
    with open(output_path, 'w') as f:
        for file, res in results.items():
            f.write(f"Results for {file}:\n")
            for line in res:
                f.write(f"{line}\n")
            f.write("\n")
    print(f"Analysis script saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 full_line_analysis.py <source_directory>")
    else:
        source_dir = sys.argv[1]
        destination_dir = os.path.join(os.getcwd(), 'full_line_output')

        dataframes = process_html_directory(source_dir)
        data = process_error_addresses(dataframes)
        analysis_results = analyze_data(data)
        save_script(destination_dir, analysis_results)

