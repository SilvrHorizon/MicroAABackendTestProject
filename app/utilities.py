import re

# From geeksforgeeks: https://www.geeksforgeeks.org/check-if-email-address-valid-or-not-in-python/
def valid_email(to_check):

    if not isinstance(to_check, str):
        return False

    email_regex = '^[a-zA-Z0-9]+[\._]?[a-zA-Z0-9]+[@]\w+[.]\w{2,3}$'
    if(re.search(email_regex, to_check)):  
        return True
    return False

def valid_password(to_check):
    if not isinstance(to_check, str):
        return False

    if len(to_check) < 1:
        return False
    
    return True