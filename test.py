from coverage import Coverage

from app.tests import run

cov = Coverage(config_file="coverage/.coveragerc")
cov.start()

run()

cov.stop()
cov.html_report()