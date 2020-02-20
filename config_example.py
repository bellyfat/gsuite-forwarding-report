# Information about your Google domain
GOOGLE_DOMAIN = "domain.edu"
CUSTOMER_ID = "your customer id" # I get this by running python gam.py info domain, it's probably in the web Admin Console somewhere too.

OUTPUT_DIR = "./output"

NUM_WORKERS = 10 # Number of simultaneous threads to run when gathering forwards
DEBUG_WORKERS = False # Use this to have each worker thread output what it does to a file

# =================================================
# Optional: If you want to email a GPG encrypted report, enable this and configure the following
# =================================================
EMAIL_ENCRYPTED_REPORT = False
MAILSERVER = "smtp.domain.edu"
GPG_PATH = "/usr/bin/gpg"
# Python list of recipients to recieve the resulting .gpg file
REPORT_RECIPIENTS = ['person1@domain.edu','person2@domain.edu']

# Address of the GPG key you want to use to encrypt the file before emailing
# I'm not GPG expert, you'll need to make sure this is configured on the local system
REPORT_GPG_ADDRESS = "person1@domain.edu"

# From Address of the resulting report
REPORT_FROM = "person1@domain.edu"


