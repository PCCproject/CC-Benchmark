import os

curr_path = os.path.dirname(os.path.realpath(__file__))
test_nickname = {
    'rtt3':'Rtt Fairness',
    'rtt4':'Rtt Fairness',
    'bw_sweep':'Bandwidth Sweep',
    'bw_sweep_w_trace':'Bandwidth Sweep with Trace',
    'q_sweep':'Queue Sweep',
    'loss_sweep':'Loss Sweep',
    'jitter_sweep':'Jitter Sweep',
    'lat_sweep':'Latency Sweep',
    'multiflow_sweep':'Multiflow Sweep'
}

display_name = {
    'bbr': 'BBR',
    'default_tcp': 'TCP Cubic',
    'vivace_latency': 'PCC Vivace',
}

def get_missing_scheme_html(path):
    list_of_schemes = set()
    for file in os.listdir(path):
        if '.DS' in file:
            continue
        list_of_schemes.add(file)

    testname = None
    testpath = os.path.join(path, '..')

    existing_html = set()

    for file in os.listdir(testpath):
        if 'index' in file or (not file.endswith('.html')):
            continue
        split = file.split('_')

        for i, entry in enumerate(split):
            # Exception where scheme is 2 word
            if entry == 'default':
                entry = 'default_tcp'
            if entry == 'vivace':
                entry = 'vivace_latency'
            if entry in list_of_schemes:
                testname = '_'.join(split[:i])
                break
        if testname != None:
            break
    for file in os.listdir(testpath):
        if 'index' in file or (not file.endswith('.html')):
            continue
        scheme = file.split('_result.html')[0].split(testname+'_')[-1]
        existing_html.add(scheme)

    if testname == None:
        raise EnvironmentError("Please add at least one HTML for public schemes")

    missing_schemes = list_of_schemes - existing_html
    return (missing_schemes, testname)

def create_detailed_flow_html(testname, scheme):
    html_template = os.path.join(curr_path, 'detailed_flow.html')
    with open(html_template) as f:
        contents = f.read().split('</TODO> -->')[-1].lstrip()

    contents = contents.replace("NAME OF THE TEST", test_nickname[testname])
    split = contents.split("SCHEME")

    try:
        displayname = display_name[scheme]
    except:
        if ',' in scheme:
            displayname = scheme.replace(',', ':')
        else:
            displayname = scheme.capitalize() 
    
    new_contents = split[0] + displayname + split[1] + displayname + split[2] + scheme + split[3]

    return new_contents

def add_detail_flows(path):
    for file in os.listdir(path):
        if not file.endswith('_test'):
            continue

        base_path = os.path.join(path, file)
        data_path = os.path.join(base_path, 'data')
        missing_schemes, testname = get_missing_scheme_html(data_path)

        for scheme in missing_schemes:
            html_contents = create_detailed_flow_html(testname, scheme)
            html_path = os.path.join(base_path, '_'.join([testname, scheme, 'result.html']))
            with open(html_path, 'w') as f:
                f.write(html_contents)
        
    
