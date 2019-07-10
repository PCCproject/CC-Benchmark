import os

# Important
# Current host is ocean0

rsa_path = '/srv/shared/PCC/.web_rsa/web_rsa'
testdata_path = '/srv/shared/PCC/testing/pcc-web/test_data/*'
website_path = 'pcctesting@web.illinois.edu:/home/pcctesting/public_html/test_data'

def rsync_with_cpanel():
    cmd = 'rsync -r -avz -e "ssh -i {}" {} {}'.format(rsa_path, testdata_path, website_path)
    print("Executing {}".format(cmd))
    print("Updating results to web...")
    os.system(cmd)
