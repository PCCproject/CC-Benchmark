import os

# Important
# Current host is ocean0

rsa_path = '~/.ssh/web_rsa'
testdata_path = '/srv/shared/PCC/testing/pcc-web/*'
website_path = 'pcctesting@web.illinois.edu:/home/pcctesting/public_html/'

def rsync_with_cpanel():
    cmd = 'rsync -r -avz -e "ssh -i {}" {} {}'.format(rsa_path, testdata_path, website_path)
    print("Updating results to web...")
    os.system(cmd)
