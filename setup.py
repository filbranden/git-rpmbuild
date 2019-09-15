from setuptools import setup

with open('README.md') as fh:
    long_description = fh.read()

setup(
    name='git-rpmbuild',
    version='0.1',
    author='Filipe Brandenburger',
    author_email='filbranden@gmail.com',
    url='https://github.com/filbranden/git-rpmbuild',
    description='Build RPM packages from Development Trees',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='GPLv2',
    license_file='LICENSE',
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Version Control :: Git',
    ],
    scripts=['git-rpmbuild'],
)
