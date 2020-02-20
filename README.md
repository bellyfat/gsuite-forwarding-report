# gsuite-forwarding-report

This script has run faithfully for a few years, but was not designed with any sort
of robustness in mind. It was quickly written one afternoon in order to gather all 
of the forwarding address in use in a GSuite domain. It also gathers Reply To and 
Send From addresses that may be configured. This information is helpful in ensuring
the security of accounts in a domain.

How to use it:
1) download / unpack it
2) rename config_example.py => config.py
3) edit config.py
4) (./oauth/readme.txt)
5) python forwards2.py initially will step through the oauth config and create oauth.txt.
