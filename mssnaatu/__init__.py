"""Project bootstrap.

Django's MySQL backend imports ``MySQLdb``. PyMySQL is a pure-Python drop-in
replacement, which keeps local setup and deployment free of C build tools.
"""

import pymysql

pymysql.version_info = (2, 2, 8, "final", 1)
pymysql.install_as_MySQLdb()
