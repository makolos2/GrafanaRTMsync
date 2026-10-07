import json
import requests
import urllib3

# Suppress the warnings about disabled SSL verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define URL and Headers
url = "https://<VCFOPSFQDN>/suite-api/api/auth/token/exchange"
service_keys_list = ["<xxxx-xxx-xxxx-xxxx-xxxxxxx>"]

# To get the service keys, use the following API:
# GET https://<VCROPSFQDN>/suite-api/api/integrations/services
# Get the value of the "key" field where type: VCF_VODAP
# That is the ServiceKey

# Define Ops Token URL
tokenurl = "https://<VCFOPSFQDN>/suite-api/api/auth/token/acquire"
ops_user = "admin"
ops_user_pw = "MyPassword"

# Define RTM FQDN. Find this under VCF Ops: Build->Lifecycle->VCF Management->Components. Look up the FQDN/IP for Real-time metrics.
rtm_url = "rtm_fqdn"

#Define vCenter UUID:
vc_uuid = "vCenterUUID"

# Run this at bash prompt to get the UUID:
#   VC=<vCenter FQDN>
#   VER=$(curl -sk "https://$VC/sdk/vimServiceVersions.xml" \
#      | grep -o '<version>[0-9][^<]*</version>' | head -1 \
#      | tr -d '<>/' | sed 's/version//g')
#
# curl -sk "https://$VC/sdk/vim25/$VER/ServiceInstance/ServiceInstance/content" \
#  | jq -r '.about.instanceUuid'

# Grafana DataSource API
grafana_uid = "<datasourcename>"
grafana_url = f"http://<GRAFANAFQDN>:3000/api/datasources/uid/{grafana_uid}"
grafana_user = "admin"
grafana_password = "Password"

#### No need to modify any of the lines below

token_headers = {
    "Content-Type": "application/json"
}
token_payload = {
    "username": f"{ops_user}",
    "password": f"{ops_user_pw}"
}


payload = {
    "serviceKeys": service_keys_list
}
#Get Ops Token with username/pw
try:
  # 1. Prepare the request details explicitly to print them
    session = requests.Session()
    req = requests.Request("POST", tokenurl, headers=token_headers, json=token_payload)
    prepared_request = session.prepare_request(req)

    # 2. Print the HTTP request to the screen
    print("=" * 30 + " OUTGOING HTTP REQUEST " + "=" * 30)
    print(f"Method:  {prepared_request.method}")
    print(f"URL:     {prepared_request.url}")
    print("\nHeaders:")
    for key, value in prepared_request.headers.items():
        print(f"  {key}: {value}")

    print("\nBody (JSON):")
    # Decode the payload bytes to string and prettify it
    body_str = prepared_request.body.decode('utf-8') if prepared_request.body else "{}"
#    try:
#        print(json.dumps(json.loads(body_str), indent=4))
#    except json.JSONDecodeError:
#        print(body_str)
    print("=" * 83 + "\n")

    # 3. Send the prepared request
    response = session.send(prepared_request, verify=False, timeout=10)
    response.raise_for_status()

    # Parse the JSON response
    data = response.json()

    # Extract the jwtToken field
    ops_token = data.get("token")

    if not ops_token:
        raise ValueError("Error: 'token' field was not found in the token exchange response.")
except requests.exceptions.RequestException as error:
    print(f"API Request failed: {error}")
    if hasattr(error, 'response') and error.response is not None:
        print(f"Server Response: {error.response.text}")


# Optional: Add your payload body here if the exchange endpoint requires credentials
# payload = {"username": "your_user", "password": "your_password"}

try:
    # 1. Prepare the request details explicitly to print them
    #    session = requests.Session()
    headers = {
       "Content-Type": "application/json",
       "Authorization": f"OpsToken {ops_token}"
    }
    req = requests.Request("POST", url, headers=headers, json=payload)
    prepared_request = session.prepare_request(req)

    # 2. Print the HTTP request to the screen
    print("=" * 30 + " OUTGOING HTTP REQUEST " + "=" * 30)
    print(f"Method:  {prepared_request.method}")
    print(f"URL:     {prepared_request.url}")
    print("\nHeaders:")
    for key, value in prepared_request.headers.items():
        print(f"  {key}: {value}")

    print("\nBody (JSON):")
    # Decode the payload bytes to string and prettify it
    body_str = prepared_request.body.decode('utf-8') if prepared_request.body else "{}"
    try:
        print(json.dumps(json.loads(body_str), indent=4))
    except json.JSONDecodeError:
        print(body_str)
    print("=" * 83 + "\n")

    # 3. Send the prepared request
    response = session.send(prepared_request, verify=False, timeout=10)
    response.raise_for_status()

    # Parse the JSON response
    data = response.json()

    # Extract the jwtToken field
    jwt_token = data.get("jwtToken")

    if not jwt_token:
        raise ValueError("Error: 'jwtToken' field was not found in the token exchange response.")

    # -----------------------------------------------------------------
    # STEP 2: Update Grafana Data Source via PUT Request
    # -----------------------------------------------------------------
    # Build the required Grafana payload configuration
    grafana_payload = {
        "uid": "vcfrtm01",
        "name": "VCFRTM",
        "type": "prometheus",
        "typeLogoUrl": "public/plugins/prometheus/img/prometheus_logo.svg",
        "access": "proxy",
        "url": f"https://{rtm_url}/data-query-service/",
        "user": "",
        "database": "",
        "basicAuth": False,
        "basicAuthUser": "",
        "withCredentials": False,
        "isDefault": True,
        "jsonData": {
            "httpHeaderName1": "Authorization",
            "httpMethod": "GET",
            "manageAlerts": True,
            "prometheusType": "Prometheus",
            "queryTimeout": "60s",
            "timeInterval": "15s",
            "tlsSkipVerify": True,
            "customQueryParameters": f"sourceId={vc_uuid}"
        },
        "secureJsonData": {
            "httpHeaderValue1": f"Bearer {jwt_token}"  # Injecting the fetched token
        }
    }

    # Set up Grafana headers
    grafana_headers = {
        "Content-Type": "application/json"
    }

    # Prepare and print Grafana PUT Request
    grafana_req = requests.Request(
        "PUT",
        grafana_url,
        headers=grafana_headers,
        json=grafana_payload,
        auth=(grafana_user, grafana_password)  # Enforces HTTP Basic Auth
    )
    prepared_grafana_req = session.prepare_request(grafana_req)

    print("=" * 30 + " OUTGOING GRAFANA PUT REQUEST " + "=" * 30)
    print(f"Method:  {prepared_grafana_req.method}")
    print(f"URL:     {prepared_grafana_req.url}")
    print("\nBody (JSON):")
    # Masking token in the console log to prevent screen-leak of sensitive details
    log_payload = json.loads(prepared_grafana_req.body.decode('utf-8'))
    # log_payload["secureJsonFields"]["httpHeaderValue1"] = "[MASKED_JWT_TOKEN]"
    print(json.dumps(log_payload, indent=4))
    print("=" * 90 + "\n")

    # Send Grafana Update Request
    grafana_response = session.send(prepared_grafana_req, verify=False, timeout=10)
    grafana_response.raise_for_status()

    print(f"Success: Grafana data source updated. HTTP Status: {grafana_response.status_code}")
    print(f"Response: {grafana_response.text}")

except requests.exceptions.RequestException as error:
    print(f"API Request failed: {error}")
    if hasattr(error, 'response') and error.response is not None:
        print(f"Server Response: {error.response.text}")
except Exception as error:
    print(f"An error occurred: {error}")
