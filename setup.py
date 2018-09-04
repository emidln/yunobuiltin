from distutils.core import setup


def readme():
    with open('README.rst') as f:
        return f.read()

version = '1.0.0'

setup(name='yunobuiltin',
      version=version,
      description='Misc Utility Functions that should be builtin',
      long_description=readme(),
      author='Brandon Adams',
      author_email='emidln@gmail.com',
      license='Eclipse Public License 2.0',
      url='https://github.com/emidln/yunobuiltin',
      py_modules=['yunobuiltin'])
