import requests
import json
import settings


class NBapi:
    session = None

    def __init__(self):
        print("NBapi object created.")
        self.session = requests.Session()
        self.session.verify = False
        self.session.proxies = settings.proxies
        self.session.headers = {'Authorization': 'Token {}'.format(settings.TOKEN),
               'Accept': 'application/json; indent=4'}

    # =========== Clusters ===========

    def get_clusters(self, type):
        clusters = self.session.get(settings.NBHOST + '/virtualization/clusters/?type={}'.format(type))
        return json.loads(clusters.text)['results']

    def get_cluster_type_id(self, type):
        type_id = self.session.get(settings.NBHOST + '/virtualization/cluster-types/?slug={}'.format(type))
        return json.loads(type_id.text)['results'][0]['id']

    def add_cluster(self, name, type):
        type_id = self.get_cluster_type_id(type)
        status = self.session.post(settings.NBHOST + '/virtualization/clusters/', json={'name': name, 'type': type_id})
        return status.status_code

    def del_cluster(self, id):
        status = self.session.delete(settings.NBHOST + '/virtualization/clusters/{}/'.format(id))
        return status.status_code

    # =========== VMs ===========

    def add_vm(self, data):
        status = self.session.post(settings.NBHOST + '/virtualization/virtual-machines/', json=data)
        return status.status_code

    def patch_vm(self, id, data):
        status = self.session.patch(settings.NBHOST + '/virtualization/virtual-machines/{}/'.format(id), json=data)
        return status.status_code

    def del_vm(self, id):
        status = self.session.delete(settings.NBHOST + '/virtualization/virtual-machines/{}/'.format(id))
        return status.status_code

    def get_vms(self):
        vms = self.session.get(settings.NBHOST + '/virtualization/virtual-machines/?limit=1000')
        return json.loads(vms.text)['results']

    # =========== Network ===========

    def get_prefix_by_vlan(self, vlan):
        prefixes = self.session.get(settings.NBHOST + '/ipam/prefixes/?vid={}'.format(vlan))
        return json.loads(prefixes.text)

    def get_available_ips_by_prefix_id(self, prefix_id):
        ips = self.session.get(settings.NBHOST + '/ipam/prefixes/{}/available-ips/'.format(prefix_id))
        return json.loads(ips.text)