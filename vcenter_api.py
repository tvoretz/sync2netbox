import requests
import json
import settings


class VCapi:
    session = None
    url = 'https://' + settings.VCHOST + '/rest'

    def __init__(self):
        print("VCapi object created.")
        self.session = requests.Session()
        self.session.verify = False
        self.session.proxies = settings.proxies
        self.session.post(self.url + '/com/vmware/cis/session', auth=(settings.USER, settings.PSWD))

    def get_clusters(self):
        clusters = self.session.get(self.url + '/vcenter/cluster')
        return json.loads(clusters.text)['value']

    def get_standalone_hosts(self):
        hosts = self.session.get(self.url + '/vcenter/host?filter.standalone=true')
        return json.loads(hosts.text)['value']

    def get_vms(self, cluster=None, host=None):
        if cluster:
            vms = self.session.get(self.url + '/vcenter/vm?filter.clusters=' + cluster)
        elif host:
            vms = self.session.get(self.url + '/vcenter/vm?filter.hosts=' + host)
        else:
            vms = self.session.get(self.url + '/vcenter/vm')
        return json.loads(vms.text)['value']
