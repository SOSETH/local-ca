import os
import testinfra.utils.ansible_runner
from cryptography import x509
from cryptography.hazmat._oid import ObjectIdentifier
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.x509.extensions import ExtendedKeyUsage

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


# Check whether all files have been created at all
def test_file_creation(host):
    files = ['/tmp/ca.crt', '/tmp/dual.crt', '/tmp/dual.key', '/tmp/server.crt', '/tmp/server.key',
             '/tmp/client.crt', '/tmp/client.key']
    for item in files:
        f = host.file(item)
        assert f.exists
        assert f.user == 'root'
        assert f.group == 'root'


# Check whether the file contents are syntactically valid
def test_file_validity(host):
    certificates = ['/tmp/ca.crt', '/tmp/dual.crt', '/tmp/client.crt', '/tmp/server.crt']
    for item in certificates:
        contents = host.file(item).content_string.encode('ascii')
        cert = x509.load_pem_x509_certificate(contents, default_backend())
        assert cert.serial_number >= 1
    for item in certificates:
        contents = host.file(item).content_string.encode('ascii')
        cert = x509.load_pem_x509_certificate(contents, default_backend())
        assert cert.serial_number >= 1

    keys = ['/tmp/dual.key', '/tmp/client.key', '/tmp/server.key']
    for item in keys:
        contents = host.file(item).content_string.encode('ascii')
        key = serialization.load_pem_private_key(contents, None, default_backend())
        assert key.key_size == 4096


# Check whether certificates have their intended properties
def test_file_contents(host):
    ca_cert = x509.load_pem_x509_certificate(host.file('/tmp/ca.crt').content_string.encode('ascii'),
                                             default_backend()).public_key()
    certificates = [
        {
            'cert': '/tmp/dual.crt',
            'key': '/tmp/dual.key',
            'ekus': ['1.3.6.1.5.5.7.3.1', '1.3.6.1.5.5.7.3.2'],  # Both server and client authentication
        },
        {
            'cert': '/tmp/server.crt',
            'key': '/tmp/server.key',
            'ekus': ['1.3.6.1.5.5.7.3.1'],  # server authentication
        },

        {
            'cert': '/tmp/client.crt',
            'key': '/tmp/client.key',
            'ekus': ['1.3.6.1.5.5.7.3.2'],  # client authentication
        }
    ]

    for item in certificates:
        uut_contents = host.file(item['cert']).content_string.encode('ascii')
        uut = x509.load_pem_x509_certificate(uut_contents, default_backend())

        # Check whether the cert is signed by the CA
        ca_cert.verify(
            uut.signature,
            uut.tbs_certificate_bytes,
            padding.PKCS1v15(),
            uut.signature_hash_algorithm
        )

        # Check extensions
        # OID 2.5.29.37 is extKeyUsage, should be server auth, client auth or both, depending on cert
        extended_key_usage = uut.extensions.get_extension_for_oid(ObjectIdentifier("2.5.29.37"))
        expected_extended_key_usage = ExtendedKeyUsage((map(lambda elem: ObjectIdentifier(elem), item['ekus'])))
        assert extended_key_usage.value == expected_extended_key_usage, \
            "%s does not have expected EKU (actual: %s, expected %s)" % (item['cert'], extended_key_usage.value,
                                                                         expected_extended_key_usage)

        # Check whether key matches cert
        uut_key_contents = host.file(item['key']).content_string.encode('ascii')
        uut_key = serialization.load_pem_private_key(uut_key_contents, None, default_backend())
        pubkeyA = uut_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        pubkeyB = uut.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        assert pubkeyA == pubkeyB
