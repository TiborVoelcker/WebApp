from coverage import Coverage

cov = Coverage(config_file="coverage/.coveragerc")
cov.start()

cov.stop()
cov.html_report()