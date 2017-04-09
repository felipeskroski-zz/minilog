## Minimum - a Python's minimalist catalog system

A minimalist catalog with full secure authentication and file management

## Requirements
1. Python 2.7
2. sqlite
3. Flask
4. bcrypt
5. functools
6. werkzeug.utils
7. flask_wtf
8. flask_sqlalchemy

You can install the dependencies using pip, example:
```
pip install flask
```

## Install and run
1. Clone this git repo

2. Change the secret in config.py for security in the config file

3. Install the sqlite database
  ```
  export FLASK_APP=minilog
  export FLASK_DEBUG=1
  flask initdb
  ```

4. _Optional_ Populate the database with dummy data
  ```
  export FLASK_APP=minilog
  export FLASK_DEBUG=1
  flask populatedb
  ```
  If you have errors here start again from step 3

5. Run this project locally from the command line

   ```
   export FLASK_APP=minilog
   export FLASK_DEBUG=1
   flask run
   ```
6. Login using the dummy user credentials **Delete this user in production**

  ```
  email: admin@example.com
  password: password
  ```


### Feedback
Star this repo if you found it useful. Use the github issue tracker to give
feedback on this repo.

## Licensing
See [LICENSE](LICENSE)

## Author
Felipe Skroski