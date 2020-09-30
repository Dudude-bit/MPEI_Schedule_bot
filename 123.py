import yaml

with open('.jobber', 'r') as f:
    yaml = yaml.safe_load(f)
print(yaml)