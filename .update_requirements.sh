#!/bin/sh

echo "Updating requirements.txt and requirements_dev.txt"
pip-compile > requirements.txt
pip-compile requirements_dev.in
sed -ie 's/^--find-links.*//' requirements*.txt

echo Done\!
echo 'You can now run (in bash)'
echo 'pip-sync requirements_dev.txt requirements.txt <(echo -- '-e' . )'
echo to update your local environment
