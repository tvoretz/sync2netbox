import vcenter_api
import netbox_api


# ====================== Sync clusters ======================
def sync_clusters_add() -> bool:
    hosts_to_add = {k: v for (k, v) in vc_hosts.items() if k not in nb_clusters.keys()}
    clusters_to_add = {k: v for (k, v) in vc_clusters.items() if k not in nb_clusters.keys()}
    resync_needed = False

    for (k, v) in clusters_to_add.items():
        result_code = nbapi.add_cluster(k, 'vsphere')
        print('Cluster "{}" added to Netbox with result_code {}'.format(k, result_code))
        resync_needed = True

    for (k, v) in hosts_to_add.items():
        result_code = nbapi.add_cluster(k, 'vsphere')
        print('Host "{}" added to Netbox with result_code {}'.format(k, result_code))
        resync_needed = True

    return resync_needed


def sync_clusters_del():
    clusters_to_del = {k: v for (k, v) in nb_clusters.items() if k not in vc_clusters.keys() and k not in vc_hosts.keys()}

    for (k, v) in clusters_to_del.items():
        result_code = nbapi.del_cluster(v)
        print('Cluster "{}" deleted from Netbox with result_code {}'.format(k, result_code))


# ====================== Sync VMs ======================
def sync_vms():
    # Add new VMs
    nb_vms_names = [itm['name'] for itm in nb_vms]
    vms_to_add = [
        {'name': k,
            'status': 1 if v['state'] == 'POWERED_ON' else 0,
            'cluster': nb_clusters.get(v['cluster_or_host_name']),
            'vcpus': v['cpu'],
            'memory': v['ram'],
        } for (k, v) in vc_vms.items() if k not in nb_vms_names]
    print("VMs to add: {}".format(vms_to_add))
    for itm in vms_to_add:
        result_code = nbapi.add_vm(itm)
        print('VM "{}" added to Netbox with result_code {}'.format(itm['name'], result_code))

    # Update VMs
    nb_vms_by_name = {
        itm['name']: {
            'id': itm['id'],
            'status': 'POWERED_ON' if itm['status']['value'] == 1 else 'POWERED_OFF',
            'cluster_id': itm['cluster']['id'],
            'cluster_name': itm['cluster']['name'],
            'vcpus': itm['vcpus'],
            'memory': itm['memory'],
        } for itm in nb_vms}

    print('======================================================')
    patch_dict = {}
    for (k, v) in vc_vms.items():
        nb_vm_to_check = nb_vms_by_name.get(k, None)
        if nb_vm_to_check:
            if nb_vm_to_check['vcpus'] != v['cpu']:
                print('VM {}: vcpus needs to be updated. Value in Netbox: {}. Value in vCenter: {}'.format(k, nb_vm_to_check['vcpus'], v['cpu']))
                patch_dict['vcpus'] = v['cpu']
            if nb_vm_to_check['memory'] != v['ram']:
                print('VM {}: memory needs to be updated. Value in Netbox: {}. Value in vCenter: {}'.format(k, nb_vm_to_check['memory'], v['ram']))
                patch_dict['memory'] = v['ram']
            if nb_vm_to_check['status'] != v['state']:
                print('VM {}: status needs to be updated. Value in Netbox: {}. Value in vCenter: {}'.format(k, nb_vm_to_check['status'], v['state']))
                patch_dict['status'] = 1 if v['state'] == 'POWERED_ON' else 0
            if nb_vm_to_check['cluster_name'] != v['cluster_or_host_name']:
                print('VM {}: cluster needs to be updated. Value in Netbox: {}. Value in vCenter: {}'.format(k, nb_vm_to_check['cluster_name'], v['cluster_or_host_name']))
                patch_dict['cluster'] = nb_clusters.get(v['cluster_or_host_name'])
            if patch_dict:
                if not patch_dict.get('cluster'):
                    patch_dict['cluster'] = nb_vm_to_check['cluster_id']
                patch_dict['name'] = k
                print('Values in patch: {}'.format(patch_dict))
                result_code = nbapi.patch_vm(nb_vm_to_check['id'], patch_dict)
                print('VM "{}" patched in Netbox with result_code {}'.format(k, result_code))
                print('======================================================')
                patch_dict.clear()

    # Delete VMs
    vms_to_del = {itm['id']: itm['name'] for itm in nb_vms if itm['name'] not in vc_vms.keys()}
    print("VMs to delete from Netbox: {}".format(vms_to_del))
    for (k, v) in vms_to_del.items():
        result_code = nbapi.del_vm(k)
        print('VM "{}" deleted from Netbox with result_code {}'.format(v, result_code))

# ======================================================


vcapi = vcenter_api.VCapi()
nbapi = netbox_api.NBapi()

# Get actual clusters
vc_hosts = {item['name']: item['host'] for item in vcapi.get_standalone_hosts()}
vc_clusters = {item['name']: item['cluster'] for item in vcapi.get_clusters()}
nb_clusters = {item['name']: item['id'] for item in nbapi.get_clusters('vsphere')}

# Sync clusters and re-read nb_clusters if new clusters added
resync_needed = sync_clusters_add()
if resync_needed:
    print('New clusters was added to Netbox. Resyncing nb_clusters.')
    nb_clusters.clear()
    nb_clusters = {item['name']: item['id'] for item in nbapi.get_clusters('vsphere')}

# Construct VMs dict from Netbox and vCenter
nb_vms = nbapi.get_vms()
vc_vms = {}
for (hostname, hostid) in vc_hosts.items():
    vc_vms.update(
        {item['name']:
             {'vmid': item['vm'],
              'cpu': item['cpu_count'],
              'ram': item['memory_size_MiB'],
              'state': item['power_state'],
              'cluster_or_host_name': hostname,
              'cluster_or_host_id': hostid,
              }
         for item in vcapi.get_vms(host=hostid)}
    )
for (clustername, clusterid) in vc_clusters.items():
    vc_vms.update(
        {item['name']:
             {'vmid': item['vm'],
              'cpu': item['cpu_count'],
              'ram': item['memory_size_MiB'],
              'state': item['power_state'],
              'cluster_or_host_name': clustername,
              'cluster_or_host_id': clusterid,
              }
         for item in vcapi.get_vms(cluster=clusterid)}
    )

sync_vms()
sync_clusters_del()
print('All sync finished')
