# local-ca

This role provides a local (i.e. on the node that executes ansible or on some
delegated node) CA.

## Configuration

| Variable name | Default value | Description |
|---------------|---------------|-------------|
| `local_ca_dhparam_size` | `2048` | Size for generated Diffie-Hellman parameters |
| `local_ca_workhost` | `localhost` | The host to generate the CA on |
| `local_ca_basepath` | undefined | Base directories of CAs on the remote host if `local_ca_workhost` is defined |
| `local_ca_fetchdir` | `fetch/ctmp` | Where to store secret material on the control node |
| `local_ca_owner` | `root` | Owner of certificates on the target node |
| `local_ca_group` | `root` | Group of certificates on the target node |
| `local_ca_mode` | `0640` | Permissions of certificates on the target node |

## How to use this?

This role has to be called with parameters, like so:

```
  - role: local-ca
    local_ca_caname: DemoPKI
    <params>
```

where params consists of at least one of the following blocks:

* `local_ca_server`: Generate a server certificate. Arguments:
  * `cn` (required): Common Name
  * `c` (optional): country code (2-letters)
  * `st` (optional): State/Province
  * `city` (optional): City/Locality
  * `email` (optional): Email addresses
  * `ou` (optional): Organisational Unit
  * `org` (optional): Organisation
  * `san` (optional): SAN in openssl cmdline format.

* `local_ca_both`: Generate a server certificate that can also be used as a
  client certificate. Parameters are the same as `local_ca_server`.

* `local_ca_ca`: Copy CA certificate to node
  * `cert` (required): destination for the PEM file
  * `crl` (optional): destination for CRL. The CRL gets regenerated each time
    this role is invoked.

* `local_ca_client`: Generate a client certificate. Arguments:
  * `cn` (required): Common Name
  * `c` (optional): country code (2-letters)
  * `st` (optional): State/Province
  * `city` (optional): City/Locality
  * `email` (optional): Email addresses
  * `ou` (optional): Organisational Unit
  * `org` (optional): Organisation

* `local_ca_dhparam`: Generate dhparam
  * `dest` (required): destination

Additionally you can specify formats for the three certificate-generating blocks
(server, client and both). PEM files of the keys are always generated on the
workhost. Supported formats are:

### PEM

Just copy the generated PEM files to the node:

```
local_ca_server:
  ...
  pem:
    key: /path/to/key       # Optional
    cert: /path/to/cert     # Optional
```

### PKCS8

Wrap the private key into a DER PKCS8 container. To achieve this specify

```
local_ca_server:
  ...
  pkcs8:
    password: changeme          # optional. If missing, key is not encrypted
    path: /path/on/target/node
```

### PKCS12

Wrap private key, certificate and CA certificate into a PKCS12 container. To
achieve this specify:

```
local_ca_server:
  ...
  pkcs12:
    password: changeme
    name: my-key                # name of the keypair inside the container
    path: /path/on/target/node
```

### Java Key Store

Wrap private key, certificate and CA certificate into an JKS container. To
achieve this specify:

```
local_ca_server:
  ...
  jks:
    password: changeme
    name: my-key                # name of the keypair inside the container
    path: /path/on/target/node
```

An example invocation might look like this:

```
  - hosts: mon-server
    roles:
      - role: local-ca
        local_ca_caname: icinga
        local_ca_group: nagios
        local_ca_both:
          cn: "{{ ansible_fqdn }}"
          san: "DNS:{{ ansible_nodename }},DNS:{{ ansible_fqdn }},IP:{{ansible_all_ipv4_addresses|join(',IP:')}},IP:127.0.0.1"
          pkcs8:
            path: "/var/lib/icinga2/certs/{{ ansible_fqdn }}.der"
          pem:
            cert: "/var/lib/icinga2/certs/{{ ansible_fqdn }}.crt"
        local_ca_ca:
          cert: "/var/lib/icinga2/certs/ca.crt"
```

which would upload the CA and generate a dual-use certificate with both the
unqualified and the fully qualified hostname and all IPv4s included.

## Rationale

### Why do you need this?

Because for some applications (redis+haproxy / kubernetes / icinga) you need
your own CA, because:

* Nodes need client certificates
* The service you use makes excessive use of SNI (ex. one entry for every IP)
* The service you use requires local domains in the certs

All of these things rule out an existing, public CA.

### Why not use Ansible Secrets?

Because I can't find a way to edit them at run time. If you know how to
accomplish this, feel free to simply convert the tar files to secrets (thats why
I tar up things in the first place).

## License

GPLv3 except for ca.template, which simply contains [EasyRSA
v3](https://github.com/OpenVPN/easy-rsa) which in turn is released under the
GPLv2.
