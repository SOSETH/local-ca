# local-ca

This role provides a local (i.e. on the node that executes ansible) CA.

## How to use this?
In your meta/main.yml, you depend on this role, like so:
` - { role: local-ca, caname: <name>, <params> } `

caname is the name of the local ca.
params can be one or more of the following:
* server: Generate a server certificate. Arguments:
	* cert (required): path to certificate on target node (pem)
	* key (required): path to key on target node (pem, unencrypted)
	* cn (required): Common Name
	* san (optional): SAN in openssl cmdline format.
* ca: Copy CA certificate to node
  * cert (required): destination
	* crl (optional): destination for CRL. The CRL gets regenerated each time this role is invoked.
* client: Generate a client certificate. Arguments:
  * cert (required): path to certificate on target node (pem)
	* key (required): path to key on target node (pem, unencrypted)
	* cn (required): Common Name
* dhparm: Generate dhparam on ansible client
	* dest (required): destination(pem)

Example:
` - { role: local-ca, caname: logstash, server: { cert: /etc/haproxy/srv.crt, key: /etc/haproxy/srv.key, cn: {{ansible_nodename}} }, ca: { cert: /etc/haproxy/ca.crt } } `

## Rationale

### Why do you need this?
Because for some applications (redis+haproxy / kubernetes) you need your own CA, because:
* Nodes need client certificates
* The service you use makes excessive use of SNI (ex. one entry for every IP)
* The service you use requires local domains in the certs
All of these things rule out an existing, public CA.

### Why not use Ansible Secrets?
Because I can't find a way to edit them at run time. If you know how to accomplish this, feel free to simply convert the tar files to secrets (thats why I tar up things in the first place).

### Why not use debops.pki?
Because they essentially bootstrap a _real_ CA, that is a node that handles the CA stuff. They then move certificate requests and certificates between nodes. On the bright side, one could argue that they're doing it *the right way* - private keys are generated on each node and never leave them. On the other hand, entropy on a freshly set up node is something to be worried about and having a dedicated CA node seems like a bit of a hassle to me...
