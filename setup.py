from setuptools import setup
import amazon_advertising_api.versions as aa_versions


setup(
    name='amazon_advertising_api_v3',
    packages=['amazon_advertising_api_v3'],
    version=aa_versions.versions['application_version'],
    description='Unofficial Amazon Sponsored Products Python client library.',
    url='https://github.com/PPCNinja/amazon-advertising-api-python')
