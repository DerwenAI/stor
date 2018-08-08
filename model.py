#!/usr/bin/env python
# encoding: utf-8

from passlib.context import CryptContext
from passlib.utils import saslprep
import datetime
import json
import os
import sys
import time


######################################################################
## set up

USER_LIST = []

PWD_CONTEXT = CryptContext(
    schemes=["bcrypt_sha256"],
    deprecated="auto",

    # Passlib:
    # Optionally, set the number of rounds that should be used.

    # Appropriate values may vary for different schemes, and the
    # amount of time you wish it to take.

    # Leaving this alone is usually safe, and uses passlib defaults.
    )


######################################################################
## login objects

class User ():
    id = len(USER_LIST) + 1
    email_addr = None
    pwd_hash = None
    active = True
    authenticated = False

    def __repr__ (self):
        return str(self.as_dict())

    def as_dict (self):
        return {
            "id" : self.id,
            "email_addr": self.email_addr
            }

    ## factory methods

    @classmethod
    def from_email (cls, email):
        for user in USER_LIST:
            if user.email_addr == email:
                return user

        return None


    @classmethod
    def from_id (cls, id):
        for user in USER_LIST:
            if user.id == id:
                return user

        return None


    ## managing roles

    def get_roles (self, session):
        return set([])

    ## password management

    def set_password (self, password):
        """throws ValueError if password violates RFC 4013"""
        global PWD_CONTEXT
        self.pwd_hash = PWD_CONTEXT.hash(saslprep(password))

    def check_password (self, password):
        global PWD_CONTEXT
        ## simple auth only, for now
        self.authenticated = PWD_CONTEXT.verify(password, self.pwd_hash)
        return self.authenticated

    ## required for Flask-Login (equiv to `UserMixin`)

    def get_id (self):
        # This method must return a unicode that uniquely identifies
        # this user, and can be used to load the user from the
        # user_loader callback. Note that this must be a unicode - if
        # the ID is natively an int or some other type, you will need
        # to convert it to unicode.
        return self.id

    def is_active (self):
        # This property should return True if this is an active user -
        # in addition to being authenticated, they also have activated
        # their account, not been suspended, or any condition your
        # application has for rejecting an account. Inactive accounts
        # may not log in (without being forced of course).
        return self.active

    def is_anonymous (self):
        # This property should return True if this is an anonymous
        # user. (Actual users should return False instead.)
        return False

    def is_authenticated (self):
        # This property should return True if the user is
        # authenticated, i.e. they have provided valid
        # credentials. (Only authenticated users will fulfill the
        # criteria of login_required.)
        return self.authenticated


def load_users (file_name):
    global USER_LIST

    with open(file_name) as f:
        model = json.load(f)

        for user_data in model["users"]:
            user = User()
            user.email_addr = user_data["email_addr"]
            user.pwd_hash = user_data["pwd_hash"]
            USER_LIST.append(user)


######################################################################
## main

if __name__ == "__main__":
    load_users("users.json")
    print(USER_LIST)
