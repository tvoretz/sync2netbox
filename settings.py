import urllib3

# Used for Proxy and vCenter
USER = ''
PSWD = ''

# Hosts
PROXY_HOST = ''
VCHOST = ''
NBHOST = ''

# Netbox token
TOKEN = ''

proxies = {
    'http': 'http://'+USER+':'+PSWD+'@'+PROXY_HOST,
    'https': 'http://'+USER+':'+PSWD+'@'+PROXY_HOST
}

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)