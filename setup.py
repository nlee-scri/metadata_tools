from setuptools import setup, find_packages

VERSION = '0.0.1' 
DESCRIPTION = 'Data Processing Tools'
LONG_DESCRIPTION = 'Data processing tools to move files between data repositories'

# Setting up
setup(
       # the name must match the folder name 'verysimplemodule'
        name="data_processing_tools", 
        version=VERSION,
        author="Nicholas Lee",
        author_email="nicholas.lee@seattlechildrens.org",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=["python-dotenv"], # add any additional packages that 
        # needs to be installed along with your package. Eg: 'caer'

        keywords=['python', 'data processing'],
        
        classifiers= [
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Professionals",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 3",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
        ]
)