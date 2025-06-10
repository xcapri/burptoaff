from setuptools import setup, find_packages

setup(
    name='burptoaff',
    version='0.1',
    packages=find_packages(), 
    entry_points={
        'console_scripts': [
            'burptoaff = burptoaff.__main__:main'
        ]
    },
    author='Your Name',
    description='CLI tool to convert BurpSuite XML to Affected HTTP request list.',
    python_requires='>=3.6',
)
