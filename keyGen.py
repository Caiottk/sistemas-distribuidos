from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import json
 
def generate_keys():
    private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
    )

    private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')   
    return public_pem,private_pem

public_key_dict = {}
private_key_dict = {}

for service in ["moist_sensor","irrigation_system","temperature_sensor","actuators"]:
    public_key, private_key = generate_keys()
    private_key_dict[service] = private_key
    public_key_dict[service] = public_key

with open("public.json", "w") as json_file:
    json.dump(public_key_dict, json_file, indent=4)

with open("private.json", "w") as json_file:
    json.dump(private_key_dict, json_file, indent=4)