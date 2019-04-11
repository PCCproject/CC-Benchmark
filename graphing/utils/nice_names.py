_nice_names = {
    "default_tcp":"TCP Cubic",
    "vivace_latency":"PCC Vivace",
    "copa":"Copa",
    "bbr":"BBR",
    "taova":"RemyCC",
    "icml_paper_final":"Aurora",
    "very_high_thpt_rand_loss":"Aurora - early ver",
    "PCC-Uspace:njay-recv-dur-infl:29451":"PCC infl. fix",
    "PCC-Uspace:njay-staged:df797":"PCC njay-staged",
    "PCC-Uspace:sub-rate:4d868":"PCC sub-rate"
}

def get_nice_name(scheme):
    if scheme in _nice_names.keys():
        return _nice_names[scheme]
    return scheme
