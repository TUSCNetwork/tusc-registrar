# Registrar
## Requests

See the individual webctrl_*.py files for supported endpoints.

Headers:
- `Content-Type`: "application/json"

In any endpoint expecting a `POST`, ensure the required fields are in a JSON object in the body of the request.

##### Example
```
POST to http://*ip address*:8080/tusc/wallet/api/register_account
```
```
{
    "account_name": "someaccountname",
    "public_key": "TUSC6xiw2BAZnZ5gB7n31Bz5E2dtGqqc9BoftEb3TGpy3hRj27Qpvq"
}
```
## Responses

All responses are in JSON objects.

### Successful responses

These will have all the necessary information directly in the response, no need to parse deeper into a JSON object.

See the individual webctrl_*.py files for example responses to each endpoint.

### Error responses

All error responses will have an `error` field in the JSON object. 
It's safe to assume the value of this `error` field can be displayed directly to an end user. 

##### Example error responses

```
{
    "error": "Something went wrong, please contact tusc support"
}
```
```
{
    "error": "Account name 'someaccountname' could not be found. "
}
```
```
{
    "error": "Account name '@12345678' is invalid. Account names must be more than 7 and less than 64 characters. 
    They must consist of lower case characters, numbers, and '-'. They Cannot start with a number."
}
```

## Docker

This is unnecessary for development but if you want to actually run a full HTTP server in Docker:

Change the `tusc_wallet_ip` in local_config.yaml to point to your system's Docker NAT address.
E.g. mine was:
```
Ethernet adapter vEthernet (nat):

   Connection-specific DNS Suffix  . :
   Link-local IPv6 Address . . . . . : fe80::f020:c87b:2c21:bcff%8
   IPv4 Address. . . . . . . . . . . : 172.23.224.1
   Subnet Mask . . . . . . . . . . . : 255.255.240.0
   Default Gateway . . . . . . . . . :
``` 

Run this in a cmd prompt/terminal in the `tusc-swap` dir:
```
docker build --tag tusc-swap .
```

Then, to start the container, run:
```
docker run -p 8080:8080 tusc-swap
```

Once started, you should be able to send commands to:
```
http://localhost:8080/tusc/wallet/api/<endpoint_>
```