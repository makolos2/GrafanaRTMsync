RTMtoken.py serves a purpose of re-authenticating to the VCF Real-time metrics (RTM) service and then updating Grafana with the current authentication token to ensure continued operation.

Why is it required?

VCF RTM access tokens have a 35-minute TTL, and there is currently no option to obtain a longer-lifetime token, nor use an alternative authentication method.
Grafana does not have a native method to request new tokens, but it does expose an API that can be used to update the datasource where the tokens are referenced.

Due to the way Grafana's API requires the entire data source config to be sent to make the update, the configuration of the data source must be contained in the RTMtoken.py script. 
Any changes to the data source made in Grafana will be overwritten by this script.

How to use it

Before it can be used, the script requires an environment with:

  - Python 3
  - json, requests and urllib3 libraries for python
  - a VCF 9.1+ instance with VCF Real-time metrics installed
  - Network connectivity to the VCF Real-time metrics (VCF Management services) instance.

The following data values are required to configure the script:

- VCF Operations FQDN
- VCF Operations username & password for a user with read-access to the VCF RTM component
- Real-time Metrics FQDN (the VCF Management Services instance FQDN)
- Real-time metrics service key from VCF Operations.
- vCenter UUID
- the Grafana FQDN
- Grafana username and password with access to modify the data source
- the name of the Data Source in Grafana

How-to get the above values:

To get the service keys, use the following API:
```
GET https://<VCROPSFQDN>/suite-api/api/integrations/services
```
Get the value of the "key" field where type: VCF_VODAP

That is the ServiceKey, entered between the quotes in the service_keys_list sample value in the script.

Run this at bash prompt to get the vCenter UUID:

```
VC=vCenter_FQDN

VER=$(curl -sk "https://$VC/sdk/vimServiceVersions.xml" \
| grep -o '<version>[0-9][^<]*</version>' | head -1 \
| tr -d '<>/' | sed 's/version//g')

curl -sk "https://$VC/sdk/vim25/$VER/ServiceInstance/ServiceInstance/content" \
| jq -r '.about.instanceUuid'

```


Limitations

This script currently only supports a single VCF instance.
- The script does not have any scheduling capabilities of its own and is intended to be run from a crontab or other scheduler, typically every 30 minutes
- The VCF Operations username & password being used with access to real-time metrics (read-only access is all that is needed) is stored in plain text in the script, 
  so access to read the script itself should be restricted once configured.
- Requires the user to manually get the RTM Service key, although it would be nice to have it automatically get that from the API. Similarly the RTM FQDN could be obtained from the API

Implementation

You can set up VCF Real-Time metrics as a prometheus data source in Grafana. There are two customizations you will need to add to make it succeed:
add sourceId=VC_UUID to the custom query parameters on the data source. 

Include an http Header with Name: "Authorization" and value "Bearer RTM_access_token".
(replace RTM_access_token with the actual token).

The rtmtoken.py script includes this configuration.


To see the list of available metrics that can be used in Grafana dashboards, you can use the RTM API:

Note: you will need to include Bearer Token authentication with a valid Real-time metrics access token (the script generates that so you can review it for how to get the token, or capture it in the output by running it manually).

```
GET https://{rtm_fqdn}/data-query-service/api/v1/metadata
```
or review the complete list published on the Broadcom TechDocs site: https://techdocs.broadcom.com/content/dam/broadcom/techdocs/us/en/assets/vmware-cis/vcf/VODAP-9.1-Metrics-List-Per-Provider.xlsx

You may need to apply different policies in VCF Operations to collect the desired metrics from different resources.




