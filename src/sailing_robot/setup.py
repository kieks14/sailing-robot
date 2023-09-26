from setuptools import setup, find_packages

setup(
    name='sailing_robot',
    version='0.0.1',
    description='The sailing_robot package',
    author='Kiki Bink',
    author_email='kikibinkk@gmail.com',
    url='https://github.com/kikibink/sailing_robot',  # Replace with your project's URL
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        # List your Python dependencies here
        # Example: 'numpy',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.x',
        'Operating System :: OS Independent',
    ],
)