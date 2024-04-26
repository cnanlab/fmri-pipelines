import re

def get_bad_zfstat_registrations(log_file):
    with open(log_file, 'r') as file:
        lines = file.readlines()

    jacobian_pattern = re.compile(r'obtained range is ([\d.]+) -- ([\d.]+)')
    fnirt_node_pattern = re.compile(r'FNIRT_NODE: (.+) ->')
    
    dicts = []

    for i in range(len(lines)):
        jacobian_match = jacobian_pattern.search(lines[i])
        if jacobian_match:
            min_range, max_range = jacobian_match.groups()
            for j in range(i + 1, len(lines)):
                fnirt_node_match = fnirt_node_pattern.search(lines[j])
                if fnirt_node_match:
                    zfstat_path = fnirt_node_match.group(1)
                    print(f"Jacobian range: {min_range} -- {max_range}")
                    print(f"zfstat path: {zfstat_path}")
                    
                    dicts.append({
                        "jacobian_range": (min_range, max_range),
                        "zfstat_path": zfstat_path                    
                    })
                    break
                
    return dicts


if __name__ == "__main__":
    log_file = 'logfile.txt'
    bad_zfstat_dicts = get_bad_zfstat_registrations(log_file)
    
    print(f"There are {len(bad_zfstat_dicts)} bad zfstat registrations.")
    
    