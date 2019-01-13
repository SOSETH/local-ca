# local-ca

This role provides a local (i.e. on the node that executes ansible or on some
delegated node) CA.

## Configuration

| Variable name | Default value | Description |
|---------------|---------------|-------------|
| `lca_dhparam_size` | `2048` | Size for generated Diffie-Hellman parameters |
| `lca_is_local` | `True` | Whether the CA is actually "local" or on some remote node |
| `lca_hostname` | undefined | Which host to delegate CA actions to if `lca_is_local` is false |
| `lca_basepath` | undefined | Base directories of CAs on the remote host if `lca_is_local` is false |
| `lca_fetchdir` | `fetch/ctmp` | Where to store secret material on the control node |
| `lca_owner` | `root` | Owner of certificates on the target node |
| `lca_group` | `root` | Group of certificates on the target node |
| `lca_mode` | `0640` | Permissions of certificates on the target node |

## How to use this?

This role has to be called with parameters, like so:

```
  - role: local-ca
    caname: DemoPKI
    <params>
```

where params consists of at least one of the following blocks:

* `server`: Generate a server certificate. Arguments:
  * `cert` (required): path to certificate on target node
  * `key` (required): path to key on target node (unencrypted)
  * `cn` (required): Common Name
  * `san` (optional): SAN in openssl cmdline format.

* `both`: Generate a server certificate that can also be used as a client
  certificate. Parameters are the same as server.

* `ca`: Copy CA certificate to node
  * `cert` (required): destination
  * `crl` (optional): destination for CRL. The CRL gets regenerated each time
    this role is invoked.

* `client`: Generate a client certificate. Arguments:
  * `cert` (required): path to certificate on target node
  * `key` (required): path to key on target node (unencrypted)
  * `cn` (required): Common Name

* `dhparm`: Generate dhparam
  * `dest` (required): destination

All files will be in PEM format.

An example invocation might look like this:

```
  - hosts: mon-server
    roles:
      - role: local-ca
        caname: icinga
        lca_group: nagios
        both:
          cert: "/var/lib/icinga2/certs/{{ ansible_fqdn }}.crt"
          key: "/var/lib/icinga2/certs/{{ ansible_fqdn }}.key"
          cn: "{{ ansible_fqdn }}"
          san: "DNS:{{ ansible_nodename }},DNS:{{ ansible_fqdn }},IP:{{ansible_all_ipv4_addresses|join(',IP:')}},IP:127.0.0.1"
        ca:
          cert: "/var/lib/icinga2/certs/ca.crt"
```

which would upload the CA and generate a dual-use certificate with both the
unqualified and the fully qualified hostname and all IPv4s included.

Before using the role for the first time, you need to extract `ca.template` in
the ca directory (`{{ lca_basepath }}/{{ caname }}` if the CA is remote,
`secrets/pki/{{ caname }}` if it is local).

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
